import wikipediaapi
import regex as re
import spacy

# --- 1. Cargar modelo spaCy ---
# python -m spacy download es_core_news_sm
nlp = spacy.load("es_core_news_sm")

# --- 2. Función para limpiar texto ---
def limpiar_texto(texto):
    texto = re.sub(r'\[\d+\]', '', texto)  # eliminar referencias
    texto = re.split(r'==\s*(Referencias|Véase también|Enlaces externos)\s*==', texto)[0]
    texto = re.sub(r'\n+', ' ', texto)
    return texto.strip()

# --- 3. Obtener artículo de Wikipedia ---
url = "https://es.wikipedia.org/wiki/Niels_Bohr"
titulo = url.split("/wiki/")[-1]

wiki_es = wikipediaapi.Wikipedia(language='es', user_agent='SpyGame/1.0 (rupalonso@gmail.com)')
articulo = wiki_es.page(titulo)

if not articulo.exists():
    raise ValueError("El artículo no existe.")

texto_limpio = limpiar_texto(articulo.text)
resumen = articulo.summary

# --- 4. Extraer frases fáciles del resumen ---
resumen_doc = nlp(resumen)
frases_faciles = [sent.text.strip() for sent in resumen_doc.sents if 8 <= len(sent.text.split()) <= 25]

# --- 5. Procesar el resto del artículo con spaCy ---
doc = nlp(texto_limpio)

frases_puntuadas = []
for sent in doc.sents:
    num_entidades = len(sent.ents)
    if num_entidades == 0:
        continue
    
    # Scoring general
    score = num_entidades
    for ent in sent.ents:
        if ent.label_ in ["NORP", "LOC"]:
            score += 1
        elif ent.label_ in ["PER", "ORG"]:
            score += 1
    
    score += sum(1 for token in sent if token.pos_ in ["NOUN", "VERB"])
    
    frases_puntuadas.append((sent.text.strip(), score))

# Ordenar frases por score descendente y tomar top 15-20
frases_puntuadas.sort(key=lambda x: x[1], reverse=True)
top_frases = [f[0] for f in frases_puntuadas[:20]]

# --- 6. Combinar resumen y frases puntuadas ---
# Resumen → pistas fáciles primero
frases_seleccionadas = frases_faciles + top_frases

# --- 7. Crear prompt para modelo ---
texto_para_modelo = " ".join(frases_seleccionadas)

prompt = f"""
Haz un listado de pistas ordenadas de menor a mayor, escritas en formato JSON usando la información siguiente: {texto_para_modelo}.
Usa esto de referencia: Niels Bohr: {{pista uno, pista dos}}
"""

print("Prompt listo para el modelo:\n")
print(prompt)
