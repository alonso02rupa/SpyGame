# Data Treatment - Procesamiento de Datos

Este directorio contiene el módulo `data_processor.py` que combina la funcionalidad de extracción de datos de Wikidata y generación de pistas de trivia.

## Archivo Principal

### `data_processor.py`

Este archivo combina las funcionalidades de:
- **`wikidata_try.py`**: Extracción de datos de personas famosas desde Wikidata
- **`wikiclean_try.py`**: Procesamiento de biografías y generación de pistas usando IA

## Funciones Principales

### 1. `get_famous_humans(limit=10, offset=0, min_sitelinks=20)`
Obtiene personas famosas de Wikidata con artículo en Wikipedia español.

**Parámetros:**
- `limit`: Número máximo de resultados
- `offset`: Número de resultados a saltar (paginación)
- `min_sitelinks`: Número mínimo de traducciones requeridas

**Retorna:** DataFrame de pandas con id, articulo_es y sitelinks

### 2. `generar_pistas(url, nombre_persona)`
Genera 8 pistas de trivia para una persona dada su URL de Wikipedia.

**Parámetros:**
- `url`: URL del artículo de Wikipedia
- `nombre_persona`: Nombre de la persona

**Retorna:** Lista de diccionarios con pistas y niveles de dificultad

### 3. `subir_pistas_a_db(pistas, nombre_persona, wikidata_id=None, url_wikipedia=None)`
Sube las pistas generadas a la base de datos MongoDB.

**Parámetros:**
- `pistas`: Lista de pistas generadas
- `nombre_persona`: Nombre de la persona
- `wikidata_id`: ID de Wikidata (opcional)
- `url_wikipedia`: URL de Wikipedia (opcional)

**Retorna:** True si se guardó exitosamente, False en caso contrario

### 4. `procesar_persona(url, nombre_persona=None, wikidata_id=None, guardar_json=True, subir_db=True)`
Función completa que procesa una persona: genera pistas y las guarda.

**Parámetros:**
- `url`: URL de Wikipedia de la persona
- `nombre_persona`: Nombre de la persona (opcional, se extrae de la URL)
- `wikidata_id`: ID de Wikidata (opcional)
- `guardar_json`: Si True, guarda en archivo JSON local
- `subir_db`: Si True, sube a MongoDB

**Retorna:** Las pistas generadas

## Uso Básico

```python
from datatreatment import data_processor

# Procesar una persona (genera pistas y las guarda en JSON y DB)
url = "https://es.wikipedia.org/wiki/Marie_Curie"
pistas = data_processor.procesar_persona(url)

# Solo generar pistas sin guardar
pistas = data_processor.generar_pistas(url, "Marie Curie")

# Obtener personas famosas de Wikidata
personas_df = data_processor.get_famous_humans(limit=10)
```

## Variables de Entorno Requeridas

Asegúrate de tener configuradas las siguientes variables en tu archivo `.env`:

- `HUGGINGFACE_API_KEY`: Tu API key de Hugging Face
- `HUGGINGFACE_MODEL_NAME`: Nombre del modelo a usar (ej: "meta-llama/Llama-3.2-3B-Instruct")
- `WIKIPEDIA_USER_AGENT`: User agent para las peticiones a Wikipedia
- `MONGODB_URI`: URI de conexión a MongoDB (default: "mongodb://localhost:27017/spygame")

## Base de Datos

Las pistas se guardan en MongoDB en la colección `pistas` con la siguiente estructura:

```json
{
  "nombre": "Marie Curie",
  "pistas": [
    {"dificultad": 5, "pista": "..."},
    {"dificultad": 4, "pista": "..."},
    ...
  ],
  "fecha_creacion": "2024-01-01T12:00:00",
  "wikidata_id": "Q7186",
  "url_wikipedia": "https://es.wikipedia.org/wiki/Marie_Curie"
}
```

## Archivos Antiguos

Los archivos `wikidata_try.py` y `wikiclean_try.py` han sido consolidados en `data_processor.py` y pueden ser eliminados si ya no son necesarios.
