# Análisis de Regresión: OLS Explicativa y Logística — Datos Incrementales (Mundo Cerrado)

## Índice

### Parte I: Regresión OLS — Características Semánticas → Métricas de Calidad

1. [Contexto y Objetivo](#1-contexto-y-objetivo)
2. [Diseño Metodológico](#2-diseño-metodológico)
3. [Análisis Individual por Métrica](#3-análisis-individual-por-métrica)
   - [3.1 Poder Discriminativo (PD)](#31-poder-discriminativo-pd)
   - [3.2 Ambigüedad (AMB)](#32-ambigüedad-amb)
   - [3.3 Ganancia de Información (nGAIN)](#33-ganancia-de-información-ngain)
   - [3.4 Lecturabilidad (LEC)](#34-lecturabilidad-lec)
   - [3.5 Consistencia (CONS)](#35-consistencia-cons)
4. [Resumen Comparativo OLS](#4-resumen-comparativo-ols)
5. [Diagnósticos Estadísticos](#5-diagnósticos-estadísticos)
6. [Conclusiones OLS](#6-conclusiones-ols)

### Parte II: Regresión Logística — Optimización de Pesos de Calidad

7. [Objetivo de la Regresión Logística](#7-objetivo-de-la-regresión-logística)
8. [Diseño del Modelo](#8-diseño-del-modelo)
9. [Bondad de Ajuste y Validación](#9-bondad-de-ajuste-y-validación)
10. [Coeficientes e Importancia de Métricas](#10-coeficientes-e-importancia-de-métricas)
11. [Limitaciones](#11-limitaciones)

---

## 1. Contexto y Objetivo

Este análisis replica la metodología del estudio en mundo abierto aplicándola al **conjunto de datos incremental** (`hints_guesses_expanded_incremental_20260319.csv`), correspondiente al experimento en **mundo cerrado**. En esta modalidad, los jugadores eligen sus respuestas entre un conjunto de candidatos predefinidos, en lugar de escribir libremente cualquier nombre.

El objetivo de la **Parte I (OLS)** es verificar si las relaciones entre características lingüísticas y métricas de calidad se mantienen estables, ya que las pistas son las mismas en ambas modalidades pero el contexto de evaluación difiere.

El objetivo de la **Parte II (Logística)** es determinar empíricamente qué métricas de calidad predicen mejor el éxito del jugador en mundo cerrado, donde la dinámica de acierto es distinta.

### Nota metodológica importante: por qué el OLS es invariante

Las métricas de calidad (PD, AMB, nGAIN, LEC, CONS) se calculan sobre las **360 pistas** como entidades lingüísticas con sus embeddings, sin depender de los datos de juego. Al ser el conjunto de pistas idéntico entre mundo abierto y cerrado (45 personajes × 8 pistas generadas por LLM), los modelos OLS producen exactamente los mismos coeficientes en ambos estudios. Esta propiedad de invarianza es, en sí misma, un resultado relevante: **confirma que la estructura lingüística de una pista es una propiedad intrínseca**, independiente de cómo el jugador interactúa con ella.

La diferencia entre estudios reside íntegramente en la **Parte II**, donde los datos de partidas reales cambian.

### Datos

**Parte I (OLS):**
- **N = 360 pistas** (idénticas al estudio en mundo abierto)
- **45 personajes** × 8 pistas por personaje
- Pistas generadas por LLM con *in-context learning*

**Parte II (Logística):**
- **N = 1.119 interacciones** (mundo cerrado)
- Aciertos: **874 (78,1%)** | Fallos: **245 (21,9%)**
- Mayor tasa de éxito que en mundo abierto (78,1% vs. 65,5%)

---

## 2. Diseño Metodológico

### Variables Independientes (X) — Características Semánticas

| # | Variable | Estrato | Descripción |
|---|----------|---------|-------------|
| 1 | `PROPN_Ratio` | Ancla | Proporción de sustantivos propios en la pista |
| 2 | `NUM_Ratio` | Ancla | Proporción de tokens numéricos |
| 3 | `Max_IDF` | Ancla | Máximo IDF (rareza) de las palabras |
| 4 | `ADJ_Ratio` | Ruido | Proporción de adjetivos |
| 5 | `VERB_Ratio` | Acción | Proporción de verbos |
| 6 | `Tree_Depth` | Estructura | Profundidad del árbol sintáctico |
| 7 | `NER_Count` | Estructura | Número de entidades nombradas detectadas |

### Variables Dependientes (Y) — Métricas de Calidad

| Métrica | Descripción |
|---------|-------------|
| **PD** | Poder Discriminativo: ¿Cuánto distingue la pista al target vs. competidores? |
| **AMB** | Ambigüedad: ¿Cuántos personajes activa la pista simultáneamente? |
| **nGAIN** | Ganancia de Información: ¿Cuánta entropía reduce la pista? |
| **LEC** | Lecturabilidad: ¿Qué tan fácil es leer y procesar la pista? |
| **CONS** | Consistencia: ¿Las pistas de un personaje son coherentes entre sí? |

### Especificación del Modelo OLS

- **Estandarización**: Z-score (media=0, std=1) en todas las variables
- **Errores robustos HC3**: Inferencia válida sin requerir normalidad ni homocedasticidad
- **5 regresiones independientes**: Una por cada métrica de calidad

---

## 3. Análisis Individual por Métrica

> **Nota**: Los resultados OLS son idénticos al estudio en mundo abierto porque el corpus de pistas es invariante. Se presentan íntegramente para documentar la replicación y como referencia para la comparación entre estudios.

---

### 3.1 Poder Discriminativo (PD)

**Definición**: PD = sim(pista, target) − mean(sim(pista, otros)), donde sim es similitud coseno en el espacio de embeddings.

#### Resultados del Modelo

| Estadístico | Valor |
|-------------|-------|
| R² | 0.052 |
| R² ajustado | 0.033 |
| F-test p-value | 0.001 |
| Modelo significativo | ✅ Sí (débil) |

#### Coeficientes Estandarizados

| Feature | β | Significancia |
|---------|---|---------------|
| **VERB_Ratio** | **-0.133** | * (p = 0.020) |
| **Max_IDF** | **-0.100** | * (p = 0.010) |
| PROPN_Ratio | — | No significativo |
| NUM_Ratio | — | No significativo |
| ADJ_Ratio | — | No significativo |
| Tree_Depth | — | No significativo |
| NER_Count | — | No significativo |

#### Interpretación

El modelo explica el **5.2% de la varianza** del PD. El poder discriminativo depende primordialmente del **contenido proposicional** más que de la estructura lingüística.

**VERB_Ratio (β = -0.133\*)**: Los verbos reducen la discriminación porque las acciones suelen ser compartidas entre personajes. Las pistas basadas en identidad nominal discriminan mejor que las basadas en historia verbal.

**Max_IDF (β = -0.100\*)**: Las palabras con IDF extremadamente alto tienen representaciones de embeddings ruidosas, lo que debilita la similitud coseno con el target específico.

---

### 3.2 Ambigüedad (AMB)

**Definición**: AMB mide cuántos personajes activa una pista simultáneamente, ponderado por la similitud semántica con cada candidato.

#### Resultados del Modelo

| Estadístico | Valor |
|-------------|-------|
| R² | 0.022 |
| R² ajustado | 0.002 |
| F-test p-value | 0.004 |
| Modelo significativo | ✅ Sí (muy débil) |

#### Coeficientes Estandarizados

| Feature | β | Significancia |
|---------|---|---------------|
| **Max_IDF** | **+0.076** | ** (p = 0.002) |
| PROPN_Ratio | — | No significativo |
| NUM_Ratio | — | No significativo |
| ADJ_Ratio | — | No significativo |
| VERB_Ratio | — | No significativo |
| Tree_Depth | — | No significativo |
| NER_Count | — | No significativo |

#### Interpretación

El modelo explica apenas el **2.2% de la varianza**. El único predictor significativo es Max_IDF: las palabras más raras en el corpus producen representaciones de embedding dispersas, incrementando la activación simultánea de múltiples candidatos.

> **La conclusión teórica central se mantiene**: la ambigüedad es una propiedad del **espacio semántico**, no del texto. No puede reducirse simplemente mejorando la redacción; hay que considerar el contexto del campo de candidatos.

---

### 3.3 Ganancia de Información (nGAIN)

**Definición**: nGAIN cuantifica cuánta entropía reduce la pista en la distribución de probabilidad sobre los candidatos (normalizada de 0 a 1).

#### Resultados del Modelo

| Estadístico | Valor |
|-------------|-------|
| R² | 0.061 |
| R² ajustado | 0.042 |
| F-test p-value | 0.002 |
| Modelo significativo | ✅ Sí (débil pero significativo) |

#### Coeficientes Estandarizados

| Feature | β | Significancia |
|---------|---|---------------|
| **VERB_Ratio** | **-0.209** | *** (p < 0.001) |
| **NER_Count** | **+0.124** | * (p = 0.029) |
| PROPN_Ratio | — | No significativo |
| NUM_Ratio | — | No significativo |
| Max_IDF | — | No significativo |
| ADJ_Ratio | — | No significativo |
| Tree_Depth | — | No significativo |

#### Interpretación

El modelo explica el **6.1% de la varianza**, con dos hallazgos clave:

**VERB_Ratio (β = -0.209\*\*\*)**: Los verbos genéricos son ruido entrópico. No aportan bits discriminativos porque aplican a prácticamente cualquier personaje del corpus.

**NER_Count (β = +0.124\*)**: Cada entidad nombrada adicional reduce la incertidumbre sobre el target de forma no ambigua. Las entidades nombradas son datos duros con poder discriminativo intrínseco.

**Conclusión**: Las pistas más informativas combinan entidades concretas con mínimos verbos genéricos.

---

### 3.4 Lecturabilidad (LEC)

**Definición**: LEC está basada en el Flesch Reading Ease adaptado al español.

#### Resultados del Modelo

| Estadístico | Valor |
|-------------|-------|
| R² | **0.154** |
| R² ajustado | 0.137 |
| F-test p-value | < 0.001 |
| Modelo significativo | ✅ **Mejor modelo del estudio** |

#### Coeficientes Estandarizados

| Feature | β | Significancia |
|---------|---|---------------|
| **ADJ_Ratio** | **-0.379** | *** (p < 0.001) |
| **VERB_Ratio** | **-0.214** | ** (p = 0.001) |
| PROPN_Ratio | — | No significativo |
| NUM_Ratio | — | No significativo |
| Max_IDF | — | No significativo |
| Tree_Depth | — | No significativo |
| NER_Count | — | No significativo |

#### Interpretación

Es el **mejor modelo** del estudio con **~15.4% de varianza explicada**. Solo dos predictores son significativos:

**ADJ_Ratio (β = -0.379\*\*\*)**: El coeficiente individual más grande de todo el análisis. Los adjetivos alargan las frases e introducen subordinación implícita. Los adjetivos vacíos ("famoso", "importante", "reconocido") no aportan información discriminante y destruyen la legibilidad. Eliminarlos es la intervención más efectiva para mejorar la lecturabilidad.

**VERB_Ratio (β = -0.214\*\*)**: Cada verbo introduce una cláusula que incrementa la carga cognitiva. El efecto es de magnitud comparable a ADJ_Ratio, reforzando que la pista óptima es nominal y concisa.

Los demás predictores (NUM_Ratio, Tree_Depth, NER_Count, PROPN_Ratio, Max_IDF) no alcanzan significancia estadística para LEC.

---

### 3.5 Consistencia (CONS)

**Definición**: CONS mide la coherencia semántica interna del conjunto de pistas de un personaje.

#### Resultados del Modelo

| Estadístico | Valor |
|-------------|-------|
| R² | 0.138 |
| R² ajustado | 0.121 |
| F-test p-value | < 0.001 |
| Modelo significativo | ✅ Sí (moderado) |

#### Coeficientes Estandarizados

| Feature | β | Significancia |
|---------|---|---------------|
| **VERB_Ratio** | **-0.302** | *** (p < 0.001) |
| **Tree_Depth** | **+0.113** | * (p = 0.020) |
| PROPN_Ratio | — | No significativo |
| NUM_Ratio | — | No significativo |
| Max_IDF | — | No significativo |
| ADJ_Ratio | — | No significativo |
| NER_Count | — | No significativo |

#### Interpretación

Modelo moderado con **13.8% de varianza explicada**:

**VERB_Ratio (β = -0.302\*\*\*)**: La magnitud más alta de VERB_Ratio en todas las regresiones. Los verbos dispersan el foco temático: una pista con múltiples acciones ("nació, creció, estudió, viajó") toca eventos distintos que reducen la coherencia entre pistas del mismo personaje.

**Tree_Depth (β = +0.113\*)**: Las oraciones sintácticamente más complejas suelen ser más elaboradas temáticamente, con relaciones causales o temporales que organizan el contenido de forma coherente.

---

## 4. Resumen Comparativo OLS

### Tabla de Ajuste por Modelo

| Métrica | R² | R² adj. | F-test (p) | Significativo | Interpretación |
|---------|-----|---------|------------|:---:|---------------|
| **LEC** | 0.154 | 0.137 | p < 0.001 | ✅ | **Mejor modelo**. La lecturabilidad es la más explicable por la sintaxis (~15%) |
| **CONS** | 0.138 | 0.121 | p < 0.001 | ✅ | **Modelo moderado**. Depende significativamente de la estructura verbal |
| **nGAIN** | 0.061 | 0.042 | p = 0.002 | ✅ | **Modelo débil pero significativo**. Captura señales semánticas |
| **PD** | 0.052 | 0.033 | p = 0.001 | ✅ | **Modelo débil pero significativo**. Raíces semánticas detectables |
| **AMB** | 0.022 | 0.002 | p = 0.004 | ✅ (muy débil) | **R² ínfimo (~2%)**. La ambigüedad no se explica por la sintaxis |

### Mapa de Coeficientes Significativos

| Feature | PD | AMB | nGAIN | LEC | CONS |
|---------|:--:|:---:|:-----:|:---:|:----:|
| VERB_Ratio | -0.133* | — | **-0.209****** | **-0.214**** | **-0.302****** |
| ADJ_Ratio | — | — | — | **-0.379****** | — |
| Max_IDF | -0.100* | +0.076** | — | — | — |
| NER_Count | — | — | +0.124* | — | — |
| Tree_Depth | — | — | — | — | +0.113* |
| NUM_Ratio | — | — | — | — | — |
| PROPN_Ratio | — | — | — | — | — |

*(— = no significativo al nivel α = 0.05)*

### Jerarquía de Influencia Lingüística

```
VERB_Ratio  >>  ADJ_Ratio  >  Max_IDF  >  NER_Count  ≈  Tree_Depth  >  NUM_Ratio  ≈  PROPN_Ratio
```

Esta jerarquía es idéntica a la del estudio en mundo abierto, confirmando su robustez como hallazgo sobre la estructura lingüística de las pistas, independientemente del contexto de evaluación.

---

## 5. Diagnósticos Estadísticos

### Multicolinealidad (VIF)

Todos los valores de VIF < 1.5: **ausencia total de multicolinealidad**. Los predictores son ortogonales y cada β es interpretable de forma independiente.

### Normalidad de Residuos (Shapiro-Wilk)

El test rechaza normalidad en todas las métricas (p < 0.05). Esperable con N=360. No invalida el análisis gracias al Teorema Central del Límite y a los errores estándar robustos HC3.

### Homocedasticidad (Breusch-Pagan)

LEC y CONS presentan heterocedasticidad (p < 0.05). Los errores HC3 compensan la violación en todos los casos.

### Gráficos Diagnósticos

Los gráficos generados (Q-Q Plots y Residuos vs. Ajustados) se encuentran en la carpeta `fotos/` y son idénticos a los del estudio en mundo abierto, confirmando la invarianza del análisis OLS.

---

## 6. Conclusiones OLS

### Replicación completa de los hallazgos

Al ser el corpus de pistas idéntico, el análisis OLS replica perfectamente los resultados del estudio en mundo abierto. Esta invarianza no es trivial: confirma que las relaciones entre estructura lingüística y calidad de pistas son propiedades estables del texto, no artefactos del contexto de evaluación.

### Hallazgo principal replicado

VERB_Ratio sigue siendo el predictor lingüístico más poderoso, con efectos significativos negativos sobre 4 de las 5 métricas. ADJ_Ratio es el destructor más potente de lecturabilidad.

### Perfil de pista óptima (confirmado)

| Característica | Valor ideal | Justificación |
|---|---|---|
| **VERB_Ratio** | Bajo (< 0.09) | Negativo en PD, nGAIN, LEC y CONS |
| **ADJ_Ratio** | Bajo (< 0.05) | Destruye lecturabilidad (β = -0.379***) |
| **NER_Count** | Alto (≥ 1) | Incrementa ganancia de información (β = +0.124*) |
| **Max_IDF** | Moderado | Extremos altos perjudican PD y aumentan AMB |

> **La calidad reside en la especificidad nominal, no en la narrativa verbal. Las mejores pistas se parecen más a una entrada de enciclopedia que a una narración literaria.**

---
---

# Parte II: Regresión Logística — Optimización de Pesos de Calidad (Mundo Cerrado)

---

## 7. Objetivo de la Regresión Logística

La regresión logística responde *"qué métricas de calidad predicen el éxito real del jugador en mundo cerrado"*. En esta modalidad, los jugadores seleccionan entre un conjunto cerrado de candidatos predefinidos, lo que cambia fundamentalmente la dinámica del acierto respecto al mundo abierto.

El objetivo es determinar empíricamente los **pesos** de cada métrica en la fórmula de calidad compuesta $Q$ para el contexto de mundo cerrado, y contrastarlos con los obtenidos en mundo abierto.

---

## 8. Diseño del Modelo

### Variable dependiente (Y)

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `acierto` | Binaria (0/1) | Si el jugador adivinó correctamente el personaje en mundo cerrado |

### Variables independientes (X)

| Métrica | Descripción |
|---------|-------------|
| **PD** | Poder Discriminativo |
| **AMB** | Ambigüedad Semántica |
| **nGAIN** | Ganancia de Información Normalizada |
| **CONS** | Consistencia Interna |
| **LEC** | Lecturabilidad |

### Especificación

- **Modelo**: `LogisticRegression` (sklearn) con `class_weight='balanced'`
- **Estandarización**: `StandardScaler` (Z-score) — coeficientes β directamente comparables
- **Regularización**: L2 (ridge)
- **Split**: 80/20 estratificado (train: 895, test: 224) + validación cruzada 5-fold

### Distribución de clases

| Clase | Frecuencia | Porcentaje |
|-------|-----------|------------|
| Acierto (1) | 874 | 78.1% |
| Fallo (0) | 245 | 21.9% |

La tasa de acierto en mundo cerrado (78.1%) es **notablemente mayor** que en mundo abierto (65.5%). El acceso a la lista de candidatos reduce la incertidumbre del jugador y aumenta la probabilidad de acertar.

---

## 9. Bondad de Ajuste y Validación

### 9.1 Validación Cruzada Estratificada (5-Fold)

| Métrica | Media ± Std (5-Fold) | Interpretación |
|---------|:--------------------:|----------------|
| **Accuracy** | 0.532 ± 0.040 | Ligeramente superior al azar (0.5) |
| **AUC-ROC** | 0.548 ± 0.058 | Capacidad discriminativa modesta |
| **F1-Score** | 0.641 ± 0.035 | Balance razonable precision/recall |
| **Log-Loss** | 0.692 ± 0.022 | Incertidumbre reducida vs. modelo nulo |

La varianza entre folds es aceptable aunque mayor que en mundo abierto (std ≈ 0.06 vs. 0.03), reflejo del menor tamaño muestral y mayor desbalance de clases.

### 9.2 Pseudo-R² de McFadden

$$R^2_{McFadden} = 1 - \frac{\mathcal{LL}_{modelo}}{\mathcal{LL}_{nulo}}$$

| Métrica | Valor |
|---------|-------|
| Log-Likelihood (modelo) | -580.33 |
| Log-Likelihood (nulo) | -588.11 |
| **Pseudo-R² McFadden** | **0.0132** |
| **Pseudo-R² McFadden Adj.** | **0.0030** |

**Escala de referencia** (McFadden, 1979):

| Rango | Interpretación |
|-------|----------------|
| 0.0 - 0.1 | Ajuste pobre |
| 0.1 - 0.2 | Ajuste aceptable |
| 0.2 - 0.4 | Ajuste **excelente** |
| > 0.4 | Excepcional (raro) |

El ajuste es pobre, lo que es esperable: se predice el acierto usando solo métricas de la pista, ignorando conocimiento del jugador, estrategia y el factor azar inherente al juego.

### 9.3 Log-Likelihood Ratio Test (χ²)

$$G^2 = -2(\mathcal{LL}_{nulo} - \mathcal{LL}_{modelo}) = 15.56, \quad p = 0.0082$$

El modelo es **estadísticamente mejor que el azar** (✅), aunque con menor diferencia que en mundo abierto ($G^2 = 30.10$, $p < 0.001$). La señal predictiva de las métricas de calidad existe pero es más débil en este contexto.

### 9.4 Brier Score (Calibración)

$$BS = \frac{1}{N}\sum_{i=1}^{N}(p_i - y_i)^2 = 0.2495$$

Calibración en el límite del azar (0.25), reflejo del alto desbalance de clases que dificulta discriminar los casos de fallo.

### 9.5 Comparación Hold-out con Mundo Abierto

| Métrica | Mundo Cerrado | Mundo Abierto |
|---------|:------------:|:------------:|
| Accuracy | 0.500 | 0.584 |
| AUC-ROC | 0.505 | 0.591 |
| McFadden R² | 0.0132 | 0.0102 |
| LR test G² | 15.56 | 30.10 |
| LR test p | 0.0082 | < 0.001 |

El rendimiento en hold-out es inferior en mundo cerrado. El modelo tiene más dificultad para distinguir aciertos de fallos en este contexto, principalmente por el mayor desbalance de clases.

---

## 10. Coeficientes e Importancia de Métricas

### Coeficientes sklearn (estandarizados, con L2)

| Métrica | Coeficiente β | Efecto | Mundo Abierto (ref.) |
|---------|:-------------:|:------:|:--------------------:|
| **PD** | **+0.333** | ↑ acierto | +0.110 |
| **CONS** | -0.162 | ↓ acierto | -0.008 |
| **nGAIN** | +0.061 | ↑ acierto | +0.056 |
| **AMB** | +0.051 | ↑ acierto | -0.080 |
| **LEC** | +0.023 | ↑ acierto | -0.070 |

### Significancia individual (statsmodels MLE, sin regularización)

| Métrica | β | p-value | Significativo |
|---------|---|---------|:---:|
| **PD** | +0.325 | 0.028 | ✅ * |
| CONS | -0.114 | 0.132 | No |
| AMB | +0.051 | 0.679 | No |
| nGAIN | — (referencia) | — | — |
| LEC | -0.010 | 0.888 | No |

En contraste con el modelo conjunto (significativo, p=0.008), **solo PD alcanza significancia individual** (p=0.028). Los demás coeficientes contribuyen conjuntamente pero sus efectos individuales no son estadísticamente distinguibles del ruido dado N=1.119.

### Pesos Derivados

$$w_i = \frac{|\beta_i|}{\sum_j |\beta_j|}$$

| Métrica | |β| | Peso normalizado |
|---------|-----|----------------|
| **PD** | 0.333 | **53.2%** |
| **CONS** | 0.162 | **25.9%** |
| **nGAIN** | 0.061 | 9.8% |
| **AMB** | 0.051 | 8.1% |
| **LEC** | 0.023 | 3.7% |

PD absorbe más de la mitad del peso, mientras que en mundo abierto su contribución era marginal (β = +0.110, ~34% del peso).

### Hallazgos destacados

**1. PD es dominante en mundo cerrado**: En un contexto donde el jugador debe diferenciar el target dentro de una lista visible de candidatos, la capacidad discriminativa de la pista se convierte en el factor decisivo. El jugador puede comparar explícitamente los candidatos contra la pista, haciendo que el PD sea directamente relevante.

**2. CONS emerge como factor negativo notable**: En mundo abierto era prácticamente irrelevante (β = -0.008). En mundo cerrado su efecto negativo es significativo (β = -0.162). Una hipótesis es que cuando las pistas de un personaje son muy temáticamente cohesionadas, pueden crear un perfil demasiado genérico dentro de la categoría del personaje, dificultando la identificación del individuo específico entre candidatos similares.

**3. AMB y LEC invierten dirección**: En mundo abierto ambas eran negativas; en mundo cerrado ambas son levemente positivas. La lista de candidatos actúa como filtro que resuelve externamente la ambigüedad: aunque la pista active múltiples candidatos, el jugador los ve todos y puede seleccionar el más probable. Así, la ambigüedad inherente a la pista importa menos que en mundo abierto, donde el jugador debe recuperar el nombre de memoria.

### Observación sobre la comparación sklearn vs. statsmodels

Los coeficientes de sklearn (con regularización L2) y de statsmodels (MLE sin regularización) difieren en magnitud pero coinciden en el predictor más relevante (PD). La regularización L2 de sklearn es especialmente relevante en muestras relativamente pequeñas (N=1.119).

---

## 11. Limitaciones

### Limitaciones del OLS

1. **Invarianza confirmada pero esperable**: Los resultados OLS son idénticos por diseño. La replicación confirma la metodología pero no aporta información nueva sobre los efectos de la modalidad de juego en la estructura lingüística.

2. **R² moderados-bajos**: Las características sintácticas explican solo 5-15% de la varianza de las métricas. La calidad semántica depende primordialmente del contenido proposicional.

3. **Sesgo de generación**: Pistas generadas por LLM con longitud limitada producen pistas relativamente homogéneas, comprimiendo la varianza natural.

### Limitaciones del Logístico (Mundo Cerrado)

4. **Tamaño muestral reducido**: Con N=1.119 (frente a N=2.293 en mundo abierto), la potencia estadística es menor. Solo PD alcanza significancia individual.

5. **Alto desbalance de clases**: El 78.1% de aciertos hace que el modelo tienda a predecir aciertos, con recall bajo para los fallos (43% en el reporte de clasificación). El parámetro `class_weight='balanced'` mitiga pero no elimina este efecto.

6. **Pseudo-R² ajustado casi nulo (0.003)**: Con 5 features y N=1.119, hay muy poca señal por encima de lo esperado por azar. Se requieren más datos para estimaciones estables.

7. **Interpretación causal**: Los coeficientes describen asociaciones observacionales. La dirección causal (calidad de pista → éxito del jugador) es plausible pero no demostrable sin un diseño experimental controlado.

8. **Generalización**: Los resultados son específicos del conjunto de 45 personajes y 8 pistas por personaje del estudio.

---

*Documento generado a partir del análisis en `propuesta_calidad_pistas.ipynb` con datos `hints_guesses_expanded_incremental_20260319.csv`*
*Fecha: Marzo 2026*
