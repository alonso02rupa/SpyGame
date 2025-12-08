# Guía de Despliegue de SpyGame en Servidor

## 📦 Qué necesitas enviar al servidor

Para desplegar SpyGame en un servidor externo, necesitas enviar los siguientes archivos y configuraciones:

### Archivos del Proyecto
```bash
# Todo el contenido del repositorio EXCEPTO:
- .git/                  # No es necesario (opcional)
- __pycache__/          # Se generará automáticamente
- *.pyc                 # Se generará automáticamente
- .env                  # NUNCA enviar este archivo (contiene contraseñas)
```

### Método Recomendado: Git Clone

La forma más fácil es que el servidor clone directamente desde GitHub:

```bash
# En el servidor
git clone https://github.com/alonso02rupa/SpyGame.git
cd SpyGame
```

### Método Alternativo: Archivo Comprimido

Si prefieres enviar los archivos manualmente:

```bash
# En tu máquina local
# Crear un archivo .tar.gz excluyendo archivos innecesarios
tar -czf spygame.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='mongodb_data' \
    --exclude='game_sessions.json' \
    .

# Enviar spygame.tar.gz al servidor (por FTP, SCP, etc.)
```

### Configuración en el Servidor

**1. Crear archivo `.env` en el servidor:**

```bash
# En el servidor, dentro de la carpeta SpyGame
cp .env.example .env
nano .env  # o vim .env
```

**Configurar variables importantes:**
```bash
# Flask Configuration
FLASK_SECRET_KEY=GENERA_UNA_CLAVE_SECRETA_ALEATORIA_AQUI
FLASK_ENV=production
FLASK_DEBUG=False

# MongoDB Configuration
MONGO_INITDB_ROOT_USERNAME=spygame
MONGO_INITDB_ROOT_PASSWORD=CAMBIA_ESTA_CONTRASEÑA_A_UNA_SEGURA

# Hugging Face API (si vas a procesar nuevas personas)
HUGGINGFACE_API_KEY=tu_clave_api_aqui

# Nginx Configuration
NGINX_PORT=80
```

**2. Generar una clave secreta segura:**

```bash
# En el servidor, ejecuta:
python3 -c 'import secrets; print(secrets.token_hex(32))'
# Copia el resultado en FLASK_SECRET_KEY
```

**3. Requisitos del Servidor:**

- **Docker**: versión 20.10 o superior
- **Docker Compose**: versión 2.0 o superior
- **Puerto 80**: debe estar disponible (o cambiar NGINX_PORT en .env)
- **Puerto 27017**: para MongoDB (solo si quieres acceso externo con MongoDB Compass)

**4. Iniciar la aplicación:**

```bash
# En el servidor
docker compose up -d
```

---

## 🔒 Acceso a las Rutas de la Aplicación

### Configuración de Rutas

La configuración de nginx está diseñada para servir la aplicación **únicamente** en `/spygame`, dejando la raíz y otras rutas disponibles para otros usos.

### Explicación Detallada

La configuración actual de nginx funciona así:

#### 1. Raíz del Servidor (/)
```
http://localhost/
```

- **No configurada** - Disponible para otros servicios o aplicaciones
- No hay redirección automática
- Devolverá 404 si no hay otro servicio configurado

#### 2. Aplicación Principal (líneas 76-104 de nginx.conf)
```nginx
location /spygame {
    # Proxy a Flask
    proxy_pass http://flask_app;
    proxy_set_header X-Script-Name /spygame;
    # ...
}
```

- **Qué hace:** Cualquier ruta que empiece con `/spygame` se envía a la aplicación Flask
- **Incluye:**
  - `/spygame/` → Página principal del juego
  - `/spygame/stats` → Estadísticas
  - `/spygame/login` → Login
  - `/spygame/register` → Registro
  - `/spygame/start_game` → API para iniciar juego
  - etc.

#### 3. Archivos Estáticos (líneas 107-115 de nginx.conf)
```nginx
location /spygame/static {
    # Archivos CSS, imágenes, etc.
    proxy_pass http://flask_app/spygame/static;
}
```

#### 4. Health Check (líneas 118-122 de nginx.conf)
```nginx
location /health {
    return 200 "healthy\n";
}
```

- Ruta especial para monitoreo
- No pasa por Flask

### Todas las Rutas Disponibles

| Ruta | Funcionamiento | Descripción |
|------|----------------|-------------|
| `http://localhost/` | ⚪ No configurada | Disponible para otros servicios |
| `http://localhost/spygame` | ✅ Funciona | Juego principal |
| `http://localhost/spygame/stats` | ✅ Funciona | Estadísticas |
| `http://localhost/spygame/static/style.css` | ✅ Funciona | Archivos CSS/JS |
| `http://localhost/health` | ✅ Funciona | Monitoreo del servidor |
| `http://localhost/otra-ruta` | ⚪ No configurada | Disponible para otros servicios |

**Nota:** La raíz (`/`) y otras rutas están disponibles para que puedas configurar otros servicios o aplicaciones en el mismo servidor nginx.

---

## ⚙️ Qué Hace Nginx - Explicación Completa

Nginx actúa como un **reverse proxy** (proxy inverso) entre internet y tu aplicación Flask. Es como un portero inteligente que:

### 1. Recibe Todas las Peticiones del Exterior

```
Internet → Puerto 80 (Nginx) → Decide qué hacer
```

### 2. Funciones Principales

#### A. **Reverse Proxy** (líneas 76-104)
```nginx
location /spygame {
    proxy_pass http://flask_app;  # Redirige a Flask en puerto 5000
}
```

**Qué hace:**
- Recibe peticiones en el puerto 80 (http://tu-servidor/spygame)
- Las reenvía internamente a Flask (http://web:5000)
- Flask responde a nginx
- Nginx devuelve la respuesta al usuario

**Ventajas:**
- Flask no está expuesto directamente a internet
- Nginx maneja mejor múltiples conexiones simultáneas
- Puedes tener múltiples aplicaciones en el mismo servidor

#### B. **Seguridad** (líneas 41-46)

```nginx
# Cabeceras de seguridad
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Content-Security-Policy "...";
```

**Qué hace:**
- **X-Frame-Options**: Previene que tu sitio se muestre en iframes maliciosos
- **X-Content-Type-Options**: Previene ataques de MIME-type sniffing
- **Content-Security-Policy**: Controla de dónde se pueden cargar scripts, estilos, etc.
- **Referrer-Policy**: Controla qué información se envía al navegar

#### C. **Rate Limiting** (Limitación de Velocidad) (líneas 48-49, 77-78)

```nginx
limit_req_zone $binary_remote_addr zone=spygame_limit:10m rate=10r/s;
limit_req zone=spygame_limit burst=20 nodelay;
```

**Qué hace:**
- Limita cada IP a **10 peticiones por segundo**
- Permite ráfagas (burst) de hasta **20 peticiones**
- Si alguien excede el límite → Error 429 (Too Many Requests)

**Por qué es importante:**
- Previene ataques DDoS (Distributed Denial of Service)
- Previene intentos de fuerza bruta en login
- Protege tu servidor de sobrecarga

#### D. **Connection Limiting** (líneas 51-52, 68)

```nginx
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;
limit_conn conn_limit 20;
```

**Qué hace:**
- Máximo **20 conexiones simultáneas** por IP
- Si alguien intenta abrir 21+ conexiones → se rechazan

#### E. **Compresión Gzip** (líneas 32-39)

```nginx
gzip on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json ...;
```

**Qué hace:**
- Comprime archivos HTML, CSS, JS antes de enviarlos
- Reduce el tamaño de transferencia ~70%
- Hace que tu sitio cargue más rápido

**Ejemplo:**
- Archivo CSS original: 100 KB
- Después de gzip: ~30 KB
- 70% menos datos transferidos

#### F. **Caché de Archivos Estáticos** (líneas 107-115)

```nginx
location /spygame/static {
    expires 1d;
    add_header Cache-Control "public, immutable";
}
```

**Qué hace:**
- Los archivos CSS/JS se cachean en el navegador por **1 día**
- El navegador no vuelve a descargarlos en cada visita
- Ahorra ancho de banda y acelera la carga

#### G. **Bloqueo de Archivos Sensibles** (líneas 124-131)

```nginx
location ~ /\. {
    deny all;  # Bloquea archivos ocultos (.env, .git, etc.)
}

location ~ \.py$ {
    deny all;  # Bloquea acceso directo a archivos Python
}
```

**Qué hace:**
- Impide acceder a `.env`, `.git`, archivos `.py`
- Protege código fuente y configuraciones sensibles

#### H. **Health Check** (líneas 118-122)

```nginx
location /health {
    access_log off;
    return 200 "healthy\n";
}
```

**Qué hace:**
- Endpoint simple para monitoreo
- Responde "healthy" si nginx funciona
- No genera logs (ahorra espacio)

### 3. Flujo Completo de una Petición

```
1. Usuario escribe: http://tu-servidor/spygame

2. Nginx recibe en puerto 80
   ↓
3. Nginx aplica:
   - Rate limiting (¿ha hecho muchas peticiones?)
   - Connection limiting (¿tiene muchas conexiones abiertas?)
   ↓
4. Nginx pasa la petición a Flask (web:5000)
   proxy_set_header X-Script-Name /spygame
   ↓
5. Flask procesa la petición
   - Lee X-Script-Name
   - Sabe que está en /spygame
   - Genera las rutas correctamente
   ↓
6. Flask devuelve HTML a nginx
   ↓
7. Nginx comprime con gzip (si aplica)
   ↓
8. Nginx añade cabeceras de seguridad
   ↓
9. Nginx envía respuesta al usuario
```

### 4. Ventajas de Usar Nginx

| Aspecto | Sin Nginx (Flask directo) | Con Nginx |
|---------|---------------------------|-----------|
| **Seguridad** | Flask expuesto directamente | Flask protegido detrás de nginx |
| **Rate Limiting** | Debe implementarse en Flask | Lo maneja nginx eficientemente |
| **Compresión** | Debe implementarse en Flask | Nginx lo hace automáticamente |
| **Múltiples Apps** | Difícil gestionar | Fácil con nginx (rutas diferentes) |
| **Performance** | Bueno para pocas conexiones | Excelente para miles de conexiones |
| **SSL/HTTPS** | Debe configurarse en Flask | Nginx lo maneja mejor |
| **Caché** | Limitado | Control fino con nginx |
| **Logs** | Solo logs de Flask | Logs separados de nginx y Flask |

### 5. Configuración de Puertos

```yaml
# docker-compose.yml

nginx:
  ports:
    - "80:80"  # Puerto 80 del servidor → Puerto 80 de nginx

web:
  expose:
    - "5000"   # Solo expuesto INTERNAMENTE en la red Docker
```

**Explicación:**
- **Puerto 80**: Accesible desde internet → Nginx
- **Puerto 5000**: Solo accesible desde otros contenedores Docker (MongoDB, Nginx)
- Flask **NO** está expuesto directamente a internet

---

## 📊 Resumen Visual

```
┌─────────────────────────────────────────────────────────────┐
│                         INTERNET                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │  Puerto 80 (Nginx)     │
          │  - Rate Limiting       │
          │  - Seguridad           │
          │  - Compresión          │
          │  - Caché               │
          └────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │  Red Interna Docker          │
    │                              │
    │  ┌──────────────────┐        │
    │  │  Flask (web:5000)│        │
    │  │  - Lógica del    │        │
    │  │    juego         │        │
    │  └────────┬─────────┘        │
    │           │                  │
    │           ▼                  │
    │  ┌──────────────────┐        │
    │  │  MongoDB (27017) │        │
    │  │  - Base de datos │        │
    │  └──────────────────┘        │
    └──────────────────────────────┘
```

---

## 🚀 Comandos Útiles en el Servidor

```bash
# Iniciar servicios
docker compose up -d

# Ver logs de nginx
docker compose logs nginx

# Ver logs de Flask
docker compose logs web

# Reiniciar nginx
docker compose restart nginx

# Ver estado de servicios
docker compose ps

# Parar todo
docker compose down

# Ver uso de recursos
docker stats
```

---

## 🔧 Solución de Problemas

### Problema: "502 Bad Gateway"
- **Causa:** Flask no está corriendo o no responde
- **Solución:** 
  ```bash
  docker compose logs web
  docker compose restart web
  ```

### Problema: "429 Too Many Requests"
- **Causa:** Se excedió el rate limit
- **Solución:** Esperar unos segundos o aumentar el límite en nginx.conf

### Problema: "Permission denied" al iniciar
- **Causa:** El puerto 80 requiere permisos de root
- **Solución:** 
  ```bash
  sudo docker compose up -d
  # O cambiar NGINX_PORT=8080 en .env
  ```

---

## 📝 Notas Adicionales

1. **MongoDB Port (27017):** Está expuesto en docker-compose.yml para poder usar MongoDB Compass. En producción real, deberías quitarlo para mayor seguridad.

2. **Volúmenes de Desarrollo:** Las líneas `volumes:` en docker-compose.yml son para desarrollo. En producción, todo se copia en la imagen Docker (ya está en el Dockerfile).

3. **HTTPS:** Para usar HTTPS (puerto 443), necesitarías:
   - Un dominio (ej: mispygame.com)
   - Certificado SSL (gratis con Let's Encrypt)
   - Configuración adicional en nginx.conf

4. **Firewall del Servidor:** Asegúrate de que el puerto 80 esté abierto:
   ```bash
   # En el servidor
   sudo ufw allow 80/tcp
   sudo ufw status
   ```
