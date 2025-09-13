#!/usr/bin/env python3
"""
Simple script to run the Sims autopilot with optimal settings for story watching.
This will start the Flask app in the background and then run the autopilot simulation.
"""

import subprocess
import time
import signal
import sys
import os
from autopilot import run_autopilot_simulation
import json

def start_flask_app():
    """Start the Flask app in the background."""
    print("🚀 Starting Flask app in background...")
    # Start Flask app as a subprocess
    flask_process = subprocess.Popen([
        sys.executable, 'app.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait a moment for Flask to start
    time.sleep(3)
    
    # Check if Flask is running
    try:
        import requests
        response = requests.get('http://localhost:5001/', timeout=5)
        if response.status_code == 200:
            print("✅ Flask app is running!")
            return flask_process
        else:
            print("❌ Flask app failed to start properly")
            flask_process.terminate()
            return None
    except Exception as e:
        print(f"❌ Flask app failed to start: {e}")
        flask_process.terminate()
        return None

def cleanup(flask_process):
    """Clean up the Flask process."""
    if flask_process:
        print("\n🛑 Stopping Flask app...")
        flask_process.terminate()
        flask_process.wait()
        print("✅ Flask app stopped.")

def main():
    print("🎮 Sims Autopilot Story Mode")
    print("=" * 50)
    
    # Check if scenarios.json exists
    if not os.path.exists('scenarios.json'):
        print("❌ scenarios.json not found. Please ensure it exists.")
        return
    
    # Load scenarios to get sim_id
    try:
        with open('scenarios.json', 'r') as f:
            scenarios = json.load(f)
        default_scenario_key = "default_horace_apartment"
        if default_scenario_key not in scenarios:
            print(f"❌ Scenario '{default_scenario_key}' not found in scenarios.json.")
            return
        sim_id = scenarios[default_scenario_key]["sim_config"]["sim_id"]
        scenario_description = scenarios[default_scenario_key].get("description", "No description")
    except Exception as e:
        print(f"❌ Error loading scenarios: {e}")
        return
    
    print(f"📖 Scenario: {scenario_description}")
    print(f"👤 Sim: {sim_id}")
    print()
    
    # Start Flask app
    flask_process = start_flask_app()
    if not flask_process:
        return
    
    try:
        # Run autopilot simulation
        print("🎭 Starting autopilot simulation...")
        print("💡 The AI will make decisions and create an unfolding story!")
        print("⏱️  Each turn takes a few seconds for AI processing...")
        print("=" * 50)
        
        # Run for a good number of turns to see a substantial story
        # You can adjust these parameters:
        num_turns = 20  # Number of actions the AI will take
        turn_delay = 2  # Seconds between turns (for readability)
        
        run_autopilot_simulation(
            sim_id=sim_id,
            num_turns=num_turns,
            turn_delay_seconds=turn_delay
        )
        
        print("\n" + "=" * 50)
        print("🎉 Story simulation completed!")
        print("💭 The AI has created a unique narrative based on its decisions.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Simulation interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error during simulation: {e}")
    finally:
        cleanup(flask_process)

if __name__ == "__main__":
    main()
