#!/usr/bin/env python
"""
dirt_builder.py

Sistema DIRT (Discovery of Inference Rules from Text)
Lee textos biográficos, extrae triples sujeto-verbo-objeto con spaCy,
calcula similitudes entre verbos usando coocurrencias y PMI,
y genera un modelo de equivalencias de inferencia.

Uso:
    python dirt_builder.py
"""

import json
import os
import math
import time
from collections import defaultdict, Counter
from dotenv import load_dotenv
import spacy
import wikipediaapi
import urllib.parse
import regex as re
from pymongo import MongoClient

# Cargar variables de entorno
load_dotenv()

# Cargar modelo de spaCy
try:
    nlp = spacy.load("es_core_news_sm")
except OSError:
    print("Error: Modelo de spaCy 'es_core_news_sm' no encontrado.")
    print("Instálalo con: python -m spacy download es_core_news_sm")
    exit(1)

# Configuración de MongoDB
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/spygame')

# Archivo de salida para el modelo DIRT
MODELO_INFERENCIAS = "modelo_inferencias.json"


def get_db_connection():
    """Establece conexión con MongoDB"""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client.spygame
        return db, True
    except Exception as e:
        print(f"MongoDB no disponible: {e}")
        return None, False


def obtener_textos_biografias(num_personas=10):
    """
    Obtiene textos de biografías directamente desde Wikidata/Wikipedia.
    Similar al proceso de data_processor.py pero solo extrae los textos.
    
    Args:
        num_personas: Número de biografías a procesar
    
    Returns:
        Lista de strings con los textos biográficos
    """
    textos = []
    
    print(f"Obteniendo {num_personas} personas desde Wikidata...")
    
    try:
        # Importar la función desde data_processor si está disponible
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'datatreatment'))
        
        try:
            from datatreatment.data_processor import get_wikidata_items
            
            # Obtener personas de Wikidata
            df = get_wikidata_items(
                limit=100, 
                offset=0, 
                min_sitelinks=150, 
                sample_size=num_personas
            )
            
            if not df.empty:
                print(f"✓ Obtenidas {len(df)} personas desde Wikidata\n")
                
                user_agent = os.getenv('WIKIPEDIA_USER_AGENT', 'SpyGame/1.0.0')
                wiki_es = wikipediaapi.Wikipedia(language='es', user_agent=user_agent)
                
                for idx, row in df.iterrows():
                    url = row['articulo_es']
                    titulo_codificado = url.split("/wiki/")[-1]
                    titulo = urllib.parse.unquote(titulo_codificado).replace('_', ' ')
                    
                    try:
                        articulo = wiki_es.page(titulo)
                        if articulo.exists():
                            texto = articulo.summary
                            # Añadir primeras secciones para más contexto
                            for section in articulo.sections[:5]:
                                texto += " " + section.text
                            
                            textos.append(limpiar_texto(texto))
                            print(f"  ✓ {titulo}: {len(texto)} caracteres")
                        else:
                            print(f"  ✗ {titulo}: artículo no encontrado")
                    except Exception as e:
                        print(f"  ✗ {titulo}: error ({str(e)[:50]})")
                    
                    # Pequeña pausa para no saturar la API
                    import time
                    time.sleep(0.5)
            else:
                print("⚠ No se obtuvieron personas desde Wikidata")
                
        except ImportError:
            print("⚠ No se pudo importar data_processor.py")
    
    except Exception as e:
        print(f"⚠ Error al obtener datos de Wikidata: {e}")
    
    # Si no hay suficientes textos, usar textos de ejemplo
    if len(textos) < 3:
        print("\n⚠ Pocos textos obtenidos. Usando textos de ejemplo para demostración...")
        textos_ejemplo = [
            """Marie Curie fue una científica polaca. Nació en Varsovia en 1867. Estudió física y química en París. 
            Descubrió dos elementos químicos: el polonio y el radio. Trabajó en investigación sobre radiactividad. 
            Recibió el Premio Nobel de Física en 1903. Fundó el Instituto Curie en París. Dirigió el departamento 
            de física. Ganó un segundo Premio Nobel en 1911. Desarrolló técnicas de radioterapia. Murió en 1934.""",
            
            """Leonardo da Vinci nació en Italia en 1452. Fue pintor, escultor e inventor. Creó la Mona Lisa y 
            La Última Cena. Diseñó máquinas voladoras y armas de guerra. Estudió anatomía humana y diseccionó 
            cadáveres. Trabajó para nobles italianos y franceses. Pintó frescos en iglesias y palacios. Inventó 
            dispositivos mecánicos innovadores. Escribió miles de páginas de notas y dibujos. Murió en Francia en 1519.""",
            
            """Albert Einstein nació en Alemania en 1879. Estudió física en Zúrich. Publicó la teoría de la 
            relatividad en 1905. Revolucionó la física moderna. Ganó el Premio Nobel en 1921. Desarrolló la 
            ecuación E=mc². Trabajó en la Universidad de Berlín. Emigró a Estados Unidos en 1933. Fundó nuevas 
            teorías sobre la gravedad. Murió en Princeton en 1955.""",
            
            """Frida Kahlo nació en México en 1907. Estudió en la Escuela Nacional Preparatoria. Sufrió un grave 
            accidente que marcó su vida. Pintó numerosos autorretratos. Desarrolló un estilo único inspirado en 
            la cultura mexicana. Se casó con Diego Rivera. Expuso sus obras en galerías de todo el mundo. Fundó 
            un movimiento artístico propio. Recibió reconocimiento internacional. Murió en 1954.""",
            
            """Nelson Mandela nació en Sudáfrica en 1918. Estudió derecho en Johannesburgo. Luchó contra el 
            apartheid. Fundó el Congreso Nacional Africano. Fue encarcelado durante 27 años. Recibió el Premio 
            Nobel de la Paz. Se convirtió en presidente de Sudáfrica. Promovió la reconciliación nacional. 
            Estableció la Fundación Nelson Mandela. Murió en 2013."""
        ]
        textos.extend(textos_ejemplo)
    
    print(f"\n✓ Total de textos para procesar: {len(textos)}\n")
    return textos


def limpiar_texto(texto):
    """Limpia y normaliza el texto"""
    texto = re.sub(r'\[\d+\]', '', texto)
    texto = re.sub(r'\([^)]*\)', '', texto)
    texto = re.sub(r'\n+', ' ', texto)
    texto = re.sub(r'\s{2,}', ' ', texto)
    return texto.strip()


def extraer_triples_svo(textos):
    """
    Extrae triples sujeto-verbo-objeto de los textos usando spaCy.
    
    Args:
        textos: Lista de strings con los textos a procesar
    
    Returns:
        Lista de tuplas (sujeto, verbo, objeto)
    """
    triples = []
    
    print("Extrayendo triples sujeto-verbo-objeto...")
    
    for i, texto in enumerate(textos):
        doc = nlp(texto)
        
        for sent in doc.sents:
            # Buscar el verbo principal
            verbos = [token for token in sent if token.pos_ == "VERB"]
            
            for verbo in verbos:
                # Buscar sujeto
                sujeto = None
                for child in verbo.children:
                    if child.dep_ in ("nsubj", "nsubjpass"):
                        sujeto = child.lemma_.lower()
                        break
                
                # Buscar objeto
                objeto = None
                for child in verbo.children:
                    if child.dep_ in ("dobj", "obj", "iobj"):
                        objeto = child.lemma_.lower()
                        break
                
                # Si encontramos sujeto y verbo, guardamos el triple
                if sujeto and verbo.lemma_:
                    triple = (sujeto, verbo.lemma_.lower(), objeto if objeto else "_")
                    triples.append(triple)
        
        if (i + 1) % 5 == 0 or i == len(textos) - 1:
            print(f"  Procesados {i + 1}/{len(textos)} textos - {len(triples)} triples extraídos")
    
    print(f"\n✓ Total de triples extraídos: {len(triples)}\n")
    return triples


def calcular_similitudes_verbos(triples, umbral_score=0.1):
    """
    Calcula similitudes entre verbos usando coocurrencias y PMI.
    
    Args:
        triples: Lista de tuplas (sujeto, verbo, objeto)
        umbral_score: Score mínimo para incluir una equivalencia
    
    Returns:
        Lista de diccionarios con equivalencias {a, b, score}
    """
    print("Calculando similitudes entre verbos...")
    
    # Contar coocurrencias: qué verbos comparten los mismos sujetos/objetos
    verbos_con_contexto = defaultdict(lambda: {"sujetos": Counter(), "objetos": Counter()})
    total_verbos = 0
    
    for sujeto, verbo, objeto in triples:
        verbos_con_contexto[verbo]["sujetos"][sujeto] += 1
        if objeto != "_":
            verbos_con_contexto[verbo]["objetos"][objeto] += 1
        total_verbos += 1
    
    # Frecuencias de verbos
    freq_verbos = Counter()
    for _, verbo, _ in triples:
        freq_verbos[verbo] += 1
    
    # Calcular similitud entre pares de verbos
    verbos = list(verbos_con_contexto.keys())
    equivalencias = []
    
    for i, verbo_a in enumerate(verbos):
        for verbo_b in verbos[i+1:]:
            if verbo_a == verbo_b:
                continue
            
            # Calcular similitud basada en contextos compartidos
            contexto_a = verbos_con_contexto[verbo_a]
            contexto_b = verbos_con_contexto[verbo_b]
            
            # Sujetos en común
            sujetos_comunes = set(contexto_a["sujetos"].keys()) & set(contexto_b["sujetos"].keys())
            # Objetos en común
            objetos_comunes = set(contexto_a["objetos"].keys()) & set(contexto_b["objetos"].keys())
            
            # Si comparten contextos, calcular PMI
            if sujetos_comunes or objetos_comunes:
                # Similitud simple basada en proporción de contextos compartidos
                total_contextos_a = len(contexto_a["sujetos"]) + len(contexto_a["objetos"])
                total_contextos_b = len(contexto_b["sujetos"]) + len(contexto_b["objetos"])
                contextos_compartidos = len(sujetos_comunes) + len(objetos_comunes)
                
                if total_contextos_a > 0 and total_contextos_b > 0:
                    # Coeficiente de Jaccard modificado
                    union = total_contextos_a + total_contextos_b - contextos_compartidos
                    similitud = contextos_compartidos / union if union > 0 else 0
                    
                    # Bonus por frecuencia similar
                    freq_a = freq_verbos[verbo_a]
                    freq_b = freq_verbos[verbo_b]
                    ratio_freq = min(freq_a, freq_b) / max(freq_a, freq_b) if max(freq_a, freq_b) > 0 else 0
                    
                    # Score final combinado
                    score = (similitud * 0.7) + (ratio_freq * 0.3)
                    
                    if score >= umbral_score:
                        equivalencias.append({
                            "a": verbo_a,
                            "b": verbo_b,
                            "score": round(score, 3),
                            "contextos_compartidos": contextos_compartidos,
                            "freq_a": freq_a,
                            "freq_b": freq_b
                        })
        
        if (i + 1) % 10 == 0 or i == len(verbos) - 1:
            print(f"  Procesados {i + 1}/{len(verbos)} verbos")
    
    # Ordenar por score descendente
    equivalencias.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"\n✓ Equivalencias encontradas: {len(equivalencias)}\n")
    
    # Mostrar top 10
    print("Top 10 equivalencias por score:")
    for eq in equivalencias[:10]:
        print(f"  {eq['a']:15} ≈ {eq['b']:15} (score: {eq['score']:.3f})")
    
    return equivalencias


def guardar_modelo(equivalencias, filepath=MODELO_INFERENCIAS):
    """
    Guarda el modelo de inferencias en formato JSON.
    
    Args:
        equivalencias: Lista de equivalencias
        filepath: Ruta del archivo de salida
    """
    modelo = {
        "version": "1.0",
        "generado": str(os.popen("date /t").read().strip() if os.name == 'nt' else os.popen("date").read().strip()),
        "num_equivalencias": len(equivalencias),
        "equivalencias": equivalencias
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(modelo, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Modelo guardado en: {filepath}")
    print(f"  Total de equivalencias: {len(equivalencias)}")


def main():
    """Función principal que ejecuta todo el pipeline DIRT"""
    print("="*60)
    print("DIRT Builder - Discovery of Inference Rules from Text")
    print("="*60 + "\n")
    
    # 1. Obtener textos de biografías
    textos = obtener_textos_biografias(num_personas=15)
    
    if not textos:
        print("✗ No se pudieron obtener textos. Abortando.")
        return
    
    # 2. Extraer triples SVO
    triples = extraer_triples_svo(textos)
    
    if not triples:
        print("✗ No se extrajeron triples. Abortando.")
        return
    
    # 3. Calcular similitudes entre verbos
    equivalencias = calcular_similitudes_verbos(triples, umbral_score=0.1)
    
    if not equivalencias:
        print("✗ No se encontraron equivalencias. Abortando.")
        return
    
    # 4. Guardar modelo
    guardar_modelo(equivalencias)
    
    print("\n" + "="*60)
    print("✓ Proceso completado exitosamente")
    print("="*60)


if __name__ == "__main__":
    main()
