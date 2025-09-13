#!/usr/bin/env python3
"""
Run the Sims autopilot locally (without Docker).
This script sets up the environment and runs the autopilot simulation.
"""

import os
import sys
import subprocess
import time
import json

# Add the parent directory to the Python path so we can import autopilot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autopilot import run_autopilot_simulation

def setup_local_environment():
    """Set up environment variables for local development."""
    os.environ["MONGODB_URI"] = "mongodb://localhost:27017/sims_mud_db"
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
    os.environ["OLLAMA_MODEL"] = "llama2:latest"
    os.environ["FLASK_APP"] = "app.py"
    os.environ["FLASK_DEBUG"] = "1"

def check_services():
    """Check if required services are running."""
    print("🔍 Checking services...")
    
    # Check Ollama
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            if any('llama2' in name for name in model_names):
                print("✅ llama2 model is available")
            else:
                print(f"❌ llama2 model not found. Available: {model_names}")
                return False
        else:
            print("❌ Ollama is not responding")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        return False
    
    # Check MongoDB (basic check)
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        client.server_info()
        print("✅ MongoDB is running")
        client.close()
    except Exception as e:
        print(f"❌ Cannot connect to MongoDB: {e}")
        print("💡 Start MongoDB with: brew services start mongodb-community")
        return False
    
    return True

def main():
    print("🎮 Sims Local Autopilot")
    print("=" * 40)
    
    # Set up environment
    setup_local_environment()
    
    # Check services
    if not check_services():
        print("\n❌ Required services are not running.")
        print("Please start:")
        print("1. Ollama: ollama serve")
        print("2. MongoDB: brew services start mongodb-community")
        return
    
    # Load scenarios
    try:
        with open('scenarios.json', 'r') as f:
            scenarios = json.load(f)
        default_scenario_key = "default_horace_apartment"
        if default_scenario_key not in scenarios:
            print(f"❌ Scenario '{default_scenario_key}' not found!")
            return
        sim_id = scenarios[default_scenario_key]["sim_config"]["sim_id"]
        scenario_description = scenarios[default_scenario_key].get("description", "No description")
    except Exception as e:
        print(f"❌ Error loading scenarios: {e}")
        return
    
    print(f"\n📖 Scenario: {scenario_description}")
    print(f"👤 Sim: {sim_id}")
    print()
    
    # Get user preferences
    print("Choose your story experience:")
    print("1. 🏃 Quick Story (5 turns, 1s delay)")
    print("2. 📖 Standard Story (15 turns, 2s delay)")
    print("3. 📚 Epic Story (30 turns, 3s delay)")
    print("4. ⚡ Lightning Fast (20 turns, 0.5s delay)")
    print("5. 🎯 Custom")
    
    try:
        choice = input("\nEnter choice (1-5): ").strip()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return
    
    # Set parameters based on choice
    if choice == "1":
        turns, delay = 5, 1
    elif choice == "2":
        turns, delay = 15, 2
    elif choice == "3":
        turns, delay = 30, 3
    elif choice == "4":
        turns, delay = 20, 0.5
    elif choice == "5":
        try:
            turns = int(input("Number of turns: "))
            delay = float(input("Delay between turns (seconds): "))
        except (ValueError, KeyboardInterrupt):
            print("❌ Invalid input!")
            return
    else:
        print("❌ Invalid choice!")
        return
    
    print(f"\n🎬 Starting story with {turns} turns, {delay}s delay...")
    print("💡 The AI will create an emergent narrative!")
    print("⏱️  Each turn involves AI decision-making...")
    print("=" * 50)
    
    try:
        run_autopilot_simulation(
            sim_id=sim_id,
            num_turns=turns,
            turn_delay_seconds=delay
        )
        print("\n" + "=" * 50)
        print("🎉 Story completed! The AI has created a unique narrative.")
    except KeyboardInterrupt:
        print("\n⏹️  Story interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error during story: {e}")

if __name__ == "__main__":
    main()
