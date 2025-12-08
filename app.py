from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from datetime import datetime
import random
import uuid
import re
import logging
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_session import Session

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# URL prefix for the application (e.g., /spygame)
# This allows the app to be served from a subpath behind a reverse proxy
APPLICATION_PREFIX = os.getenv('APPLICATION_PREFIX', '/spygame')

# Configure Flask with the correct static URL path to match our prefix
app = Flask(__name__, static_url_path=f'{APPLICATION_PREFIX}/static')

# Configure app to work behind a reverse proxy (nginx)
# ProxyFix handles X-Forwarded headers
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=0)

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback_secret_key_change_in_production')

# Configure server-side sessions using MongoDB
app.config['SESSION_TYPE'] = 'mongodb'
app.config['SESSION_MONGODB'] = MongoClient(os.getenv('MONGODB_URI', 'mongodb://mongodb:27017/spygame'))
app.config['SESSION_MONGODB_DB'] = 'spygame'
app.config['SESSION_MONGODB_COLLECT'] = 'flask_sessions'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
app.config['SESSION_USE_SIGNER'] = True  # Sign session cookies for security
app.config['SESSION_KEY_PREFIX'] = 'spygame:'

# Initialize server-side session
Session(app)

# Configure session cookie to work properly
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# CSRF Protection
csrf = CSRFProtect(app)

# Rate Limiting - global limits: 200 requests per day, 50 per hour
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# MongoDB configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/spygame')

def get_db_collections():
    """Get MongoDB collections with error handling"""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.admin.command('ping')
        db = client.spygame
        return db.sessions, db.users, db.pistas, True
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        return None, None, None, False

def load_hints_from_json(filepath='pistas.json'):
    """
    Load hints from a JSON file into the database on startup.
    If the file doesn't exist or MongoDB is not available, the app starts normally.
    """
    if not os.path.exists(filepath):
        logger.info(f"No hints file found at {filepath}. Starting without loading hints.")
        return
    
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if not mongodb_available:
        logger.warning("MongoDB not available. Skipping hints loading from JSON.")
        return
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both list and dictionary formats
        if isinstance(data, list):
            personas = data
        elif isinstance(data, dict):
            personas = list(data.values())
        else:
            logger.warning(f"Unrecognized JSON format in {filepath}. Skipping hints loading.")
            return
        
        if not personas:
            logger.warning(f"No persons found in {filepath}. Skipping hints loading.")
            return
        
        loaded = 0
        
        for person_data in personas:
            nombre = person_data.get('nombre')
            if not nombre:
                continue
            
            if 'pistas' not in person_data or not person_data['pistas']:
                continue
            
            try:
                # Use upsert to insert or update in a single operation
                pistas_collection.update_one(
                    {"nombre": nombre},
                    {"$set": person_data},
                    upsert=True
                )
                loaded += 1
            except Exception as e:
                logger.error(f"Error loading person {nombre}: {e}")
        
        total = pistas_collection.count_documents({})
        logger.info(f"Hints loaded from {filepath}: {loaded} persons processed. Total in DB: {total}")
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file {filepath}: {e}")
    except Exception as e:
        logger.error(f"Error loading hints from {filepath}: {e}")

def get_person_from_db():
    """Get a random person from the database, prioritizing unplayed ones"""
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if mongodb_available and pistas_collection is not None:
        try:
            # Contar cuántas personas hay en la base de datos
            count = pistas_collection.count_documents({})
            
            if count > 0:
                # Obtener personajes ya jugados por este usuario
                username = get_current_user()
                query = {'username': username} if username != 'guest' else {'username': {'$exists': False}}
                
                played_persons = sessions_collection.distinct('person', query)
                played_persons_set = set(played_persons)
                
                # 90% de probabilidad de elegir un personaje no jugado
                use_unplayed = random.random() < 0.90
                
                if use_unplayed and len(played_persons_set) < count:
                    # Intentar seleccionar un personaje NO jugado
                    pipeline = [
                        {"$match": {"nombre": {"$nin": list(played_persons_set)}}},
                        {"$sample": {"size": 1}}
                    ]
                    result = list(pistas_collection.aggregate(pipeline))
                    
                    if result:
                        persona = result[0]
                        return {
                            'nombre': persona['nombre'],
                            'pistas': persona['pistas'],
                            'from_db': True
                        }
                
                # Fallback: seleccionar cualquier persona (incluyendo ya jugadas)
                pipeline = [{"$sample": {"size": 1}}]
                result = list(pistas_collection.aggregate(pipeline))
                
                if result:
                    persona = result[0]
                    return {
                        'nombre': persona['nombre'],
                        'pistas': persona['pistas'],
                        'from_db': True
                    }
            else:
                logger.info("No hay personas en la base de datos. Usando datos de fallback.")
        except Exception as e:
            logger.error(f"Error al obtener persona de MongoDB: {e}")
    
    # Fallback: usar pistas.json si existe
    pistas_file = 'pistas.json'
    if os.path.exists(pistas_file):
        try:
            with open(pistas_file, 'r', encoding='utf-8') as f:
                personas = json.load(f)
            
            # Pick a random person from the list
            if isinstance(personas, list) and len(personas) > 0:
                persona = random.choice(personas)
                return {
                    'nombre': persona.get('nombre', 'Unknown Person'),
                    'pistas': persona.get('pistas', []),
                    'from_db': False
                }
        except Exception as e:
            logger.error(f"Error al leer pistas.json: {e}")
    
    # Last resort fallback with minimal data
    return {
        'nombre': 'Unknown Person',
        'pistas': [
            {"dificultad": 5, "pista": "This is a test person"},
            {"dificultad": 4, "pista": "No database available"},
            {"dificultad": 3, "pista": "Please set up MongoDB"},
            {"dificultad": 2, "pista": "Or provide pistas.json"},
            {"dificultad": 1, "pista": "Check the documentation"}
        ],
        'from_db': False
    }

def get_person_by_name(name):
    """Get a specific person by name from the database"""
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if mongodb_available and pistas_collection is not None:
        try:
            persona = pistas_collection.find_one({'nombre': name})
            if persona:
                return {
                    'nombre': persona.get('nombre', name),
                    'pistas': persona.get('pistas', []),
                    'from_db': True
                }
        except Exception as e:
            logger.error(f"MongoDB error getting person {name}: {e}")
    
    # Fallback to pistas.json
    if os.path.exists('pistas.json'):
        try:
            with open('pistas.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                personas = data.get('personas', [])
                for persona in personas:
                    if persona.get('nombre') == name:
                        return {
                            'nombre': persona.get('nombre', name),
                            'pistas': persona.get('pistas', []),
                            'from_db': False
                        }
        except Exception as e:
            logger.error(f"Error al leer pistas.json: {e}")
    
    # Not found
    return None

# File to store game sessions (legacy - now using MongoDB)
SESSIONS_FILE = 'game_sessions.json'

def get_current_user():
    """Get the current user context (username or 'guest')"""
    return session.get('username', 'guest')

def load_sessions(username=None):
    """Load game sessions from MongoDB, optionally filtered by user"""
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if mongodb_available:
        try:
            if username is None:
                username = get_current_user()
            
            query = {'username': username} if username != 'guest' else {'username': {'$exists': False}}
            sessions = list(sessions_collection.find(query, {'_id': 0}))
            return sessions
        except Exception as e:
            logger.error(f"MongoDB error: {e}")
    
    # Fallback to JSON file if MongoDB is not available
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'r') as f:
            all_sessions = json.load(f)
            # Filter sessions for the user (legacy sessions don't have username)
            if username is None:
                username = get_current_user()
            if username == 'guest':
                return [s for s in all_sessions if 'username' not in s]
            else:
                return [s for s in all_sessions if s.get('username') == username]
    return []

def create_game_session(person, session_id, first_hint):
    """Create a new game session in MongoDB with first hint"""
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    username = get_current_user()
    session_data = {
        'session_id': session_id,
        'person': person,
        'pista': [first_hint],  # Array of hints requested
        'guesses': [],  # Array of user guesses (same length as pista when game ends)
        'acierto': False,  # Will be set to true only on correct guess
        'timestamp': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat()
    }
    
    # Add username for registered users
    if username != 'guest':
        session_data['username'] = username
    
    if mongodb_available:
        try:
            sessions_collection.insert_one(session_data)
            return
        except Exception as e:
            logger.error(f"MongoDB error: {e}")
    
    # Fallback to JSON file if MongoDB is not available
    sessions = []
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'r') as f:
            sessions = json.load(f)
    sessions.append(session_data)
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f, indent=2)

def update_game_session_hint(session_id, hint):
    """Update game session with a new hint (sets acierto to false)"""
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if mongodb_available:
        try:
            sessions_collection.update_one(
                {'session_id': session_id},
                {
                    '$push': {'pista': hint},
                    '$set': {
                        'acierto': False,
                        'last_updated': datetime.now().isoformat()
                    }
                }
            )
            return
        except Exception as e:
            logger.error(f"MongoDB error: {e}")
    
    # Fallback to JSON file if MongoDB is not available
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'r') as f:
            sessions = json.load(f)
        
        for sess in sessions:
            if sess.get('session_id') == session_id:
                sess['pista'].append(hint)
                sess['acierto'] = False
                sess['last_updated'] = datetime.now().isoformat()
                break
        
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)

def update_game_session_result(session_id, correct):
    """Update game session with guess result (sets acierto to true if correct)"""
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if mongodb_available:
        try:
            sessions_collection.update_one(
                {'session_id': session_id},
                {
                    '$set': {
                        'acierto': correct,
                        'last_updated': datetime.now().isoformat()
                    }
                }
            )
            return
        except Exception as e:
            logger.error(f"MongoDB error: {e}")
    
    # Fallback to JSON file if MongoDB is not available
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'r') as f:
            sessions = json.load(f)
        
        for sess in sessions:
            if sess.get('session_id') == session_id:
                sess['acierto'] = correct
                sess['last_updated'] = datetime.now().isoformat()
                break
        
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)

def add_guess_to_session(session_id, guess):
    """Add a guess to the game session"""
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if mongodb_available:
        try:
            sessions_collection.update_one(
                {'session_id': session_id},
                {
                    '$push': {'guesses': guess},
                    '$set': {'last_updated': datetime.now().isoformat()}
                }
            )
            return
        except Exception as e:
            logger.error(f"MongoDB error: {e}")
    
    # Fallback to JSON file if MongoDB is not available
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'r') as f:
            sessions = json.load(f)
        
        for sess in sessions:
            if sess.get('session_id') == session_id:
                if 'guesses' not in sess:
                    sess['guesses'] = []
                sess['guesses'].append(guess)
                sess['last_updated'] = datetime.now().isoformat()
                break
        
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)

def is_guess_correct(guess, person_name):
    """
    Check if a guess matches a person's name.
    Accepts full name or any individual part (first name, last name, etc.)
    Case-insensitive matching.
    
    Examples:
        - "Niels Bohr" matches: "niels bohr", "Niels", "bohr", "BOHR"
        - "Marie Curie" matches: "marie", "Curie", "marie curie"
    """
    # Normalize both strings: lowercase and strip whitespace
    guess_normalized = guess.lower().strip()
    person_normalized = person_name.lower().strip()
    
    # Check for exact match first (most common case)
    if guess_normalized == person_normalized:
        return True
    
    # Split person's name into parts (words)
    name_parts = person_normalized.split()
    
    # Check if guess matches any individual part of the name
    for part in name_parts:
        if guess_normalized == part:
            return True
    
    return False

# Input validation patterns for NoSQL injection prevention
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
# Special characters allowed in passwords (simplified and commonly accepted set)
PASSWORD_SPECIAL_CHARS = r'[!@#$%^&*()_+=\-]'

def validate_username(username):
    """
    Validate username to prevent NoSQL injection.
    Username must be alphanumeric and underscore only, 3-20 characters.
    Returns (is_valid, error_message)
    """
    if not username:
        return False, 'El nombre de usuario es necesario'
    if len(username) < 3:
        return False, 'El nombre de usuario debe tener al menos 3 caracteres'
    if len(username) > 20:
        return False, 'El nombre de usuario debe tener como máximo 20 caracteres'
    if not USERNAME_PATTERN.match(username):
        return False, 'El nombre de usuario solo puede contener letras, números y guiones bajos'
    return True, None

def validate_password(password):
    """
    Validate password strength.
    Password must be at least 12 characters with uppercase, lowercase, number, and special character.
    Returns (is_valid, error_message)
    """
    if not password:
        return False, 'La contraseña es necesaria'
    if len(password) < 12:
        return False, 'La contraseña debe tener al menos 12 caracteres'
    if not re.search(r'[A-Z]', password):
        return False, 'La contraseña debe contener al menos una letra mayúscula'
    if not re.search(r'[a-z]', password):
        return False, 'La contraseña debe contener al menos una letra minúscula'
    if not re.search(r'[0-9]', password):
        return False, 'La contraseña debe contener al menos un número'
    if not re.search(PASSWORD_SPECIAL_CHARS, password):
        return False, 'La contraseña debe contener al menos un carácter especial (!@#$%^&*()_+=-)'
    return True, None

@app.context_processor
def inject_csrf_token():
    """Inject CSRF token into all templates"""
    return dict(csrf_token=generate_csrf)

@app.route('/spygame/')
@app.route('/spygame')
def index():
    """Main game page"""
    current_user = get_current_user()
    return render_template('index.html', current_user=current_user)

@app.route('/spygame/register', methods=['POST'])
@limiter.limit("3 per minute")
@csrf.exempt  # Exempt because this endpoint uses JSON API with fetch
def register():
    """Register a new user"""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Datos de solicitud inválidos'})
    
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Usuario y contraseña son necesarios'})
    
    # Validate username (NoSQL injection prevention)
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        return jsonify({'status': 'error', 'message': error_msg})
    
    # Validate password strength
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return jsonify({'status': 'error', 'message': error_msg})
    
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if not mongodb_available:
        return jsonify({'status': 'error', 'message': 'El registro requiere conexión a la base de datos. Por favor, inténtalo más tarde o juega como invitado.'})
    
    try:
        # Check if user already exists (use validated username)
        if users_collection.find_one({'username': username}):
            return jsonify({'status': 'error', 'message': 'El nombre de usuario ya existe'})
        
        # Create new user
        hashed_password = generate_password_hash(password)
        user_data = {
            'username': username,
            'password': hashed_password,
            'created_at': datetime.now().isoformat()
        }
        
        users_collection.insert_one(user_data)
        session['username'] = username
        
        return jsonify({
            'status': 'success',
            'message': f'¡Bienvenido/a {username}! Te has registrado e iniciado sesión.'
        })
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'status': 'error', 'message': 'Error en el registro. Por favor, inténtalo de nuevo.'})

@app.route('/spygame/login', methods=['POST'])
@limiter.limit("5 per minute")
@csrf.exempt  # Exempt because this endpoint uses JSON API with fetch
def login():
    """Login an existing user"""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Datos de solicitud inválidos'})
    
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Usuario y contraseña son necesarios'})
    
    # Validate username format (NoSQL injection prevention)
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        return jsonify({'status': 'error', 'message': 'Usuario o contraseña incorrectos'})
    
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if not mongodb_available:
        return jsonify({'status': 'error', 'message': 'El inicio de sesión requiere conexión a la base de datos. Por favor, inténtalo más tarde o juega como invitado.'})
    
    try:
        user = users_collection.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return jsonify({
                'status': 'success',
                'message': f'¡Bienvenido/a de nuevo, {username}!'
            })
        else:
            return jsonify({'status': 'error', 'message': 'Usuario o contraseña incorrectos'})
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'status': 'error', 'message': 'Error al iniciar sesión. Por favor, inténtalo de nuevo.'})

@app.route('/spygame/logout', methods=['POST'])
@csrf.exempt  # Exempt because this endpoint uses JSON API with fetch
def logout():
    """Logout the current user"""
    username = session.get('username')
    session.pop('username', None)
    # Also clear game session when logging out
    session.pop('current_person', None)
    session.pop('hints_used', None)
    session.pop('game_start_time', None)
    session.pop('game_session_id', None)
    
    message = f'¡Hasta pronto, {username}!' if username else '¡Sesión cerrada correctamente!'
    return jsonify({
        'status': 'success',
        'message': message
    })

@app.route('/spygame/save_knowledge_profile', methods=['POST'])
@csrf.exempt  # Exempt because this endpoint uses JSON API with fetch
def save_knowledge_profile():
    """Save the optional knowledge profile survey for a user"""
    data = request.get_json()
    username = session.get('username')
    
    if not username or username == 'guest':
        return jsonify({'status': 'error', 'message': 'El perfil de conocimientos solo está disponible para usuarios registrados'})
    
    # Validate the survey data
    required_fields = [
        'cultura_general',
        'geografia',
        'actualidad_noticias',
        'cultura_popular',
        'tecnologia_tendencias',
        'uso_wikipedia',
        'habilidad_busqueda',
        'pensamiento_critico'
    ]
    
    profile_data = {}
    for field in required_fields:
        value = data.get(field)
        if value is None:
            return jsonify({'status': 'error', 'message': f'Campo faltante: {field}'})
        
        # Validate that value is between 1 and 5
        try:
            value_int = int(value)
            if value_int < 1 or value_int > 5:
                return jsonify({'status': 'error', 'message': f'Valor inválido para {field}. Debe estar entre 1 y 5.'})
            profile_data[field] = value_int
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': f'Valor inválido para {field}. Debe ser un número entre 1 y 5.'})
    
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if not mongodb_available:
        return jsonify({'status': 'error', 'message': 'Se requiere conexión a la base de datos para guardar el perfil.'})
    
    try:
        # Update user with knowledge profile and timestamp
        profile_data['profile_completed_at'] = datetime.now().isoformat()
        
        users_collection.update_one(
            {'username': username},
            {
                '$set': {
                    'knowledge_profile': profile_data
                }
            }
        )
        
        return jsonify({
            'status': 'success',
            'message': '¡Perfil de conocimientos guardado correctamente! Gracias por tu participación.'
        })
        
    except Exception as e:
        logger.error(f"Error saving knowledge profile: {e}")
        return jsonify({'status': 'error', 'message': 'Error al guardar el perfil de conocimientos. Por favor, inténtalo de nuevo.'})

@app.route('/spygame/check_knowledge_profile', methods=['GET'])
def check_knowledge_profile():
    """Check if the current user has completed the knowledge profile survey"""
    username = session.get('username')
    
    if not username or username == 'guest':
        return jsonify({'status': 'success', 'has_profile': False, 'is_guest': True})
    
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if not mongodb_available:
        return jsonify({'status': 'success', 'has_profile': False})
    
    try:
        user = users_collection.find_one({'username': username})
        has_profile = user and 'knowledge_profile' in user and user['knowledge_profile'] is not None
        
        return jsonify({
            'status': 'success',
            'has_profile': has_profile,
            'is_guest': False
        })
        
    except Exception as e:
        logger.error(f"Error checking knowledge profile: {e}")
        return jsonify({'status': 'error', 'message': 'Error al verificar el estado del perfil.'})

@app.route('/spygame/play_as_guest', methods=['POST'])
@csrf.exempt  # Exempt because this endpoint uses JSON API with fetch
def play_as_guest():
    """Start playing as guest"""
    session.pop('username', None)  # Remove any existing login
    return jsonify({
        'status': 'success',
        'message': 'Jugando como invitado. Tus partidas no se guardarán en tu perfil.'
    })

@app.route('/spygame/start_game', methods=['POST'])
@csrf.exempt  # Exempt because this endpoint uses JSON API with fetch
def start_game():
    """Start a new game by selecting a random person and providing first hint automatically"""
    persona_data = get_person_from_db()
    
    # Generate unique session ID for this game
    game_session_id = str(uuid.uuid4())
    
    # Store minimal data in session to avoid cookie size limits
    session['current_person'] = persona_data['nombre']
    # Don't store current_pistas - we'll fetch from DB when needed
    session['game_session_id'] = game_session_id
    session['game_start_time'] = datetime.now().isoformat()
    session.modified = True  # Explicitly mark session as modified
    
    # Ordenar pistas por dificultad (de mayor a menor)
    pistas_ordenadas = sorted(persona_data['pistas'], key=lambda x: x.get('dificultad', 0), reverse=True)
    
    # Get the first hint automatically
    if pistas_ordenadas:
        first_hint_obj = pistas_ordenadas[0]
        first_hint = first_hint_obj['pista']
        hints_used = [first_hint]
        session['hints_used'] = hints_used
        session.modified = True
        
        # Create game session with first hint
        create_game_session(
            person=persona_data['nombre'],
            session_id=game_session_id,
            first_hint=first_hint
        )
        
        # Calculate remaining hints
        hints_remaining = len(pistas_ordenadas) - 1
        
        return jsonify({
            'status': 'success',
            'message': f'¡Nueva partida iniciada! Aquí tienes tu primera pista:',
            'source': 'database' if persona_data['from_db'] else 'fallback',
            'first_hint': first_hint,
            'difficulty': first_hint_obj.get('dificultad', 0),
            'hints_remaining': hints_remaining
        })
    else:
        # No hints available (shouldn't happen but handle gracefully)
        session['hints_used'] = []
        session.modified = True
        return jsonify({
            'status': 'error',
            'message': 'Error: No hay pistas disponibles para este personaje.',
            'source': 'database' if persona_data['from_db'] else 'fallback'
        })

@app.route('/spygame/get_hint', methods=['POST'])
@csrf.exempt  # Exempt because this endpoint uses JSON API with fetch
def get_hint():
    """Get a hint for the current person"""
    if 'current_person' not in session:
        return jsonify({'status': 'error', 'message': 'No hay partida en curso. ¡Inicia una nueva partida primero!'})
    
    person = session['current_person']
    hints_used = session.get('hints_used', [])
    game_session_id = session.get('game_session_id')
    
    # Fetch pistas from database instead of session to avoid cookie size limits
    persona_data = get_person_by_name(person)
    if not persona_data:
        return jsonify({'status': 'error', 'message': 'Error: No se encontraron pistas para este personaje.'})
    
    pistas = persona_data.get('pistas', [])
    
    # Ordenar pistas por dificultad (de mayor a menor)
    pistas_ordenadas = sorted(pistas, key=lambda x: x.get('dificultad', 0), reverse=True)
    
    # Filtrar pistas que ya se usaron
    available_hints = [p for p in pistas_ordenadas if p['pista'] not in hints_used]
    
    if not available_hints:
        return jsonify({
            'status': 'success', 
            'hint': '',
            'message': '¡No quedan más pistas! Intenta adivinar.',
            'hints_remaining': 0
        })
    
    # Tomar la siguiente pista (la más difícil disponible)
    hint_obj = available_hints[0]
    hint = hint_obj['pista']
    hints_used.append(hint)
    session['hints_used'] = hints_used
    session.modified = True  # Explicitly mark session as modified
    
    # Update game session with new hint (sets acierto to false)
    if game_session_id:
        update_game_session_hint(game_session_id, hint)
        # Add empty string to guesses to maintain correspondence with hints
        add_guess_to_session(game_session_id, "")
    
    return jsonify({
        'status': 'success',
        'hint': hint,
        'difficulty': hint_obj.get('dificultad', 0),
        'hints_remaining': len(available_hints) - 1
    })

@app.route('/spygame/make_guess', methods=['POST'])
@limiter.limit("20 per minute")
@csrf.exempt  # Exempt because this endpoint uses JSON API with fetch
def make_guess():
    """Make a guess for the current person"""
    if 'current_person' not in session:
        return jsonify({'status': 'error', 'message': 'No hay partida en curso. ¡Inicia una nueva partida primero!'})
    
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Datos de solicitud inválidos'})
    
    guess = data.get('guess', '').strip()
    
    # --- CAMBIO 1: Si el guess está vacío, lo tratamos como pedir pista ---
    if not guess:
        return get_hint()
    # ---------------------------------------------------------------------
    
    person = session['current_person']
    game_session_id = session.get('game_session_id')
    hints_used = session.get('hints_used', [])
    correct = is_guess_correct(guess, person)
    
    # Fetch pistas from database instead of session
    persona_data = get_person_by_name(person)
    pistas = persona_data.get('pistas', []) if persona_data else []
    
    # Count hints used
    hints_count = len(hints_used)
    
    # Store the guess
    if game_session_id:
        add_guess_to_session(game_session_id, guess)
    
    # Get total attempts (including this one)
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    attempts_count = 1  # At least this guess
    
    if mongodb_available and game_session_id:
        try:
            session_data = sessions_collection.find_one({'session_id': game_session_id})
            if session_data and 'guesses' in session_data:
                # --- CAMBIO 2: Filtramos las pistas (strings vacíos) para contar solo intentos reales ---
                real_guesses = [g for g in session_data['guesses'] if g.strip()]
                attempts_count = len(real_guesses) + 1  # +1 for current guess
                # --------------------------------------------------------------------------------------
        except Exception as e:
            logger.error(f"Error counting attempts: {e}")
    
    if correct:
        # Correct guess - update session and end game
        if game_session_id:
            update_game_session_result(game_session_id, True)
        
        session.pop('current_person', None)
        session.pop('hints_used', None)
        session.pop('game_start_time', None)
        session.pop('game_session_id', None)
        session.pop('current_pistas', None)
        
        return jsonify({
            'status': 'success',
            'correct': True,
            'person': person,
            'hints_count': hints_count,
            'attempts_count': attempts_count - 1,
            'message': f'¡Felicidades! Has acertado. Era {person}.'
        })
    else:
        # Wrong guess - give another hint automatically
        # Sort hints by difficulty (highest to lowest)
        pistas_ordenadas = sorted(pistas, key=lambda x: x.get('dificultad', 0), reverse=True)
        
        # Find available hints (not yet used)
        available_hints = [p for p in pistas_ordenadas if p['pista'] not in hints_used]
        
        if available_hints:
            # Give next hint automatically
            hint_obj = available_hints[0]
            hint = hint_obj['pista']
            hints_used.append(hint)
            session['hints_used'] = hints_used
            session.modified = True  # Explicitly mark as modified
            
            # Update session with new hint
            if game_session_id:
                update_game_session_hint(game_session_id, hint)
            
            hints_remaining = len(available_hints) - 1
            
            return jsonify({
                'status': 'success',
                'correct': False,
                'message': f'¡Incorrecto! Aquí tienes otra pista para ayudarte.',
                'new_hint': hint,
                'difficulty': hint_obj.get('dificultad', 0),
                'hints_remaining': hints_remaining
            })
        else:
            # No more hints available
            if game_session_id:
                update_game_session_result(game_session_id, False)
            
            return jsonify({
                'status': 'success',
                'correct': False,
                'message': f'¡Incorrecto! No quedan más pistas. Inténtalo de nuevo o revela la respuesta.',
                'hints_remaining': 0
            })

@app.route('/spygame/get_answer', methods=['POST'])
@csrf.exempt  # Exempt because this endpoint uses JSON API with fetch
def get_answer():
    """Reveal the answer and end the game"""
    if 'current_person' not in session:
        return jsonify({'status': 'error', 'message': 'No hay partida en curso.'})
    
    person = session['current_person']
    game_session_id = session.get('game_session_id')
    hints_used = session.get('hints_used', [])
    
    # Count hints and attempts
    hints_count = len(hints_used)
    
    # Get total attempts
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    attempts_count = 0
    
    if mongodb_available and game_session_id:
        try:
            session_data = sessions_collection.find_one({'session_id': game_session_id})
            if session_data and 'guesses' in session_data:
                # --- CAMBIO: Filtramos las pistas (strings vacíos) ---
                real_guesses = [g for g in session_data['guesses'] if g.strip()]
                attempts_count = len(real_guesses)
                # -----------------------------------------------------
        except Exception as e:
            logger.error(f"Error counting attempts: {e}")
    
    # Mark session as not successful (revealed answer)
    if game_session_id:
        update_game_session_result(game_session_id, False)
    
    session.pop('current_person', None)
    session.pop('hints_used', None)
    session.pop('game_start_time', None)
    session.pop('game_session_id', None)
    session.pop('current_pistas', None)
    
    return jsonify({
        'status': 'success',
        'answer': person,
        'hints_count': hints_count,
        'attempts_count': attempts_count - 1,
        'message': f'La respuesta era {person}. ¡Mejor suerte la próxima vez!'
    })

@app.route('/spygame/stats')
def stats():
    """View game statistics"""
    sessions = load_sessions()
    current_user = get_current_user()
    return render_template('stats.html', sessions=sessions, current_user=current_user)

if __name__ == '__main__':
    # Load hints from pistas.json into the database on startup
    load_hints_from_json()
    
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 'yes']
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(debug=debug_mode, host=host, port=port)