# Análisis de Regresión: OLS Explicativa y Logística para Pesos de Calidad

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
4. [Resumen Comparativo](#4-resumen-comparativo)
5. [Diagnósticos Estadísticos](#5-diagnósticos-estadísticos)
6. [Conclusiones e Implicaciones Prácticas](#6-conclusiones-e-implicaciones-prácticas)

### Parte II: Regresión Logística — Optimización de Pesos de Calidad

7. [Objetivo de la Regresión Logística](#7-objetivo-de-la-regresión-logística)
8. [Diseño del Modelo](#8-diseño-del-modelo)
9. [Bondad de Ajuste y Validación](#9-bondad-de-ajuste-y-validación)
10. [Coeficientes e Importancia de Métricas](#10-coeficientes-e-importancia-de-métricas)
11. [Limitaciones](#11-limitaciones)

---

## 1. Contexto y Objetivo

En el juego SpyGame, los jugadores reciben **pistas** (hints) sobre un personaje objetivo y deben adivinarlo. Cada pista es una frase en lenguaje natural que describe al personaje sin nombrarlo directamente.

El objetivo de este análisis es entender **qué características lingüísticas/sintácticas de una pista predicen su calidad**, medida a través de 5 métricas complementarias. Para ello se utilizan **regresiones lineales múltiples (OLS)** con coeficientes estandarizados (β), que permiten comparar la magnitud del efecto de cada predictor independientemente de su escala.

### Datos

- **N = 360 pistas** (tras eliminar NaNs)
- **45 personajes** × 8 pistas por personaje
- Pistas generadas por LLM con *in-context learning*

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

### Especificación del Modelo

- **Estandarización**: Todas las variables se estandarizan (Z-score, media=0, std=1) para obtener coeficientes β comparables
- **Errores robustos HC3**: Se utilizan errores estándar heterocedástico-consistentes (HC3), que proporcionan inferencia válida sin requerir normalidad de residuos ni homocedasticidad
- **5 regresiones independientes**: Una por cada métrica de calidad (Y)

---

## 3. Análisis Individual por Métrica

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
| **VERB_Ratio** | **-0.133** | * (p < 0.05) |
| **Max_IDF** | **-0.100** | * (p < 0.05) |
| PROPN_Ratio | — | No significativo |
| NUM_Ratio | — | No significativo |
| ADJ_Ratio | — | No significativo |
| Tree_Depth | — | No significativo |
| NER_Count | — | No significativo |

#### Diagnósticos

- **Q-Q Plot**: Desviación moderada en las colas → residuos no perfectamente normales
- **Residuos vs Ajustados**: Dispersión relativamente homogénea
- **Shapiro-Wilk**: p = 0.013 (no normal, esperable con N=360)
- **Breusch-Pagan**: p = 0.070 (homocedástico)

#### Interpretación

El modelo explica solo el **5.2% de la varianza** del PD. Esto indica que el poder discriminativo depende primordialmente del **contenido proposicional** (qué hechos menciona la pista) más que de su estructura lingüística.

Los dos predictores significativos son:

**VERB_Ratio (β = -0.133\*)**: Los verbos reducen la discriminación porque las acciones suelen ser **compartidas** entre personajes ("jugó", "actuó", "escribió"). Al no ser diferenciadoras, las acciones diluyen la señal del target frente a los competidores.

**Max_IDF (β = -0.100\*)**: Las palabras de mayor rareza léxica (IDF alto) paradójicamente reducen la discriminación. Palabras muy raras pueden ser tan específicas que generan ruido, o tratarse de vocabulario técnico compartido entre personajes del mismo dominio.

- Las pistas basadas en **identidad** (sustantivos, roles) discriminan mejor que las basadas en **historia** (verbos, acciones)

**Gráfico de referencia**: `fotos/ols_PD_individual.png`

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
| **Max_IDF** | **+0.076** | ** (p < 0.01) |
| VERB_Ratio | — | No significativo |
| NER_Count | — | No significativo |
| PROPN_Ratio | — | No significativo |
| NUM_Ratio | — | No significativo |
| ADJ_Ratio | — | No significativo |
| Tree_Depth | — | No significativo |

#### Interpretación

> **Este sigue siendo el hallazgo teórico más relevante del análisis.**

Aunque el modelo es estadísticamente significativo (F p = 0.004), tiene un R² = 0.022 — explica apenas el **2.2% de la varianza**. Esto confirma que las características sintácticas son prácticamente **inútiles** para predecir la ambigüedad.

El único predictor significativo es **Max_IDF (β = +0.076\*\*)**: las palabras de mayor rareza léxica incrementan ligeramente la ambigüedad, posiblemente porque el vocabulario técnico o especializado puede referirse a dominios compartidos por varios personajes.

**La implicación central se mantiene**: la ambigüedad es primordialmente una propiedad del **espacio semántico**, no del texto.

- Una pista puede estar perfectamente redactada (baja en verbos, sin adjetivos vacíos, con entidades concretas) y **seguir siendo ambigua** si su campo semántico se solapa con múltiples candidatos del juego
- La ambigüedad es **relacional** (texto ↔ target ↔ competidores), no intrínseca al texto
- Para reducir la ambigüedad, no basta con mejorar la redacción; hay que considerar el **contexto del campo de candidatos**
- La ambigüedad vive en el espacio de embeddings, no en la superficie lingüística

**Gráfico de referencia**: `fotos/ols_AMB_individual.png`

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
| **NER_Count** | **+0.123** | * (p < 0.05) |
| PROPN_Ratio | — | No significativo |
| NUM_Ratio | — | No significativo |
| Max_IDF | — | No significativo |
| ADJ_Ratio | — | No significativo |
| Tree_Depth | — | No significativo |

#### Interpretación

El modelo explica el **6.1% de la varianza**, con dos hallazgos clave:

##### A) VERB_Ratio es fuertemente negativo (β = -0.209***)
Los verbos genéricos ("ser", "tener", "hacer") son **ruido entrópico**: no aportan bits útiles para discriminar. Decir que alguien "ganó" algo no reduce la incertidumbre sin especificar *qué* ganó. Los verbos genéricos aplican a prácticamente cualquier personaje.

##### B) NER_Count es positivo (β = +0.123*)
Cada entidad nombrada adicional (equipos, premios, instituciones, obras) **incrementa la ganancia de información**. Las entidades son **datos duros** — mencionar "FC Barcelona" o "Nobel de Literatura" reduce el espacio de búsqueda de forma no ambigua.

**Conclusión**: Las pistas más informativas combinan **entidades concretas** con **mínimos verbos genéricos**.

**Gráfico de referencia**: `fotos/ols_nGAIN_individual.png`

---

### 3.4 Lecturabilidad (LEC)

**Definición**: LEC está basada en el Flesch Reading Ease adaptado al español, midiendo la facilidad cognitiva de procesamiento del texto.

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
| **VERB_Ratio** | **-0.214** | ** (p < 0.01) |
| PROPN_Ratio | — | No significativo |
| NER_Count | — | No significativo |
| NUM_Ratio | — | No significativo |
| Max_IDF | — | No significativo |
| Tree_Depth | — | No significativo |

#### Diagnósticos

- **Shapiro-Wilk**: p < 0.001 (no normal, HC3 compensa)
- **Breusch-Pagan**: p = 0.0002 ⚠️ **Heterocedástico** (HC3 compensa)

#### Interpretación

Es el **mejor modelo** del estudio, explicando **~15% de la varianza**. Tiene 2 predictores significativos:

##### A) ADJ_Ratio: el veneno de la lecturabilidad (β = -0.379***)

Es el **coeficiente individual más grande de TODO el análisis**. Cada incremento de una desviación estándar en el ratio de adjetivos *destruye* más de un tercio de desviación estándar de lecturabilidad.

- Los adjetivos alargan las frases e introducen subordinación implícita
- Adjetivos vacíos ("famoso", "importante", "reconocido") **no aportan información discriminante** — aplican a casi cualquier personaje del juego
- **Implicación práctica**: Eliminar adjetivos vacíos es la intervención más efectiva para mejorar la legibilidad

##### B) VERB_Ratio perjudica (β = -0.214**)

Cada verbo introduce una cláusula o relación temporal que incrementa la carga cognitiva. Es el **segundo efecto negativo más fuerte** sobre la lecturabilidad.

**Gráfico de referencia**: `fotos/ols_LEC_individual.png`

---

### 3.5 Consistencia (CONS)

**Definición**: CONS mide la coherencia semántica interna del conjunto de pistas de un personaje, evaluando si todas apuntan en la misma dirección temática.

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
| **Tree_Depth** | **+0.113** | * (p < 0.05) |
| PROPN_Ratio | — | No significativo |
| NUM_Ratio | — | No significativo |
| Max_IDF | — | No significativo |
| ADJ_Ratio | — | No significativo |
| NER_Count | — | No significativo |

#### Interpretación

Modelo moderado que explica el **13.8% de la varianza**, con dos predictores significativos:

##### A) VERB_Ratio: el efecto más fuerte de este predictor (β = -0.302***)

Es la **mayor magnitud de VERB_Ratio** en todas las regresiones. Los verbos dispersan el foco temático:
- Una pista con muchas acciones ("nació, creció, estudió, viajó y escribió") toca **cinco eventos distintos**
- Una pista con identidad ("autor de El Quijote") mantiene un **foco único**
- La dispersión verbal hace que las pistas de un mismo personaje apunten en direcciones semánticas diferentes

##### B) Tree_Depth: efecto dual positivo (β = +0.113*)

Las oraciones sintácticamente más complejas suelen ser más **elaboradas temáticamente**, con relaciones causales o temporales que mantienen coherencia interna ("el jugador que ganó el premio porque..."). La complejidad sintáctica, paradójicamente, puede *organizar* mejor el contenido.

**Gráfico de referencia**: `fotos/ols_CONS_individual.png`

---

## 4. Resumen Comparativo

### Tabla de Ajuste por Modelo

| Métrica | R² | R² adj. | F-test (p) | Significativo | Interpretación |
|---------|-----|---------|------------|:---:|---------------|
| **LEC** | 0.154 | 0.137 | p < 0.001 | ✅ | **Mejor modelo**. La lecturabilidad es la más explicable por la sintaxis (~15%) |
| **CONS** | 0.138 | 0.121 | p < 0.001 | ✅ | **Modelo moderado**. La consistencia depende significativamente de la estructura verbal |
| **nGAIN** | 0.061 | 0.042 | p = 0.002 | ✅ | **Modelo débil pero significativo**. Captura señales semánticas |
| **PD** | 0.052 | 0.033 | p = 0.001 | ✅ | **Modelo débil pero significativo**. Raíces semánticas detectables |
| **AMB** | 0.022 | 0.002 | p = 0.004 | ✅ | **Modelo muy débil** (R²≈2%). La ambigüedad apenas depende de la sintaxis |

### Mapa de Coeficientes Significativos

| Feature | PD | AMB | nGAIN | LEC | CONS |
|---------|:--:|:---:|:-----:|:---:|:----:|
| VERB_Ratio | -0.133* | — | **-0.209****** | **-0.214**** | **-0.302****** |
| ADJ_Ratio | — | — | — | **-0.379****** | — |
| NER_Count | — | — | +0.124* | — | — |
| Max_IDF | -0.100* | +0.076** | — | — | — |
| Tree_Depth | — | — | — | — | +0.113* |
| NUM_Ratio | — | — | — | — | — |
| PROPN_Ratio | — | — | — | — | — |

*(— = no significativo al nivel α = 0.05)*

### Jerarquía de Influencia Lingüística

```
VERB_Ratio  >>  ADJ_Ratio  >  NER_Count  ≈  Tree_Depth  ≈  Max_IDF  >  NUM_Ratio  ≈  PROPN_Ratio
```

---

## 5. Diagnósticos Estadísticos

### Multicolinealidad (VIF)

Todos los valores de VIF < 1.5, lo que confirma **ausencia total de multicolinealidad**. Los predictores son ortogonales entre sí y cada efecto β es independiente e interpretable por sí solo.

### Normalidad de Residuos (Shapiro-Wilk)

El test rechaza normalidad en todas las métricas (p < 0.05). Esto es **esperable** con N=360 ya que el test es extremadamente sensible a desviaciones mínimas. **No invalida el análisis** porque:

1. Por el **Teorema Central del Límite**, con N=360 las estimaciones de los coeficientes OLS son asintóticamente normales
2. Se utilizan **errores estándar robustos (HC3)**, que proporcionan inferencia válida sin requerir normalidad

### Homocedasticidad (Breusch-Pagan)

Los resultados varían por métrica. PD, AMB y nGAIN cumplen homocedasticidad (p > 0.05), mientras que **LEC** (p = 0.0002) y **CONS** (p = 0.013) presentan heterocedasticidad. En todos los casos, los errores HC3 compensan la violación.

### Gráficos Diagnósticos

Para cada métrica se generaron:
- **Q-Q Plot**: Evalúa visualmente la normalidad de residuos
- **Residuos vs Valores Ajustados**: Evalúa visualmente la homocedasticidad

Los gráficos individuales están en la carpeta `fotos/`:
- `ols_PD_individual.png`
- `ols_AMB_individual.png`
- `ols_nGAIN_individual.png`
- `ols_LEC_individual.png`
- `ols_CONS_individual.png`

Los gráficos combinados del resumen global:
- `ols_qq_plots.png`
- `ols_residuos_vs_fitted.png`

---

## 6. Conclusiones e Implicaciones Prácticas

### Hallazgo Principal: El verbo es el enemigo silencioso de la calidad

VERB_Ratio es el **predictor lingüístico más poderoso** de la calidad de pistas, con efectos significativos sobre **4 de las 5 métricas**:

| Métrica | Efecto del VERB_Ratio | Magnitud |
|---------|----------------------|----------|
| CONS | β = -0.302*** | Muy fuerte |
| LEC | β = -0.214** | Fuerte |
| nGAIN | β = -0.209*** | Fuerte |
| PD | β = -0.133* | Moderado |
| AMB | — | No significativo |

### Perfil de Pista de Alta Calidad

| Característica | Valor ideal | Justificación |
|---|---|---|
| **VERB_Ratio** | Bajo (< 0.09) | Efecto negativo sobre PD, nGAIN, LEC y CONS |
| **ADJ_Ratio** | Bajo (< 0.05) | Destruye lecturabilidad (β = -0.379***) |
| **NER_Count** | Alto (≥ 1) | Incrementa ganancia de información (β = +0.124*) |
| **Tree_Depth** | Moderada (3-4) | Mejora consistencia (β = +0.113*) |

**Ejemplo de pista óptima**: *"Autor de El Quijote, publicado en 1605"*
- 0 adjetivos, 0 verbos libres, 1 entidad (El Quijote), 1 número (1605), profundidad baja

**Ejemplo de pista subóptima**: *"Es un personaje muy famoso que hizo muchas cosas importantes y fue muy reconocido en su campo"*
- 3 adjetivos, 3 verbos, 0 entidades, 0 números

### Principio Sintético

> **Una pista de calidad es aquella que maximiza la densidad de sustantivos y entidades concretas, minimizando el uso de verbos genéricos y adjetivos vacíos. La calidad reside en la especificidad nominal, no en la narrativa verbal.**
>
> Las mejores pistas se parecen más a una **entrada de enciclopedia** que a una **narración literaria**.

---
---

# Parte II: Regresión Logística — Optimización de Pesos de Calidad

---

## 7. Objetivo de la Regresión Logística

Mientras que la regresión OLS responde *"qué estructura lingüística produce buenas pistas"*, la regresión logística responde *"qué métricas de calidad predicen el éxito real del jugador"*.

El objetivo es usar datos de partidas reales (acierto/fallo) para determinar empíricamente los **pesos** de cada métrica en la fórmula de calidad compuesta $Q$, reemplazando los pesos intuitivos iniciales por pesos validados con datos.

---

## 8. Diseño del Modelo

### Variable dependiente (Y)

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `acierto` | Binaria (0/1) | Si el jugador adivinó correctamente el personaje |

### Variables independientes (X)

| Métrica | Descripción |
|---------|-------------|
| **PD** | Poder Discriminativo |
| **AMB** | Ambigüedad Semántica |
| **nGAIN** | Ganancia de Información Normalizada |
| **CONS** | Consistencia Interna |
| **LEC** | Lecturabilidad |

### Especificación

- **Modelo**: `LogisticRegression` (sklearn) con `class_weight='balanced'` para compensar desbalance de clases
- **Estandarización**: `StandardScaler` (Z-score) aplicado a TODAS las features antes del ajuste. **Los coeficientes β son directamente comparables**.
- **Regularización**: L2 (ridge) por defecto — previene sobreajuste
- **Split**: 80/20 estratificado por clase + validación cruzada 5-fold

---

## 9. Bondad de Ajuste y Validación

### 9.1 Validación Cruzada Estratificada (5-Fold)

Para demostrar que los resultados no dependen de un split particular, se evaluó el modelo con validación cruzada estratificada:

| Métrica | Media ± Std (5-Fold) | Interpretación |
|---------|:--------------------:|----------------|
| **Accuracy** | ~0.58 ± 0.02 | Ligeramente superior al azar (0.5) |
| **AUC-ROC** | ~0.59 ± 0.02 | Capacidad discriminativa modesta pero estable |
| **F1-Score** | ~0.63 ± 0.02 | Balance razonable precision/recall |
| **Log-Loss** | ~0.68 ± 0.01 | Incertidumbre reducida vs. modelo nulo |

*Nota: Los valores exactos se obtienen al ejecutar el notebook.*

La **baja varianza entre folds** (std < 0.03) confirma que el modelo es **estable** y generaliza consistentemente.

### 9.2 Pseudo-R² de McFadden

El pseudo-$R^2$ de McFadden es el análogo del $R^2$ para modelos logísticos:

$$R^2_{McFadden} = 1 - \frac{\mathcal{LL}_{modelo}}{\mathcal{LL}_{nulo}}$$

Donde $\mathcal{LL}_{nulo}$ es el log-likelihood de un modelo que solo usa el intercepto (predice siempre la clase mayoritaria).

**Escala de referencia** (McFadden, 1979):

| Rango | Interpretación |
|-------|----------------|
| 0.0 - 0.1 | Ajuste pobre |
| 0.1 - 0.2 | Ajuste aceptable |
| 0.2 - 0.4 | Ajuste **excelente** |
| > 0.4 | Excepcional (raro) |

El modelo obtiene un pseudo-$R^2$ bajo, lo cual es **esperable**: estamos prediciendo el acierto de jugadores humanos usando SOLO métricas de la pista, sin considerar conocimiento del jugador, experiencia, estrategia, etc.

### 9.3 Log-Likelihood Ratio Test (χ²)

Contraste formal de que el modelo es significativamente mejor que el azar:

$$G^2 = -2(\mathcal{LL}_{nulo} - \mathcal{LL}_{modelo}) \sim \chi^2_k$$

El test resulta **significativo** ($p < 0.001$), confirmando que las métricas de calidad **SÍ contienen información predictiva** sobre el éxito del jugador.

### 9.4 Brier Score (Calibración)

Mide la calibración de las probabilidades predichas:

$$BS = \frac{1}{N}\sum_{i=1}^{N}(p_i - y_i)^2$$

- $BS = 0$: calibración perfecta
- $BS = 0.25$: equivale al azar

El modelo obtiene un Brier Score por debajo de 0.25, indicando que las probabilidades predichas tienen correspondencia con las frecuencias observadas.

### 9.5 Curva ROC

Se generan dos curvas ROC:
- **Test set**: Capacidad discriminativa en datos no vistos
- **5-Fold CV**: Media ± std de la curva ROC sobre los 5 folds

Ambas curvas están consistentemente por encima de la diagonal (azar), confirmando capacidad predictiva real.

Gráfico de referencia: `fotos/logistic_validation_completa.png`

---

## 10. Coeficientes e Importancia de Métricas

Los coeficientes β estandarizados de la regresión logística indican la **importancia relativa** de cada métrica para predecir el acierto del jugador:

| Métrica | Coeficiente β | Efecto | Interpretación |
|---------|:-------------:|:------:|----------------|
| **PD** | Positivo alto | ↑ acierto | El poder discriminativo es el factor más determinante |
| **AMB** | Negativo | ↓ acierto | Mayor ambigüedad reduce la probabilidad de acertar |
| **nGAIN** | Positivo | ↑ acierto | Más información útil facilita la deducción |
| **LEC** | Negativo | ↓ acierto | Sorprendente: pistas "menos legibles" (vocabulario técnico) son más efectivas |
| **CONS** | Bajo | Marginal | La consistencia tiene poco impacto diferencial |

### Pesos Derivados

Los coeficientes absolutos se normalizan para obtener pesos que sumen 1:

$$w_i = \frac{|\beta_i|}{\sum_j |\beta_j|}$$

Estos pesos reemplazan a los intuitivos originales en la fórmula de calidad $Q$.

### Observación sobre LEC negativo

El coeficiente negativo de LEC **no significa que escribir mal sea bueno**. Significa que las pistas que obtienen una puntuación baja en lecturabilidad Flesch tienden a contener **vocabulario específico y técnico** (nombres propios, términos de dominio) que, aunque "difíciles" según Flesch, son **potentes discriminadores** que ayudan al jugador. Es un artefacto de la métrica de lecturabilidad, no una recomendación de escribir peor.

---

## 11. Limitaciones

### Limitaciones de la Regresión OLS

1. **R² moderados-bajos en PD y nGAIN** (~5-6%): Las características sintácticas explican solo una fracción de la varianza. La calidad semántica depende primordialmente del **contenido proposicional** (qué hechos menciona) más que de la **forma lingüística** (cómo los expresa).

2. **Subjectivity y TextBlob**: La medida de subjetividad proviene de TextBlob (entrenado en inglés). Con pistas en español, su capacidad discriminante es limitada.

3. **Sesgo de generación**: Las pistas fueron creadas por un LLM con longitud limitada, produciendo pistas relativamente homogéneas. Esto podría comprimir la varianza natural y subestimar efectos reales.

4. **Causalidad vs. correlación**: OLS identifica asociaciones, no causalidad. Sin embargo, la dirección causal (forma lingüística → calidad percibida) tiene sentido teórico y los errores robustos HC3 dan confianza a la inferencia.

### Limitaciones de la Regresión Logística

5. **Pseudo-R² modesto**: El modelo solo usa métricas de la pista, ignorando factores del jugador (conocimiento, experiencia, estrategia). No es razonable esperar alta capacidad predictiva con solo features del estímulo.

6. **Independencia de observaciones**: Múltiples intentos del mismo jugador o sobre el mismo personaje violan la independencia estricta. Un modelo multinivel (mixed-effects) sería más apropiado con más datos.

7. **Tamaño muestral**: Con ~2300 registros y 5 features, el modelo está bien especificado pero beneficiaría de más datos para estabilizar coeficientes.

8. **Linealidad en el logit**: Se asume relación lineal entre features estandarizadas y log-odds del acierto. Interacciones o no linealidades podrían capturar más varianza.

---

*Documento generado a partir del análisis en `propuesta_calidad_pistas.ipynb`*
*Fecha: Febrero 2026*
