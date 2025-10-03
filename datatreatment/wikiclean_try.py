import wikipediaapi
import regex as re
import spacy
import os
import json
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
nlp = spacy.load("es_core_news_sm")

huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
if not huggingface_api_key:
    raise ValueError("HUGGINGFACE_API_KEY no está configurada en las variables de entorno.")

client = InferenceClient(token=huggingface_api_key)
model = os.getenv('HUGGINGFACE_MODEL_NAME')
if not model:
    raise ValueError("Configura un modelo de Hugging Face en las variables de entorno.")

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

Tu tarea es:

1. Extraer hechos relevantes de la biografía (hitos, nacimiento, muerte, logros, lugares, curiosidades, etc.).
2. Transformarlos en pistas en formato JSON.
3. Cada pista debe tener un campo "dificultad" (1 a 5), donde:

   - 1 = muy fácil / general: profesión, nacionalidad, campo de actividad o época histórica. 
         Ejemplos: "Fue una científica muy reconocida a nivel mundial", "Se destacó en física y química". 
         *Nunca pongas años, fechas exactas, cifras ni nombres propios aquí.*
         
   - 2 = fácil: información conocida pero no obvia, como premios, instituciones importantes o contexto cultural.  
         Ejemplos: "Trabajó en Francia durante gran parte de su carrera", "Su familia también estuvo vinculada a la ciencia".  
         
   - 3 = medio: contribuciones concretas o logros importantes que requieren cierto conocimiento.  
         Ejemplos: "Realizó estudios pioneros sobre radiactividad", "Fue de las primeras mujeres en recibir reconocimiento académico".  
         
   - 4 = difícil: detalles poco conocidos o curiosidades históricas relevantes.  
         Ejemplos: "Nombró un elemento químico en honor a su país de origen", "Ocupó una cátedra universitaria inédita para su época".  
         
   - 5 = muy difícil: hechos muy específicos, poco evidentes, pero sin revelar la identidad directamente.  
         Ejemplos: "Recibió sepultura con honores en un lugar reservado solo a figuras históricas excepcionales", 
                   "Fue la primera persona en lograr un hito científico doble único en la historia".

4. Genera **8 pistas en total**, no más, distribuidas según la dificultad, respetando la estructura que te doy en el ejemplo en todo momento.  
5. Usa **sinónimos y variaciones en el lenguaje**: no empieces todas las pistas con la misma estructura.  
6. **Bajo ningún concepto menciones nombres reales, apodos, títulos, o variantes del nombre de la persona, es más, solo puedes referirte a ella en voz impropia.**
7. Nunca incluyas números de elementos, cifras exactas de premios ni fechas exactas de nacimiento o muerte.
8. Ordena las pistas de **mayor a menor dificultad** (5 → 1).  
9. Devuelve solo **JSON válido**, sin comentarios ni texto adicional.

Ejemplo de salida esperado (8 pistas):

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

Aquí está el texto de la biografía:

"{"; ".join(frases_sin_puntuacion)}"
"""



    return prompt

# --- Uso ---
url = "https://es.wikipedia.org/wiki/Marie_Curie"
nombre = url.split("/wiki/")[-1].replace("_", " ")
prompt = (generar_frases_trivia(url, nombre))
print(prompt)
messages=[
        {"role": "system", "content": "Eres un asistente experto en generar pistas de trivia."},
        {"role": "user", "content": prompt}
    ]
response = client.chat_completion(
    messages=messages,
    model=model,
    max_tokens=600,
    temperature=0.7
)
output = response.choices[0].message.content
# 5. Guardar en archivo JSON
try:
    pistas = json.loads(output)  # intentar parsear directamente
except:
    # si no está limpio, lo guardamos como texto bruto
    pistas = {"raw_response": output}

with open("pistas.json", "w", encoding="utf-8") as f:
    json.dump(pistas, f, indent=4, ensure_ascii=False)

print(f"✅ Guardado {nombre} en pistas.json")
