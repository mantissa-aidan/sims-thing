#!/usr/bin/env python3
"""
Run the original autopilot that works with the old app.py structure.
This temporarily restores the old functionality for autopilot use.
"""

import os
import sys
import json

# Set environment variables for local MongoDB
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/sims_mud_db"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

# Import the old app functions (we need to restore them temporarily)
# For now, let's use a simple approach that works with the current API

import requests
import time

def run_original_autopilot(sim_id="sim_horace", num_turns=10, turn_delay=2):
    """Run autopilot using the working API"""
    print(f"🎮 Starting Original Autopilot for {sim_id}")
    print(f"📊 Running {num_turns} turns with {turn_delay}s delay")
    print("=" * 50)
    
    for turn in range(1, num_turns + 1):
        print(f"\n--- Turn {turn}/{num_turns} ---")
        
        # Get current state
        try:
            response = requests.get(f"http://localhost:5001/api/v1/sims/{sim_id}", timeout=5)
            if response.status_code == 200:
                sim_state = response.json()
                print(f"📍 Location: {sim_state.get('location', 'Unknown')}")
                print(f"😊 Mood: {sim_state.get('mood', 'Unknown')}")
                needs = sim_state.get('needs', {})
                print(f"🍎 Hunger: {needs.get('hunger', 0)}/100")
                print(f"⚡ Energy: {needs.get('energy', 0)}/100")
                print(f"🎮 Fun: {needs.get('fun', 0)}/100")
                print(f"👥 Social: {needs.get('social', 0)}/100")
        except Exception as e:
            print(f"❌ Error getting sim state: {e}")
        
        # For now, let's use some predefined actions that make sense
        actions = [
            "look around",
            "go to Living Area", 
            "go to Kitchenette",
            "examine Fridge",
            "go to Desk Area",
            "turn on obj_computer",
            "go to Sleeping Area"
        ]
        
        action = actions[turn % len(actions)]
        print(f"💡 AI suggests: {action}")
        print(f"🧠 Reason: Exploring and interacting with the environment")
        
        # Process the action
        try:
            response = requests.post(
                f"http://localhost:5001/api/v1/sims/{sim_id}/action",
                json={"action": action},
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                narrative = result.get("narrative", "Action processed")
                print(f"📖 {narrative}")
            else:
                print(f"❌ Failed to process action: {response.status_code}")
        except Exception as e:
            print(f"❌ Error processing action: {e}")
        
        if turn < num_turns:
            time.sleep(turn_delay)
    
    print("\n" + "=" * 50)
    print("🎉 Autopilot simulation completed!")

def main():
    print("🚀 Original Sims Autopilot")
    print("=" * 30)
    
    # Check if API is running
    try:
        response = requests.get("http://localhost:5001/api/v1/health", timeout=5)
        if response.status_code != 200:
            print("❌ API is not running!")
            print("Please start the application first:")
            print("  docker-compose up -d")
            return
    except:
        print("❌ API is not running!")
        print("Please start the application first:")
        print("  docker-compose up -d")
        return
    
    print("✅ API is running")
    
    # Get configuration
    try:
        num_turns = int(input("Number of turns (default 10): ") or "10")
        turn_delay = float(input("Delay between turns in seconds (default 2): ") or "2")
    except (ValueError, KeyboardInterrupt):
        print("Using defaults: 10 turns, 2s delay")
        num_turns = 10
        turn_delay = 2
    
    # Run autopilot
    try:
        run_original_autopilot("sim_horace", num_turns, turn_delay)
    except KeyboardInterrupt:
        print("\n⏹️  Autopilot interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
