#!/usr/bin/env python3
"""
Interactive script to watch the Sims story unfold with the new API.
"""

import requests
import time
import json

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get("http://localhost:5001/api/v1/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_sim_state(sim_id):
    """Get current sim state"""
    try:
        response = requests.get(f"http://localhost:5001/api/v1/sims/{sim_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_ai_suggestion(sim_id):
    """Get AI suggestion for next action"""
    try:
        response = requests.get(f"http://localhost:5001/api/v1/sims/{sim_id}/suggest", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def process_action(sim_id, action):
    """Process an action for the sim"""
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

def display_sim_state(sim_state):
    """Display the current sim state"""
    if not sim_state:
        print("❌ Could not get sim state")
        return
    
    print(f"📍 Location: {sim_state.get('location', 'Unknown')}")
    print(f"😊 Mood: {sim_state.get('mood', 'Unknown')}")
    needs = sim_state.get('needs', {})
    print(f"🍎 Hunger: {needs.get('hunger', 0)}/100")
    print(f"⚡ Energy: {needs.get('energy', 0)}/100")
    print(f"🎮 Fun: {needs.get('fun', 0)}/100")
    print(f"👥 Social: {needs.get('social', 0)}/100")

def run_autopilot_simulation(sim_id, num_turns=10, turn_delay_seconds=2):
    """Run the autopilot simulation"""
    print(f"🎮 Starting Autopilot for {sim_id}")
    print(f"📊 Running {num_turns} turns with {turn_delay_seconds}s delay")
    print("=" * 50)
    
    for turn in range(1, num_turns + 1):
        print(f"\n--- Turn {turn}/{num_turns} ---")
        
        # Get current state
        sim_state = get_sim_state(sim_id)
        display_sim_state(sim_state)
        
        # Get AI suggestion
        print("🤖 AI is thinking...")
        suggestion = get_ai_suggestion(sim_id)
        
        if suggestion and suggestion.get("action"):
            action = suggestion["action"]
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
            time.sleep(turn_delay_seconds)
    
    print("\n" + "=" * 50)
    print("🎉 Autopilot simulation completed!")

def load_scenarios():
    """Load scenarios from scenarios.json"""
    try:
        with open('scenarios.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ scenarios.json not found!")
        return None
    except json.JSONDecodeError:
        print("❌ Error reading scenarios.json!")
        return None

def show_menu():
    """Show the story watching menu"""
    print("\n🎭 Sims Story Watcher (New API)")
    print("=" * 40)
    print("Choose your story experience:")
    print()
    print("1. 🏃 Quick Story (5 turns, 1s delay)")
    print("2. 📖 Standard Story (15 turns, 2s delay)")
    print("3. 📚 Epic Story (30 turns, 3s delay)")
    print("4. 🌟 Marathon Story (50 turns, 2s delay)")
    print("5. ⚡ Lightning Fast (20 turns, 0.5s delay)")
    print("6. 🎯 Custom Configuration")
    print("0. ❌ Exit")
    print()

def get_custom_config():
    """Get custom configuration from user"""
    print("\n🎯 Custom Configuration")
    print("-" * 25)
    
    try:
        turns = int(input("Number of turns (1-100): "))
        if turns < 1 or turns > 100:
            print("❌ Invalid number of turns!")
            return None
            
        delay = float(input("Delay between turns in seconds (0.1-10): "))
        if delay < 0.1 or delay > 10:
            print("❌ Invalid delay!")
            return None
            
        return turns, delay
    except ValueError:
        print("❌ Invalid input!")
        return None

def run_story(turns, delay, sim_id):
    """Run the story simulation"""
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

def main():
    # Check API health
    if not check_api_health():
        print("❌ API is not running! Please start the Docker services first:")
        print("   docker-compose up -d")
        return
    
    print("✅ API is running")
    
    # Load scenarios
    scenarios = load_scenarios()
    if not scenarios:
        return
    
    # Get default sim
    default_scenario_key = "default_horace_apartment"
    if default_scenario_key not in scenarios:
        print(f"❌ Scenario '{default_scenario_key}' not found!")
        return
    
    sim_id = scenarios[default_scenario_key]["sim_config"]["sim_id"]
    scenario_description = scenarios[default_scenario_key].get("description", "No description")
    
    print(f"👤 Sim: {sim_id}")
    print(f"📖 Scenario: {scenario_description}")
    
    while True:
        show_menu()
        
        try:
            choice = input("Enter your choice (0-6): ").strip()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            run_story(5, 1, sim_id)
        elif choice == "2":
            run_story(15, 2, sim_id)
        elif choice == "3":
            run_story(30, 3, sim_id)
        elif choice == "4":
            run_story(50, 2, sim_id)
        elif choice == "5":
            run_story(20, 0.5, sim_id)
        elif choice == "6":
            config = get_custom_config()
            if config:
                turns, delay = config
                run_story(turns, delay, sim_id)
        else:
            print("❌ Invalid choice! Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
