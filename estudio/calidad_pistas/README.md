# Sistema de Evaluación de Calidad de Pistas

## 📋 Descripción

Sistema para evaluar la calidad de pistas en SpyGame basado en **métricas latentes semánticas** en lugar de clasificación binaria.

### Contexto del Juego
- 45 personajes fijos
- 1 target por partida
- Guesses libres (texto)
- Similitud semántica como señal principal
- 8 pistas por personaje (con duplicados entre niveles de dificultad)

## 🎯 Enfoque Metodológico

**NO clasificación • NO QA • NO accuracy binaria**  
✅ **Ranking + desplazamiento semántico**

## 🏗️ Arquitectura del Sistema

### 1️⃣ Representación Semántica Base
Cálculo de embeddings para todo el contenido textual:
- Personajes (descripciones implícitas)
- Pistas (texto de cada hint)
- Guesses (texto de intentos de usuarios)

**Modelo**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

### 2️⃣ Métricas Latentes (CORE)

#### Poder Discriminativo (PD)
```
PD = sim(hint, target) - mean(sim(hint, vecinos_k))
```
- **Qué mide**: cuánto empuja la pista hacia el target vs sus vecinos semánticos
- **Por qué es clave**: correlaciona con mejora de guesses, no depende del usuario
- **Interpretación**: valores positivos = buena discriminación

#### Ambigüedad Semántica
```
Amb = H(softmax(sim(hint, todos_personajes)))
```
- **Qué mide**: cuántos personajes "enciende" la pista simultáneamente
- **Por qué importa**: pistas ambiguas bloquean convergencia humana
- **Interpretación**: 0 = específica, 1 = máxima ambigüedad

#### Cercanía al Target
```
Prox = sim(hint, target)
```
- **Qué mide**: información directa sobre el target
- **NO es malo**: tiene utilidad decreciente (saturación)
- **Uso**: con función no lineal, no como penalización

### 3️⃣ Features Intrínsecos (Predictores)

#### Features Semánticos (6)
- Especificidad (rareza léxica media)
- Densidad informativa (proporción tokens de contenido)
- Cobertura conceptual (similitud con top-k vecinos)
- Número de conceptos distintos
- Varianza semántica interna

#### Features Lingüísticos (9)
- Lecturabilidad (Flesch adaptado)
- Complejidad sintáctica (profundidad árbol)
- Tipo de lenguaje (nombres propios, sustantivos, verbos, adjetivos)
- Número de entidades nombradas
- Longitud del texto

### 4️⃣ Dataset Estructurado

```
X = [15 features semánticos + lingüísticos]
Y = [PD, Ambigüedad, Proximidad]
```

**Salida**: `../results/hint_quality_dataset.csv`

## 🚀 Instalación

```bash
# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Descargar modelo de spaCy para español
python -m spacy download es_core_news_sm
```

## 📊 Uso

1. **Ejecutar el notebook**: `propuesta_calidad_pistas.ipynb`
2. Las celdas están organizadas secuencialmente:
   - Carga de datos
   - Cálculo de embeddings
   - Definición de métricas
   - Extracción de features
   - Generación de dataset
   - Análisis exploratorio
   - Visualizaciones
   - Exportación

3. **Resultado**: Dataset en `../results/hint_quality_dataset.csv`

## 📈 Salidas del Análisis

### Visualizaciones
- Distribuciones de métricas latentes
- Correlaciones entre métricas
- Relación dificultad vs métricas
- Heatmap features vs métricas

### Insights
- Top/bottom pistas por cada métrica
- Promedios por nivel de dificultad
- Features más correlacionados con PD

## 🔬 Próximos Pasos

### Fase 1: Validación con Datos de Usuario
- Integrar con `hints_guesses_expanded.csv`
- Correlacionar métricas con mejora de guesses
- Validar hipótesis sobre ambigüedad y estancamiento

### Fase 2: Modelo Predictivo
```python
# Entrenar regresores X → Y
# Random Forest / XGBoost
# Interpretar importancia de features
```

### Fase 3: Función de Calidad Compuesta
```python
Q(h) = α·PD(h) - β·Amb(h) + γ·f(Prox(h))
# donde f(Prox) es no lineal (utilidad decreciente)
```

### Fase 4: Aplicación
- Rankear pistas existentes
- Evaluar pistas generadas por LLM
- Optimizar set de pistas por personaje

## ⚠️  Notas Metodológicas

1. **NO usar PD como ground truth**: es una métrica latente, debe validarse con comportamiento humano
2. **Considerar curva de utilidad**: proximidad alta es útil pero satura
3. **Ambigüedad contextual**: puede ser estratégica en primeras pistas
4. **Validación empírica**: todas las métricas deben correlacionar con mejora observable

## 📁 Estructura de Archivos

```
calidad_pistas/
├── README.md                          # Este archivo
├── requirements.txt                   # Dependencias
├── propuesta_calidad_pistas.ipynb     # Notebook principal
└── (outputs)
    └── ../results/hint_quality_dataset.csv
```

## 🤝 Contribuciones

Este sistema es extensible. Áreas de mejora:
- Nuevos features semánticos (e.g., topic modeling)
- Integración con datos temporales de sesiones
- Análisis de secuencias de pistas
- Personalización por perfil de usuario

## 📝 Referencias

- Modelo de embeddings: [sentence-transformers](https://www.sbert.net/)
- spaCy: [https://spacy.io/](https://spacy.io/)
- Métricas de entropía: [scipy.stats](https://docs.scipy.org/doc/scipy/reference/stats.html)
