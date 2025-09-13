#!/usr/bin/env python3
"""
Simple autopilot that uses the API to run the simulation.
This works with the new modular structure.
"""

import requests
import time
import json
import sys

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get("http://localhost:5001/api/v1/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_sim_id():
    """Get the first available sim ID"""
    try:
        response = requests.get("http://localhost:5001/api/v1/sims", timeout=5)
        if response.status_code == 200:
            data = response.json()
            sims = data.get("sims", [])
            if sims:
                return sims[0]["sim_id"]
        return None
    except:
        return None

def get_ai_suggestion(sim_id):
    """Get AI suggestion for a sim"""
    try:
        response = requests.get(f"http://localhost:5001/api/v1/sims/{sim_id}/suggest", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def process_action(sim_id, action):
    """Process an action for a sim"""
    try:
        response = requests.post(
            f"http://localhost:5001/api/v1/sims/{sim_id}/action",
            json={"action": action},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_sim_state(sim_id):
    """Get current sim state"""
    try:
        response = requests.get(f"http://localhost:5001/api/v1/sims/{sim_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def run_simple_autopilot(sim_id, num_turns=10, turn_delay=2):
    """Run a simple autopilot simulation"""
    print(f"🎮 Starting Simple Autopilot for {sim_id}")
    print(f"📊 Running {num_turns} turns with {turn_delay}s delay")
    print("=" * 50)
    
    for turn in range(1, num_turns + 1):
        print(f"\n--- Turn {turn}/{num_turns} ---")
        
        # Get current state
        sim_state = get_sim_state(sim_id)
        if sim_state:
            print(f"📍 Location: {sim_state.get('location', 'Unknown')}")
            print(f"😊 Mood: {sim_state.get('mood', 'Unknown')}")
            needs = sim_state.get('needs', {})
            print(f"🍎 Hunger: {needs.get('hunger', 0)}/100")
            print(f"⚡ Energy: {needs.get('energy', 0)}/100")
            print(f"🎮 Fun: {needs.get('fun', 0)}/100")
            print(f"👥 Social: {needs.get('social', 0)}/100")
        
        # Get AI suggestion
        print("🤖 AI is thinking...")
        suggestion = get_ai_suggestion(sim_id)
        
        if suggestion:
            action = suggestion.get("action", "look around")
            reason = suggestion.get("reason", "No reason provided")
            print(f"💡 AI suggests: {action}")
            print(f"🧠 Reason: {reason}")
            
            # Process the action
            print("⚡ Processing action...")
            result = process_action(sim_id, action)
            
            if result:
                narrative = result.get("narrative", "Action processed")
                print(f"📖 {narrative}")
            else:
                print("❌ Failed to process action")
        else:
            print("❌ Could not get AI suggestion")
        
        if turn < num_turns:
            time.sleep(turn_delay)
    
    print("\n" + "=" * 50)
    print("🎉 Autopilot simulation completed!")

def main():
    print("🚀 Simple Sims Autopilot")
    print("=" * 30)
    
    # Check if API is running
    if not check_api_health():
        print("❌ API is not running!")
        print("Please start the application first:")
        print("  docker-compose up -d")
        return
    
    print("✅ API is running")
    
    # Get sim ID
    sim_id = get_sim_id()
    if not sim_id:
        print("❌ No sims available!")
        return
    
    print(f"👤 Using sim: {sim_id}")
    
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
        run_simple_autopilot(sim_id, num_turns, turn_delay)
    except KeyboardInterrupt:
        print("\n⏹️  Autopilot interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
