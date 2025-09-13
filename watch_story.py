#!/usr/bin/env python3
"""
Interactive script to watch the Sims story unfold with different configurations.
"""

import os
import sys
import json
from autopilot import run_autopilot_simulation

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
    print("\n🎭 Sims Story Watcher")
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
