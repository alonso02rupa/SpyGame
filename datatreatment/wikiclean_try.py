import wikipediaapi
import regex as re
# URL del artículo
url = "https://es.wikipedia.org/wiki/Niels_Bohr"

# Extraemos el título
titulo = url.split("/wiki/")[-1]

# Creamos objeto Wikipedia con user_agent
wiki_es = wikipediaapi.Wikipedia(
    language='es',
    user_agent='MiScriptPython/1.0 (contacto@ejemplo.com)'  # <- aquí tu user agent
)

# Obtenemos el artículo
articulo = wiki_es.page(titulo)

if articulo.exists():
    pass
else:
    print("El artículo no existe.")

# Limpiar el texto eliminando referencias y otros elementos no deseados
def limpiar_texto(texto):
    # Eliminar referencias entre corchetes
    texto = re.sub(r'\[\d+\]', '', texto)
    # Eliminar secciones de "Referencias", "Véase también", etc.
    texto = re.split(r'==\s*(Referencias|Véase también|Enlaces externos)\s*==', texto)[0]
    # Eliminar múltiples saltos de línea
    texto = re.sub(r'\n+', '\n', texto)
    return texto.strip()

texto_limpio = limpiar_texto(articulo.text)

# Ahora separamos en frases
frases = re.split(r'(?<=[.!?]) +', texto_limpio)
for frase in frases:
    if len(frase) > 5:  # Filtrar frases muy cortas
        print(frase)
