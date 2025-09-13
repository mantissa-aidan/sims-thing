#!/usr/bin/env python3
"""
Run the Sims autopilot using the Docker setup.
This connects to the running Docker containers.
"""

import os
import sys
import json
import requests
import time

def check_docker_services():
    """Check if Docker services are running."""
    print("🔍 Checking Docker services...")
    
    # Check if Flask app is running
    try:
        response = requests.get('http://localhost:5001/', timeout=5)
        if response.status_code == 200:
            print("✅ Flask app is running")
        else:
            print("❌ Flask app not responding")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Flask app: {e}")
        return False
    
    return True

def run_autopilot_via_api():
    """Run autopilot simulation via API calls."""
    print("🎮 Starting Sims Autopilot via API")
    print("=" * 50)
    
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
    
    print(f"📖 Scenario: {scenario_description}")
    print(f"👤 Sim: {sim_id}")
    print()
    
    # Get user preferences
    print("Choose your story experience:")
    print("1. 🏃 Quick Story (5 turns)")
    print("2. 📖 Standard Story (10 turns)")
    print("3. 📚 Epic Story (20 turns)")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return
    
    # Set parameters
    if choice == "1":
        num_turns = 5
    elif choice == "2":
        num_turns = 10
    elif choice == "3":
        num_turns = 20
    else:
        print("❌ Invalid choice!")
        return
    
    print(f"\n🎬 Starting story with {num_turns} turns...")
    print("💡 The AI will create an emergent narrative!")
    print("⏱️  Each turn involves AI decision-making...")
    print("=" * 50)
    
    # Run the simulation
    for turn in range(1, num_turns + 1):
        print(f"\n--- Turn {turn}/{num_turns} ---")
        
        # Get current game state
        try:
            response = requests.get(f'http://localhost:5001/game/full_state?sim_id={sim_id}')
            if response.status_code == 200:
                state = response.json()
                if 'sim' in state:
                    sim = state['sim']
                    print(f"Current state for {sim['name']}:")
                    print(f"  Location: {sim['location']}")
                    print(f"  Mood: {sim['mood']}")
                    print(f"  Needs: {sim['needs']}")
                    inventory = sim.get('inventory', [])
                    inventory_str = ", ".join(inventory) if inventory else "empty"
                    print(f"  Inventory: {inventory_str}")
                else:
                    print("❌ Could not get sim state")
                    continue
            else:
                print("❌ Could not get game state")
                continue
        except Exception as e:
            print(f"❌ Error getting state: {e}")
            continue
        
        # Simulate AI decision making
        print("🤔 Horace is deciding what to do...")
        time.sleep(2)  # Simulate thinking time
        
        # Simple AI decision logic (you could make this more sophisticated)
        possible_actions = [
            "look around",
            "go to Kitchenette", 
            "go to Living Area",
            "go to Sleeping Area",
            "eat banana",
            "sit on sofa",
            "sleep",
            "use computer"
        ]
        
        # Choose a random action (in a real implementation, this would be AI-driven)
        import random
        action = random.choice(possible_actions)
        print(f"Horace chose action: {action}")
        
        # Process the action
        print("🎭 Game is processing the action...")
        time.sleep(1)
        
        try:
            response = requests.post(
                'http://localhost:5001/game/action',
                json={"sim_id": sim_id, "action": action},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                narrative = result.get("narrative", "No narrative provided.")
                print(f"Narrative: {narrative}")
                
                # Show any state updates
                if "sim_state_updates" in result:
                    updates = result["sim_state_updates"]
                    if updates.get("mood"):
                        print(f"  Mood changed to: {updates['mood']}")
                    if updates.get("location"):
                        print(f"  Moved to: {updates['location']}")
                    if updates.get("inventory_add"):
                        print(f"  Picked up: {updates['inventory_add']}")
                    if updates.get("inventory_remove"):
                        print(f"  Used/ate: {updates['inventory_remove']}")
            else:
                print(f"❌ Error processing action: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Error processing action: {e}")
        
        print(f"--- End of Turn {turn} ---")
        if turn < num_turns:
            time.sleep(2)  # Pause between turns
    
    print("\n" + "=" * 50)
    print("🎉 Story completed! The AI has created a unique narrative.")

def main():
    if not check_docker_services():
        print("\n❌ Docker services are not running.")
        print("Please start with: docker-compose up --build -d")
        return
    
    run_autopilot_via_api()

if __name__ == "__main__":
    main()
