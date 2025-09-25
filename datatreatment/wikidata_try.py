import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd 

def get_famous_humans(limit=5, offset=0, min_sitelinks=20):
    """
    Devuelve personas (Q5) con artículo en Wikipedia en español y con un número minimo de traducciones (sitelinks).
    como un DataFrame de pandas.
    Parámetros:
    - limit: número máximo de resultados a devolver.
    - offset: número de resultados a saltar (para paginación).
    - min_sitelinks: número mínimo de traducciones (sitelinks) que debe tener la persona.
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
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "SpyGame/1.0.0 (contact: rupalonso@gmail.com)"
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


if __name__ == "__main__":
    personas_df = get_famous_humans(limit=5, offset=0)
    print(personas_df)
