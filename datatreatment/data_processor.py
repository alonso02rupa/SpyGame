import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
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

# Load environment variables
load_dotenv()

# Initialize spacy for Spanish language processing
nlp = spacy.load("es_core_news_sm")

# Hugging Face API configuration
huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
if not huggingface_api_key:
    raise ValueError("HUGGINGFACE_API_KEY no está configurada en las variables de entorno.")

client = InferenceClient(token=huggingface_api_key)
model = os.getenv('HUGGINGFACE_MODEL_NAME')
if not model:
    raise ValueError("Configura un modelo de Hugging Face en las variables de entorno.")

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

def get_wikidata_items(limit=200 , offset=0, min_sitelinks=150, sample_size=1):
    """
    Devuelve personas (Q5) con artículo en Wikipedia en español y con un número minimo de traducciones (sitelinks).
    como un DataFrame de pandas.
    Parámetros:
    - limit: número máximo de resultados a devolver desde Wikidata.
    - offset: número de resultados a saltar (para paginación).
    - min_sitelinks: número mínimo de traducciones (sitelinks) que debe tener la persona.
    - sample_size: número de resultados aleatorios a seleccionar del bloque descargado.
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
    data = r.json()

    bindings = data.get("results", {}).get("bindings", [])
    
    # Selección aleatoria de elementos para poder cargar más personas, lo hago limitado por los tokens de huggingface
    if len(bindings) > sample_size:
        bindings = random.sample(bindings, sample_size)
    
    results = []
    for item in bindings:
        results.append({
            "id": item["person"]["value"].replace("http://www.wikidata.org/entity/", ""),
            "articulo_es": item["esArticle"]["value"],
            "sitelinks": int(item.get("count", {}).get("value", 0)),
        })

    # Convertir a DataFrame
    df = pd.DataFrame(results)
    return df

def limpiar_texto(texto):
    # Quitar referencias y paréntesis
    texto = re.sub(r'\[\d+\]', '', texto)
    texto = re.sub(r'\([^)]*\)', '', texto)
    # Normalizar saltos de línea y espacios
    texto = re.sub(r'\n+', ' ', texto)
    texto = re.sub(r'\s{2,}', ' ', texto)
    # Corregir errores típicos de OCR o escritura
    texto = re.sub(r'\bdiirección\b', 'dirección', texto)
    texto = re.sub(r'\bjuggaron\b', 'jugaron', texto)
    texto = re.sub(r'\bquue\b', 'que', texto)
    texto = re.sub(r'\ba\s\s\b', 'a ', texto)
    return texto.strip()

def generar_frases_trivia(url, nombre_persona):
    titulo = url.split("/wiki/")[-1]
    user_agent = os.getenv('WIKIPEDIA_USER_AGENT', 'App/1.0 (contact: user@example.com)')
    wiki_es = wikipediaapi.Wikipedia(language='es', user_agent=user_agent)
    articulo = wiki_es.page(titulo)
    if not articulo.exists():
        raise ValueError("El artículo no existe.")

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
        if len(s.split()) < 5:  # frase demasiado corta
            continue

        # Detectamos entidades importantes
        entidades_en_frase = [ent.text for ent in sent.ents if ent.label_ in ["PER","LOC","ORG","DATE"]]
        if not entidades_en_frase:
            continue

        # Evitar repeticiones de la misma entidad
        if any(ent.lower() in entidades_vistas for ent in entidades_en_frase):
            continue
        entidades_vistas.update([ent.lower() for ent in entidades_en_frase])

        # Guardar frase completa y legible
        frases.append(s)

    # Limitar número de frases
    frases_lista = frases[:12]
    
    # Limpiar puntos y comas justo antes del prompt para ahorrar tokens
    frases_sin_puntuacion = [re.sub(r'[.,]', '', frase) for frase in frases_lista]

    # Crear prompt
    prompt = f"""
Eres un asistente experto en generar pistas de trivia a partir de biografías. 
Recibirás un texto con información sobre la vida de una persona. 

REGLAS CRÍTICAS QUE DEBES SEGUIR:

1. **PROHIBIDO ABSOLUTO:** NO menciones NUNCA el nombre, apellido, apodos, títulos nobiliarios, ni cualquier variante del nombre de la persona. Refiérete a ella SIEMPRE en tercera persona de forma genérica ("esta persona", "este científico", "esta figura histórica", etc.).

2. **PROHIBIDO:** NO uses fechas exactas de nacimiento o muerte, números específicos de premios, cifras exactas, ni datos únicos que identifiquen a la persona inmediatamente.

3. Cada pista debe tener un campo "dificultad" (1 a 5):
   
   **Dificultad 5 (MUY DIFÍCIL):** Hechos muy específicos, detalles históricos poco conocidos, anécdotas raras.
   Ejemplo: "Recibió sepultura con honores en un lugar reservado solo a figuras excepcionales de la nación"
   
   **Dificultad 4 (DIFÍCIL):** Detalles importantes pero menos conocidos, contribuciones específicas.
   Ejemplo: "Nombró un elemento químico en honor a su país natal"
   
   **Dificultad 3 (MEDIA):** Logros importantes que requieren conocimiento del área.
   Ejemplo: "Realizó estudios pioneros sobre fenómenos radiactivos"
   
   **Dificultad 2 (FÁCIL):** Información general conocida, premios importantes, instituciones.
   Ejemplo: "Trabajó en una prestigiosa universidad europea durante gran parte de su carrera"
   
   **Dificultad 1 (MUY FÁCIL):** Información muy general: profesión, nacionalidad, campo de actividad.
   Ejemplo: "Fue una científica reconocida a nivel mundial" o "Se destacó en el campo de las ciencias físicas"

4. Genera **8 pistas en total** distribuidas así: 1 de dificultad 5, 1 de dificultad 4, 2 de dificultad 3, 2 de dificultad 2, 2 de dificultad 1.

5. **ORDEN OBLIGATORIO:** Las pistas deben estar ordenadas de MAYOR a MENOR dificultad (5 → 4 → 3 → 3 → 2 → 2 → 1 → 1).

6. Usa lenguaje variado: no empieces todas las pistas igual.

7. Devuelve SOLO JSON válido, sin comentarios ni texto adicional.

Formato de salida (OBLIGATORIO):

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

Texto de la biografía:

"{"; ".join(frases_sin_puntuacion)}"
"""

    return prompt

def generar_pistas(url, nombre_persona):
    """
    Genera pistas de trivia para una persona dada su URL de Wikipedia.
    Devuelve las pistas en formato JSON.
    """
    prompt = generar_frases_trivia(url, nombre_persona)
    
    messages = [
        {"role": "system", "content": "Eres un asistente experto en generar pistas de trivia. NUNCA menciones nombres propios de la persona en las pistas. Sigue las instrucciones AL PIE DE LA LETRA."},
        {"role": "user", "content": prompt}
    ]
    
    response = client.chat_completion(
        messages=messages,
        model=model,
        max_tokens=800,
        temperature=0.5
    )
    
    output = response.choices[0].message.content
    
    # Intentar parsear el JSON
    try:
        pistas = json.loads(output)
    except:
        # si no está limpio, lo guardamos como texto bruto
        pistas = {"raw_response": output}
    
    return pistas

def guardar_pistas_json(pistas, nombre_persona, filepath="pistas.json"):
    """
    Guarda las pistas en un archivo JSON local.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(pistas, f, indent=4, ensure_ascii=False)
    print(f"Guardado {nombre_persona} en {filepath}")

def subir_pistas_a_db(pistas, nombre_persona, wikidata_id=None, url_wikipedia=None):
    """
    Sube las pistas generadas a la base de datos MongoDB.
    
    Parámetros:
    - pistas: Lista de diccionarios con las pistas generadas
    - nombre_persona: Nombre de la persona
    - wikidata_id: ID de Wikidata (opcional)
    - url_wikipedia: URL del artículo de Wikipedia (opcional)
    """
    db, mongodb_available = get_db_connection()
    
    if not mongodb_available:
        print("No se pudo conectar a MongoDB.")
        return False
    
    try:
        # Preparar documento para la base de datos
        documento = {
            "nombre": nombre_persona,
            "pistas": pistas,
            "fecha_creacion": pd.Timestamp.now().isoformat()
        }
        
        if wikidata_id:
            documento["wikidata_id"] = wikidata_id
        
        if url_wikipedia:
            documento["url_wikipedia"] = url_wikipedia
        
        # Insertar en la colección de hints
        hints_collection = db.hints
        result = hints_collection.insert_one(documento)
        return True
        
    except Exception as e:
        return False

def procesar_persona(url, wikidata_id=None, guardar_json=False, subir_db=True):
    """
    Función completa que procesa una persona: genera pistas y las guarda.
    
    Parámetros:
    - url: URL de Wikipedia de la persona
    - nombre_persona: Nombre de la persona (opcional, se extrae de la URL si no se provee)
    - wikidata_id: ID de Wikidata (opcional)
    - guardar_json: Si es True, guarda las pistas en un archivo JSON local
    - subir_db: Si es True, sube las pistas a la base de datos MongoDB
    """
    nombre_persona = url.split("/wiki/")[-1].replace("_", " ")
    
    print(f"Procesando: {nombre_persona}")
    
    # Generar pistas
    pistas = generar_pistas(url, nombre_persona)
    
    # Guardar en JSON si se solicita
    if guardar_json:
        guardar_pistas_json(pistas, nombre_persona)
    
    # Subir a la base de datos si se solicita
    if subir_db:
        subir_pistas_a_db(pistas, nombre_persona, wikidata_id, url)
    
    return pistas

# USO
df = get_wikidata_items()
enlaces = df['articulo_es'].tolist()  # Tomamos los enlaces
for enlace in enlaces:  
    procesar_persona(enlace)  # Pasamos las personas una a una 





