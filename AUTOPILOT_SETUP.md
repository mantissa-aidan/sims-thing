# 🎮 Sims Autopilot Setup Guide

## Quick Start - Watch the Story Unfold!

You now have everything set up to watch the AI create an emergent Sims story automatically! Here are your options:

### Option 1: Docker (Recommended - Easiest)
```bash
# Start everything with Docker
docker-compose up --build

# In another terminal, run the autopilot
python run_autopilot.py
```

### Option 2: Local Development
```bash
# 1. Activate virtual environment
source venv/bin/activate.fish

# 2. Start MongoDB (if not already running)
brew services start mongodb-community

# 3. Make sure Ollama is running (should already be running)
ollama serve

# 4. Run the local autopilot
python run_local_autopilot.py
```

### Option 3: Interactive Story Watcher
```bash
# Activate virtual environment
source venv/bin/activate.fish

# Run the interactive story watcher
python watch_story.py
```

## What You'll See

The autopilot will:
1. **Initialize** the game world with Horace in his studio apartment
2. **Show current state** - location, mood, needs, inventory, objects in room
3. **AI decides** what action to take (with animated thinking indicator)
4. **Processes action** - AI generates narrative and updates game state
5. **Repeats** for the specified number of turns

## Story Examples

The AI might create stories like:
- Horace gets hungry, goes to kitchen, finds food, eats it
- Horace gets tired, goes to bed, sleeps, wakes up refreshed
- Horace gets bored, plays with objects, discovers new interactions
- Horace explores different rooms, finds hidden items
- Horace's mood changes based on his needs and environment

## Configuration Options

### Quick Story (5 turns, 1s delay)
Perfect for a quick demo - see the AI make 5 decisions

### Standard Story (15 turns, 2s delay)
Good balance - enough time to see a meaningful story unfold

### Epic Story (30 turns, 3s delay)
Longer narrative - the AI can develop complex storylines

### Lightning Fast (20 turns, 0.5s delay)
Fast-paced - see many actions quickly

### Custom
Set your own number of turns and delay between actions

## Tips for Best Experience

1. **Watch the narrative** - The AI creates unique stories each time
2. **Notice the state changes** - Mood, needs, inventory, object states
3. **See emergent behavior** - The AI makes surprising decisions
4. **Try different scenarios** - Each run creates a different story

## Troubleshooting

### If MongoDB connection fails:
```bash
brew services start mongodb-community
```

### If Ollama connection fails:
```bash
ollama serve
ollama list  # Check available models
```

### If you get import errors:
```bash
source venv/bin/activate.fish
pip install -r requirements.txt
```

## Enjoy the Show! 🎭

The AI will create unique, emergent narratives every time you run it. Each story is different and unpredictable - that's the magic of AI-driven gameplay!
