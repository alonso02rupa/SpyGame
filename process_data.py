#!/usr/bin/env python
"""
Script para ejecutar el procesamiento de datos desde Docker.
Wrapper que facilita la ejecución de data_processor.py
"""

import sys
import os

# Añadir el directorio datatreatment al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'datatreatment'))

from datatreatment.data_processor import procesar_batch

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Procesar personas de Wikipedia y subir pistas a MongoDB')
    parser.add_argument('--num', type=int, default=5, help='Número de personas a procesar (default: 5)')
    parser.add_argument('--limit', type=int, default=200, help='Límite de resultados de Wikidata (default: 200)')
    parser.add_argument('--offset', type=int, default=0, help='Offset para paginación (default: 0)')
    parser.add_argument('--min-sitelinks', type=int, default=150, help='Mínimo de sitelinks (default: 150)')
    
    args = parser.parse_args()
    
    print("Iniciando procesamiento de datos...")
    print(f"Personas a procesar: {args.num}")
    print(f"Límite Wikidata: {args.limit}")
    print(f"Offset: {args.offset}")
    print(f"Mínimo sitelinks: {args.min_sitelinks}")
    print()
    
    try:
        procesar_batch(
            num_personas=args.num,
            limit=args.limit,
            offset=args.offset,
            min_sitelinks=args.min_sitelinks
        )
        print("\n✅ Procesamiento completado exitosamente")
    except KeyboardInterrupt:
        print("\n\nProcesamiento interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nError durante el procesamiento: {e}")
        sys.exit(1)
