# MongoDB con Datos Precargados

Este directorio contiene la configuración para construir una imagen Docker de MongoDB con los datos de las pistas ya precargados durante la construcción de la imagen.

## Archivos

- **Dockerfile**: Define la imagen MongoDB personalizada con datos precargados
- **init-data.sh**: Script que se ejecuta durante el build para cargar los datos
- **custom-entrypoint.sh**: Script de arranque personalizado que inicializa la autenticación en el primer inicio
- **pistas.json**: Datos de las 20 personalidades con sus pistas

## Funcionamiento

### Durante el Build de la Imagen

1. Se copia `pistas.json` a la imagen
2. Se ejecuta `init-data.sh` que:
   - Inicia MongoDB temporalmente sin autenticación
   - Importa los 20 personajes con sus pistas a la colección `spygame.pistas`
   - Detiene MongoDB correctamente
   - Los datos quedan guardados en `/data/db` dentro de la imagen

### Durante el Primer Inicio del Contenedor

1. El `custom-entrypoint.sh` verifica si la autenticación está configurada
2. Si no está configurada:
   - Inicia MongoDB temporalmente sin autenticación
   - Crea el usuario admin usando las variables de entorno `MONGO_INITDB_ROOT_USERNAME` y `MONGO_INITDB_ROOT_PASSWORD`
   - Marca la autenticación como inicializada
   - Detiene MongoDB
3. Luego inicia MongoDB normalmente con autenticación habilitada

### Arranques Posteriores

MongoDB inicia normalmente con los datos y la autenticación ya configurados.

## Uso

### Con Docker Compose

```bash
docker compose up -d mongodb
```

Las credenciales se toman del archivo `.env`:
- `MONGO_INITDB_ROOT_USERNAME` (por defecto: spygame)
- `MONGO_INITDB_ROOT_PASSWORD` (por defecto: change_this_password_in_production)

### Construcción Manual

```bash
docker build -t spygame-mongodb ./mongodb
```

### Ejecución Manual

```bash
docker run -d \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=spygame \
  -e MONGO_INITDB_ROOT_PASSWORD=tu_password_seguro \
  -e MONGO_INITDB_DATABASE=spygame \
  -v mongodb_data:/data/db \
  spygame-mongodb
```

## Verificación

Para verificar que los datos están cargados correctamente:

```bash
docker exec <container_name> mongosh spygame \
  -u spygame \
  -p <password> \
  --authenticationDatabase admin \
  --quiet \
  --eval "db.pistas.countDocuments({})"
```

Debería devolver `20`.

Para ver los nombres de los personajes:

```bash
docker exec <container_name> mongosh spygame \
  -u spygame \
  -p <password> \
  --authenticationDatabase admin \
  --quiet \
  --eval "db.pistas.find({}, {nombre: 1, _id: 0}).toArray()"
```

## Personajes Incluidos

La imagen contiene datos de 20 personalidades históricas:

1. Isaac Newton
2. Ludwig van Beethoven
3. Galileo Galilei
4. Albert Einstein
5. Karl Marx
6. Miguel Angel
7. Pablo Picasso
8. Charles Chaplin
9. Winston Churchill
10. Vladimir Putin
11. Iosif Stalin
12. Napoleon Bonaparte
13. Mahatma Gandhi
14. Julio Cesar
15. Jesus de Nazaret
16. Sócrates
17. Leonardo da Vinci
18. Dante Alighieri
19. Buda Gautama
20. Alejandro Magno

Cada personaje incluye 8 pistas con diferentes niveles de dificultad (1-5).

## Ventajas de este Enfoque

✅ **Datos precargados**: No requiere scripts de inicialización en el arranque
✅ **Listo para producción**: La imagen está lista para desplegarse en cualquier servidor
✅ **Autenticación flexible**: Las credenciales se configuran mediante variables de entorno
✅ **Sin dependencias externas**: No requiere archivos externos o scripts de inicialización
✅ **Rápido despliegue**: El contenedor está listo para usar inmediatamente después del primer arranque

## Notas de Seguridad

⚠️ **IMPORTANTE**: Cambia las credenciales por defecto en producción usando el archivo `.env`:

```env
MONGO_INITDB_ROOT_USERNAME=tu_usuario_seguro
MONGO_INITDB_ROOT_PASSWORD=tu_password_muy_seguro
```

## Troubleshooting

### El contenedor no inicia
- Verifica los logs: `docker logs <container_name>`
- Asegúrate de que las variables de entorno están configuradas correctamente

### No se puede autenticar
- Verifica que estás usando las credenciales correctas del archivo `.env`
- Asegúrate de usar `--authenticationDatabase admin`

### Los datos no están presentes
- Reconstruye la imagen: `docker compose build mongodb`
- Verifica que `pistas.json` existe en el directorio `mongodb/`
