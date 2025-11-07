#!/usr/bin/env python
"""
Script de inicialización de la base de datos.
Carga personas desde archivos JSON a MongoDB.

Uso:
    python init_db.py --from-json file.json  # Carga múltiples personas desde JSON
    python init_db.py --list                 # Lista personas en DB
    python init_db.py --clear                # Limpia la base de datos
"""

import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import sys
import argparse

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/spygame')

def get_db_connection():
    """Establish connection to MongoDB"""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client.spygame
        return db, True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return None, False

def cargar_desde_json(filepath):
    """
    Carga múltiples personas desde un archivo JSON generado por process_local.py
    """
    if not os.path.exists(filepath):
        print(f"No se encontró el archivo {filepath}")
        return False
    
    print(f"Cargando personas desde {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    db, connected = get_db_connection()
    
    if not connected:
        return False
    
    try:
        pistas_collection = db.pistas
        
        insertadas = 0
        actualizadas = 0
        errores = 0
        
        if isinstance(data, dict):
            personas = data.values()
            total = len(data)
        elif isinstance(data, list):
            print("Formato antiguo detectado (lista). Se esperaba un diccionario.")
            return False
        else:
            print("Formato de JSON no reconocido")
            return False
        
        print(f"\nProcesando {total} personas...")
        
        for i, persona_data in enumerate(personas, 1):
            nombre = persona_data.get('nombre', 'Desconocido')
            
            try:
                if 'pistas' not in persona_data or not persona_data['pistas']:
                    print(f"[{i}/{total}] {nombre}: Sin pistas, saltando...")
                    errores += 1
                    continue
                
                existente = pistas_collection.find_one({"nombre": nombre})
                
                if existente:
                    pistas_collection.update_one(
                        {"nombre": nombre},
                        {"$set": persona_data}
                    )
                    actualizadas += 1
                    print(f"[{i}/{total}] {nombre}: Actualizado")
                else:
                    pistas_collection.insert_one(persona_data)
                    insertadas += 1
                    print(f"[{i}/{total}] {nombre}: Insertado")
                    
            except Exception as e:
                errores += 1
                print(f"[{i}/{total}] {nombre}: Error - {e}")
        
        print(f"\nResumen:")
        print(f"Insertadas: {insertadas}")
        print(f"Actualizadas: {actualizadas}")
        print(f"Errores: {errores}")
        print(f"Total en DB: {pistas_collection.count_documents({})}")
        
        return True
        
    except Exception as e:
        print(f"Error al cargar datos: {e}")
        return False

def limpiar_db():
    """Limpia completamente la base de datos"""
    db, connected = get_db_connection()
    
    if not connected:
        return False
    
    try:
        pistas_collection = db.pistas
        count = pistas_collection.count_documents({})
        
        if count == 0:
            print("\nLa base de datos ya está vacía")
            return True
        
        print(f"\nEsto eliminará {count} personas de la base de datos")
        respuesta = input("¿Estás seguro? (sí/no): ")
        
        if respuesta.lower() in ['sí', 'si', 's', 'yes', 'y']:
            result = pistas_collection.delete_many({})
            print(f"Eliminadas {result.deleted_count} personas")
            return True
        else:
            print("Operación cancelada")
            return False
            
    except Exception as e:
        print(f"Error al limpiar base de datos: {e}")
        return False

def listar_personas():
    """Lista todas las personas en la base de datos"""
    db, connected = get_db_connection()
    
    if not connected:
        return
    
    try:
        pistas_collection = db.pistas
        personas = list(pistas_collection.find({}, {"_id": 0, "nombre": 1, "fecha_creacion": 1, "wikidata_id": 1}))
        
        if not personas:
            print("\nNo hay personas en la base de datos")
            return
        
        print(f"\nPersonas en la base de datos ({len(personas)}):")
        for i, persona in enumerate(personas, 1):
            nombre = persona.get('nombre', 'Desconocido')
            fecha = persona.get('fecha_creacion', 'N/A')
            wikidata = persona.get('wikidata_id', 'N/A')
            print(f"{i:3d}. {nombre:40s} | {wikidata:10s} | {fecha}")
        
    except Exception as e:
        print(f"Error al listar personas: {e}")
