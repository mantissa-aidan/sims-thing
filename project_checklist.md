# Project Checklist

## Core Game: Sims MUD
- [ ] Define Core Game Loop (Player Action -> Python Logic -> LLM Engine -> State Update -> Player Feedback)
- [ ] Sim Character
  - [ ] Define Sim attributes (e.g., name, location, mood, needs like hunger/energy, inventory)
  - [ ] MongoDB schema for Sim state
- [ ] Environment: Studio Apartment
  - [ ] Define initial apartment layout and interactable objects (e.g., bed, fridge, computer)
  - [ ] MongoDB schema for environment/object states
- [ ] Player Actions
  - [ ] Define a basic set of valid player actions (e.g., look, go to, use <object>, eat, sleep, work, play)
  - [x] Enforce "verb-first" principle for actions (Python pre-validation)
  - [ ] Implement action parsing and validation in Python
- [ ] LLM as Game Engine
  - [ ] Design prompts for the LLM to process actions and generate outcomes
    - [ ] Include Sim state, environment state, and player action in prompt
    - [ ] Instruct LLM to describe results, update Sim mood/needs, and modify environment
  - [ ] Develop logic to parse LLM responses and extract state changes
- [ ] Persistence
  - [ ] Functions to load/save Sim state from/to MongoDB
  - [ ] Functions to load/save environment state from/to MongoDB

## Backend (Python & Flask)
- [-] Initialize Flask App (`app.py`) - (Marking as complete for now, will be heavily modified)
- [-] Setup `requirements.txt` - (Marking as complete)
- [-] Create `.env` file for environment variables - (Marking as complete)
- [ ] MongoDB Integration
  - [-] Connect to MongoDB - (Marking as complete)
  - [ ] Implement CRUD operations for Sim and Environment states
- [ ] Langchain & Ollama Integration
  - [x] Configure Ollama client - (Marking as complete, model is now qwen2:8b and configurable)
  - [ ] Refine LLM interaction logic for game engine purposes
- [ ] API Endpoints
  - [ ] `/game/action` (POST): Endpoint to send player actions and receive game responses
  - [ ] `/game/state` (GET): Endpoint to retrieve current game state (optional/for debugging)
- [ ] Error Handling (specific to game logic)
- [ ] Logging (for game events and LLM interactions)

## Frontend (Text-based for now)
- [ ] Basic command-line interface (CLI) for player interaction (can be a separate script or integrated testing)

## DevOps & Deployment
- [x] Create `README.md` with setup and run instructions
- [x] Dockerize application (optional)
  - [x] Create `Dockerfile`
  - [x] Add Docker instructions to `README.md`
  - [x] Create `run.sh` script for easy execution (now secondary to Docker Compose)
  - [x] Implement Docker Compose setup (`docker-compose.yml`, `docker-compose.test.yml`)
    - [x] Add MongoDB as a service in Docker Compose setups
- [ ] Setup CI/CD pipeline (optional)

## Testing
- [x] Unit tests for action validation and state updates
  - [x] Test Python-handled actions (e.g., 'go to', invalid verb)
  - [x] Test LLM-response processing for Sim need changes (mocked LLM)
  - [x] Test LLM-response processing for environment object state changes (mocked LLM)
  - [x] Test LLM-response processing for inventory changes (mocked LLM)
  - [x] Test error handling for invalid LLM JSON output (mocked LLM)
- [-] Integration tests for game loop and LLM interaction (partially covered by above, full LLM integration tests are next)
- [x] Setup basic testing framework (`pytest`, `pytest-mock`)
- [x] Add initial tests for core API endpoints and game initialization
- [x] Configure Docker Compose for running tests (including MongoDB service)

## Documentation
- [ ] API documentation (if other frontends are envisioned)
- [ ] Game design document (outlining mechanics, states, goals - can evolve) 