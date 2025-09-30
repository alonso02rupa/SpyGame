#  SpyGame

A dark purple/noir-themed web-based guessing game where players try to identify famous people based on automatically generated and difficulty progressive hints. Built with Flask and featuring a sleek, spy-movie inspired interface.

## Game Overview

SpyGame challenges players to guess famous Wikipedia personalities using a hint system. Players can request up to 5 hints per game, with each hint providing more specific information about the historical figure. The game tracks statistics and provides a detailed history of all gameplay sessions.


##  Getting Started

### Prerequisites
- Docker

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/alonso02rupa/SpyGame.git
   cd SpyGame
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Open your web browser** and navigate to:
   ```
   http://localhost:5000
   ```

   This setup includes:
   - Flask web application container built on an original image
   - MongoDB database container
   - Persistent data storage via volumes
   - Automatic container networking

## Environment Configuration

The application uses environment variables for sensitive configuration. Before running the application, set up your environment variables:

### 1. Create Environment File
Copy the example environment file and customize it:
```bash
cp .env.example .env
```

### 2. Configure Your Variables
Edit `.env` with your specific values:

```bash
# Flask Configuration
FLASK_SECRET_KEY=your_unique_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Database Configuration
MONGODB_URI=mongodb://mongodb:27017/spygame
MONGODB_HOST=mongodb
MONGODB_PORT=27017
MONGO_INITDB_DATABASE=spygame

# Wikipedia API Configuration
WIKIPEDIA_USER_AGENT=YourApp/1.0.0 (contact: your_email@example.com)

# Docker Configuration
DOCKER_WEB_PORT=5000
DOCKER_MONGO_PORT=27017
```

### 3. Important Security Notes
- **Never commit your `.env` file** to version control
- The `.env` file contains sensitive information and is excluded via `.gitignore`
- Use strong, unique values for `FLASK_SECRET_KEY` in production
- Replace the contact email in `WIKIPEDIA_USER_AGENT` with your actual email

## How to Play

### Starting a Game
1. Click the **"Start New Game"** button on the main page
2. The system randomly selects a historical figure for you to guess
3. The hints and guess sections become available

### Getting Hints
1. Click **"Get Hint"** to receive a clue about the person
2. Each game provides up to 5 hints
3. Hints become progressively more specific
4. The hint counter shows how many hints remain

### Making Guesses
1. Type your guess in the input field
2. Click **"Submit Guess"** or press Enter
3. Get immediate feedback on whether your guess is correct
4. You can make multiple guesses per game

## Statistics & Tracking

The game automatically tracks all your gameplay activities:

### Summary Statistics
- **Total Games**: Number of games you've started
- **Correct Guesses**: How many you've gotten right
- **Success Rate**: Your percentage of correct guesses

### Detailed History
- **Date & Time**: When each action occurred
- **Person**: Which historical figure was being guessed
- **Action Type**: Whether it was a hint request or guess attempt
- **Details**: The actual hint text or guess content
- **Result**: Whether guesses were correct or incorrect

## Technical Architecture

### Backend (Python/Flask)
- **`app.py`**: Main Flask application with game logic
- **Session management**: Tracks current game state
- **Data persistence**: Stores game history in MongoDB (with JSON fallback for local development)
- **API endpoints**: Handle game actions via AJAX requests
- **MongoDB integration**: PyMongo for database operations

### Database
- **MongoDB**: Primary database for production deployment
- **JSON fallback**: Local file storage for development when MongoDB is unavailable
- **Collections**: Game sessions with timestamps, hints, guesses, and results

### Deployment
- **Docker support**: Complete containerization with Docker Compose
- **MongoDB container**: Persistent data storage with volume mounting
- **Network isolation**: Secure container networking

### Frontend (HTML/CSS/JavaScript)
- **`templates/index.html`**: Main game interface
- **`templates/stats.html`**: Statistics and history page  
- **`static/style.css`**: Complete styling with dark theme
- **Vanilla JavaScript**: Handles user interactions and API communication

### Key Features
- **RESTful API design** for clean client-server communication
- **Mobile-responsive** design using CSS Grid and Flexbox
- **Accessibility features** with proper ARIA labels and semantic HTML

## Project Structure

```
SpyGame/
├── app.py                 # Flask application and game logic
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile            # Docker container definition
├── .dockerignore         # Docker build exclusions
├── game_sessions.json     # Game history storage (fallback for local dev)
├── static/
│   └── style.css         # Complete CSS styling
├── templates/
│   ├── index.html        # Main game page
│   └── stats.html        # Statistics page
├── LICENSE               # MIT License
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