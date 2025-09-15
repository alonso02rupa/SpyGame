# 🕵️ SpyGame

A dark purple/noir-themed web-based guessing game where players try to identify famous historical figures based on progressive hints. Built with Flask and featuring a sleek, spy-movie inspired interface.

## 🎮 Game Overview

SpyGame challenges players to guess famous Wikipedia personalities using a hint system. Players can request up to 5 hints per game, with each hint providing more specific information about the historical figure. The game tracks statistics and provides a detailed history of all gameplay sessions.

### Featured Historical Figures
- **Albert Einstein** - The brilliant physicist
- **Marie Curie** - The pioneering scientist  
- **Leonardo da Vinci** - The Renaissance genius
- **William Shakespeare** - The legendary playwright
- **Cleopatra** - The last pharaoh of Egypt

## 🎨 Design Features

### Dark Purple/Noir Theme
- **Deep purple gradient backgrounds** with subtle texture overlays
- **Glass-morphism effects** with backdrop blur and transparency
- **Neon purple accents** and glowing button effects
- **Dramatic typography** with gradient text and shadows
- **Spy-movie aesthetic** perfect for the guessing game theme

### Interactive Elements
- **Animated buttons** with hover effects and state changes
- **Shimmer animations** on message boxes
- **Smooth transitions** throughout the interface
- **Responsive design** that works on all devices
- **Progressive disclosure** - sections appear as the game progresses

## 🚀 Getting Started

### Prerequisites
- Python 3.7 or higher
- Flask web framework

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/alonso02rupa/SpyGame.git
   cd SpyGame
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your web browser** and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## 🎯 How to Play

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

### Game Options
- **Reveal Answer**: Give up and see the correct answer (ends the game)
- **Start New Game**: Begin a fresh game with a new historical figure
- **View Statistics**: See your gameplay history and performance metrics

## 📊 Statistics & Tracking

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

## 🏗️ Technical Architecture

### Backend (Python/Flask)
- **`app.py`**: Main Flask application with game logic
- **Session management**: Tracks current game state
- **Data persistence**: Stores game history in JSON format
- **API endpoints**: Handle game actions via AJAX requests

### Frontend (HTML/CSS/JavaScript)
- **`templates/index.html`**: Main game interface
- **`templates/stats.html`**: Statistics and history page  
- **`static/style.css`**: Complete styling with dark theme
- **Vanilla JavaScript**: Handles user interactions and API communication

### Key Features
- **RESTful API design** for clean client-server communication
- **Progressive enhancement** - works without JavaScript for basic functionality
- **Mobile-responsive** design using CSS Grid and Flexbox
- **Accessibility features** with proper ARIA labels and semantic HTML

## 📁 Project Structure

```
SpyGame/
├── app.py                 # Flask application and game logic
├── requirements.txt       # Python dependencies
├── game_sessions.json     # Game history storage (auto-created)
├── static/
│   └── style.css         # Complete CSS styling
├── templates/
│   ├── index.html        # Main game page
│   └── stats.html        # Statistics page
├── LICENSE               # MIT License
└── README.md            # This file
```

## 🎨 CSS Architecture & Styling

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

## 🔧 Customization

### Adding New Historical Figures
Edit the `PERSONS_DATA` dictionary in `app.py`:

```python
PERSONS_DATA = {
    "Your Historical Figure": [
        "Hint 1 about this person",
        "Hint 2 about this person", 
        "Hint 3 about this person",
        "Hint 4 about this person",
        "Hint 5 about this person"
    ]
}
```

### Modifying the Theme
The CSS is extensively commented and organized by component. Key customization areas:

- **Colors**: Modify CSS custom properties at the top of `style.css`
- **Animations**: Adjust transition durations and effects
- **Layout**: Change container widths and spacing values
- **Typography**: Update font families and sizing scales

## 🤝 Contributing

This project was created as part of a Bachelor's thesis. Contributions are welcome!

### Development Setup
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

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎓 Academic Context

This project was developed as part of a Bachelor's thesis exploring web development with modern design principles. It demonstrates:

- **Full-stack web development** with Python and JavaScript
- **Modern CSS techniques** including Grid, Flexbox, and animations
- **User experience design** with progressive disclosure and feedback
- **Data visualization** through statistics and history tracking
- **Responsive design principles** for cross-device compatibility

## 🔮 Future Enhancements

Potential improvements for future versions:

- **Difficulty levels** with varying hint specificity
- **Multiplayer support** for competitive guessing
- **Achievement system** with badges and rewards
- **Expanded person database** with categories and themes
- **Audio effects** and enhanced animations
- **Social sharing** of game results and statistics

---

**Enjoy playing SpyGame! 🕵️‍♂️🎯**