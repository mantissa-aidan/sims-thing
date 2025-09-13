#!/usr/bin/env python3
"""
Comprehensive AI Demonstration Script
Shows the full AI functionality with detailed output
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
    """Get AI suggestion for a sim"""
    try:
        response = requests.get(f"http://localhost:5001/api/v1/sims/{sim_id}/suggest", timeout=30)
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
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def display_sim_state(sim_state):
    """Display the current sim state with detailed information"""
    if not sim_state:
        print("❌ Could not get sim state")
        return
    
    print(f"📍 Location: {sim_state.get('location', 'Unknown')}")
    print(f"😊 Mood: {sim_state.get('mood', 'Unknown')}")
    print(f"🎭 Activity: {sim_state.get('current_activity', 'Unknown')}")
    
    needs = sim_state.get('needs', {})
    print(f"🍎 Hunger: {needs.get('hunger', 0)}/100")
    print(f"⚡ Energy: {needs.get('energy', 0)}/100")
    print(f"🎮 Fun: {needs.get('fun', 0)}/100")
    print(f"👥 Social: {needs.get('social', 0)}/100")
    
    inventory = sim_state.get('inventory', [])
    if inventory:
        print(f"🎒 Inventory: {', '.join(inventory) if isinstance(inventory, list) else str(inventory)}")
    else:
        print("🎒 Inventory: empty")

def run_comprehensive_demo(sim_id, num_turns=5):
    """Run a comprehensive demonstration of the AI functionality"""
    print("🤖 COMPREHENSIVE AI DEMONSTRATION")
    print("=" * 60)
    print(f"👤 Sim: {sim_id}")
    print(f"📊 Running {num_turns} turns")
    print("=" * 60)
    
    for turn in range(1, num_turns + 1):
        print(f"\n🎬 TURN {turn}/{num_turns}")
        print("-" * 40)
        
        # Get current state
        print("📊 Current State:")
        sim_state = get_sim_state(sim_id)
        display_sim_state(sim_state)
        
        # Get AI suggestion
        print(f"\n🤖 AI Decision Making:")
        print("   Thinking...")
        suggestion = get_ai_suggestion(sim_id)
        
        if suggestion and suggestion.get("action"):
            action = suggestion.get("action", "look around")
            reason = suggestion.get("reason", "No reason provided")
            print(f"   💡 Suggested Action: {action}")
            print(f"   🧠 Reasoning: {reason}")
            
            # Process the action
            print(f"\n⚡ Processing Action:")
            print("   Executing...")
            result = process_action(sim_id, action)
            
            if result:
                narrative = result.get("narrative", "Action processed")
                print(f"   📖 Result: {narrative}")
                
                # Show detailed state updates
                sim_updates = result.get("sim_state_updates", {})
                if sim_updates:
                    print(f"\n🔄 State Changes:")
                    if "location" in sim_updates:
                        print(f"   🏠 Location: {sim_updates['location']}")
                    if "mood" in sim_updates:
                        print(f"   😊 Mood: {sim_updates['mood']}")
                    if "current_activity" in sim_updates:
                        print(f"   🎭 Activity: {sim_updates['current_activity']}")
                    if "needs_delta" in sim_updates:
                        needs_delta = sim_updates["needs_delta"]
                        print(f"   📊 Needs Changes:")
                        for need, delta in needs_delta.items():
                            if delta != 0:
                                print(f"      {need.capitalize()}: {delta:+d}")
                
                # Show environment updates
                env_updates = result.get("environment_updates", [])
                if env_updates:
                    print(f"\n🔧 Environment Changes:")
                    for update in env_updates:
                        if update.get("new_state_key"):
                            print(f"   {update['object_id']}: {update['new_state_key']}")
                
                # Show available actions
                available_actions = result.get("available_actions", [])
                if available_actions:
                    print(f"\n🎯 Available Actions: {', '.join(available_actions[:3])}")
            else:
                print("   ❌ Failed to process action")
        else:
            print("   ❌ Could not get AI suggestion")
        
        if turn < num_turns:
            print(f"\n⏱️  Waiting 3 seconds before next turn...")
            time.sleep(3)
    
    print(f"\n🎉 DEMONSTRATION COMPLETE!")
    print("=" * 60)
    print("The AI has demonstrated:")
    print("✅ Intelligent decision making based on needs")
    print("✅ Context-aware action suggestions")
    print("✅ Real-time state updates")
    print("✅ Environment interaction")
    print("✅ Emergent storytelling")

def main():
    if not check_api_health():
        print("❌ API is not running! Please start the Docker services first:")
        print("   docker-compose up -d")
        return
    
    print("✅ API is running")
    
    # Get the sim ID
    try:
        response = requests.get("http://localhost:5001/api/v1/sims", timeout=5)
        if response.status_code == 200:
            data = response.json()
            sims = data.get("sims", [])
            if sims:
                sim_id = sims[0]["sim_id"]
                run_comprehensive_demo(sim_id, 5)
            else:
                print("❌ No sims found")
        else:
            print("❌ Could not get sims")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
