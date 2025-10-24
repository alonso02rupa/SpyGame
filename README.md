#  SpyGame

A dark purple/noir-themed web-based guessing game where players try to identify famous people based on automatically generated and difficulty progressive hints. Built with Flask, MongoDB, and AI-powered hint generation featuring a sleek, spy-movie inspired interface.

## 🎮 Game Overview

SpyGame challenges players to guess famous Wikipedia personalities using an AI-powered hint system. Players can request hints per game, with each hint progressively revealing more information. The game uses machine learning to generate contextual and difficulty-graded hints from Wikipedia biographies.

**New Features:**
- 🤖 AI-generated hints using Hugging Face models
- 🗄️ MongoDB database for scalable data storage
- 🌐 Automatic Wikipedia data processing
- 📊 Advanced statistics tracking
- 👤 User authentication system
- 🐳 Full Docker containerization

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Hugging Face API key (for generating new hints)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/alonso02rupa/SpyGame.git
   cd SpyGame
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database with an example**
   ```bash
   docker-compose exec web python init_db.py
   ```

5. **Open your browser**
   ```
   http://localhost:5000
   ```

**Using helper scripts (recommended):**

Windows (PowerShell):
```powershell
.\spygame.ps1 start
.\spygame.ps1 init
```

Linux/Mac:
```bash
chmod +x spygame.sh
./spygame.sh start
./spygame.sh init
```

## 📚 Documentation

- **[USAGE.md](USAGE.md)** - Complete usage guide and Docker commands
- **[.env.example](.env.example)** - Environment variables template

## 🗄️ Database Management

### Adding People to the Database

The application can automatically process Wikipedia articles and generate AI-powered hints:

```bash
# Process 5 people from Wikipedia
docker-compose exec web python process_data.py --num 5

# Process 10 people with custom parameters
docker-compose exec web python process_data.py --num 10 --min-sitelinks 200

# List all people in the database
docker-compose exec web python init_db.py --list
```

**Using helper scripts:**

Windows:
```powershell
.\spygame.ps1 process 10
.\spygame.ps1 list
```

Linux/Mac:
```bash
./spygame.sh process 10
./spygame.sh list
```

### 🧠 DIRT System - Language Diversification

The project includes a **DIRT (Discovery of Inference Rules from Text)** system that learns semantic equivalences between verbs to diversify the language used in hint generation.

**Building the DIRT model:**

```bash
# Generate inference model from biographies
python dirt_builder.py
```

This creates `modelo_inferencias.json` with learned verb equivalences (e.g., "fundó" ≈ "estableció").

**Testing the system:**

```bash
# Run interactive test
python test_dirt.py
```

**How it works:**
1. Extracts subject-verb-object triples from biographical texts using spaCy
2. Calculates verb similarities based on shared contexts
3. Generates equivalence pairs with confidence scores
4. Automatically applies reformulations during hint generation

The system integrates seamlessly - hints are automatically diversified when `modelo_inferencias.json` exists. See **[DIRT_README.md](DIRT_README.md)** for detailed documentation.

**Benefits:**
- ✨ Increases language variety in generated hints
- 🔄 Reduces repetitive phrasing
- 📚 Learns from your own corpus of biographies
- 🎯 Improves hint quality and player experience

## 🔧 Environment Configuration

The application requires environment variables for configuration:

### Required Variables

```bash
# Flask Configuration
FLASK_SECRET_KEY=your_unique_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# MongoDB Configuration
MONGODB_URI=mongodb://mongodb:27017/spygame
MONGO_INITDB_DATABASE=spygame
MONGODB_PORT=27017

# Hugging Face API (Required for processing new people)
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
HUGGINGFACE_MODEL_NAME=meta-llama/Meta-Llama-3-8B-Instruct

# Wikipedia API Configuration
WIKIPEDIA_USER_AGENT=SpyGame/1.0.0 (contact: your_email@example.com)

# Docker Ports
DOCKER_WEB_PORT=5000
DOCKER_MONGO_PORT=27017
```

### Security Notes
- ⚠️ **Never commit your `.env` file** to version control
- Use strong, unique values for `FLASK_SECRET_KEY` in production
- Get your Hugging Face API key from: https://huggingface.co/settings/tokens
- Replace the contact email in `WIKIPEDIA_USER_AGENT` with your actual email

## 🎯 How to Play

### Starting a Game
1. Click **"Start New Game"** on the main page
2. The system randomly selects a person from the database
3. The hints and guess sections become available

### Getting Hints
1. Click **"Get Hint"** to receive a clue
2. Hints are ordered by difficulty (hardest to easiest)
3. Each hint has a difficulty rating (1-5)
4. The counter shows remaining hints

### Making Guesses
1. Type your guess in the input field
2. Click **"Submit Guess"** or press Enter
3. Get immediate feedback on correctness
4. You can make multiple guesses per game

### User Accounts
- **Guest Mode**: Play without registration (no stats saved to profile)
- **Register**: Create an account to track your personal statistics
- **Login**: Access your game history and stats

## 📊 Statistics & Tracking

The game automatically tracks all gameplay activities:

### Summary Statistics
- **Total Games**: Number of games started
- **Correct Guesses**: Successfully identified people
- **Success Rate**: Percentage of correct guesses
- **Per-User Stats**: When logged in, see your personal performance

### Detailed History
- **Timestamp**: When each action occurred
- **Person**: Which figure was being guessed
- **Action**: Hint request or guess attempt
- **Details**: Actual hint text or guess content
- **Result**: Correctness of guesses

## 🏗️ Technical Architecture

### Backend Stack
- **Flask**: Web framework and API
- **MongoDB**: Primary database (PyMongo driver)
- **Python-dotenv**: Environment configuration
- **Werkzeug**: Password hashing and security

### AI & Data Processing
- **Hugging Face**: LLM for hint generation
- **spaCy**: NLP for text processing
- **DIRT System**: Discovery of Inference Rules from Text for language diversification
- **Wikipedia API**: Biography data source
- **Pandas**: Data manipulation
- **Wikidata SPARQL**: Person discovery

### Frontend
- **Vanilla JavaScript**: Dynamic interactions
- **CSS Grid/Flexbox**: Responsive layout
- **Dark theme**: Spy-movie aesthetic

### Deployment
- **Docker**: Application containerization
- **Docker Compose**: Multi-container orchestration
- **MongoDB**: Persistent data with volume mounting

## 📁 Project Structure

```
SpyGame/
├── app.py                      # Flask application & game logic
├── init_db.py                  # Database initialization script
├── process_data.py             # Data processing wrapper
├── dirt_builder.py             # DIRT model builder
├── utils_dirt.py               # DIRT utilities for reformulation
├── test_dirt.py                # DIRT system testing script
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container definition
├── spygame.ps1                 # Windows helper script
├── spygame.sh                  # Linux/Mac helper script
├── USAGE.md                    # Detailed usage guide
├── DIRT_README.md              # DIRT system documentation
├── game_sessions.json          # Fallback storage
├── pistas.json                 # Example hints (for init only)
├── modelo_inferencias.json     # DIRT inference model (generated)
├── datatreatment/
│   └── data_processor.py       # Wikipedia processing & AI
├── static/
│   └── style.css               # Application styling
├── templates/
│   ├── index.html              # Main game interface
│   └── stats.html              # Statistics page
└── LICENSE                     # MIT License
```
└── README.md            # This file
```

## CSS Architecture & Styling

### Design System
- **Color Palette**: Deep purples, neon accents, dark backgrounds
- **Typography**: Segoe UI font stack with dramatic effects
- **Spacing**: Consistent padding and margins using multiples of 4-8px
- **Shadows**: Layered box-shadows for depth and atmosphere

### Component Structure
- **Container System**: Centered layout with max-width constraints
- **Card Components**: Glass-morphism cards for content sections
- **Button System**: Multiple button types with consistent styling
- **Table Design**: Dark-themed data tables with hover effects
- **Message System**: Color-coded feedback with animations

### Responsive Breakpoints
- **Mobile**: 480px and below - Optimized for small screens
- **Tablet**: 768px and below - Adjusted layouts and sizing
- **Desktop**: 1200px and above - Enhanced spacing and larger elements

## Customization

### Adding New Historical Figures
Edit the `PERSONS_DATA` dictionary in `app.py`:

### Modifying the Theme
The CSS is extensively commented and organized by component. Key customization areas:

- **Colors**: Modify CSS custom properties at the top of `style.css`
- **Animations**: Adjust transition durations and effects
- **Layout**: Change container widths and spacing values
- **Typography**: Update font families and sizing scales

## Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate comments
4. Test thoroughly across different devices
5. Submit a pull request

### Code Style
- **Comprehensive comments** explaining all HTML, CSS, and JavaScript
- **Semantic HTML** with proper accessibility features
- **Modular CSS** organized by component and purpose
- **Clean JavaScript** with clear function names and documentation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Academic Context

This project was developed as part of a Bachelor's thesis exploring web development with modern design principles. It demonstrates:

- **Full-stack web development** with Python and JavaScript
- **Modern CSS techniques** including Grid, Flexbox, and animations
- **User experience design** with progressive disclosure and feedback
- **Data visualization** through statistics and history tracking
- **Responsive design principles** for cross-device compatibility

**Enjoy playing SpyGame! 🕵️‍♂️🎯**