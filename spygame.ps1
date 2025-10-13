# SpyGame - Script de ayuda para Docker (PowerShell)

param(
    [Parameter(Position=0)]
    [string]$Command = "",
    [Parameter(Position=1)]
    [int]$Num = 5
)

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "SpyGame - Docker Helper" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

switch ($Command) {
    "start" {
        Write-Host "Iniciando servicios..." -ForegroundColor Yellow
        docker-compose up -d
        Write-Host "Servicios iniciados" -ForegroundColor Green
        Write-Host "Aplicacion disponible en: http://localhost:5000" -ForegroundColor Cyan
    }
    
    "build" {
        Write-Host "Reconstruyendo imagen Docker..." -ForegroundColor Yellow
        docker-compose up -d --build
        Write-Host "Imagen reconstruida y servicios iniciados" -ForegroundColor Green
        Write-Host "Aplicacion disponible en: http://localhost:5000" -ForegroundColor Cyan
    }
    
    "stop" {
        Write-Host "Deteniendo servicios..." -ForegroundColor Yellow
        docker-compose down
        Write-Host "Servicios detenidos" -ForegroundColor Green
    }
    
    "restart" {
        Write-Host "Reiniciando servicios..." -ForegroundColor Yellow
        docker-compose restart
        Write-Host "Servicios reiniciados" -ForegroundColor Green
    }
    
    "init" {
        Write-Host "Inicializando base de datos con ejemplo..." -ForegroundColor Yellow
        docker-compose exec web python init_db.py
    }
    
    "check" {
        Write-Host "Verificando estado del sistema..." -ForegroundColor Yellow
        docker-compose exec web python check_system.py
    }
    
    "list" {
        Write-Host "Listando personas en la base de datos..." -ForegroundColor Yellow
        docker-compose exec web python init_db.py --list
    }
    
    "process" {
        Write-Host "Procesando $Num personas desde Wikipedia..." -ForegroundColor Yellow
        docker-compose exec web python process_data.py --num $Num
    }
    
    "logs" {
        Write-Host "Mostrando logs de la aplicacion..." -ForegroundColor Yellow
        docker-compose logs -f web
    }
    
    "logs-db" {
        Write-Host "Mostrando logs de MongoDB..." -ForegroundColor Yellow
        docker-compose logs -f mongodb
    }
    
    "shell" {
        Write-Host "Abriendo shell en el contenedor web..." -ForegroundColor Yellow
        docker-compose exec web bash
    }
    
    "mongo" {
        Write-Host "Conectando a MongoDB..." -ForegroundColor Yellow
        docker-compose exec mongodb mongosh spygame
    }
    
    "clean" {
        Write-Host "Estas seguro de que quieres eliminar TODOS los datos? (S/N)" -ForegroundColor Red
        $response = Read-Host
        if ($response -eq "S" -or $response -eq "s") {
            Write-Host "Eliminando contenedores y volumenes..." -ForegroundColor Yellow
            docker-compose down -v
            Write-Host "Limpieza completada" -ForegroundColor Green
        } else {
            Write-Host "Operacion cancelada" -ForegroundColor Red
        }
    }
    
    default {
        Write-Host "Uso: .\spygame.ps1 {comando} [opciones]" -ForegroundColor White
        Write-Host ""
        Write-Host "Comandos disponibles:" -ForegroundColor Yellow
        Write-Host "  start          - Iniciar todos los servicios"
        Write-Host "  build          - Reconstruir imagen y iniciar servicios"
        Write-Host "  stop           - Detener todos los servicios"
        Write-Host "  restart        - Reiniciar todos los servicios"
        Write-Host "  init           - Inicializar BD con ejemplo de Donald Trump"
        Write-Host "  check          - Verificar estado del sistema"
        Write-Host "  list           - Listar personas en la base de datos"
        Write-Host "  process [N]    - Procesar N personas de Wikipedia (default: 5)"
        Write-Host "  logs           - Ver logs de la aplicacion web"
        Write-Host "  logs-db        - Ver logs de MongoDB"
        Write-Host "  shell          - Abrir shell en el contenedor web"
        Write-Host "  mongo          - Conectar a MongoDB CLI"
        Write-Host "  clean          - Eliminar contenedores y datos (DESTRUCTIVO)"
        Write-Host ""
        Write-Host "Ejemplos:" -ForegroundColor Cyan
        Write-Host "  .\spygame.ps1 build      # Primera vez o despues de cambios"
        Write-Host "  .\spygame.ps1 start"
        Write-Host "  .\spygame.ps1 init"
        Write-Host "  .\spygame.ps1 check"
        Write-Host "  .\spygame.ps1 process 10"
        Write-Host "  .\spygame.ps1 list"
    }
}
