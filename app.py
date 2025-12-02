from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from datetime import datetime
import random
import uuid
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback_secret_key_change_in_production')

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
        print(f"MongoDB connection failed: {e}")
        return None, None, None, False

def load_hints_from_json(filepath='pistas.json'):
    """
    Load hints from a JSON file into the database on startup.
    If the file doesn't exist or MongoDB is not available, the app starts normally.
    """
    if not os.path.exists(filepath):
        print(f"No hints file found at {filepath}. Starting without loading hints.")
        return
    
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if not mongodb_available:
        print("MongoDB not available. Skipping hints loading from JSON.")
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
            print(f"Unrecognized JSON format in {filepath}. Skipping hints loading.")
            return
        
        if not personas:
            print(f"No persons found in {filepath}. Skipping hints loading.")
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
                print(f"Error loading person {nombre}: {e}")
        
        total = pistas_collection.count_documents({})
        print(f"Hints loaded from {filepath}: {loaded} persons processed. Total in DB: {total}")
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file {filepath}: {e}")
    except Exception as e:
        print(f"Error loading hints from {filepath}: {e}")

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
                print("No hay personas en la base de datos. Usando datos de fallback.")
        except Exception as e:
            print(f"Error al obtener persona de MongoDB: {e}")
    
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
            print(f"Error al leer pistas.json: {e}")
    
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
            print(f"MongoDB error: {e}")
    
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
            print(f"MongoDB error: {e}")
    
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
            print(f"MongoDB error: {e}")
    
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
            print(f"MongoDB error: {e}")
    
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
            print(f"MongoDB error: {e}")
    
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

@app.route('/')
def index():
    """Main game page"""
    current_user = get_current_user()
    return render_template('index.html', current_user=current_user)

@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Username and password are required'})
    
    if len(username) < 3:
        return jsonify({'status': 'error', 'message': 'Username must be at least 3 characters long'})
    
    if len(password) < 6:
        return jsonify({'status': 'error', 'message': 'Password must be at least 6 characters long'})
    
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if not mongodb_available:
        return jsonify({'status': 'error', 'message': 'User registration requires database connection. Please try again later or play as guest.'})
    
    try:
        # Check if user already exists
        if users_collection.find_one({'username': username}):
            return jsonify({'status': 'error', 'message': 'Username already exists'})
        
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
            'message': f'Welcome {username}! You have been registered and logged in.'
        })
        
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'status': 'error', 'message': 'Registration failed. Please try again.'})

@app.route('/login', methods=['POST'])
def login():
    """Login an existing user"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Username and password are required'})
    
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if not mongodb_available:
        return jsonify({'status': 'error', 'message': 'User login requires database connection. Please try again later or play as guest.'})
    
    try:
        user = users_collection.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return jsonify({
                'status': 'success',
                'message': f'Welcome back, {username}!'
            })
        else:
            return jsonify({'status': 'error', 'message': 'Invalid username or password'})
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'status': 'error', 'message': 'Login failed. Please try again.'})

@app.route('/logout', methods=['POST'])
def logout():
    """Logout the current user"""
    username = session.get('username')
    session.pop('username', None)
    # Also clear game session when logging out
    session.pop('current_person', None)
    session.pop('hints_used', None)
    session.pop('game_start_time', None)
    session.pop('game_session_id', None)
    
    message = f'Goodbye, {username}!' if username else 'Logged out successfully!'
    return jsonify({
        'status': 'success',
        'message': message
    })

@app.route('/save_knowledge_profile', methods=['POST'])
def save_knowledge_profile():
    """Save the optional knowledge profile survey for a user"""
    data = request.get_json()
    username = session.get('username')
    
    if not username or username == 'guest':
        return jsonify({'status': 'error', 'message': 'Knowledge profile is only available for registered users'})
    
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
            return jsonify({'status': 'error', 'message': f'Missing field: {field}'})
        
        # Validate that value is between 1 and 5
        try:
            value_int = int(value)
            if value_int < 1 or value_int > 5:
                return jsonify({'status': 'error', 'message': f'Invalid value for {field}. Must be between 1 and 5.'})
            profile_data[field] = value_int
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': f'Invalid value for {field}. Must be a number between 1 and 5.'})
    
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if not mongodb_available:
        return jsonify({'status': 'error', 'message': 'Database connection required to save profile.'})
    
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
            'message': 'Knowledge profile saved successfully. Thank you for your participation!'
        })
        
    except Exception as e:
        print(f"Error saving knowledge profile: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to save knowledge profile. Please try again.'})

@app.route('/check_knowledge_profile', methods=['GET'])
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
        print(f"Error checking knowledge profile: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to check profile status.'})

@app.route('/play_as_guest', methods=['POST'])
def play_as_guest():
    """Start playing as guest"""
    session.pop('username', None)  # Remove any existing login
    return jsonify({
        'status': 'success',
        'message': 'Playing as guest. Your games will not be saved to your profile.'
    })

@app.route('/start_game', methods=['POST'])
def start_game():
    """Start a new game by selecting a random person and providing first hint automatically"""
    persona_data = get_person_from_db()
    
    # Generate unique session ID for this game
    game_session_id = str(uuid.uuid4())
    
    session['current_person'] = persona_data['nombre']
    session['current_pistas'] = persona_data['pistas']
    session['game_session_id'] = game_session_id
    session['game_start_time'] = datetime.now().isoformat()
    
    # Ordenar pistas por dificultad (de mayor a menor)
    pistas_ordenadas = sorted(persona_data['pistas'], key=lambda x: x.get('dificultad', 0), reverse=True)
    
    # Get the first hint automatically
    if pistas_ordenadas:
        first_hint_obj = pistas_ordenadas[0]
        first_hint = first_hint_obj['pista']
        hints_used = [first_hint]
        session['hints_used'] = hints_used
        
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
            'message': f'New game started! Here is your first hint:',
            'source': 'database' if persona_data['from_db'] else 'fallback',
            'first_hint': first_hint,
            'difficulty': first_hint_obj.get('dificultad', 0),
            'hints_remaining': hints_remaining
        })
    else:
        # No hints available (shouldn't happen but handle gracefully)
        session['hints_used'] = []
        return jsonify({
            'status': 'error',
            'message': 'Error: No hints available for this person.',
            'source': 'database' if persona_data['from_db'] else 'fallback'
        })

@app.route('/get_hint', methods=['POST'])
def get_hint():
    """Get a hint for the current person"""
    if 'current_person' not in session:
        return jsonify({'status': 'error', 'message': 'No game in progress. Start a new game first!'})
    
    person = session['current_person']
    pistas = session.get('current_pistas', [])
    hints_used = session.get('hints_used', [])
    game_session_id = session.get('game_session_id')
    
    # Ordenar pistas por dificultad (de mayor a menor)
    pistas_ordenadas = sorted(pistas, key=lambda x: x.get('dificultad', 0), reverse=True)
    
    # Filtrar pistas que ya se usaron
    available_hints = [p for p in pistas_ordenadas if p['pista'] not in hints_used]
    
    if not available_hints:
        return jsonify({
            'status': 'success', 
            'hint': '',
            'message': 'No more hints available! Try to make a guess.',
            'hints_remaining': 0
        })
    
    # Tomar la siguiente pista (la más difícil disponible)
    hint_obj = available_hints[0]
    hint = hint_obj['pista']
    hints_used.append(hint)
    session['hints_used'] = hints_used
    
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

@app.route('/make_guess', methods=['POST'])
def make_guess():
    """Make a guess for the current person"""
    if 'current_person' not in session:
        return jsonify({'status': 'error', 'message': 'No game in progress. Start a new game first!'})
    
    guess = request.json.get('guess', '').strip()
    if not guess:
        return jsonify({'status': 'error', 'message': 'Please enter a guess!'})
    
    person = session['current_person']
    game_session_id = session.get('game_session_id')
    pistas = session.get('current_pistas', [])
    hints_used = session.get('hints_used', [])
    correct = is_guess_correct(guess, person)
    
    # Store the guess
    if game_session_id:
        add_guess_to_session(game_session_id, guess)
    
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
            'message': f'Congratulations! You guessed correctly. It was {person}!'
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
            
            # Update session with new hint
            if game_session_id:
                update_game_session_hint(game_session_id, hint)
            
            hints_remaining = len(available_hints) - 1
            
            return jsonify({
                'status': 'success',
                'correct': False,
                'message': f'Wrong guess! Here is another hint to help you.',
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
                'message': f'Wrong guess! No more hints available. Try again or reveal the answer.',
                'hints_remaining': 0
            })

@app.route('/get_answer', methods=['POST'])
def get_answer():
    """Reveal the answer and end the game"""
    if 'current_person' not in session:
        return jsonify({'status': 'error', 'message': 'No game in progress.'})
    
    person = session['current_person']
    game_session_id = session.get('game_session_id')
    
    # Mark session as not successful (revealed answer)
    if game_session_id:
        update_game_session_result(game_session_id, False)
    
    session.pop('current_person', None)
    session.pop('hints_used', None)
    session.pop('game_start_time', None)
    session.pop('game_session_id', None)
    
    return jsonify({
        'status': 'success',
        'answer': person,
        'message': f'The answer was {person}. Better luck next time!'
    })

@app.route('/stats')
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