#!/usr/bin/env python
"""
Script de verificación rápida del sistema.
Verifica que MongoDB esté conectado y que haya datos.
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# MongoDB configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/spygame')

def test_connection():
    """Prueba la conexión a MongoDB"""
    print("Verificando conexión a MongoDB...")
    
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("Conexión a MongoDB exitosa")
        return True
    except Exception as e:
        print(f"Error de conexión a MongoDB: {e}")
        return False

def check_collections():
    """Verifica las colecciones y cuenta documentos"""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client.spygame
        
        print("\nEstado de las colecciones:")
        print("=" * 60)
        
        # Pistas
        pistas_count = db.pistas.count_documents({})
        print(f"  Personas (pistas): {pistas_count}")
        
        if pistas_count > 0:
            # Mostrar algunos nombres
            personas = list(db.pistas.find({}, {"nombre": 1, "_id": 0}).limit(5))
            print("     Ejemplos:")
            for persona in personas:
                print(f"       - {persona.get('nombre', 'N/A')}")
        
        # Usuarios
        users_count = db.users.count_documents({})
        print(f"  Usuarios registrados: {users_count}")
        
        # Sesiones
        sessions_count = db.sessions.count_documents({})
        print(f"  Sesiones de juego: {sessions_count}")
        
        print("=" * 60)
        
        # Advertencias
        if pistas_count == 0:
            print("\nNo hay personas en la base de datos.")
            print("   Ejecuta: docker-compose exec web python init_db.py")
        
        return True
        
    except Exception as e:
        print(f"Error al verificar colecciones: {e}")
        return False

def check_env_vars():
    """Verifica que las variables de entorno estén configuradas"""
    print("\nVerificando variables de entorno:")
    print("=" * 60)
    
    required_vars = [
        'MONGODB_URI',
        'FLASK_SECRET_KEY',
        'HUGGINGFACE_API_KEY',
        'HUGGINGFACE_MODEL_NAME'
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Ocultar parcialmente valores sensibles
            if 'KEY' in var or 'SECRET' in var:
                display_value = value[:10] + "..." if len(value) > 10 else "***"
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
            print(f"  OK {var}: {display_value}")
        else:
            print(f"  ERROR {var}: NO CONFIGURADA")
            missing.append(var)
    
    print("=" * 60)
    
    if missing:
        print(f"\nVariables faltantes: {', '.join(missing)}")
        print("   Configura estas variables en el archivo .env")
        return False
    
    return True

def main():
    """Función principal"""
    print("=" * 60)
    print("SpyGame - Verificación del Sistema")
    print("=" * 60)
    print()
    
    # Verificar variables de entorno
    env_ok = check_env_vars()
    
    # Verificar conexión
    conn_ok = test_connection()
    
    if not conn_ok:
        print("\nNo se puede continuar sin conexión a MongoDB")
        print("   Asegúrate de que Docker esté corriendo:")
        print("   docker-compose up -d")
        sys.exit(1)
    
    # Verificar colecciones
    coll_ok = check_collections()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("Resumen de la Verificación:")
    print("=" * 60)
    print(f"  Variables de entorno: {'OK' if env_ok else 'Incompletas'}")
    print(f"  Conexión MongoDB:     {'OK' if conn_ok else 'Error'}")
    print(f"  Colecciones:          {'OK' if coll_ok else 'Error'}")
    print("=" * 60)
    
    if env_ok and conn_ok and coll_ok:
        print("\nTodo está listo para jugar!")
        print("   Abre http://localhost:5000 en tu navegador")
    else:
        print("\nHay algunos problemas que debes resolver")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nVerificación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nError inesperado: {e}")
        sys.exit(1)
