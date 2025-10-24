#!/usr/bin/env python
"""
test_dirt.py

Script de prueba rápida para el sistema DIRT.
Demuestra las capacidades del sistema sin necesidad de MongoDB.
"""

import os
import sys

def test_dirt_simple():
    """Test simple del sistema DIRT"""
    print("="*70)
    print("TEST DEL SISTEMA DIRT")
    print("="*70)
    
    # Verificar si existe el modelo
    if not os.path.exists("modelo_inferencias.json"):
        print("\n⚠ No existe modelo_inferencias.json")
        print("\nGenerando modelo de ejemplo...")
        print("Ejecutando: python dirt_builder.py\n")
        
        import subprocess
        result = subprocess.run([sys.executable, "dirt_builder.py"], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error al generar modelo: {result.stderr}")
            return
        
        print(result.stdout)
    
    # Importar utils_dirt
    try:
        from utils_dirt import (
            aplicar_DIRT, 
            obtener_estadisticas_modelo, 
            listar_equivalencias_verbo
        )
    except ImportError as e:
        print(f"Error al importar utils_dirt: {e}")
        return
    
    print("\n" + "="*70)
    print("1. ESTADÍSTICAS DEL MODELO")
    print("="*70)
    
    stats = obtener_estadisticas_modelo()
    if stats:
        print(f"\n  Versión: {stats['version']}")
        print(f"  Generado: {stats.get('generado', 'N/A')}")
        print(f"  Equivalencias totales: {stats['num_equivalencias']}")
        print(f"  Verbos únicos: {stats['verbos_unicos']}")
        print(f"  Score promedio: {stats['score_promedio']:.3f}")
        print(f"  Score máximo: {stats['score_max']:.3f}")
        print(f"  Score mínimo: {stats['score_min']:.3f}")
    else:
        print("\n  ✗ No se pudo cargar el modelo")
        return
    
    print("\n" + "="*70)
    print("2. REFORMULACIÓN DE FRASES")
    print("="*70)
    
    frases_test = [
        "Esta persona fundó una importante institución científica en Europa",
        "Recibió múltiples premios internacionales por su trabajo",
        "Estudió física y química en universidades de renombre",
        "Desarrolló nuevas teorías sobre la composición de la materia",
        "Trabajó en colaboración con destacados científicos de la época",
        "Descubrió elementos químicos que revolucionaron la ciencia",
        "Creó técnicas innovadoras para el tratamiento médico",
        "Ganó reconocimiento mundial por sus contribuciones"
    ]
    
    print("\n📝 Frases originales:")
    print("-" * 70)
    for i, frase in enumerate(frases_test, 1):
        print(f"{i}. {frase}")
    
    print("\n🔄 Aplicando DIRT (probabilidad=0.5, min_score=0.15)...")
    frases_reformuladas = aplicar_DIRT(
        frases_test, 
        probabilidad=0.5, 
        min_score=0.15
    )
    
    print("\n✨ Frases reformuladas:")
    print("-" * 70)
    cambios = 0
    for i, (original, reformulada) in enumerate(zip(frases_test, frases_reformuladas), 1):
        marca = "✓" if original != reformulada else " "
        if original != reformulada:
            cambios += 1
        print(f"{marca} {i}. {reformulada}")
    
    print(f"\n  Total de frases modificadas: {cambios}/{len(frases_test)}")
    
    print("\n" + "="*70)
    print("3. EQUIVALENCIAS DE VERBOS ESPECÍFICOS")
    print("="*70)
    
    verbos_test = ["fundar", "recibir", "estudiar", "desarrollar", "trabajar"]
    
    for verbo in verbos_test:
        print(f"\n📌 Equivalencias para '{verbo}':")
        equivalencias = listar_equivalencias_verbo(verbo, top_n=5)
        
        if equivalencias:
            for i, (eq_verbo, score) in enumerate(equivalencias, 1):
                print(f"   {i}. {eq_verbo:15} (score: {score:.3f})")
        else:
            print(f"   - No se encontraron equivalencias")
    
    print("\n" + "="*70)
    print("4. COMPARACIÓN ANTES/DESPUÉS")
    print("="*70)
    
    print("\nEjemplo de cómo DIRT diversifica el lenguaje:\n")
    
    # Seleccionar solo las frases que cambiaron
    ejemplos_cambios = []
    for original, reformulada in zip(frases_test, frases_reformuladas):
        if original != reformulada:
            ejemplos_cambios.append((original, reformulada))
    
    if ejemplos_cambios:
        for i, (antes, despues) in enumerate(ejemplos_cambios[:3], 1):
            print(f"Ejemplo {i}:")
            print(f"  Antes:   {antes}")
            print(f"  Después: {despues}")
            print()
    else:
        print("  No se realizaron cambios en esta ejecución.")
        print("  (Esto puede ocurrir debido a la probabilidad aleatoria)")
    
    print("="*70)
    print("✓ TEST COMPLETADO")
    print("="*70)
    
    print("\n💡 Sugerencias:")
    print("  - Ajusta 'probabilidad' para más/menos sustituciones")
    print("  - Ajusta 'min_score' para controlar la calidad de equivalencias")
    print("  - Regenera el modelo con más datos: python dirt_builder.py")
    print()


if __name__ == "__main__":
    try:
        test_dirt_simple()
    except KeyboardInterrupt:
        print("\n\nTest interrumpido por el usuario")
    except Exception as e:
        print(f"\n✗ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
