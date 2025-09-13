# Development Guide

## Getting Started

### Prerequisites
- Python 3.9+
- MongoDB
- Ollama with Gemma 3:12b model
- Git

### Setup Development Environment

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd sims-thing
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run setup script**
   ```bash
   python scripts/setup_dev.py
   ```

3. **Start services**
   ```bash
   # Terminal 1: MongoDB
   mongod
   
   # Terminal 2: Ollama
   ollama serve
   
   # Terminal 3: Application
   python app_clean.py
   ```

## Project Structure

```
src/
├── api/           # API routes and endpoints
│   ├── __init__.py
│   └── routes.py
├── models/        # Data models (future)
├── utils/         # Utility functions
│   ├── __init__.py
│   └── validation.py
├── config.py      # Configuration management
├── database.py    # Database connections
└── game_engine.py # Core game logic

scripts/           # Utility scripts
├── run_autopilot.py
├── setup_dev.py
└── watch_story.py

docs/             # Documentation
├── API.md
└── DEVELOPMENT.md

tests/            # Test suite
└── test_app.py
```

## Development Workflow

### 1. Making Changes

- **API Changes**: Modify `src/api/routes.py`
- **Game Logic**: Update `src/game_engine.py`
- **Configuration**: Edit `src/config.py`
- **Database**: Modify `src/database.py`

### 2. Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_app.py::test_specific_function
```

### 3. Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## API Development

### Adding New Endpoints

1. **Add route to `src/api/routes.py`**
   ```python
   @api.route('/new-endpoint', methods=['GET'])
   def new_endpoint():
       return jsonify({"message": "Hello"}), 200
   ```

2. **Add validation if needed**
   ```python
   from src.utils.validation import validate_input
   
   if not validate_input(data):
       return jsonify({"error": "Invalid input"}), 400
   ```

3. **Update documentation in `docs/API.md`**

### Error Handling

Always use proper HTTP status codes:
- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

```python
try:
    result = game_engine.process_action(sim_id, action)
    return jsonify(result), 200
except ValueError as e:
    return jsonify({"error": str(e)}), 400
except Exception as e:
    return jsonify({"error": "Internal server error"}), 500
```

## Database Development

### Adding New Collections

1. **Update `src/database.py`**
   ```python
   class Database:
       def __init__(self):
           # ... existing code ...
           self.new_collection = self.db['new_collection']
   ```

2. **Add to exports**
   ```python
   new_collection = db.new_collection
   ```

### Database Queries

Use proper error handling:
```python
try:
    result = collection.find_one({"_id": object_id})
    if not result:
        return None
    return result
except Exception as e:
    logger.error(f"Database error: {e}")
    raise
```

## Game Engine Development

### Adding New Game Logic

1. **Add methods to `GameEngine` class**
   ```python
   def new_game_feature(self, sim_id: str) -> Dict[str, Any]:
       """New game feature implementation"""
       # Implementation here
       pass
   ```

2. **Add validation**
   ```python
   if not validate_sim_id(sim_id):
       raise ValueError("Invalid sim_id")
   ```

3. **Add error handling**
   ```python
   try:
       # Game logic here
       pass
   except Exception as e:
       raise Exception(f"Game engine error: {str(e)}")
   ```

## Testing

### Writing Tests

```python
import pytest
from src.game_engine import GameEngine

def test_game_engine_initialization():
    engine = GameEngine()
    assert engine is not None

def test_get_all_sims():
    engine = GameEngine()
    sims = engine.get_all_sims()
    assert isinstance(sims, list)
```

### Test Structure

- **Unit Tests**: Test individual functions
- **Integration Tests**: Test API endpoints
- **End-to-End Tests**: Test complete workflows

## Deployment

### Docker Development

```bash
# Build and run
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment

1. **Use production Dockerfile**
   ```bash
   docker build -f Dockerfile.clean -t sims-thing:latest .
   ```

2. **Set production environment variables**
   ```bash
   export FLASK_DEBUG=0
   export MONGODB_URI=mongodb://production-db:27017/sims_mud_db
   ```

## Debugging

### Common Issues

1. **MongoDB Connection**
   - Check if MongoDB is running
   - Verify connection string
   - Check network connectivity

2. **Ollama Connection**
   - Ensure Ollama is running
   - Verify model is available
   - Check base URL configuration

3. **Import Errors**
   - Check Python path
   - Verify virtual environment
   - Check module structure

### Debug Tools

```python
# Add logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints
print(f"Debug: {variable}")

# Use Flask debug mode
app.run(debug=True)
```

## Contributing

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings
- Write tests

### Commit Messages

Use conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation
- `style:` Code style
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Maintenance

### Pull Request Process

1. Create feature branch
2. Make changes
3. Add tests
4. Update documentation
5. Submit pull request

## Performance

### Optimization Tips

1. **Database Queries**
   - Use indexes
   - Limit result sets
   - Use projections

2. **API Responses**
   - Cache frequently accessed data
   - Use pagination for large datasets
   - Compress responses

3. **AI Calls**
   - Cache LLM responses
   - Use connection pooling
   - Implement rate limiting

## Security

### Best Practices

1. **Input Validation**
   - Validate all inputs
   - Sanitize user data
   - Use parameterized queries

2. **Authentication** (Future)
   - Implement JWT tokens
   - Use HTTPS
   - Validate permissions

3. **Error Handling**
   - Don't expose internal errors
   - Log security events
   - Use proper status codes
