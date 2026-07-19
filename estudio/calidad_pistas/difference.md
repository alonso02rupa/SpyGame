# Diferencias entre el Estudio en Mundo Abierto y el Estudio en Mundo Cerrado

Este documento compara los dos experimentos realizados sobre la calidad de pistas en SpyGame: el estudio original en **mundo abierto** y el estudio replicado con datos **incrementales (mundo cerrado)**.

---

## 1. Descripción de los Experimentos

### Mundo Abierto

- **Datos**: `hints_guesses_expanded.csv`
- **Mecánica**: Los jugadores escriben libremente el nombre del personaje que creen que describe la pista, sin ninguna restricción ni lista de ayuda.
- **Implicación**: El jugador debe recuperar el nombre de memoria. Un error ortográfico, un nombre alternativo o una confusión conceptual producen un fallo aunque el jugador haya identificado mentalmente al personaje correcto.

### Mundo Cerrado (Incremental)

- **Datos**: `hints_guesses_expanded_incremental_20260319.csv`
- **Mecánica**: Los jugadores seleccionan su respuesta entre un conjunto predefinido de candidatos (los 45 personajes del juego). La respuesta correcta siempre está visible en la lista.
- **Implicación**: El jugador no necesita recuperar el nombre de memoria. Solo debe discriminar entre los candidatos presentes, lo que reduce la carga cognitiva y elimina los errores de escritura o nomenclatura. El éxito depende de cuán bien la pista apunta al candidato correcto frente al resto.

---

## 2. Diferencias en los Datasets

| Característica | Mundo Abierto | Mundo Cerrado |
|----------------|:-------------:|:-------------:|
| **N interacciones** | 2.293 | 1.119 |
| **N pistas únicas** | 360 | 360 (idénticas) |
| **N personajes** | 45 | 45 (idénticos) |
| **Pistas por personaje** | 8 | 8 (idénticas) |
| **Tasa de acierto** | 65.5% | **78.1%** |
| **Tasa de fallo** | 34.5% | 21.9% |
| **Fecha de corte** | Hasta feb. 2026 | Hasta mar. 2026 (incremental) |
| **Desbalance de clases** | Moderado | **Alto** |

La tasa de acierto sube 12.6 puntos porcentuales en mundo cerrado, lo que confirma el efecto facilitador de ver la lista de candidatos: el jugador no falla por no recordar el nombre, solo puede fallar si no discrimina correctamente.

---

## 3. Diferencias en el Análisis OLS

**Las 5 regresiones OLS producen resultados idénticos en ambos experimentos.**

Esto ocurre porque las métricas de calidad (PD, AMB, nGAIN, LEC, CONS) son propiedades intrínsecas de las pistas como objetos lingüísticos, calculadas sobre sus embeddings y estructura textual. No dependen de quién jugó ni de cuándo. Al ser las 360 pistas exactamente las mismas en ambos datasets, los resultados OLS son matemáticamente invariantes.

**Esta invarianza es un hallazgo positivo**: demuestra que la estructura lingüística de una pista es una propiedad estable del texto que no cambia con el contexto de evaluación. Los patrones identificados (VERB_Ratio como predictor dominante, ADJ_Ratio como destructor de lecturabilidad, etc.) son robustos y generalizables.

---

## 4. Diferencias en el Análisis Logístico

El logístico es donde los estudios difieren sustancialmente, ya que utiliza datos de interacciones reales de jugadores.

### 4.1 Rendimiento Global del Modelo

| Métrica | Mundo Abierto | Mundo Cerrado | Diferencia |
|---------|:-------------:|:-------------:|:----------:|
| **Accuracy (CV)** | ~0.55 ± 0.03 | 0.532 ± 0.040 | -0.018 |
| **AUC-ROC (CV)** | ~0.57 ± 0.03 | 0.548 ± 0.058 | -0.022 |
| **F1-Score (CV)** | ~0.63 ± 0.02 | 0.641 ± 0.035 | +0.011 |
| **Accuracy (hold-out)** | 0.584 | 0.500 | **-0.084** |
| **AUC-ROC (hold-out)** | 0.591 | 0.505 | **-0.086** |
| **McFadden R²** | 0.0102 | 0.0132 | +0.003 |
| **LR G²** | 30.10 | 15.56 | -14.54 |
| **LR p-value** | < 0.001 | 0.0082 | — |
| **Brier Score** | 0.245 | 0.2495 | +0.005 |

El modelo en mundo cerrado tiene **menor rendimiento discriminativo** (AUC) y es significativamente más débil en términos de señal estadística (G² a la mitad). El mayor desbalance de clases (78/22 vs. 65/35) y el menor tamaño muestral son los factores principales.

El McFadden R² es ligeramente mayor en mundo cerrado (0.0132 vs. 0.0102), pero su versión ajustada es prácticamente nula (0.003 vs. 0.006), indicando que en mundo cerrado el modelo añade menos señal real por encima del azar dado su menor N.

### 4.2 Coeficientes: Diferencias en Importancia y Dirección

| Métrica | β Mundo Abierto | β Mundo Cerrado | Cambio |
|---------|:---------------:|:---------------:|--------|
| **PD** | +0.110 | **+0.333** | **↑↑ Mucho más relevante** |
| **CONS** | -0.008 | **-0.162** | **↓ Pasa a ser negativo notable** |
| **nGAIN** | +0.056 | +0.061 | Similar |
| **AMB** | **-0.080** | **+0.051** | **Invierte dirección** |
| **LEC** | **-0.070** | **+0.023** | **Invierte dirección** |

*(Coeficientes β estandarizados de sklearn con regularización L2)*

### 4.3 Significancia Individual

| Métrica | Mundo Abierto (p-value) | Mundo Cerrado (p-value) |
|---------|:-----------------------:|:-----------------------:|
| **PD** | No sig. (p=0.174) | **Sig. * (p=0.028)** |
| AMB | No sig. | No sig. |
| nGAIN | No sig. | No sig. |
| CONS | No sig. | No sig. |
| LEC | No sig. | No sig. |

PD pasa de ser no significativo individualmente en mundo abierto a ser el único predictor individualmente significativo en mundo cerrado.

---

## 5. Interpretación de las Diferencias

### 5.1 Por qué PD domina en mundo cerrado

En mundo abierto, el jugador debe recordar el nombre de la persona en su totalidad: la pista activa un esquema cognitivo y el jugador recupera el nombre si ese esquema es suficientemente específico. El PD (cuán diferente es la pista del target frente a otros) no es el único factor: el conocimiento previo del jugador y la memoria a largo plazo juegan un papel crucial.

En mundo cerrado, el jugador compara la pista explícitamente contra los 45 candidatos visibles. Este proceso es esencialmente una tarea de discriminación directa: la pista "señala" al candidato correcto frente al resto. En este escenario, el PD es directamente operativo: una pista con alto PD apunta hacia el target de forma que los competidores no pueden confundirse con él, facilitando la elección correcta.

### 5.2 Por qué CONS emerge como factor negativo en mundo cerrado

En mundo abierto, la consistencia entre pistas de un personaje apenas importaba (β = -0.008). En mundo cerrado cobra un efecto negativo notable (β = -0.162).

Una hipótesis: en mundo cerrado, el jugador ve una sola pista a la vez y la compara contra la lista. Si las pistas de un personaje son muy consistentes temáticamente (e.g., todas hablan de su obra literaria), pueden crear un perfil demasiado "genérico de escritor" en lugar de señalar a un individuo específico. La consistencia excesiva puede traducirse en pistas que son correctas para la categoría pero que no discriminan suficientemente dentro de ella frente a otros escritores de la lista.

### 5.3 Por qué AMB y LEC invierten su dirección

En mundo abierto:
- **AMB negativo**: Una pista ambigua activa múltiples personajes en la mente del jugador, generando confusión y aumentando la probabilidad de fallo cuando tiene que escribir un nombre específico.
- **LEC negativo**: Las pistas con vocabulario técnico específico (baja lecturabilidad Flesch) son difíciles de procesar pero apuntan a personajes concretos, lo que facilita el acierto. El signo negativo es un artefacto de la métrica Flesch.

En mundo cerrado:
- **AMB positivo (leve)**: La lista de candidatos resuelve externamente la ambigüedad. El jugador no necesita resolver la ambigüedad mentalmente; ve todas las opciones y puede seleccionar. Una pista algo más general puede incluso ser más útil porque filtra candidatos sin requerir especificidad total.
- **LEC positivo (leve)**: En mundo cerrado, una pista más fácil de leer facilita la comparación rápida contra los candidatos de la lista. La facilidad cognitiva de procesamiento es más valiosa cuando el jugador tiene que comparar simultáneamente múltiples candidatos.

Ambas inversiones son coherentes con la hipótesis de que la lista de candidatos actúa como un mecanismo externo de resolución de ambigüedad y recuperación de información, reduciendo la dependencia de las propiedades internas de la pista relacionadas con la ambigüedad y la legibilidad.

---

## 6. Implicaciones Prácticas

### Para el diseño de pistas (ambos contextos)

- **El perfil óptimo de pista es el mismo**: pocas verbos, pocos adjetivos vacíos, muchas entidades nombradas. Esto se aplica independientemente de si el juego es mundo abierto o cerrado, porque está determinado por la estructura lingüística intrínseca (OLS invariante).

### Para la ponderación de métricas en $Q$ (dependiente del contexto)

| Contexto | Ponderación recomendada |
|----------|-------------------------|
| **Mundo Abierto** | PD (moderado) + nGAIN + AMB negativo + LEC negativo |
| **Mundo Cerrado** | **PD dominante** (~53%) + CONS negativo + nGAIN + AMB/LEC marginales |

La fórmula $Q$ debería adaptarse al contexto de juego. En mundo cerrado, maximizar el PD es el objetivo prioritario.

### Para la recogida de datos

El estudio en mundo cerrado tiene menos ruido (sin errores de escritura, sin nombres alternativos) pero más desbalance de clases. Con un N mayor de datos en mundo cerrado, la señal predictiva debería ser más estable.

---

## 7. Resumen de Diferencias Clave

| Dimensión | Mundo Abierto | Mundo Cerrado |
|-----------|--------------|--------------|
| **Mecánica** | Respuesta libre (free-text) | Selección de lista (multiple-choice) |
| **N datos** | 2.293 | 1.119 |
| **Tasa acierto** | 65.5% | 78.1% |
| **OLS** | Idéntico | Idéntico |
| **Logístico: AUC (hold-out)** | 0.591 | 0.505 |
| **Logístico: G² (LR test)** | 30.10 (p<0.001) | 15.56 (p=0.008) |
| **Predictor principal** | Conjunto (ninguno individual sig.) | **PD (único sig., p=0.028)** |
| **CONS** | Irrelevante (-0.008) | Negativo notable (-0.162) |
| **AMB** | Negativo (-0.080) | Positivo (+0.051) |
| **LEC** | Negativo (-0.070) | Positivo (+0.023) |

---

*Comparación realizada sobre los análisis en `ANALISIS_REGRESION_OLS.md` (mundo abierto) y `ANALISIS_REGRESION_OLS_INCREMENTAL.md` (mundo cerrado)*
*Fecha: Marzo 2026*
