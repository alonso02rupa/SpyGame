# Sistema DIRT - Discovery of Inference Rules from Text

## Descripción

El sistema DIRT implementado en este proyecto aprende equivalencias semánticas entre verbos a partir de textos biográficos y las utiliza para reformular y diversificar el lenguaje antes de generar pistas con el modelo de Hugging Face.

## Componentes

### 1. `dirt_builder.py`

**Función**: Construye el modelo de inferencias DIRT.

**Proceso**:
1. Obtiene personas famosas directamente de Wikidata (igual que `data_processor.py`)
2. Descarga sus biografías completas desde Wikipedia
3. Extrae triples sujeto-verbo-objeto usando spaCy
4. Calcula similitudes entre verbos basándose en:
   - Contextos compartidos (sujetos y objetos comunes)
   - Frecuencia de coocurrencias
   - Índice de similitud (Coeficiente de Jaccard modificado)
5. Genera pares de equivalencias con score de confianza
6. Guarda el modelo en `modelo_inferencias.json`

**Nota importante**: El sistema obtiene los textos directamente de Wikidata/Wikipedia, **NO requiere que MongoDB tenga datos previos**. Funciona de forma independiente.

**Uso**:
```bash
python dirt_builder.py
```

**Salida**: Archivo `modelo_inferencias.json` con formato:
```json
{
  "version": "1.0",
  "generado": "2025-10-24",
  "num_equivalencias": 150,
  "equivalencias": [
    {
      "a": "fundar",
      "b": "establecer",
      "score": 0.82,
      "contextos_compartidos": 12,
      "freq_a": 45,
      "freq_b": 38
    },
    ...
  ]
}
```

### 2. `utils_dirt.py`

**Función**: Utilidades para aplicar el modelo DIRT durante la generación de pistas.

**Funciones principales**:

#### `aplicar_DIRT(frases, probabilidad=0.3, min_score=0.2, max_sustituciones=None)`
Reformula frases sustituyendo verbos por equivalentes aprendidos.

**Parámetros**:
- `frases`: Lista de strings con las frases a reformular
- `probabilidad`: Probabilidad de sustituir cada verbo (0.0 - 1.0)
- `min_score`: Score mínimo de similitud para aceptar una equivalencia
- `max_sustituciones`: Máximo de sustituciones totales (None = sin límite)

**Retorna**: Lista de frases reformuladas

**Ejemplo**:
```python
from utils_dirt import aplicar_DIRT

frases = [
    "Esta persona fundó una universidad",
    "Recibió un premio importante"
]

frases_reformuladas = aplicar_DIRT(frases, probabilidad=0.5)
# Resultado posible:
# [
#     "Esta persona estableció una universidad",
#     "Recibió un premio importante"
# ]
```

#### `obtener_estadisticas_modelo()`
Retorna estadísticas del modelo cargado.

#### `listar_equivalencias_verbo(verbo, top_n=5)`
Lista las equivalencias de un verbo específico.

**Uso standalone**:
```bash
python utils_dirt.py
```
Ejecuta un ejemplo de uso mostrando las capacidades del sistema.

### 3. Integración en `data_processor.py`

El sistema DIRT se integra automáticamente en el pipeline de generación de pistas:

```python
# En la función generar_frases_trivia()
frases_lista = frases[:12]

# Aplicar DIRT antes de enviar al modelo de Hugging Face
if DIRT_DISPONIBLE:
    frases_lista = aplicar_DIRT(frases_lista, probabilidad=0.3, min_score=0.2)
```

**Ventajas**:
- ✅ Diversifica el vocabulario del input
- ✅ Reduce repeticiones en las pistas generadas
- ✅ Mejora la variedad del lenguaje
- ✅ Manejo gracioso de errores (continúa sin DIRT si no está disponible)

## Workflow completo

### Paso 1: Generar el modelo DIRT (INDEPENDIENTE de MongoDB)
```bash
python dirt_builder.py
```
Esto:
- Consulta Wikidata para obtener personas famosas
- Descarga sus biografías desde Wikipedia
- Crea `modelo_inferencias.json` con las equivalencias aprendidas
- **No requiere que MongoDB tenga datos**

### Paso 2: Procesar personas con DIRT activo
```bash
python process_data.py --num 10
```
El sistema aplicará automáticamente las reformulaciones DIRT durante la generación y guardará las pistas en MongoDB.

### Paso 3 (Opcional): Actualizar el modelo periódicamente
A medida que quieras mejorar las equivalencias con más datos:
```bash
python dirt_builder.py
```
Regenera el modelo consultando nuevamente Wikidata/Wikipedia.

## Requisitos

- spaCy con modelo español: `python -m spacy download es_core_news_sm`
- Acceso a Internet (para consultar Wikidata y Wikipedia)
- Variables de entorno configuradas (`.env` con `WIKIPEDIA_USER_AGENT`)
- Python 3.8+

**Nota**: MongoDB NO es necesario para generar el modelo DIRT, solo para el juego principal.

## Configuración avanzada

### Ajustar umbral de similitud
En `dirt_builder.py`, línea ~240:
```python
equivalencias = calcular_similitudes_verbos(triples, umbral_score=0.1)
```
- Aumentar el umbral → menos equivalencias, mayor calidad
- Disminuir el umbral → más equivalencias, posibles false positives

### Ajustar probabilidad de sustitución
En `data_processor.py`, línea ~196:
```python
frases_lista = aplicar_DIRT(frases_lista, probabilidad=0.3, min_score=0.2)
```
- `probabilidad=0.3` → 30% de los verbos se sustituyen
- `min_score=0.2` → solo acepta equivalencias con score ≥ 0.2

### Número de biografías para entrenar
En `dirt_builder.py`, función `main()`:
```python
textos = obtener_textos_biografias(num_personas=15)
```
Aumentar este número mejora el modelo pero requiere más tiempo de procesamiento.

## Ejemplos de equivalencias aprendidas

El sistema puede aprender equivalencias como:
- `fundar` ≈ `establecer` ≈ `crear`
- `recibir` ≈ `obtener` ≈ `ganar`
- `estudiar` ≈ `cursar` ≈ `formarse`
- `trabajar` ≈ `colaborar` ≈ `desempeñarse`
- `descubrir` ≈ `hallar` ≈ `encontrar`

## Limitaciones y consideraciones

1. **Dependencia de spaCy**: Requiere análisis sintáctico, puede ser lento en textos largos
2. **Idioma**: Actualmente solo español (modelo `es_core_news_sm`)
3. **Conjugación**: Las sustituciones intentan preservar la conjugación pero pueden no ser perfectas
4. **Contexto**: Las equivalencias son generales, pueden no ser apropiadas en todos los contextos

## Troubleshooting

### "Modelo DIRT no disponible"
- Ejecuta `python dirt_builder.py` para generarlo

### "Error: Modelo de spaCy no encontrado"
- Instala el modelo: `python -m spacy download es_core_news_sm`

### "MongoDB no disponible"
- No es problema. El sistema obtiene datos directamente de Wikidata/Wikipedia
- MongoDB solo se usa en el juego principal, no en DIRT builder

### Las sustituciones no son apropiadas
- Ajusta `min_score` más alto en `aplicar_DIRT()`
- Regenera el modelo con más datos (aumentar `num_personas`)
- Reduce la `probabilidad` de sustitución

## Referencias

El sistema está inspirado en:
- Lin, D., & Pantel, P. (2001). "DIRT - Discovery of Inference Rules from Text"
- Adaptado para generación de contenido diversificado en español

## Contribuciones futuras

Posibles mejoras:
- [ ] Soporte multiidioma
- [ ] Mejor preservación de conjugaciones verbales
- [ ] Equivalencias contextuales (dependientes del dominio)
- [ ] Cache de análisis spaCy para mejorar rendimiento
- [ ] Interfaz web para explorar equivalencias
- [ ] Métricas de calidad de las equivalencias aprendidas
