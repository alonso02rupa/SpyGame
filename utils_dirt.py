#!/usr/bin/env python
"""
utils_dirt.py

Utilidades para aplicar el modelo DIRT (Discovery of Inference Rules from Text)
durante la generación de pistas. Permite reformular frases sustituyendo verbos
por equivalentes aprendidos para diversificar el lenguaje.

Uso:
    from utils_dirt import aplicar_DIRT
    
    frases = ["Esta persona fundó una universidad", "Recibió un premio"]
    frases_reformuladas = aplicar_DIRT(frases, probabilidad=0.3)
"""

import json
import os
import random
from typing import List, Dict, Any, Optional

# Ruta al modelo de inferencias
MODELO_INFERENCIAS = "modelo_inferencias.json"

# Cache del modelo en memoria
_modelo_cache: Optional[Dict[str, Any]] = None


def cargar_modelo(filepath: str = MODELO_INFERENCIAS) -> Optional[Dict[str, Any]]:
    """
    Carga el modelo de inferencias DIRT desde un archivo JSON.
    
    Args:
        filepath: Ruta al archivo del modelo
    
    Returns:
        Diccionario con el modelo o None si no existe
    """
    global _modelo_cache
    
    # Si ya está en cache, retornarlo
    if _modelo_cache is not None:
        return _modelo_cache
    
    # Intentar cargar desde archivo
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            modelo = json.load(f)
        
        # Validar estructura básica
        if "equivalencias" not in modelo:
            print(f"⚠ Modelo DIRT inválido: falta campo 'equivalencias'")
            return None
        
        # Cachear el modelo
        _modelo_cache = modelo
        return modelo
    
    except Exception as e:
        print(f"⚠ Error al cargar modelo DIRT: {e}")
        return None


def construir_diccionario_equivalencias(modelo: Dict[str, Any]) -> Dict[str, List[tuple]]:
    """
    Construye un diccionario de búsqueda rápida para equivalencias.
    
    Args:
        modelo: Modelo DIRT cargado
    
    Returns:
        Diccionario {verbo: [(equivalente, score), ...]}
    """
    equivalencias_dict = {}
    
    for eq in modelo.get("equivalencias", []):
        verbo_a = eq["a"]
        verbo_b = eq["b"]
        score = eq["score"]
        
        # Añadir en ambas direcciones
        if verbo_a not in equivalencias_dict:
            equivalencias_dict[verbo_a] = []
        equivalencias_dict[verbo_a].append((verbo_b, score))
        
        if verbo_b not in equivalencias_dict:
            equivalencias_dict[verbo_b] = []
        equivalencias_dict[verbo_b].append((verbo_a, score))
    
    # Ordenar por score descendente
    for verbo in equivalencias_dict:
        equivalencias_dict[verbo].sort(key=lambda x: x[1], reverse=True)
    
    return equivalencias_dict


def sustituir_verbo_en_frase(frase: str, verbo_original: str, verbo_nuevo: str) -> str:
    """
    Sustituye un verbo en una frase por su equivalente.
    Intenta preservar la conjugación cuando es posible.
    
    Args:
        frase: Frase original
        verbo_original: Verbo a sustituir (en infinitivo/lemma)
        verbo_nuevo: Verbo nuevo (en infinitivo/lemma)
    
    Returns:
        Frase con el verbo sustituido
    """
    # Importar spaCy solo si es necesario
    try:
        import spacy
        nlp = spacy.load("es_core_news_sm")
    except:
        # Si no hay spaCy, hacer sustitución simple
        return frase.replace(verbo_original, verbo_nuevo)
    
    doc = nlp(frase)
    nueva_frase = frase
    
    for token in doc:
        if token.lemma_.lower() == verbo_original.lower() and token.pos_ == "VERB":
            # Sustituir el verbo conjugado por el nuevo verbo
            # (simplificado: usar el infinitivo del nuevo verbo)
            nueva_frase = nueva_frase.replace(token.text, verbo_nuevo, 1)
            break
    
    return nueva_frase


def aplicar_DIRT(
    frases: List[str], 
    probabilidad: float = 0.3,
    min_score: float = 0.2,
    max_sustituciones: Optional[int] = None,
    filepath: str = MODELO_INFERENCIAS
) -> List[str]:
    """
    Aplica el modelo DIRT para reformular frases sustituyendo verbos
    por equivalentes aprendidos.
    
    Args:
        frases: Lista de frases a reformular
        probabilidad: Probabilidad de sustituir cada verbo encontrado (0.0 - 1.0)
        min_score: Score mínimo de similitud para aceptar una equivalencia
        max_sustituciones: Máximo número de sustituciones a realizar (None = sin límite)
        filepath: Ruta al archivo del modelo
    
    Returns:
        Lista de frases reformuladas
    """
    # Cargar modelo
    modelo = cargar_modelo(filepath)
    
    # Si no hay modelo, retornar frases originales sin error
    if modelo is None:
        return frases
    
    # Construir diccionario de equivalencias
    equiv_dict = construir_diccionario_equivalencias(modelo)
    
    if not equiv_dict:
        return frases
    
    # Importar spaCy para análisis
    try:
        import spacy
        nlp = spacy.load("es_core_news_sm")
    except:
        # Si no hay spaCy disponible, retornar frases originales
        return frases
    
    frases_reformuladas = []
    sustituciones_realizadas = 0
    
    for frase in frases:
        if max_sustituciones is not None and sustituciones_realizadas >= max_sustituciones:
            # Ya alcanzamos el máximo, no sustituir más
            frases_reformuladas.append(frase)
            continue
        
        doc = nlp(frase)
        frase_actual = frase
        sustituido_en_esta_frase = False
        
        # Buscar verbos en la frase
        for token in doc:
            if token.pos_ == "VERB":
                verbo_lemma = token.lemma_.lower()
                
                # Verificar si hay equivalencias para este verbo
                if verbo_lemma in equiv_dict:
                    # Decidir aleatoriamente si sustituir
                    if random.random() < probabilidad:
                        # Obtener equivalencias con score suficiente
                        candidatos = [
                            (eq_verbo, score) 
                            for eq_verbo, score in equiv_dict[verbo_lemma] 
                            if score >= min_score
                        ]
                        
                        if candidatos:
                            # Elegir un equivalente (ponderado por score)
                            # Simplificado: elegir el de mayor score
                            nuevo_verbo, score = candidatos[0]
                            
                            # Sustituir en la frase
                            frase_actual = sustituir_verbo_en_frase(frase_actual, verbo_lemma, nuevo_verbo)
                            sustituido_en_esta_frase = True
                            sustituciones_realizadas += 1
                            
                            # Solo sustituir un verbo por frase
                            break
        
        frases_reformuladas.append(frase_actual)
    
    return frases_reformuladas


def obtener_estadisticas_modelo(filepath: str = MODELO_INFERENCIAS) -> Optional[Dict[str, Any]]:
    """
    Obtiene estadísticas del modelo DIRT cargado.
    
    Args:
        filepath: Ruta al archivo del modelo
    
    Returns:
        Diccionario con estadísticas o None si no hay modelo
    """
    modelo = cargar_modelo(filepath)
    
    if modelo is None:
        return None
    
    equivalencias = modelo.get("equivalencias", [])
    
    if not equivalencias:
        return {
            "version": modelo.get("version", "desconocida"),
            "num_equivalencias": 0,
            "verbos_unicos": 0,
            "score_promedio": 0,
            "score_max": 0,
            "score_min": 0
        }
    
    # Calcular estadísticas
    verbos_unicos = set()
    scores = []
    
    for eq in equivalencias:
        verbos_unicos.add(eq["a"])
        verbos_unicos.add(eq["b"])
        scores.append(eq["score"])
    
    return {
        "version": modelo.get("version", "desconocida"),
        "generado": modelo.get("generado", "desconocido"),
        "num_equivalencias": len(equivalencias),
        "verbos_unicos": len(verbos_unicos),
        "score_promedio": round(sum(scores) / len(scores), 3) if scores else 0,
        "score_max": round(max(scores), 3) if scores else 0,
        "score_min": round(min(scores), 3) if scores else 0
    }


def listar_equivalencias_verbo(
    verbo: str, 
    filepath: str = MODELO_INFERENCIAS,
    top_n: int = 5
) -> List[tuple]:
    """
    Lista las equivalencias de un verbo específico.
    
    Args:
        verbo: Verbo a consultar (infinitivo/lemma)
        filepath: Ruta al archivo del modelo
        top_n: Número máximo de equivalencias a retornar
    
    Returns:
        Lista de tuplas (verbo_equivalente, score)
    """
    modelo = cargar_modelo(filepath)
    
    if modelo is None:
        return []
    
    equiv_dict = construir_diccionario_equivalencias(modelo)
    
    verbo_lower = verbo.lower()
    if verbo_lower not in equiv_dict:
        return []
    
    return equiv_dict[verbo_lower][:top_n]


# Función de ejemplo/test
def ejemplo_uso():
    """Función de ejemplo que muestra cómo usar las utilidades DIRT"""
    print("="*60)
    print("Ejemplo de uso de utils_dirt.py")
    print("="*60 + "\n")
    
    # Estadísticas del modelo
    stats = obtener_estadisticas_modelo()
    if stats:
        print("Estadísticas del modelo DIRT:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()
    else:
        print("⚠ No hay modelo DIRT disponible")
        print("  Ejecuta 'python dirt_builder.py' para generar uno\n")
        return
    
    # Frases de ejemplo
    frases_ejemplo = [
        "Esta persona fundó una importante institución científica",
        "Recibió múltiples premios internacionales",
        "Estudió física en una universidad europea",
        "Desarrolló nuevas teorías sobre la materia",
        "Trabajó en colaboración con otros científicos"
    ]
    
    print("Frases originales:")
    for i, frase in enumerate(frases_ejemplo, 1):
        print(f"  {i}. {frase}")
    
    print("\nAplicando DIRT (probabilidad=0.5)...")
    frases_reformuladas = aplicar_DIRT(frases_ejemplo, probabilidad=0.5)
    
    print("\nFrases reformuladas:")
    for i, frase in enumerate(frases_reformuladas, 1):
        marca = "✓" if frase != frases_ejemplo[i-1] else " "
        print(f"  {marca} {i}. {frase}")
    
    # Buscar equivalencias de un verbo específico
    print("\n" + "-"*60)
    verbo_test = "fundar"
    print(f"Equivalencias para '{verbo_test}':")
    equivalencias = listar_equivalencias_verbo(verbo_test)
    if equivalencias:
        for eq_verbo, score in equivalencias:
            print(f"  - {eq_verbo} (score: {score:.3f})")
    else:
        print(f"  No se encontraron equivalencias para '{verbo_test}'")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    ejemplo_uso()
