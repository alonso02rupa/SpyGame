from flask import Flask, render_template, request, jsonify, session
import json
import os
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'spygame_secret_key_2024'

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

# File to store game sessions
SESSIONS_FILE = 'game_sessions.json'

def load_sessions():
    """Load game sessions from file"""
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_session(person, hint, guess, correct, timestamp):
    """Save a game session to file"""
    sessions = load_sessions()
    session_data = {
        'person': person,
        'hint': hint,
        'guess': guess,
        'correct': correct,
        'timestamp': timestamp
    }
    sessions.append(session_data)
    
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f, indent=2)

@app.route('/')
def index():
    """Main game page"""
    return render_template('index.html')

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
    available_hints = [h for h in PERSONS_DATA[person] if h not in hints_used]
    
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

@app.route('/stats')
def stats():
    """View game statistics"""
    sessions = load_sessions()
    return render_template('stats.html', sessions=sessions)

if __name__ == '__main__':
    app.run(debug=True)