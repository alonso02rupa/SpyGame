"""
Script para procesar personas de Wikipedia y generar pistas usando Hugging Face API.
Guarda los resultados en pistas.json para luego importarlos a MongoDB.

Uso:
    python datatreatment/process_local.py --num 10 --min-sitelinks 200
"""

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
import random
import time

load_dotenv()

try:
    nlp = spacy.load("es_core_news_sm")
except OSError:
    print("Modelo spaCy 'es_core_news_sm' no encontrado.")
    print("Instálalo con: python -m spacy download es_core_news_sm")
    exit(1)


huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
if not huggingface_api_key:
    raise ValueError("HUGGINGFACE_API_KEY no está configurada en las variables de entorno.")

model = os.getenv('HUGGINGFACE_MODEL_NAME', 'mistralai/Mistral-7B-Instruct-v0.3')
client = InferenceClient(model=model, token=huggingface_api_key)


def get_wikidata_items(limit=150, offset=0, min_sitelinks=200, sample_size=1):
    """
    Devuelve personas (Q5) con artículo en Wikipedia en español.
    """
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
        total=2,
        connect=2,
        read=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    r = session.get(url, params=params, headers=headers, timeout=(10, 60))
    r.raise_for_status()
    
    text = r.content.decode('utf-8', errors='replace')
    data = json.loads(text, strict=False)
    bindings = data.get("results", {}).get("bindings", [])
    
    # Selección aleatoria
    if len(bindings) > sample_size:
        bindings = random.sample(bindings, sample_size)
    
    results = []
    for item in bindings:
        results.append({
            "id": item["person"]["value"].replace("http://www.wikidata.org/entity/", ""),
            "articulo_es": item["esArticle"]["value"],
            "sitelinks": int(item.get("count", {}).get("value", 0)),
        })

    df = pd.DataFrame(results)
    return df


def limpiar_texto(texto):
    """Limpia el texto de referencias y caracteres innecesarios"""
    texto = re.sub(r'\[\d+\]', '', texto)
    texto = re.sub(r'\([^)]*\)', '', texto)
    texto = re.sub(r'\n+', ' ', texto)
    texto = re.sub(r'\s{2,}', ' ', texto)
    texto = re.sub(r'\bdiirección\b', 'dirección', texto)
    texto = re.sub(r'\bjuggaron\b', 'jugaron', texto)
    texto = re.sub(r'\bquue\b', 'que', texto)
    texto = re.sub(r'\ba\s\s\b', 'a ', texto)
    return texto.strip()


def extraer_frases_biografia(url, nombre_persona):
    """Extrae frases relevantes de la biografía de Wikipedia"""
    titulo_codificado = url.split("/wiki/")[-1]
    titulo = urllib.parse.unquote(titulo_codificado)
    titulo = titulo.replace('_', ' ')
    
    user_agent = os.getenv('WIKIPEDIA_USER_AGENT', 'App/1.0 (contact: user@example.com)')
    wiki_es = wikipediaapi.Wikipedia(language='es', user_agent=user_agent)
    articulo = wiki_es.page(titulo)
    
    if not articulo.exists():
        raise ValueError(f"El artículo no existe: {titulo}")

    # Resumen + primeras secciones
    texto_base = articulo.summary
    for section in articulo.sections[:3]:
        texto_base += " " + section.text
    texto_limpio = limpiar_texto(texto_base)

    doc = nlp(texto_limpio)

    frases = []
    entidades_vistas = set()

    for sent in doc.sents:
        s = sent.text.strip()
        if len(s.split()) < 5:
            continue

        entidades_en_frase = [ent.text for ent in sent.ents if ent.label_ in ["PER","LOC","ORG","DATE"]]
        if not entidades_en_frase:
            continue

        if any(ent.lower() in entidades_vistas for ent in entidades_en_frase):
            continue
        entidades_vistas.update([ent.lower() for ent in entidades_en_frase])

        frases.append(s)

    # Limitar número de frases
    frases_lista = frases[:12]
    
    # Limpiar puntos y comas para ahorrar tokens
    frases_sin_puntuacion = [re.sub(r'[.,]', '', frase) for frase in frases_lista]
    
    return frases_sin_puntuacion


def crear_prompt(frases_biografia):
    """Crea el prompt para el modelo"""
    prompt = f"""Eres un generador profesional de pistas de trivia basadas estrictamente en la biografía proporcionada.
Debes producir pistas claras, factuales y NO inventadas.

REGLAS OBLIGATORIAS (MODO ESTRICTO):
1. PROHIBIDO mencionar nombres, apellidos, alias, gentilicios derivados del nombre o referencias directas a la identidad.
2. PROHIBIDO usar fechas exactas, años, días, siglos concretos, números de premios o cantidades identificables.
3. SOLO puedes usar información contenida en la biografía. NO inventes datos.
4. Si una regla entra en conflicto con otra, prioriza SIEMPRE las reglas de prohibición (1-3).
5. Genera 8 pistas con estas dificultades:
   - 1 pista de dificultad 5 (muy difícil)
   - 1 pista de dificultad 4
   - 2 pistas de dificultad 3
   - 2 pistas de dificultad 2
   - 2 pistas de dificultad 1
6. Las pistas deben estar ORDENADAS: 5 → 4 → 3 → 3 → 2 → 2 → 1 → 1.
7. Usa lenguaje variado. No repitas estructuras. No copies frases textuales.
8. No generes pistas redundantes ni contradictorias.
9. Devuelve EXCLUSIVAMENTE un JSON válido. Sin comas finales, sin comentarios, sin texto fuera del array.

EJEMPLO DE SALIDA CORRECTA (FORMATO):
[
  {{"dificultad": 5, "pista": "..." }},
  {{"dificultad": 4, "pista": "..." }},
  {{"dificultad": 3, "pista": "..." }},
  {{"dificultad": 3, "pista": "..." }},
  {{"dificultad": 2, "pista": "..." }},
  {{"dificultad": 2, "pista": "..." }},
  {{"dificultad": 1, "pista": "..." }},
  {{"dificultad": 1, "pista": "..." }}
]

EJEMPLO DE SALIDA INCORRECTA (NUNCA HAGAS ESTO):
"Aquí tienes el JSON..."
{ "respuesta": "..." }
Nombres reales, fechas exactas o datos inventados.

BIOGRAFÍA A ANALIZAR:
"{"; ".join(frases_biografia)}"

Responde SOLO con el JSON, sin texto adicional.
"""
    return prompt



def generar_pistas_local(url, nombre_persona):
    """
    Genera pistas usando Hugging Face API.
    """
    try:
        frases = extraer_frases_biografia(url, nombre_persona)
        
        if not frases:
            print(f"No se encontraron frases relevantes para {nombre_persona}")
            return None
        
        prompt = crear_prompt(frases)
        
        print(f"Generando pistas para {nombre_persona}...")
        
        messages = [
            {"role": "system", "content": "Eres un asistente experto en generar pistas de trivia. NUNCA menciones nombres propios de la persona en las pistas. Sigue las instrucciones AL PIE DE LA LETRA."},
            {"role": "user", "content": prompt}
        ]
        
        response = client.chat_completion(
    model=model,
    messages=messages,
    temperature=0.2,         
    max_tokens=700,
    top_p=0.9,
    frequency_penalty=0,
    presence_penalty=0
)
        output = response.choices[0].message.content.strip()

        try:
            json_match = re.search(r'\[.*\]', output, re.DOTALL)
            if json_match:
                pistas = json.loads(json_match.group(0))
            else:
                pistas = json.loads(output)
            
            if isinstance(pistas, list) and len(pistas) > 0:
                return pistas
            else:
                return {"raw_response": output}
                
        except json.JSONDecodeError:
            print(f"No se pudo parsear JSON. Respuesta: {output[:200]}...")
            return {"raw_response": output}
    
    except Exception as e:
        print(f"Error al generar pistas: {e}")
        return None


def cargar_pistas_existentes(filepath="pistas.json"):
    """Carga las pistas existentes desde el archivo JSON"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Si el archivo tiene una lista, convertirlo a dict
                if isinstance(data, list):
                    return {}
                return data
        except:
            return {}
    return {}


def guardar_pistas_json(todas_las_pistas, filepath="pistas.json"):
    """
    Guarda todas las pistas en un archivo JSON.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(todas_las_pistas, f, indent=2, ensure_ascii=False)


def procesar_batch_local(num_personas=5, limit=200, offset=0, min_sitelinks=150, output_file="pistas.json"):
    """
    Procesa un lote de personas usando Hugging Face API y guarda en JSON.
    """
    print(f"\nProcesamiento de {num_personas} personas")
    print(f"Modelo: {model}")
    print(f"Archivo de salida: {output_file}\n")
    
    todas_las_pistas = cargar_pistas_existentes(output_file)
    print(f"Cargadas {len(todas_las_pistas)} personas existentes\n")
    
    print(f"Buscando personas en Wikidata...")
    df = get_wikidata_items(limit=limit, offset=offset, 
                           min_sitelinks=min_sitelinks, sample_size=num_personas)
    
    if df.empty:
        print("No se encontraron personas en Wikidata")
        return
    
    print(f"Encontradas {len(df)} personas\n")
    
    exitosas = 0
    fallidas = 0
    saltadas = 0
    
    for idx, row in df.iterrows():
        url = row['articulo_es']
        wikidata_id = row['id']
        
        titulo_codificado = url.split("/wiki/")[-1]
        nombre_persona = urllib.parse.unquote(titulo_codificado.replace("_", " "))
        
        print(f"[{idx+1}/{len(df)}] {nombre_persona}")
        
        if nombre_persona in todas_las_pistas:
            print(f"Ya existe en el archivo, saltando...")
            saltadas += 1
            continue
        
        pistas = generar_pistas_local(url, nombre_persona)
        
        if pistas is not None:
            todas_las_pistas[nombre_persona] = {
                "nombre": nombre_persona,
                "pistas": pistas,
                "url_wikipedia": url,
                "wikidata_id": wikidata_id,
                "sitelinks": int(row['sitelinks']),
                "fecha_creacion": pd.Timestamp.now().isoformat()
            }
            exitosas += 1
            print(f"Pistas generadas exitosamente")
            
            guardar_pistas_json(todas_las_pistas, output_file)
        else:
            fallidas += 1
            print(f"Error al generar pistas")
        
        time.sleep(1)
    
    print(f"\nResumen:")
    print(f"Exitosas: {exitosas}")
    print(f"Fallidas: {fallidas}")
    print(f"Saltadas: {saltadas}")
    print(f"Total en archivo: {len(todas_las_pistas)}")
    print(f"\nArchivo guardado en: {os.path.abspath(output_file)}")
    print(f"Para importar a MongoDB: python init_db.py --from-json {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Procesar personas de Wikipedia y guardar en JSON')
    
    parser.add_argument('--num', type=int, default=5, help='Número de personas a procesar')
    parser.add_argument('--limit', type=int, default=200, help='Límite de resultados de Wikidata')
    parser.add_argument('--offset', type=int, default=0, help='Offset para paginación')
    parser.add_argument('--min-sitelinks', type=int, default=150, help='Mínimo de sitelinks')
    parser.add_argument('--output', type=str, default='pistas.json', help='Archivo de salida JSON')
    
    args = parser.parse_args()
    
    procesar_batch_local(
        num_personas=args.num,
        limit=args.limit,
        offset=args.offset,
        min_sitelinks=args.min_sitelinks,
        output_file=args.output
    )
