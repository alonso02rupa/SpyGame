# Análisis de Calidad de Pistas en un Sistema de Adivinación Basado en Similitud Semántica

---

## Índice

1. [Metodología](#1-metodología)
   - 1.1 [Contexto y diseño del sistema](#11-contexto-y-diseño-del-sistema)
   - 1.2 [Representación semántica mediante embeddings](#12-representación-semántica-mediante-embeddings)
   - 1.3 [Diseño del sistema de métricas de calidad](#13-diseño-del-sistema-de-métricas-de-calidad)
   - 1.4 [Extracción de características lingüísticas](#14-extracción-de-características-lingüísticas)
   - 1.5 [Modelos de regresión empleados](#15-modelos-de-regresión-empleados)
2. [Evaluación](#2-evaluación)
   - 2.1 [Métricas de calidad latente](#21-métricas-de-calidad-latente)
   - 2.2 [Función de calidad compuesta Q](#22-función-de-calidad-compuesta-q)
   - 2.3 [Características semánticas y lingüísticas](#23-características-semánticas-y-lingüísticas)
3. [Resultados](#3-resultados)
   - 3.1 [Distribución de las métricas de calidad](#31-distribución-de-las-métricas-de-calidad)
   - 3.2 [Estructura correlacional de las métricas](#32-estructura-correlacional-de-las-métricas)
   - 3.3 [Determinación empírica de pesos: regresión logística](#33-determinación-empírica-de-pesos-regresión-logística)
   - 3.4 [Comparación entre Q original y Q optimizada](#34-comparación-entre-q-original-y-q-optimizada)
   - 3.5 [Regresión explicativa: de la sintaxis a la calidad](#35-regresión-explicativa-de-la-sintaxis-a-la-calidad)
   - 3.6 [Diagnóstico de multicolinealidad](#36-diagnóstico-de-multicolinealidad)
4. [Conclusiones](#4-conclusiones)
   - 4.1 [Definición formal de pista](#41-definición-formal-de-pista)
   - 4.2 [Perfil empírico de una pista de calidad](#42-perfil-empírico-de-una-pista-de-calidad)
   - 4.3 [Limitaciones del estudio](#43-limitaciones-del-estudio)
   - 4.4 [Líneas de trabajo futuro](#44-líneas-de-trabajo-futuro)
   - 4.5 [Contribución del proyecto](#45-contribución-del-proyecto)

---

## 1. Metodología

### 1.1 Contexto y diseño del sistema

El presente trabajo se enmarca en el análisis de un juego de adivinación (*SpyGame*) cuya mecánica central enfrenta a los jugadores con la tarea de identificar a un personaje objetivo a partir de pistas textuales. El sistema opera bajo las siguientes restricciones:

- Un catálogo fijo de **45 personajes** que constituyen el espacio de estados posibles.
- **8 pistas** predefinidas por personaje, distribuidas en niveles de dificultad progresiva y con duplicados ocasionales entre niveles.
- **Guesses de texto libre**: los jugadores introducen sus respuestas en lenguaje natural, sin restricción de formato.
- **Similitud semántica** como mecanismo de evaluación: la corrección de una respuesta se determina mediante la proximidad vectorial entre el *guess* del jugador y el nombre del personaje objetivo en un espacio de embeddings.

Este diseño plantea un problema que no puede abordarse con paradigmas clásicos de clasificación o *question-answering*. No existe una respuesta binaria correcta/incorrecta a nivel de la pista; lo que existe es un **gradiente de utilidad** que depende de cuánto reduce la incertidumbre del jugador. Por ello, el enfoque adoptado es el de **ranking y desplazamiento semántico**: evaluar la capacidad de cada pista para desplazar la distribución de probabilidad del jugador hacia el personaje correcto.

### 1.2 Representación semántica mediante embeddings

La representación vectorial de personajes, pistas y *guesses* se realizó mediante el modelo `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, un modelo multilingüe pre-entrenado optimizado para tareas de similitud semántica. Este modelo proyecta textos en español a un espacio vectorial de 384 dimensiones donde la similitud del coseno entre vectores refleja la proximidad semántica de los textos que representan.

Se calcularon embeddings para tres tipos de entidades:

- **Personajes**: el nombre de cada uno de los 45 personajes del catálogo.
- **Pistas**: el texto completo de cada una de las 360 pistas (45 personajes × 8 pistas).
- **Guesses**: las respuestas de texto libre de los jugadores, registradas en 2.293 interacciones reales.

La elección de un modelo multilingüe se justifica por la necesidad de operar en español sin sacrificar la calidad de las representaciones semánticas. El modelo seleccionado ha demostrado rendimiento competitivo en tareas de *semantic textual similarity* (STS) para lenguas romances.

### 1.3 Diseño del sistema de métricas de calidad

El sistema de evaluación de calidad se construyó sobre una premisa fundamental: la calidad de una pista no es una propiedad intrínseca del texto, sino una propiedad **relacional** que emerge de la interacción entre el texto de la pista, el personaje objetivo y el campo semántico del juego (los 45 candidatos). En consecuencia, se diseñaron métricas que capturan esta relación tripartita.

Se definieron cinco métricas latentes de calidad (*core metrics*), complementadas por un factor de penalización y una función compuesta:

1. **Poder Discriminativo (PD)**: capacidad de la pista para separar al personaje objetivo del resto.
2. **Ambigüedad Normalizada (AMB)**: grado de confusión con el competidor semántico más cercano.
3. **Ganancia de Información Normalizada (nGAIN)**: reducción de la entropía del espacio de candidatos.
4. **Consistencia Interna (CONS)**: coherencia semántica dentro de la propia pista.
5. **Lecturabilidad (LEC)**: facilidad de decodificación lingüística del texto.
6. **CLAMP**: factor de penalización por sobre-especificidad.
7. **Q**: función de calidad compuesta que integra las métricas anteriores.

### 1.4 Extracción de características lingüísticas

Para investigar la relación entre la estructura lingüística de las pistas y su calidad medida, se implementó un extractor de características basado en procesamiento de lenguaje natural. Se emplearon las siguientes herramientas:

- **spaCy** (`es_core_news_sm`): modelo de NLP en español para *part-of-speech tagging*, análisis de dependencias sintácticas y reconocimiento de entidades nombradas (NER).
- **TF-IDF** (scikit-learn): para el cálculo de la rareza léxica de cada término en el contexto del corpus completo de pistas.
- **TextBlob**: para la estimación de subjetividad.
- **textstat**: para el cálculo de índices de lecturabilidad (Flesch Reading Ease).

Las características se organizaron en cuatro estratos funcionales:

| Estrato | Características | Justificación |
|---|---|---|
| **Ancla** (Sustancia) | `PROPN_Ratio`, `NUM_Ratio`, `Max_IDF` | Elementos que anclan al receptor en hechos concretos e identificables |
| **Ruido** (Descripción) | `ADJ_Ratio`, `Subjectivity` | Elementos que aportan color descriptivo pero diluyen la precisión |
| **Acción** (Contexto) | `VERB_Ratio` | Verbos que sitúan al objetivo en una narrativa dinámica |
| **Estructura** (Forma) | `Tree_Depth`, `NER_Count` | Elementos que determinan la complejidad cognitiva de decodificación |

Todas las ratios se calcularon como **proporción sobre el total de tokens válidos** (excluyendo puntuación y espacios), lo que neutraliza el efecto de la longitud de la frase sobre la medida.

### 1.5 Modelos de regresión empleados

Se aplicaron dos familias de modelos de regresión con objetivos complementarios:

**a) Regresión logística (clasificación).** Modelo supervisado entrenado sobre 2.293 interacciones reales, donde la variable dependiente es el acierto del jugador (binaria: acierto/fallo) y las variables independientes son las cinco métricas de calidad (PD, AMB, nGAIN, CONS, LEC). El objetivo de este modelo es doble: evaluar la capacidad predictiva de las métricas sobre el comportamiento real de los jugadores y extraer pesos empíricos para la función de calidad Q.

**b) Regresión lineal múltiple OLS con coeficientes estandarizados.** Se ajustaron cinco modelos OLS independientes, uno por cada métrica de calidad como variable dependiente, utilizando como predictores las ocho características lingüísticas extraídas por NLP. Todas las variables se estandarizaron (*z-score*) previamente para obtener coeficientes beta comparables. El objetivo es explicar qué propiedades lingüísticas de la pista influyen en cada dimensión de la calidad.

---

## 2. Evaluación

### 2.1 Métricas de calidad latente

A continuación se presenta la definición formal y la justificación de cada una de las métricas diseñadas.

#### 2.1.1 Poder Discriminativo (PD)

$$PD = \text{sim}(h, t) - \frac{1}{N-1} \sum_{i \neq t} \text{sim}(h, c_i)$$

donde $h$ es el embedding de la pista, $t$ el del personaje objetivo y $c_i$ los de los restantes candidatos. La similitud empleada es la similitud del coseno.

**Interpretación**: PD mide cuánto destaca el personaje objetivo respecto al promedio del campo cuando se observa desde la pista. Un PD alto indica que la pista apunta de forma clara y diferenciada hacia su objetivo. Un PD negativo indicaría que la pista está, en promedio, más cerca de otros personajes que de su propio target, lo que constituye una señal de baja calidad.

**Justificación**: esta métrica es esencial porque captura la función primaria de una pista — señalar al objetivo. Sin capacidad discriminativa, la pista no cumple su propósito independientemente de lo bien escrita que esté.

#### 2.1.2 Ambigüedad Normalizada (AMB)

$$AMB = \frac{\text{sim}_{\text{rival}}}{\text{sim}_{\text{rival}} + \text{sim}_{\text{target}}}$$

donde $\text{sim}_{\text{rival}} = \max_{i \neq t} \text{sim}(h, c_i)$ es la similitud con el competidor más peligroso.

**Interpretación**: AMB toma valores en $[0, 1]$. Un valor de $0.5$ indica que el rival y el target están igualmente activados por la pista — máxima ambigüedad. Valores cercanos a 0 indican que el target domina completamente. A diferencia de PD, que compara contra el *promedio*, AMB se focaliza en el *peor caso*: el competidor individual más confuso.

**Justificación**: dos pistas pueden tener el mismo PD pero distinta AMB si una distribuye su similitud uniformemente entre muchos personajes (dispersión benigna) y otra concentra toda la confusión en un único rival (confusión peligrosa).

#### 2.1.3 Ganancia de Información Normalizada (nGAIN)

$$nGAIN = \frac{H_0 - H(P(s|h))}{H_0}$$

donde $H_0 = \log(N)$ es la entropía máxima (distribución uniforme sobre los $N = 45$ candidatos) y $H(P(s|h))$ es la entropía de la distribución *a posteriori* obtenida aplicando *softmax* con temperatura $\tau = 0.05$ sobre las similitudes del coseno entre la pista y todos los candidatos.

**Interpretación**: nGAIN mide la fracción de incertidumbre total que la pista elimina. Un valor de 1 indica reducción completa (certeza absoluta), mientras que 0 indica que la pista no aporta información útil. La elección de $\tau = 0.05$ amplifica las diferencias entre similitudes para producir distribuciones más concentradas, lo que permite una mejor discriminación entre pistas de calidad variable.

**Justificación**: desde una perspectiva teórico-informacional, esta métrica captura directamente la utilidad epistémica de la pista como reductora de entropía. Es la métrica más cercana al concepto teórico de *información*.

#### 2.1.4 Consistencia Interna (CONS)

Se calcula mediante una técnica de ventana deslizante:

1. Se divide el texto de la pista en ventanas de 3 palabras consecutivas.
2. Se calculan los embeddings de cada ventana.
3. Se mide la similitud del coseno entre ventanas consecutivas.
4. CONS es el promedio de estas similitudes.

**Interpretación**: CONS mide la coherencia temática interna de la pista. Una pista que salta entre temas no relacionados obtendrá un score bajo, mientras que una pista que mantiene un hilo conductor temático obtendrá un score alto.

**Justificación**: la consistencia temática es un requisito de calidad textual independiente de la relación pista-personaje. Una pista puede tener alto PD y alto nGAIN pero ser internamente incoherente, lo que dificultaría su procesamiento cognitivo.

#### 2.1.5 Lecturabilidad (LEC)

$$LEC = \frac{1}{1 + e^{-(F - 50)/10}}$$

donde $F$ es el índice Flesch Reading Ease del texto.

**Interpretación**: la función sigmoide mapea el score Flesch (teóricamente $(-\infty, +\infty)$, típicamente $[0, 100]$) a un rango $(0, 1)$ de forma suave, con centro en $F = 50$ y una pendiente de transición controlada por el denominador $10$. Valores cercanos a 1 indican textos muy legibles; cercanos a 0, textos difíciles.

**Justificación**: la facilidad de lectura actúa como un modulador de la eficacia de la pista. Una pista con alto contenido informativo pero redactada de forma ininteligible no puede cumplir su función porque el jugador no consigue decodificarla.

#### 2.1.6 Penalización por sobre-especificidad (CLAMP)

$$CLAMP = \begin{cases} e^{-10 \cdot (\text{sim}_t - 0.9)} & \text{si } \text{sim}_t > 0.9 \\ 1.0 & \text{en caso contrario} \end{cases}$$

**Interpretación**: CLAMP penaliza exponencialmente las pistas cuya similitud con el target supera el umbral de 0.9, ya que una similitud tan elevada indica que la pista prácticamente *contiene* el nombre del personaje o una referencia inequívoca que trivializa el juego.

**Justificación**: el diseño de un juego educativo requiere que las pistas reduzcan la incertidumbre *de forma calibrada*, no que la eliminen completamente. Una pista que dice directamente quién es el personaje pierde su valor pedagógico y lúdico.

### 2.2 Función de calidad compuesta Q

La función Q integra las cinco métricas en un score único, modulado por CLAMP:

$$Q = CLAMP \cdot \left( w_{PD} \cdot PD + w_{AMB} \cdot (1 - 1.5 \cdot AMB) + w_{nGAIN} \cdot nGAIN + w_{CONS} \cdot CONS + w_{LEC} \cdot LEC \right)$$

Los pesos $w_i$ se definieron inicialmente de forma teórica (basados en una jerarquización pedagógica) y posteriormente se optimizaron de forma empírica mediante regresión logística sobre datos reales de partidas.

| Métrica | Peso teórico | Peso optimizado | Variación |
|---|---|---|---|
| PD | 0.200 | 0.335 | +67.7% |
| AMB | 0.200 | 0.215 | +7.3% |
| nGAIN | 0.300 | 0.139 | −53.7% |
| CONS | 0.150 | 0.009 | −94.3% |
| LEC | 0.150 | 0.303 | +101.7% |

La jerarquía teórica, que priorizaba nGAIN como métrica dominante, fue parcialmente revertida por los datos empíricos, que revelaron que el Poder Discriminativo y la Lecturabilidad son los factores más determinantes en el acierto real de los jugadores.

### 2.3 Características semánticas y lingüísticas

Las ocho características extraídas para cada pista se definen como sigue:

| Característica | Definición | Rango típico |
|---|---|---|
| `PROPN_Ratio` | Fracción de tokens clasificados como sustantivos propios (nombres de personas, lugares, organizaciones) | [0, 0.43] |
| `NUM_Ratio` | Fracción de tokens numéricos (años, cantidades) | [0, 0.30] |
| `Max_IDF` | Valor IDF máximo entre todos los tokens de la pista, calculado sobre el corpus completo de 360 pistas | [4.81, 6.20] |
| `ADJ_Ratio` | Fracción de tokens clasificados como adjetivos | [0, 0.42] |
| `Subjectivity` | Score de subjetividad (0 = objetivo, 1 = subjetivo) estimado mediante TextBlob | [0, 1.0] |
| `VERB_Ratio` | Fracción de tokens clasificados como verbos | [0, 0.29] |
| `Tree_Depth` | Profundidad máxima del árbol de dependencias sintácticas | [2, 10] |
| `NER_Count` | Número absoluto de entidades nombradas reconocidas por el modelo NER | [0, 4] |

---

## 3. Resultados

### 3.1 Distribución de las métricas de calidad

El análisis descriptivo de las métricas sobre las 360 pistas del catálogo revela distribuciones diferenciadas para cada dimensión de la calidad.

<!-- Figura 1: Distribución de Métricas de Calidad de Pistas (histogramas de PD, AMB, nGAIN, CONS, LEC, CLAMP y Q) -->
> **Figura 1.** Distribución de las métricas de calidad sobre las 360 pistas del catálogo. Se muestra la mediana de cada distribución (línea roja discontinua).

Las principales observaciones son:

- **PD** presenta una distribución aproximadamente normal centrada en torno a 0.10, con un rango que abarca valores negativos (pistas que están más cerca de otros personajes que de su target). Esto indica que existe una proporción no despreciable de pistas cuyo poder discriminativo es deficiente.
- **AMB** muestra una distribución asimétrica positiva con concentración entre 0.45 y 0.65, lo que sugiere que la mayoría de las pistas padecen un grado sustancial de ambigüedad respecto a su competidor más cercano.
- **nGAIN** se distribuye de forma amplia entre 0.15 y 0.75, lo que indica una heterogeneidad notable en la capacidad informativa de las pistas.
- **CONS** se concentra fuertemente en la región alta (0.70–0.85), con escasa varianza. Esta homogeneidad es atribuible al proceso de generación de las pistas (modelos de lenguaje con restricción de longitud), que produce textos breves y temáticamente coherentes por diseño.
- **LEC** exhibe una distribución bimodal, con un grupo de pistas de baja legibilidad (textos técnicos o con vocabulario específico) y otro de alta legibilidad (textos sencillos y directos). Esta bimodalidad es relevante porque, como se demostrará, la legibilidad tiene un rol paradójico en la calidad.
- **CLAMP** presenta una distribución degenerada: la inmensa mayoría de las pistas obtienen un valor de 1.0 (sin penalización), lo que indica que la sobre-especificidad no es un problema prevalente en el corpus actual.
- **Q** manifiesta una distribución unimodal con media 0.354 y desviación estándar 0.118, lo que implica que el score compuesto logra discriminar entre pistas pero dentro de un rango relativamente comprimido.

### 3.2 Estructura correlacional de las métricas

El análisis de correlación de Pearson entre las métricas revela relaciones estructurales de gran interés teórico.

<!-- Figura 2: Matriz de Correlación entre Métricas de Calidad (heatmap) -->
> **Figura 2.** Matriz de correlación de Pearson entre las métricas de calidad. Se aprecian tres clusters funcionales claramente diferenciados.

Los hallazgos más relevantes son:

- **PD y AMB** presentan una correlación negativa muy fuerte ($r = -0.80$), lo que confirma que son dos caras de la misma moneda: a mayor poder discriminativo, menor ambigüedad. Sin embargo, el hecho de que la correlación no sea perfecta ($|r| < 1$) justifica mantener ambas métricas como dimensiones separadas, puesto que capturan matices distintos (PD mide contra el promedio del campo; AMB, contra el peor caso individual).
- **PD y nGAIN** correlacionan positivamente ($r = 0.62$), lo cual es esperable: las pistas que separan bien al target del campo también reducen la entropía. La magnitud moderada de esta correlación indica que son métricas complementarias, no redundantes.
- **Q** está fuertemente correlacionada con PD ($r = 0.83$) y nGAIN ($r = 0.76$), y negativamente con AMB ($r = -0.68$), lo que valida que la función compuesta captura las dimensiones de calidad más relevantes.
- **CONS** y **LEC** muestran correlaciones débiles con el resto de métricas ($|r| < 0.15$), lo que confirma que son dimensiones ortogonales que capturan aspectos de la calidad textual no cubiertos por las métricas semánticas.
- **CLAMP** presenta valores NaN por su distribución degenerada (varianza prácticamente nula), lo que la excluye del análisis correlacional.

### 3.3 Determinación empírica de pesos: regresión logística

Se entrenó un modelo de regresión logística sobre 2.293 interacciones reales de jugadores (65.5% aciertos, 34.5% fallos) para determinar el impacto relativo de cada métrica sobre la probabilidad de acierto. El conjunto de datos se dividió en entrenamiento (80%, $n = 1834$) y test (20%, $n = 459$) con estratificación de la variable objetivo. Las características se estandarizaron previamente ($\mu = 0, \sigma = 1$) para garantizar la comparabilidad de los coeficientes.

<!-- Figura 3: Impacto de cada métrica en la probabilidad de acierto (barplot horizontal) y Pesos Originales vs Detectados por Regresión (barplot comparativo) -->
> **Figura 3.** Izquierda: coeficientes $\beta$ de la regresión logística (verde = incrementa acierto, rojo = lo disminuye). Derecha: comparación entre los pesos teóricos y los pesos derivados de los datos.

El modelo alcanzó una *accuracy* de 0.564 y un AUC-ROC de 0.590 en el conjunto de test. Si bien estas cifras pueden parecer modestas, es necesario contextualizarlas: el modelo solo utiliza propiedades de la pista como predictores, sin considerar la habilidad del jugador, el número de pistas previas reveladas ni el conocimiento previo del jugador sobre el personaje. En este contexto, un AUC de 0.59 indica que las métricas de calidad de la pista contribuyen de forma real, aunque modesta, a explicar el acierto.

Los coeficientes del modelo revelan la siguiente jerarquía de importancia:

| Métrica | Coeficiente $\beta$ | Importancia absoluta | Dirección |
|---|---|---|---|
| PD | +0.112 | 0.112 | Incrementa acierto |
| LEC | −0.101 | 0.101 | Decrementa acierto |
| AMB | −0.072 | 0.072 | Decrementa acierto |
| nGAIN | +0.046 | 0.046 | Incrementa acierto |
| CONS | −0.003 | 0.003 | Efecto nulo |

La interpretación del coeficiente negativo de LEC resulta especialmente relevante: una mayor legibilidad (texto más sencillo) **disminuye** la probabilidad de acierto. Este resultado, inicialmente contraintuitivo, se explica por el hecho de que la lecturabilidad baja suele ser consecuencia del uso de vocabulario técnico o específico, el cual actúa como un potente discriminador. Una pista que menciona *"relatividad"* obtiene un score Flesch bajo pero apunta directamente a Einstein.

Se evaluó la inclusión de CLAMP en el modelo, resultando en un coeficiente de exactamente 0.000 y sin mejora en *accuracy* ni AUC (ambos invariantes en 0.564 y 0.590, respectivamente), lo que confirma la irrelevancia de esta penalización en el corpus actual.

<!-- Figura 4: Matriz de Confusión y Distribución de Probabilidades Predichas -->
> **Figura 4.** Izquierda: Matriz de confusión del modelo de regresión logística. Derecha: distribución de las probabilidades predichas para aciertos (verde) y fallos (rojo). El solapamiento indica la dificultad inherente de la tarea predictiva.

La matriz de confusión muestra 172 verdaderos positivos, 87 verdaderos negativos, 72 falsos positivos y 128 falsos negativos. El modelo presenta un *recall* del 57% para aciertos y del 55% para fallos, con un *F1-score* ponderado de 0.57. La distribución de probabilidades predichas (Figura 4, derecha) evidencia un solapamiento sustancial entre las clases, lo que refleja la complejidad del problema: muchos factores ajenos a la calidad intrínseca de la pista influyen en el acierto del jugador.

### 3.4 Comparación entre Q original y Q optimizada

Tras la determinación empírica de los pesos, se recalculó la función Q con los nuevos coeficientes y se compararon ambas versiones.

<!-- Figura 5: Análisis Comparativo de Calidad de Pistas (histogramas superpuestos, box plots, violin plots, scatter, estadísticas) -->
> **Figura 5.** Comparación multidimensional entre Q original (azul) y Q optimizada (púrpura). La correlación de Pearson entre ambas es $r = 0.912$.

Las estadísticas comparativas revelan:

|  | Q Original | Q Optimizada |
|---|---|---|
| Media | 0.3542 | 0.2750 |
| Mediana | 0.3353 | 0.2730 |
| Desviación estándar | 0.1181 | 0.1385 |
| Mínimo | −0.0902 | −0.1511 |
| Máximo | 0.6879 | 0.6081 |

Se observa que:

- La Q optimizada tiene una **media más baja** (0.275 vs 0.354), lo que indica que los pesos empíricos son más estrictos: penalizan más las deficiencias reales.
- La Q optimizada tiene una **mayor dispersión** ($\sigma = 0.139$ vs $\sigma = 0.118$), lo que mejora su capacidad discriminante: separa mejor las pistas buenas de las malas.
- La **correlación de 0.912** confirma que ambas métricas miden el mismo constructo latente pero con distinta calibración. La Q optimizada no contradice la teórica; la refina.
- El *scatter plot* muestra que la relación es fuertemente lineal pero con una pendiente ligeramente inferior a 1, indicando que la Q optimizada comprime el rango superior y expande el inferior.

### 3.5 Regresión explicativa: de la sintaxis a la calidad

Se ajustaron cinco modelos de regresión lineal múltiple OLS, uno por cada métrica de calidad como variable dependiente, utilizando las ocho características lingüísticas como predictores. Todas las variables fueron estandarizadas previamente para obtener coeficientes $\beta$ comparables. El análisis se realizó sobre $n = 360$ pistas.

#### 3.5.1 Ajuste global de los modelos

| Métrica | $R^2$ | $R^2_{adj}$ | F-test (p-valor) | Significación del modelo |
|---|---|---|---|---|
| **LEC** | 0.239 | 0.222 | $p < 0.001$ | Altamente significativo |
| **CONS** | 0.138 | 0.118 | $p < 0.001$ | Altamente significativo |
| **nGAIN** | 0.065 | 0.044 | $p = 0.003$ | Significativo |
| **PD** | 0.053 | 0.031 | $p = 0.014$ | Significativo |
| **AMB** | 0.022 | −0.001 | $p = 0.452$ | No significativo |

La Lecturabilidad es la métrica mejor explicada por las características lingüísticas, con un $R^2 = 0.239$, lo que indica que la sintaxis explica casi una cuarta parte de la varianza de la legibilidad. La Consistencia también presenta un ajuste apreciable ($R^2 = 0.138$). En cambio, las métricas más semánticas (PD, nGAIN) muestran $R^2$ bajos pero estadísticamente significativos, lo que revela que la sintaxis explica solo una fracción de su varianza. La Ambigüedad resulta completamente inexpicable por los rasgos lingüísticos superficiales.

#### 3.5.2 Tabla de coeficientes estandarizados

<!-- Figura 6: Coeficientes estandarizados - barplots para cada métrica con significancia coloreada -->
> **Figura 6.** Coeficientes estandarizados $\beta$ de las regresiones OLS para cada métrica de calidad. Colores: rojo oscuro = $p < 0.001$, naranja = $p < 0.01$, amarillo = $p < 0.05$, gris = no significativo.

| Característica | PD | AMB | nGAIN | LEC | CONS |
|---|---|---|---|---|---|
| **VERB_Ratio** | −0.133* | n.s. | **−0.209***| **−0.152**| **−0.302***|
| **ADJ_Ratio** | n.s. | n.s. | n.s. | **−0.429***| n.s. |
| **NER_Count** | n.s. | n.s. | +0.123* | n.s. | n.s. |
| **NUM_Ratio** | n.s. | n.s. | n.s. | +0.122* | n.s. |
| **Tree_Depth** | n.s. | n.s. | n.s. | −0.119* | +0.113* |
| **PROPN_Ratio** | n.s. | n.s. | n.s. | n.s. | n.s. |
| **Max_IDF** | n.s. | n.s. | n.s. | n.s. | n.s. |
| **Subjectivity** | n.s. | n.s. | n.s. | n.s. | n.s. |

*Significancia: \*\*\* p < 0.001, \*\* p < 0.01, \* p < 0.05, n.s. = no significativo.*

#### 3.5.3 Interpretación detallada de los hallazgos

**El ratio de verbos como predictor transversal.** El hallazgo más robusto y consistente del análisis es el efecto negativo del `VERB_Ratio` sobre cuatro de las cinco métricas de calidad. Es la única característica lingüística con significación estadística sobre múltiples dimensiones simultáneamente:

- Sobre CONS ($\beta = -0.302, p < 0.001$): es el efecto más intenso de todo el estudio. Los verbos introducen acciones que dispersan el foco temático de la pista. Una pista que concatena múltiples acciones (*"nació, estudió, viajó, escribió"*) pierde coherencia interna frente a una focalizada (*"autor de El Quijote"*).
- Sobre nGAIN ($\beta = -0.209, p < 0.001$): los verbos genéricos (*ser, tener, hacer*) constituyen ruido entrópico que no aporta información diferenciadora. La acción *"jugó al fútbol"* aplica a decenas de personajes; el nombre propio *"FC Barcelona"* aplica a pocos.
- Sobre LEC ($\beta = -0.152, p < 0.01$): cada verbo introduce una cláusula o relación temporal adicional que incrementa la carga cognitiva de decodificación.
- Sobre PD ($\beta = -0.133, p < 0.05$): las acciones tienden a ser compartidas entre personajes del mismo campo semántico, lo que diluye la capacidad discriminativa de la pista.

**El ratio de adjetivos como destructor de la lecturabilidad.** El `ADJ_Ratio` presenta el coeficiente individual más grande del estudio ($\beta = -0.429, p < 0.001$) sobre LEC. Cada incremento de una desviación estándar en el ratio de adjetivos destruye casi media desviación estándar de legibilidad. Los adjetivos alargan las frases, introducen subordinación implícita y, críticamente, no aportan información discriminante: *"famoso"*, *"importante"* y *"reconocido"* se aplican por igual a prácticamente cualquier personaje del catálogo.

**Las entidades nombradas como vehículos de información.** El `NER_Count` tiene un efecto positivo significativo sobre nGAIN ($\beta = +0.123, p < 0.05$). Las entidades nombradas (personas, organizaciones, lugares reconocidos por el modelo NER) constituyen datos duros que reducen el espacio de búsqueda de forma no ambigua. Mencionar el *"Nobel de Literatura"* o el *"FC Barcelona"* ancla al receptor en referentes concretos que pocos candidatos comparten.

**Los números como facilitadores de la lectura.** El `NUM_Ratio` presenta un efecto positivo sobre LEC ($\beta = +0.122, p < 0.05$). Los tokens numéricos (*"1605"*, *"3 veces"*, *"8 premios"*) son procesados rápidamente por el lector y transmiten información densa en pocos caracteres, lo que contrasta con los adjetivos vacíos.

**El efecto dual de la profundidad sintáctica.** `Tree_Depth` muestra un efecto negativo sobre LEC ($\beta = -0.119, p < 0.05$) y positivo sobre CONS ($\beta = +0.113, p < 0.05$). La primera relación es esperable: oraciones con subcláusulas anidadas son más difíciles de leer. La segunda tiene una interpretación sutil: las oraciones sintácticamente más complejas suelen ser más elaboradas temáticamente, con relaciones causales o temporales que mantienen coherencia interna.

**La opacidad de la ambigüedad.** El modelo para AMB resulta no significativo ($R^2 = 0.022, p = 0.452$): ninguna característica lingüística explica la ambigüedad. Este hallazgo tiene una implicación teórica profunda: la ambigüedad de una pista no depende de *cómo* está escrita sino de *qué dice* en relación al campo semántico del juego. La ambigüedad reside en el espacio de embeddings, no en la superficie lingüística.

### 3.6 Diagnóstico de multicolinealidad

Se calculó el *Variance Inflation Factor* (VIF) para validar la independencia de los predictores del modelo OLS.

| Característica | VIF | Estado |
|---|---|---|
| PROPN_Ratio | 1.460 | Sin problema |
| NER_Count | 1.356 | Sin problema |
| ADJ_Ratio | 1.275 | Sin problema |
| VERB_Ratio | 1.119 | Sin problema |
| NUM_Ratio | 1.087 | Sin problema |
| Max_IDF | 1.046 | Sin problema |
| Tree_Depth | 1.042 | Sin problema |
| Subjectivity | 1.012 | Sin problema |

Todos los valores de VIF se sitúan por debajo de 1.5, muy lejos del umbral de preocupación (VIF > 5). Esto confirma que los predictores son prácticamente ortogonales y que la interpretación individual de cada coeficiente $\beta$ es fiable: los efectos reportados no son artefactos de correlaciones entre predictores.

---

## 4. Conclusiones

### 4.1 Definición formal de pista

A partir de la evidencia acumulada, proponemos la siguiente definición formal:

> **Pista**: Unidad de información compuesta en lenguaje natural, condicionada por un objetivo latente $t$, cuya función es reducir la entropía del espacio de estados posibles $\mathcal{S}$ en la mente del receptor, guiándole hacia la identificación de $t$ sin revelarlo explícitamente. Formalmente, una pista $h$ opera como un **filtro bayesiano lingüístico**: transforma la distribución de probabilidad *a priori* $P(s)$, uniforme sobre los $|\mathcal{S}| = 45$ candidatos, en una distribución *a posteriori* $P(s|h)$ donde la masa de probabilidad se concentra progresivamente sobre $t$.

Esta definición se sustenta en tres propiedades que la evidencia empírica ha revelado como esenciales:

1. **Composicionalidad**: una pista no es un dato atómico sino una estructura compuesta (sustantivos, verbos, adjetivos, relaciones sintácticas) donde cada componente contribuye de forma diferenciada a la reducción de entropía. Las regresiones OLS demuestran que los verbos destruyen calidad mientras que las entidades nombradas la incrementan.
2. **Condicionalidad**: la calidad de una pista es relacional, no intrínseca. Emerge de la interacción entre el texto, el personaje objetivo y el campo semántico de los 45 candidatos. Esto explica por qué AMB no es predecible desde la sintaxis.
3. **No-trivialidad**: el objetivo no es eliminar toda la entropía (eso sería revelar la respuesta) sino reducirla de forma calibrada. El mecanismo CLAMP formaliza esta restricción.

### 4.2 Perfil empírico de una pista de calidad

La convergencia de los análisis de regresión logística (predicción de acierto) y OLS (explicación lingüística) permite trazar un perfil empírico de la pista ideal:

**Pista de alta calidad:**
- Bajo ratio de verbos (< 0.09): evita la dispersión narrativa y maximiza la consistencia y la ganancia de información.
- Bajo ratio de adjetivos (< 0.05): elimina el relleno léxico que destruye la lecturabilidad sin aportar discriminación.
- Presencia de entidades nombradas (≥ 1): ancla la pista en referentes concretos que reducen el espacio de búsqueda.
- Presencia de datos numéricos: facilita la lectura y aporta hechos verificables.
- Profundidad sintáctica moderada (3–4): equilibra la coherencia interna con la facilidad de lectura.
- Baja subjetividad: hechos en lugar de opiniones.

**Pista de baja calidad:**
- Alto ratio de verbos: dispersa el foco temático y diluye la información.
- Alto ratio de adjetivos: frases largas y vacías de información discriminante.
- Ausencia de entidades nombradas y datos numéricos: todo es descripción genérica.
- Alta subjetividad: opiniones que no contribuyen a la identificación.

Esta dicotomía se sintetiza en un principio fundamental: **las mejores pistas se asemejan a una entrada de enciclopedia, no a una narración literaria**. La calidad reside en la densidad nominal (sustantivos propios, entidades, datos) y no en la riqueza verbal o adjetival.

### 4.3 Limitaciones del estudio

Es necesario señalar las siguientes limitaciones que condicionan el alcance de los resultados:

1. **Varianza explicada moderada en las métricas semánticas.** Los modelos OLS para PD ($R^2 = 0.053$) y nGAIN ($R^2 = 0.065$) explican solo una fracción reducida de la varianza. Esto no invalida los efectos encontrados (que son estadísticamente significativos), pero confirma que la calidad semántica de una pista depende primordialmente del contenido proposicional y no de la forma lingüística. La sintaxis es un modulador, no el determinante.

2. **Herramientas de análisis de sentimiento.** TextBlob fue diseñado para inglés, lo que limita la capacidad discriminante de la variable `Subjectivity` sobre textos en español. La mayoría de las pistas obtienen una subjetividad de 0, lo que suprime la variabilidad de esta característica. Un modelo de sentimiento nativo en español podría revelar efectos ocultos.

3. **Sesgo de generación.** Las pistas fueron creadas por un modelo de lenguaje con *in-context learning* y restricción de longitud, lo que produce textos relativamente homogéneos en estructura. Esto comprime la varianza natural de las características lingüísticas (especialmente CONS) y podría subestimar los efectos reales de la estructura sintáctica.

4. **Ausencia de variables del jugador en el modelo predictivo.** La regresión logística solo utiliza características de la pista como predictores. Variables como la habilidad del jugador, el número de pistas previas reveladas o el conocimiento previo sobre el personaje no se incorporaron al modelo, lo que explica parcialmente el AUC moderado (0.59).

5. **Tamaño del catálogo.** Con 45 personajes y 360 pistas, el corpus es suficiente para detectar efectos de tamaño mediano-grande pero puede ser insuficiente para capturar interacciones entre características o efectos no lineales.

### 4.4 Líneas de trabajo futuro

1. **Modelos no lineales.** La adopción de modelos de tipo *gradient boosting* o redes neuronales podría capturar no linealidades e interacciones entre características que los modelos lineales ignoran (por ejemplo, la interacción entre `NER_Count` y `VERB_Ratio`).

2. **Incorporación de variables contextuales.** Añadir al modelo predictivo la secuencia de pistas previas, el perfil del jugador y la dificultad acumulada, lo que permitiría modelar el efecto de la pista en su contexto real de uso.

3. **Análisis de sentimiento nativo en español.** Reemplazar TextBlob por un modelo entrenado específicamente en español (como `pysentimiento` o un modelo BETO *fine-tuned*) para recuperar la señal de subjetividad.

4. **Generación de pistas guiada por métricas.** Utilizar los hallazgos de este estudio como restricciones en el prompt de un modelo generativo (por ejemplo, *"genera una pista sin adjetivos vacíos, con al menos una entidad nombrada y máximo un verbo"*).

5. **Validación con catálogos más amplios.** Replicar el estudio con un catálogo expandido (> 100 personajes) para evaluar si los efectos se mantienen o se intensifican al aumentar la densidad semántica del espacio de candidatos.

### 4.5 Contribución del proyecto

El presente trabajo ofrece tres contribuciones principales:

1. **Un sistema formal y replicable de evaluación de calidad de pistas**, basado en métricas que operan en el espacio de embeddings y que capturan dimensiones complementarias de la utilidad informativa (discriminación, ambigüedad, ganancia, consistencia, lecturabilidad).

2. **La demostración empírica de que la estructura lingüística de una pista influye de forma medible en su calidad**, con efectos que siguen una jerarquía clara: el ratio de verbos es el predictor más potente y transversal, seguido del ratio de adjetivos y de las entidades nombradas.

3. **Una definición operativa de "pista de calidad"** que trasciende la intuición y se sustenta en datos: una pista eficaz maximiza la densidad de sustantivos y entidades concretas, minimizando el uso de verbos genéricos y adjetivos vacíos. Esta definición tiene aplicación directa en la generación automática de pistas y en el diseño de sistemas educativos gamificados.

---

> *Documento generado a partir del análisis experimental realizado en `propuesta_calidad_pistas.ipynb`. Todas las figuras referenciadas corresponden a las gráficas producidas en el cuaderno de trabajo.*
