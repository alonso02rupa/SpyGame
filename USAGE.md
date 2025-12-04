# SpyGame - Guia de Uso con Docker

## Inicio Rapido

### 1. Levantar los servicios

```bash
docker-compose up -d --build
```

Esto iniciara:
- **MongoDB** en el puerto 27017
- **Web App** en el puerto 5000

**Nota:** La primera vez tardara unos minutos para descargar el modelo de spaCy.

### 2. Inicializar la base de datos con un ejemplo

```bash
docker-compose exec web python init_db.py
```

Este comando carga Donald Trump desde `pistas.json` como ejemplo inicial.

### 3. Acceder a la aplicacion

Abre tu navegador en: http://localhost:5000

---

## Procesamiento de Datos

### Anadir personas desde Wikipedia a la base de datos

Una vez que el servicio esta corriendo, puedes procesar personas desde Wikipedia:

```bash
# Procesar 5 personas (por defecto)
docker-compose exec web python process_data.py

# Procesar 10 personas
docker-compose exec web python process_data.py --num 10

# Procesar con parametros personalizados
docker-compose exec web python process_data.py --num 20 --min-sitelinks 200 --offset 100
```

#### Parametros disponibles:
- `--num`: Numero de personas a procesar (default: 5)
- `--limit`: Limite de resultados de Wikidata (default: 200)
- `--offset`: Offset para paginacion (default: 0)
- `--min-sitelinks`: Minimo de sitelinks en Wikipedia (default: 150)

### Listar personas en la base de datos

```bash
docker-compose exec web python init_db.py --list
```

---

## Comandos Utiles

### Ver logs de la aplicacion
```bash
docker-compose logs -f web
```

### Ver logs de MongoDB
```bash
docker-compose logs -f mongodb
```

### Acceder a la shell del contenedor web
```bash
docker-compose exec web bash
```

### Acceder a MongoDB CLI
```bash
# Con autenticación (requerido)
docker-compose exec mongodb mongosh -u spygame -p your_password --authenticationDatabase admin spygame
```

### Backup de la base de datos
```bash
# Crear backup
docker-compose exec mongodb mongodump -u spygame -p your_password --authenticationDatabase admin --db spygame --out /data/db/backup

# Copiar backup al host
docker cp $(docker-compose ps -q mongodb):/data/db/backup ./backup
```

### Restaurar base de datos
```bash
# Copiar backup al contenedor
docker cp ./backup $(docker-compose ps -q mongodb):/data/db/backup

# Restaurar
docker-compose exec mongodb mongorestore -u spygame -p your_password --authenticationDatabase admin --db spygame /data/db/backup/spygame
```

### Reiniciar servicios
```bash
docker-compose restart
```

### Detener servicios
```bash
docker-compose down
```

### Detener y eliminar volumenes (ADVERTENCIA: BORRA LA BASE DE DATOS)
```bash
docker-compose down -v
```

---

## Estructura de la Base de Datos

### Colección: `pistas`

Cada documento tiene la siguiente estructura:

```json
{
  "nombre": "Donald Trump",
  "pistas": [
    {
      "dificultad": 5,
      "pista": "Este estadounidense es el 47º presidente..."
    },
    {
      "dificultad": 4,
      "pista": "Fue el primer presidente estadounidense..."
    }
  ],
  "wikidata_id": "Q22686",
  "url_wikipedia": "https://es.wikipedia.org/wiki/Donald_Trump",
  "fecha_creacion": "2025-10-07T12:00:00"
}
```

### Coleccion: `users`
Almacena usuarios registrados con contrasenas hasheadas.

### Coleccion: `sessions`
Almacena el historial de juegos.

---

## Desarrollo Local (sin Docker)

Si prefieres ejecutar sin Docker:

### 1. Instalar MongoDB localmente

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```

### 4. Configurar variables de entorno
Crear archivo `.env` con:
```
MONGODB_URI=mongodb://localhost:27017/spygame
HUGGINGFACE_API_KEY=tu_api_key
HUGGINGFACE_MODEL_NAME=meta-llama/Meta-Llama-3-8B-Instruct
FLASK_SECRET_KEY=tu_secret_key
```

### 5. Inicializar base de datos
```bash
python init_db.py
```

### 6. Ejecutar aplicacion
```bash
python app.py
```

### 7. Procesar datos
```bash
cd datatreatment
python data_processor.py --num 5
```

---

## Flujo de Trabajo Recomendado

1. **Levantar servicios**: `docker-compose up -d --build`
2. **Cargar ejemplo inicial**: `docker-compose exec web python init_db.py`
3. **Probar la aplicacion**: Visita http://localhost:5000
4. **Anadir mas personas**: `docker-compose exec web python process_data.py --num 10`
5. **Verificar datos**: `docker-compose exec web python init_db.py --list`

---

## Notas Importantes

- Las personas se procesan desde Wikipedia en espanol
- Se requiere API key de Hugging Face para generar pistas
- El procesamiento puede tardar varios minutos dependiendo del numero de personas
- Las pistas se generan usando IA y se almacenan directamente en MongoDB
- El archivo `pistas.json` es solo para el ejemplo inicial y no se usa durante el juego

---

## Solucion de Problemas

### Error de conexion a MongoDB
```bash
# Verificar que MongoDB esta corriendo
docker-compose ps

# Reiniciar MongoDB
docker-compose restart mongodb
```

### Error: Can't find model 'es_core_news_sm'
```bash
# Reconstruir la imagen Docker
docker-compose down
docker-compose up -d --build
```

### Error de API de Hugging Face
Verifica que tu API key esta correctamente configurada en `.env`:
```
HUGGINGFACE_API_KEY=hf_tu_key_aqui
```

### No hay personas en la base de datos
```bash
# Cargar ejemplo inicial
docker-compose exec web python init_db.py

# O procesar nuevas personas
docker-compose exec web python process_data.py --num 5
```

---

## Variables de Entorno

Crear archivo `.env` en la raiz del proyecto:

```env
# Flask
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False

# MongoDB
MONGO_INITDB_DATABASE=spygame
MONGODB_PORT=27017
# MongoDB Authentication (required for Docker deployment)
MONGO_INITDB_ROOT_USERNAME=spygame
MONGO_INITDB_ROOT_PASSWORD=change_this_password_in_production

# Docker
DOCKER_WEB_PORT=5000

# Hugging Face
HUGGINGFACE_API_KEY=your-huggingface-api-key
HUGGINGFACE_MODEL_NAME=meta-llama/Meta-Llama-3-8B-Instruct

# Wikipedia
WIKIPEDIA_USER_AGENT=SpyGame/1.0.0 (contact: your@email.com)
```

---

## Seguridad

### Autenticación MongoDB

MongoDB ahora requiere autenticación. Configura las credenciales en tu archivo `.env`:

```env
MONGO_INITDB_ROOT_USERNAME=spygame
MONGO_INITDB_ROOT_PASSWORD=tu_password_segura_aqui
```

**Importante:** 
- Cambia las credenciales por defecto en producción
- MongoDB solo es accesible internamente (los puertos no están expuestos al host)

### Requisitos de Contraseña

Las contraseñas de usuario deben cumplir:
- Mínimo 12 caracteres
- Al menos una letra mayúscula
- Al menos una letra minúscula
- Al menos un número
- Al menos un carácter especial

### Rate Limiting

La aplicación incluye límites de peticiones:
- `/login`: 5 intentos por minuto
- `/register`: 3 intentos por minuto
- `/make_guess`: 20 intentos por minuto
- Global: 200 peticiones/día, 50 peticiones/hora

Para más información sobre seguridad, consulta [SECURITY.md](SECURITY.md).
