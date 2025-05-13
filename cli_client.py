import requests
import json

BASE_URL = "http://localhost:5001"
SIM_ID = "sim_alex" # Default Sim ID, matches app.py

def print_game_state(response_json):
    print("\n--- Narrative ---")
    print(response_json.get("narrative", "No narrative received."))
    
    sim_updates = response_json.get("sim_state_updates", {})
    if sim_updates:
        print("\n--- Sim Updated ---")
        if sim_updates.get("location"):
            print(f"Location: {sim_updates['location']}")
        if sim_updates.get("mood"):
            print(f"Mood: {sim_updates['mood']}")
        if sim_updates.get("current_activity"):
            print(f"Activity: {sim_updates['current_activity']}")
        if sim_updates.get("needs_delta"):
            print(f"Needs changes: {sim_updates['needs_delta']}")
        if sim_updates.get("inventory_add"):
            print(f"Inventory added: {sim_updates['inventory_add']}")
        if sim_updates.get("inventory_remove"):
            print(f"Inventory removed: {sim_updates['inventory_remove']}")

    env_updates = response_json.get("environment_updates", [])
    if env_updates:
        print("\n--- Environment Updated ---")
        for update in env_updates:
            print(f"- Object: {update.get('object_name')}, New State: {update.get('new_state_key')}, New Zone: {update.get('new_zone')}")

    available_actions = response_json.get("available_actions", [])
    if available_actions:
        print("\n--- Suggested Actions ---")
        for i, action in enumerate(available_actions):
            print(f"{i+1}. {action}")
    print("\n-----------------------")

def main():
    print("Welcome to the Sims MUD CLI!")
    print("Type 'quit' or 'exit' to end the game.")
    print("Example actions: 'look around', 'go to Kitchenette', 'examine Fridge', 'take Banana from Fridge', 'peel Banana', 'eat Banana'")

    # Optional: Fetch and print initial full state for context
    try:
        response = requests.get(f"{BASE_URL}/game/full_state")
        if response.status_code == 200:
            full_state = response.json()
            sim_location = full_state.get("sim", {}).get("location", "Unknown")
            print(f"\nInitial State: Alex is in the {sim_location}.")
            # Could print more details from full_state if desired
        else:
            print(f"Error fetching initial state: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to the game server at {BASE_URL}. Is it running?")
        return

    while True:
        try:
            action_input = input("\nWhat do you want Alex to do? > ")
            if action_input.lower() in ["quit", "exit"]:
                print("Exiting game. Goodbye!")
                break
            if not action_input.strip():
                continue

            payload = {"action": action_input, "sim_id": SIM_ID}
            response = requests.post(f"{BASE_URL}/game/action", json=payload)

            if response.status_code == 200:
                response_data = response.json()
                print_game_state(response_data)
            else:
                print(f"Error from server ({response.status_code}):")
                try:
                    error_data = response.json()
                    print(json.dumps(error_data, indent=2))
                except json.JSONDecodeError:
                    print(response.text) # Print raw text if not JSON
        
        except requests.exceptions.ConnectionError:
            print(f"Error: Could not connect to the game server at {BASE_URL}. Is it running?")
            break
        except KeyboardInterrupt:
            print("\nExiting game. Goodbye!")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

if __name__ == "__main__":
    main() 