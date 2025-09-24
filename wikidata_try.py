import requests
import random

def get_famous_humans(limit=10, offset=0):
    url = "https://query.wikidata.org/sparql"
    query = f"""
    SELECT ?person ?personLabel ?esArticle
    WHERE {{
      ?person wdt:P31 wd:Q5 .
      ?person wikibase:sitelinks ?count .
      FILTER(?count > 8)
      ?esArticle schema:about ?person ;
                 schema:isPartOf <https://es.wikipedia.org/> .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es". }}
    }}
    LIMIT {limit} OFFSET {offset}
    """
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "SpyGame/1.0 (https://github.com/alonso02_rupa)"  # <-- importante
    }
    r = requests.get(url, params={"query": query}, headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json()
    
    results = [
        {
            "id": item["person"]["value"],
            "nombre": item["personLabel"]["value"],
            "articulo_es": item["esArticle"]["value"]
        }
        for item in data["results"]["bindings"]
    ]
    
    return results

# Ejemplo de uso
personas = get_famous_humans(limit=5, offset=0)
print(personas)
