#!/bin/bash

# SpyGame - Script de ayuda para Docker

echo "=================================="
echo "SpyGame - Docker Helper"
echo "=================================="
echo ""

case "$1" in
  start)
    echo "Iniciando servicios..."
    docker-compose up -d
    echo "Servicios iniciados"
    echo "Aplicacion disponible en: http://localhost:5000"
    ;;
    
  build)
    echo "Reconstruyendo imagen Docker..."
    docker-compose up -d --build
    echo "Imagen reconstruida y servicios iniciados"
    echo "Aplicacion disponible en: http://localhost:5000"
    ;;
    
  stop)
    echo "Deteniendo servicios..."
    docker-compose down
    echo "Servicios detenidos"
    ;;
    
  restart)
    echo "Reiniciando servicios..."
    docker-compose restart
    echo "Servicios reiniciados"
    ;;
    
  init)
    echo "Inicializando base de datos con ejemplo..."
    docker-compose exec web python init_db.py
    ;;
    
  check)
    echo "Verificando estado del sistema..."
    docker-compose exec web python check_system.py
    ;;
    
  list)
    echo "Listando personas en la base de datos..."
    docker-compose exec web python init_db.py --list
    ;;
    
  process)
    NUM="${2:-5}"
    echo "Procesando $NUM personas desde Wikipedia..."
    docker-compose exec web python process_data.py --num $NUM
    ;;
    
  logs)
    echo "Mostrando logs de la aplicacion..."
    docker-compose logs -f web
    ;;
    
  logs-db)
    echo "Mostrando logs de MongoDB..."
    docker-compose logs -f mongodb
    ;;
    
  shell)
    echo "Abriendo shell en el contenedor web..."
    docker-compose exec web bash
    ;;
    
  mongo)
    echo "Conectando a MongoDB..."
    docker-compose exec mongodb mongosh spygame
    ;;
    
  backup)
    BACKUP_FILE="spygame_backup_$(date +%Y%m%d_%H%M%S).archive"
    echo "Creando backup de la base de datos..."
    docker-compose exec -T mongodb mongodump --username=admin --password="${MONGO_INITDB_ROOT_PASSWORD}" --authenticationDatabase=admin --db=spygame --archive > "$BACKUP_FILE"
    echo "Backup creado: $BACKUP_FILE"
    ;;
    
  restore)
    if [ -z "$2" ]; then
      echo "Error: Especifica el archivo de backup"
      echo "Uso: $0 restore <archivo.archive>"
      exit 1
    fi
    echo "Restaurando desde $2..."
    docker-compose exec -T mongodb mongorestore --username=admin --password="${MONGO_INITDB_ROOT_PASSWORD}" --authenticationDatabase=admin --archive < "$2"
    echo "Restauracion completada"
    ;;
    
  export-json)
    mkdir -p backups
    echo "Exportando colecciones a JSON..."
    docker-compose exec mongodb mongoexport --username=admin --password="${MONGO_INITDB_ROOT_PASSWORD}" --authenticationDatabase=admin --db=spygame --collection=persons --out=/tmp/persons.json
    docker-compose exec mongodb mongoexport --username=admin --password="${MONGO_INITDB_ROOT_PASSWORD}" --authenticationDatabase=admin --db=spygame --collection=game_sessions --out=/tmp/game_sessions.json
    docker cp $(docker-compose ps -q mongodb):/tmp/persons.json ./backups/
    docker cp $(docker-compose ps -q mongodb):/tmp/game_sessions.json ./backups/
    echo "JSON exportados a ./backups/"
    ;;
  
  clean)
    echo "Estas seguro de que quieres eliminar TODOS los datos? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
      echo "Eliminando contenedores y volumenes..."
      docker-compose down -v
      echo "Limpieza completada"
    else
      echo "Operacion cancelada"
    fi
    ;;
    
  *)
    echo "Uso: $0 {comando} [opciones]"
    echo ""
    echo "Comandos disponibles:"
    echo "  start          - Iniciar todos los servicios"
    echo "  build          - Reconstruir imagen y iniciar servicios"
    echo "  stop           - Detener todos los servicios"
    echo "  restart        - Reiniciar todos los servicios"
    echo "  init           - Inicializar BD con ejemplo de Donald Trump"
    echo "  check          - Verificar estado del sistema"
    echo "  list           - Listar personas en la base de datos"
    echo "  process [N]    - Procesar N personas de Wikipedia (default: 5)"
    echo "  logs           - Ver logs de la aplicacion web"
    echo "  logs-db        - Ver logs de MongoDB"
    echo "  shell          - Abrir shell en el contenedor web"
    echo "  mongo          - Conectar a MongoDB CLI"
    echo "  backup         - Crear backup de la base de datos"
    echo "  restore <file> - Restaurar desde un archivo de backup"
    echo "  export-json    - Exportar colecciones a JSON legible"
    echo "  clean          - Eliminar contenedores y datos (DESTRUCTIVO)"
    echo ""
    echo "Ejemplos:"
    echo "  $0 build       # Primera vez o despues de cambios"
    echo "  $0 start"
    echo "  $0 init"
    echo "  $0 check"
    echo "  $0 process 10"
    echo "  $0 list"
    echo "  $0 backup"
    echo "  $0 restore spygame_backup_20231204.archive"
    ;;
esac
