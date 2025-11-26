import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib.parse
import pandas as pd
import wikipediaapi
import regex as re
import spacy
import os
import json
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from pymongo import MongoClient
import random
import time

# Load environment variables
load_dotenv()

# Initialize spacy for Spanish language processing
try:
    nlp = spacy.load("es_core_news_sm")
except OSError:
    print("Modelo de Spacy no encontrado. Descargando...")
    from spacy.cli import download
    download("es_core_news_sm")
    nlp = spacy.load("es_core_news_sm")

# Configurar Hugging Face
huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
if not huggingface_api_key:
    raise ValueError("HUGGINGFACE_API_KEY no está configurada en las variables de entorno.")

# RECOMENDACIÓN: Usar Llama 3.1 si es posible
model = os.getenv('HUGGINGFACE_MODEL_NAME', 'meta-llama/Llama-3.1-8B-Instruct')

client = InferenceClient(model=model, token=huggingface_api_key)

# MongoDB configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/spygame')

def get_db_connection():
    """Establish connection to MongoDB"""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.admin.command('ping')
        db = client.spygame
        return db, True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return None, False

def get_wikidata_items(limit=150, offset=None, min_sitelinks=200, sample_size=1):
    if offset is None:
        offset = random.randint(0, 1000)
    
    url = "https://query.wikidata.org/sparql"
    query = f"""
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX schema: <http://schema.org/>

    SELECT ?person ?esArticle ?count
    WHERE {{
      ?person wdt:P31 wd:Q5 .
      ?person wikibase:sitelinks ?count .
      FILTER(?count > {int(min_sitelinks)})

      ?esArticle schema:about ?person ;
                 schema:isPartOf <https://es.wikipedia.org/> .
    }}
    LIMIT {int(limit)} OFFSET {int(offset)}
    """
    
    user_agent = os.getenv('WIKIPEDIA_USER_AGENT', 'SpyGame/1.0.0 (contact: user@example.com)')
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": user_agent
    }
    params = {"query": query, "format": "json"}

    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)

    try:
        r = session.get(url, params=params, headers=headers, timeout=(10, 60))
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Error obteniendo datos de Wikidata: {e}")
        return pd.DataFrame()

    bindings = data.get("results", {}).get("bindings", [])
    
    if len(bindings) > sample_size:
        bindings = random.sample(bindings, sample_size)
    
    results = []
    for item in bindings:
        results.append({
            "id": item["person"]["value"].replace("http://www.wikidata.org/entity/", ""),
            "articulo_es": item["esArticle"]["value"],
            "sitelinks": int(item.get("count", {}).get("value", 0)),
        })

    return pd.DataFrame(results)

def limpiar_texto(texto):
    # Quitar referencias [1], [2]...
    texto = re.sub(r'\[\d+\]', '', texto)
    # Quitar contenido entre paréntesis si es muy corto (aclaraciones)
    # texto = re.sub(r'\([^)]*\)', '', texto) # A veces quita info útil, cuidado aquí
    # Normalizar espacios
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

def generar_prompt_trivia(url, nombre_persona):
    """
    Genera el prompt manteniendo la estructura formal original del usuario,
    pero añadiendo reglas gramaticales estrictas para evitar repeticiones.
    """
    # 1. Obtener datos de Wikipedia
    titulo_codificado = url.split("/wiki/")[-1]
    titulo = urllib.parse.unquote(titulo_codificado).replace('_', ' ')
    
    user_agent = os.getenv('WIKIPEDIA_USER_AGENT', 'SpyGame/1.0')
    wiki_es = wikipediaapi.Wikipedia(language='es', user_agent=user_agent)
    articulo = wiki_es.page(titulo)
    
    if not articulo.exists():
        raise ValueError("El artículo no existe.")

    # Resumen + primeras secciones
    texto_base = articulo.summary
    for section in articulo.sections[:6]:
        texto_base += " " + section.text
    
    texto_limpio = limpiar_texto(texto_base)

    # 2. Procesamiento con SpaCy
    doc = nlp(texto_limpio)
    frases_candidatas = []
    nombre_tokens = nombre_persona.lower().split()

    for i, sent in enumerate(doc.sents):
        s_text = sent.text.strip()
        if len(s_text.split()) < 6 or len(s_text.split()) > 80: continue
            
        score = 0
        entidades = [ent.label_ for ent in sent.ents]
        
        if "DATE" in entidades: score += 2
        if "LOC" in entidades: score += 1
        if "ORG" in entidades: score += 1
        
        found_ref = False
        for token in sent:
            if token.dep_ == "nsubj":
                if token.pos_ == "PRON": score += 1; found_ref = True
                elif token.text.lower() in nombre_tokens: score += 2; found_ref = True
        
        if not found_ref and sent[0].pos_ == "VERB": score += 1

        if score >= 1:
            frases_candidatas.append({"index": i, "texto": s_text, "score": score})

    # 3. Selección y orden cronológico
    frases_candidatas.sort(key=lambda x: x["score"], reverse=True)
    seleccion = frases_candidatas[:25]
    seleccion.sort(key=lambda x: x["index"])
    texto_contexto = " ".join([item["texto"] for item in seleccion])

    # 4. PROMPT FORMAL (Tu estilo original, reglas mejoradas)
    prompt = f"""
Eres un experto redactor de contenido para juegos de trivia cultural.
Recibirás un texto biográfico y deberás generar 8 pistas de adivinanza.

REGLAS CRÍTICAS DE REDACCIÓN:

1. **ANONIMATO ABSOLUTO:** NO menciones el nombre "{nombre_persona}", ni apodos, ni variantes. Refiérete al sujeto de forma implícita.

2. **USO DEL SUJETO TÁCITO:** En español es incorrecto y antinatural repetir constantemente el sujeto.
   - **PROHIBIDO:** Empezar las frases con "Esta persona", "Este científico", "La figura", "El político".
   - **OBLIGATORIO:** Empieza las oraciones directamente con el verbo conjugado o con complementos circunstanciales.
     *Ejemplo correcto:* "Escribió su obra maestra en..." (En lugar de "Esta persona escribió...")
     *Ejemplo correcto:* "Durante su exilio, aprendió a..." (En lugar de "La figura aprendió a...")

3. **VARIEDAD LÉXICA:** No utilices la misma estructura gramatical en dos pistas seguidas. Varía el inicio de las oraciones.

4. **CONTENIDO REAL:** Básate ÚNICAMENTE en el texto proporcionado abajo. No inventes información externa.

5. **JERARQUÍA DE DIFICULTAD:**
   - **Dificultad 5 (MUY DIFÍCIL):** Detalles curiosos del final de su vida, lugar de entierro o hechos muy específicos. No menciones la nacionalidad aquí.
   - **Dificultad 4 (DIFÍCIL):** Logros secundarios o específicos.
   - **Dificultad 3 (MEDIA):** Obras principales o hitos de carrera.
   - **Dificultad 2 (FÁCIL):** Datos biográficos de origen, estudios o familia.
   - **Dificultad 1 (MUY FÁCIL):** Resumen general de su profesión y legado (aquí puedes mencionar la nacionalidad).

Formato de salida (JSON válido estrictamente):

{{
  "pistas": [
    {{"dificultad": 5, "pista": "..."}},
    {{"dificultad": 4, "pista": "..."}},
    {{"dificultad": 3, "pista": "..."}},
    {{"dificultad": 3, "pista": "..."}},
    {{"dificultad": 2, "pista": "..."}},
    {{"dificultad": 2, "pista": "..."}},
    {{"dificultad": 1, "pista": "..."}},
    {{"dificultad": 1, "pista": "..."}}
  ]
}}

Texto de la biografía:
"{texto_contexto}"
"""
    return prompt

def generar_pistas(url, nombre_persona):
    """
    Genera pistas de trivia usando Hugging Face.
    """
    try:
        prompt_content = generar_prompt_trivia(url, nombre_persona)
        
        messages = [
            {"role": "system", "content": "Eres un asistente estricto que genera JSON basado solo en el texto provisto."},
            {"role": "user", "content": prompt_content}
        ]
        
        response = client.chat_completion(
            messages=messages,
            model=model,
            max_tokens=1000,
            temperature=0.2, # Baja temperatura para evitar invenciones
            response_format={"type": "json_object"} # Fuerza salida JSON (Soportado en Llama 3)
        )

        output = response.choices[0].message.content.strip()

        # Parseo robusto del JSON
        try:
            data = json.loads(output)
            # Manejar si el modelo devuelve una lista directa o un objeto con clave "pistas"
            if isinstance(data, list):
                return data
            elif "pistas" in data:
                return data["pistas"]
            else:
                # Intento de rescate si devuelve un dict raro
                return list(data.values())[0] if data else []
                
        except json.JSONDecodeError:
            print("Error: El modelo no devolvió un JSON válido.")
            # Fallback simple con regex si falla el json puro
            import re
            match = re.search(r'\[.*\]', output, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return None

    except Exception as e:
        print(f"Error al generar pistas con Hugging Face: {e}")
        return None

def guardar_pistas_json(pistas, nombre_persona, wikidata_id=None, url_wikipedia=None, filepath="pistas.json"):
    if not pistas: return

    timestamp = pd.Timestamp.now().isoformat()
    datos = {
        "nombre": nombre_persona,
        "pistas": pistas,
        "wikidata_id": wikidata_id,
        "url_wikipedia": url_wikipedia,
        "ultima_actualizacion": timestamp
    }
    
    lista_actual = []
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lista_actual = json.load(f)
                if not isinstance(lista_actual, list): lista_actual = [lista_actual]
        except:
            lista_actual = []
    
    lista_actual.append(datos)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(lista_actual, f, indent=4, ensure_ascii=False)
    print(f"Guardado localmente: {nombre_persona}")

def subir_pistas_a_db(pistas, nombre_persona, wikidata_id=None, url_wikipedia=None):
    if not pistas: return False

    db, mongodb_available = get_db_connection()
    if not mongodb_available: return False
    
    try:
        pistas_collection = db.pistas
        filtro = {"nombre": nombre_persona} # Idealmente usar wikidata_id si es único
        if wikidata_id:
            filtro = {"wikidata_id": wikidata_id}

        datos_actualizar = {
            "$set": {
                "nombre": nombre_persona,
                "pistas": pistas,
                "ultima_actualizacion": pd.Timestamp.now().isoformat(),
                "url_wikipedia": url_wikipedia,
                "wikidata_id": wikidata_id
            },
            "$setOnInsert": {
                "fecha_creacion": pd.Timestamp.now().isoformat()
            }
        }
        
        result = pistas_collection.update_one(filtro, datos_actualizar, upsert=True)
        if result.upserted_id:
            print(f" [DB] Nueva entrada: {nombre_persona}")
        else:
            print(f" [DB] Actualizado: {nombre_persona}")
            
        return True
    except Exception as e:
        print(f"Error MongoDB: {e}")
        return False

def procesar_batch(num_personas=5, limit=200, offset=0, min_sitelinks=150):
    print(f"\n{'='*60}")
    print(f"Iniciando procesamiento: {num_personas} personas (Offset: {offset})")
    print(f"{'='*60}\n")
    
    df = get_wikidata_items(limit=limit, offset=offset, min_sitelinks=min_sitelinks, sample_size=num_personas)
    
    if df.empty:
        print("No se encontraron resultados en Wikidata.")
        return
    
    exitosas = 0
    
    for idx, row in df.iterrows():
        url = row['articulo_es']
        wikidata_id = row['id']
        nombre_raw = url.split("/wiki/")[-1]
        nombre_persona = urllib.parse.unquote(nombre_raw).replace("_", " ")
        
        print(f"[{idx+1}/{len(df)}] {nombre_persona}...")
        
        pistas = generar_pistas(url, nombre_persona)
        
        if pistas:
            guardar_pistas_json(pistas, nombre_persona, wikidata_id, url)
            subir_pistas_a_db(pistas, nombre_persona, wikidata_id, url)
            exitosas += 1
        else:
            print(f" -> Fallo generando pistas para {nombre_persona}")
            
        time.sleep(1) # Respetar límites de API

    print(f"\nResumen: {exitosas} procesadas correctamente de {len(df)}.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--num', type=int, default=5)
    parser.add_argument('--limit', type=int, default=200)
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--min-sitelinks', type=int, default=150)
    
    args = parser.parse_args()
    
    procesar_batch(
        num_personas=args.num,
        limit=args.limit,
        offset=args.offset,
        min_sitelinks=args.min_sitelinks
    )