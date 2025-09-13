# Sims Thing - Emergent AI Simulation

A sophisticated AI-powered simulation system that creates emergent storytelling through intelligent character behavior and dynamic world interactions.

## 🌟 Features

- **Emergent Storytelling**: AI characters make intelligent decisions that create unique, evolving narratives
- **Dynamic World State**: Objects are consumed, moved, and transformed based on character actions
- **Action History System**: Characters learn from their previous actions and adapt their behavior
- **Pre-validation**: Robust error handling prevents invalid interactions
- **RESTful API**: Clean API endpoints for easy UI integration
- **Docker Support**: Easy deployment with Docker and Docker Compose

## 🏗️ Architecture

```
src/
├── api/           # API routes and endpoints
├── models/        # Data models and schemas
├── utils/         # Utility functions and validation
├── config.py      # Application configuration
├── database.py    # Database connection and collections
└── game_engine.py # Core game logic and AI integration

scripts/           # Autopilot and utility scripts
docs/             # Documentation
tests/            # Test suite
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- MongoDB
- Ollama (with Gemma 3:12b model)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sims-thing
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start MongoDB**
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 mongo:latest
   
   # Or using local installation
   mongod
   ```

5. **Start Ollama**
   ```bash
   ollama serve
   ollama pull gemma3:12b
   ```

6. **Run the application**
   ```bash
   python app_clean.py
   ```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🎮 Usage

### API Endpoints

The application provides a RESTful API for interacting with the simulation:

- `GET /api/v1/health` - Health check
- `GET /api/v1/sims` - List all Sims
- `GET /api/v1/sims/{sim_id}` - Get Sim details
- `GET /api/v1/sims/{sim_id}/state` - Get current game state
- `POST /api/v1/sims/{sim_id}/action` - Process an action
- `GET /api/v1/sims/{sim_id}/suggest` - Get AI-suggested action
- `GET /api/v1/sims/{sim_id}/history` - Get action history

See [API Documentation](docs/API.md) for detailed endpoint information.

### Example API Usage

```bash
# Get all Sims
curl http://localhost:5001/api/v1/sims

# Get Sim state
curl http://localhost:5001/api/v1/sims/sim_horace/state

# Process an action
curl -X POST http://localhost:5001/api/v1/sims/sim_horace/action \
  -H "Content-Type: application/json" \
  -d '{"action": "sit on obj_sofa"}'

# Get AI suggestion
curl http://localhost:5001/api/v1/sims/sim_horace/suggest
```

### Autopilot Mode

Run the simulation automatically:

```bash
# Using the autopilot script
python scripts/run_autopilot.py

# Or with custom parameters
python scripts/watch_story.py
```

## 🧠 How It Works

### AI Decision Making
- Characters analyze their current state (needs, mood, location)
- AI considers available objects and previous actions
- Decisions are made based on character needs and logical reasoning
- Actions are validated before execution

### World State Management
- Objects can be consumed, moved, or transformed
- Character inventory and location are tracked
- Action history influences future decisions
- Dynamic world changes create emergent narratives

### Action Processing
1. **Pre-validation**: Check if objects exist and actions are valid
2. **AI Processing**: Generate narrative and state changes
3. **State Updates**: Apply changes to character and world
4. **History Recording**: Store action for future reference

## 🎭 Emergent Storytelling

The system creates unique stories through:

- **Resource Scarcity**: Characters must adapt when food runs out
- **Logical Progression**: Actions follow natural cause-and-effect
- **Character Development**: Moods and needs change based on experiences
- **Environmental Interaction**: World state affects available options
- **Learning Behavior**: Characters remember and learn from past actions

## 🔧 Configuration

### Environment Variables

```bash
# Database
MONGODB_URI=mongodb://localhost:27017/sims_mud_db

# AI Model
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:12b

# Flask
FLASK_DEBUG=1
```

### Scenarios

Scenarios define the initial world state and character setup. See `scenarios.json` for examples.

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## 📚 Documentation

- [API Documentation](docs/API.md) - Complete API reference
- [Architecture Guide](docs/ARCHITECTURE.md) - System design overview
- [Development Guide](docs/DEVELOPMENT.md) - Contributing guidelines

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with Flask and MongoDB
- AI powered by Ollama and Gemma 3:12b
- Inspired by The Sims and emergent gameplay concepts
