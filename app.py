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
        return db.sessions, db.users, db.hints, True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return None, None, None, False

# Sample Wikipedia persons data (this will be changed for a DB call in which the person will be stored)
PERSONS_DATA = {
    "Albert Einstein": [
        "I was born in Germany in 1879",
        "I developed the theory of relativity", 
        "I won the Nobel Prize in Physics in 1921",
        "My most famous equation is E=mc²",
        "I had wild, unkempt hair"
    ],
    "Marie Curie": [
        "I was the first woman to win a Nobel Prize",
        "I discovered the elements polonium and radium",
        "I won Nobel Prizes in both Physics and Chemistry",
        "I was born in Poland but worked in France",
        "I died from radiation exposure"
    ],
    "Leonardo da Vinci": [
        "I lived during the Renaissance period",
        "I painted the Mona Lisa",
        "I designed flying machines centuries before they were built",
        "I was both an artist and an inventor",
        "I studied human anatomy by dissecting corpses"
    ],
    "William Shakespeare": [
        "I wrote Romeo and Juliet",
        "I lived in England during the 16th and 17th centuries",
        "I wrote approximately 39 plays",
        "I invented many words that are still used today",
        "I married Anne Hathaway"
    ],
    "Cleopatra": [
        "I was the last pharaoh of Egypt",
        "I spoke nine languages fluently",
        "I had relationships with Julius Caesar and Mark Antony",
        "I ruled Egypt for nearly three decades",
        "I died by snake bite"
    ]
}

# File to store game sessions (legacy - now using MongoDB)
SESSIONS_FILE = 'game_sessions.json'

def get_all_persons_from_db():
    """Get all available persons from the hints collection"""
    sessions_collection, users_collection, hints_collection, mongodb_available = get_db_collections()
    
    if not mongodb_available:
        # Fallback to hardcoded data if DB is not available
        return list(PERSONS_DATA.keys())
    
    try:
        # Get all unique person names from hints collection
        persons = hints_collection.distinct("nombre")
        return persons if persons else list(PERSONS_DATA.keys())
    except Exception as e:
        print(f"Error loading persons from DB: {e}")
        return list(PERSONS_DATA.keys())

def get_hints_for_person(person_name):
    """Get hints for a specific person from the hints collection"""
    sessions_collection, users_collection, hints_collection, mongodb_available = get_db_collections()
    
    if not mongodb_available:
        # Fallback to hardcoded data if DB is not available
        return PERSONS_DATA.get(person_name, [])
    
    try:
        # Find the person's hints document
        person_doc = hints_collection.find_one({"nombre": person_name})
        
        if person_doc and "pistas" in person_doc:
            # Extract hints from the pistas array
            pistas = person_doc["pistas"]
            # If pistas is a list of dicts with 'pista' field, extract them
            if isinstance(pistas, list) and len(pistas) > 0:
                if isinstance(pistas[0], dict) and 'pista' in pistas[0]:
                    return [p['pista'] for p in pistas]
                else:
                    return pistas
            return []
        else:
            # Fallback to hardcoded data
            return PERSONS_DATA.get(person_name, [])
    except Exception as e:
        print(f"Error loading hints for {person_name}: {e}")
        return PERSONS_DATA.get(person_name, [])

def get_current_user():
    """Get the current user context (username or 'guest')"""
    return session.get('username', 'guest')

def load_sessions(username=None):
    """Load game sessions from MongoDB, optionally filtered by user"""
    sessions_collection, users_collection, hints_collection, mongodb_available = get_db_collections()
    
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
    sessions_collection, users_collection, hints_collection, mongodb_available = get_db_collections()
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
    
    sessions_collection, users_collection, hints_collection, mongodb_available = get_db_collections()
    
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
    
    sessions_collection, users_collection, hints_collection, mongodb_available = get_db_collections()
    
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
    # Get available persons from database or fallback to hardcoded data
    available_persons = get_all_persons_from_db()
    
    if not available_persons:
        return jsonify({
            'status': 'error',
            'message': 'No persons available for the game. Please add some hints first.'
        })
    
    person = random.choice(available_persons)
    session['current_person'] = person
    session['hints_used'] = []
    session['game_start_time'] = datetime.now().isoformat()
    
    return jsonify({
        'status': 'success',
        'message': f'New game started! Try to guess who I am by asking for hints.'
    })

@app.route('/get_hint', methods=['POST'])
def get_hint():
    """Get a hint for the current person"""
    if 'current_person' not in session:
        return jsonify({'status': 'error', 'message': 'No game in progress. Start a new game first!'})
    
    person = session['current_person']
    hints_used = session.get('hints_used', [])
    
    # Get hints from database
    all_hints = get_hints_for_person(person)
    available_hints = [h for h in all_hints if h not in hints_used]
    
    if not available_hints:
        return jsonify({
            'status': 'error', 
            'message': 'No more hints available! Try to make a guess.'
        })
    
    hint = random.choice(available_hints)
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

@app.route('/generate_hints', methods=['POST'])
def generate_hints():
    """Generate hints for a person from Wikipedia and save to database"""
    data = request.get_json()
    url = data.get('url', '').strip()
    wikidata_id = data.get('wikidata_id', None)
    
    if not url:
        return jsonify({'status': 'error', 'message': 'Wikipedia URL is required'})
    
    # Import the data processor module
    try:
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), 'datatreatment'))
        from data_processor import procesar_persona
        
        # Process the person (generate hints and save to DB)
        pistas = procesar_persona(url, wikidata_id=wikidata_id, guardar_json=False, subir_db=True)
        
        # Extract person name from URL
        nombre_persona = url.split("/wiki/")[-1].replace("_", " ")
        
        return jsonify({
            'status': 'success',
            'message': f'Hints generated and saved for {nombre_persona}',
            'person': nombre_persona,
            'hints_count': len(pistas) if isinstance(pistas, list) else 0
        })
    except Exception as e:
        print(f"Error generating hints: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to generate hints: {str(e)}'
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