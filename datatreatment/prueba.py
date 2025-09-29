from gensim.summarization import summarize

texto = """
Python es un lenguaje de programación muy popular.
Se utiliza para desarrollo web, ciencia de datos, automatización y más.
Su sintaxis es clara y fácil de aprender.
"""

resumen = summarize(texto, ratio=0.5)  # ratio indica qué porcentaje del texto conservar
print(resumen)
