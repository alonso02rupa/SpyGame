from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from datetime import datetime
import random
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

def get_person_from_db():
    """Get a random person from the database"""
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    
    if mongodb_available and pistas_collection is not None:
        try:
            # Contar cuántas personas hay en la base de datos
            count = pistas_collection.count_documents({})
            
            if count > 0:
                # Seleccionar una persona aleatoria usando aggregation
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
    
    
    # Convertir al formato de la base de datos para compatibilidad
    pistas_formateadas = [{"dificultad": 5 - i//2, "pista": hint} for i, hint in enumerate(hints)]
    
    return {
        'nombre': person_name,
        'pistas': pistas_formateadas,
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

def save_session(person, hint, guess, correct, timestamp):
    """Save a game session to MongoDB"""
    sessions_collection, users_collection, pistas_collection, mongodb_available = get_db_collections()
    username = get_current_user()
    session_data = {
        'person': person,
        'hint': hint,
        'guess': guess,
        'correct': correct,
        'timestamp': timestamp
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

@app.route('/')
def index():
    """Main game page"""
    return render_template('index.html')

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
    
    message = f'Goodbye, {username}!' if username else 'Logged out successfully!'
    return jsonify({
        'status': 'success',
        'message': message
    })

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
    """Start a new game by selecting a random person"""
    persona_data = get_person_from_db()
    
    session['current_person'] = persona_data['nombre']
    session['current_pistas'] = persona_data['pistas']
    session['hints_used'] = []
    session['game_start_time'] = datetime.now().isoformat()
    
    return jsonify({
        'status': 'success',
        'message': f'New game started! Try to guess who I am by asking for hints.',
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
    
    # Ordenar pistas por dificultad (de mayor a menor)
    pistas_ordenadas = sorted(pistas, key=lambda x: x.get('dificultad', 0), reverse=True)
    
    # Filtrar pistas que ya se usaron
    available_hints = [p for p in pistas_ordenadas if p['pista'] not in hints_used]
    
    if not available_hints:
        return jsonify({
            'status': 'error', 
            'message': 'No more hints available! Try to make a guess.'
        })
    
    # Tomar la siguiente pista (la más difícil disponible)
    hint_obj = available_hints[0]
    hint = hint_obj['pista']
    hints_used.append(hint)
    session['hints_used'] = hints_used
    
    # Save hint request to sessions
    save_session(
        person=person,
        hint=hint,
        guess='',
        correct=None,
        timestamp=datetime.now().isoformat()
    )
    
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
    correct = guess.lower() == person.lower()
    
    # Save guess to sessions
    save_session(
        person=person,
        hint='',
        guess=guess,
        correct=correct,
        timestamp=datetime.now().isoformat()
    )
    
    if correct:
        session.pop('current_person', None)
        session.pop('hints_used', None)
        session.pop('game_start_time', None)
        return jsonify({
            'status': 'success',
            'correct': True,
            'message': f'Congratulations! You guessed correctly. It was {person}!'
        })
    else:
        return jsonify({
            'status': 'success',
            'correct': False,
            'message': f'Wrong guess! Try asking for more hints.'
        })

@app.route('/get_answer', methods=['POST'])
def get_answer():
    """Reveal the answer and end the game"""
    if 'current_person' not in session:
        return jsonify({'status': 'error', 'message': 'No game in progress.'})
    
    person = session['current_person']
    session.pop('current_person', None)
    session.pop('hints_used', None)
    session.pop('game_start_time', None)
    
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
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 'yes']
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(debug=debug_mode, host=host, port=port)