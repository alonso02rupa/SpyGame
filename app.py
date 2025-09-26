from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from datetime import datetime
import random
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'spygame_secret_key_2024'

# MongoDB configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/spygame')

def get_db_collections():
    """Get MongoDB collections with error handling"""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.admin.command('ping')
        db = client.spygame
        return db.sessions, db.users, True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return None, None, False

# Sample Wikipedia persons data (in a real app, this would come from Wikipedia API)
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

# Game configuration
MAX_HINTS = 5  # Maximum number of hints allowed per game

def get_current_user():
    """Get the current user context (username or 'guest')"""
    return session.get('username', 'guest')

def load_sessions(username=None):
    """Load game sessions from MongoDB, optionally filtered by user"""
    sessions_collection, users_collection, mongodb_available = get_db_collections()
    
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
        try:
            with open(SESSIONS_FILE, 'r') as f:
                content = f.read().strip()
                if content:  # Only try to parse if file is not empty
                    all_sessions = json.loads(content)
                else:
                    all_sessions = []
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading sessions file: {e}")
            all_sessions = []
            
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
    sessions_collection, users_collection, mongodb_available = get_db_collections()
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
        try:
            with open(SESSIONS_FILE, 'r') as f:
                content = f.read().strip()
                if content:  # Only try to parse if file is not empty
                    sessions = json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading sessions file: {e}")
            sessions = []
    
    sessions.append(session_data)
    
    try:
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)
    except IOError as e:
        print(f"Error writing sessions file: {e}")

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
    
    sessions_collection, users_collection, mongodb_available = get_db_collections()
    
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
    
    sessions_collection, users_collection, mongodb_available = get_db_collections()
    
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
    person = random.choice(list(PERSONS_DATA.keys()))
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
    
    # Check if maximum hints reached BEFORE giving another hint
    if len(hints_used) >= MAX_HINTS:
        # Game over - save as loss and end game
        save_session(
            person=person,
            hint='',
            guess=None,  # null for loss due to hint limit
            correct=False,
            timestamp=datetime.now().isoformat()
        )
        
        # Clear game session
        session.pop('current_person', None)
        session.pop('hints_used', None)
        session.pop('game_start_time', None)
        
        return jsonify({
            'status': 'game_over', 
            'message': f'Game over! You\'ve used all {MAX_HINTS} hints. The answer was {person}. Better luck next time!',
            'answer': person
        })
    
    available_hints = [h for h in PERSONS_DATA[person] if h not in hints_used]
    
    if not available_hints:
        # No more unique hints available, but we haven't reached the MAX_HINTS limit
        # This shouldn't happen with our current data, but handle it gracefully
        return jsonify({
            'status': 'error', 
            'message': 'No more unique hints available! Try to make a guess.'
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
    
    # Calculate remaining hints based on MAX_HINTS limit
    hints_remaining = MAX_HINTS - len(hints_used)
    
    # Check if this was the last hint allowed
    if hints_remaining == 0:
        return jsonify({
            'status': 'success',
            'hint': hint,
            'hints_remaining': hints_remaining,
            'last_hint': True
        })
    
    return jsonify({
        'status': 'success',
        'hint': hint,
        'hints_remaining': hints_remaining
    })

@app.route('/make_guess', methods=['POST'])
def make_guess():
    """Make a guess for the current person"""
    if 'current_person' not in session:
        return jsonify({'status': 'error', 'message': 'No game in progress. Start a new game first!'})
    
    guess = request.json.get('guess', '').strip()
    person = session['current_person']
    
    # Handle empty guess - save as null but don't process as error
    if not guess:
        save_session(
            person=person,
            hint='',
            guess=None,  # Save empty guess as null
            correct=False,
            timestamp=datetime.now().isoformat()
        )
        return jsonify({'status': 'error', 'message': 'Please enter a guess!'})
    
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

@app.route('/check_game_status', methods=['POST'])
def check_game_status():
    """Check if game should end due to hint limit"""
    if 'current_person' not in session:
        return jsonify({'status': 'no_game'})
    
    hints_used = session.get('hints_used', [])
    
    # If player has used all 5 hints and tries to interact, end the game
    if len(hints_used) >= MAX_HINTS:
        person = session['current_person']
        
        # Save as loss
        save_session(
            person=person,
            hint='',
            guess=None,  # null for loss due to hint limit
            correct=False,
            timestamp=datetime.now().isoformat()
        )
        
        # Clear game session
        session.pop('current_person', None)
        session.pop('hints_used', None)
        session.pop('game_start_time', None)
        
        return jsonify({
            'status': 'game_over',
            'message': f'Game over! You\'ve used all {MAX_HINTS} hints without guessing. The answer was {person}.',
            'answer': person
        })
    
    return jsonify({
        'status': 'active',
        'hints_used': len(hints_used),
        'hints_remaining': MAX_HINTS - len(hints_used)
    })

@app.route('/get_answer', methods=['POST'])
def get_answer():
    """Reveal the answer and end the game"""
    if 'current_person' not in session:
        return jsonify({'status': 'error', 'message': 'No game in progress.'})
    
    person = session['current_person']
    
    # Save as loss when revealing answer
    save_session(
        person=person,
        hint='',
        guess=None,  # null for giving up
        correct=False,
        timestamp=datetime.now().isoformat()
    )
    
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
    app.run(debug=True, host='0.0.0.0', port=5000)