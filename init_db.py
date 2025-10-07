#!/usr/bin/env python
"""
Script de inicialización de la base de datos.
Carga una persona de ejemplo desde pistas.json a MongoDB.
"""

import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import sys

# Cargar variables de entorno
load_dotenv()

# MongoDB configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/spygame')

def get_db_connection():
    """Establish connection to MongoDB"""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.admin.command('ping')
        db = client.spygame
        return db, True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return None, False

def cargar_ejemplo_trump():
    """Carga el ejemplo de Donald Trump desde pistas.json"""
    
    # Leer el archivo pistas.json
    pistas_file = 'pistas.json'
    
    if not os.path.exists(pistas_file):
        print(f"❌ No se encontró el archivo {pistas_file}")
        return False
    
    with open(pistas_file, 'r', encoding='utf-8') as f:
        pistas = json.load(f)
    
    # Conectar a la base de datos
    db, connected = get_db_connection()
    
    if not connected:
        return False
    
    try:
        pistas_collection = db.pistas
        
        # Crear documento para Donald Trump
        documento = {
            "nombre": "Donald Trump",
            "pistas": pistas,
            "url_wikipedia": "https://es.wikipedia.org/wiki/Donald_Trump",
            "fecha_creacion": "2025-10-07T00:00:00"
        }
        
        # Verificar si ya existe
        existente = pistas_collection.find_one({"nombre": "Donald Trump"})
        
        if existente:
            print("Donald Trump ya existe en la base de datos. Actualizando...")
            pistas_collection.update_one(
                {"nombre": "Donald Trump"},
                {"$set": documento}
            )
            print("Donald Trump actualizado en la base de datos")
        else:
            pistas_collection.insert_one(documento)
            print("Donald Trump agregado a la base de datos")
        
        # Mostrar estadísticas
        total_personas = pistas_collection.count_documents({})
        print(f"\nTotal de personas en la base de datos: {total_personas}")
        
        return True
        
    except Exception as e:
        print(f"Error al cargar datos: {e}")
        return False

def listar_personas():
    """Lista todas las personas en la base de datos"""
    db, connected = get_db_connection()
    
    if not connected:
        return
    
    try:
        pistas_collection = db.pistas
        personas = list(pistas_collection.find({}, {"_id": 0, "nombre": 1, "fecha_creacion": 1}))
        
        if not personas:
            print("\nNo hay personas en la base de datos")
            return
        
        print(f"\nPersonas en la base de datos ({len(personas)}):")
        print("=" * 60)
        for i, persona in enumerate(personas, 1):
            nombre = persona.get('nombre', 'Desconocido')
            fecha = persona.get('fecha_creacion', 'N/A')
            print(f"{i}. {nombre} (creado: {fecha})")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error al listar personas: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("SpyGame - Inicialización de Base de Datos")
    print("=" * 60)
    print()
    
    # Verificar argumentos
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        listar_personas()
    else:
        print("Cargando ejemplo de Donald Trump desde pistas.json...")
        print()
        
        if cargar_ejemplo_trump():
            print()
            listar_personas()
        else:
            print("\nNo se pudo completar la inicialización")
            sys.exit(1)
    
    print()
    print("Proceso completado")
    print()
