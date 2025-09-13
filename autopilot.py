import time
import logging
import sys
import threading
import json
from app import get_llm_suggested_action, process_sim_action, initialize_game_world, app as flask_app, get_current_game_state

# Configure basic logging for the root logger (e.g., for this script's own direct logging)
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# Explicitly set the Flask app's logger level to WARNING to suppress its DEBUG messages
if flask_app:
    flask_app.logger.setLevel(logging.WARNING)

# --- Animation for waiting ---
stop_animation_event = threading.Event()

def animate(label="Thinking", animation_start_time=None):
    chars = r"-\\|/"
    idx = 0
    if animation_start_time is None:
        animation_start_time = time.monotonic() # Fallback, though should always be passed
    while not stop_animation_event.is_set():
        elapsed_time = time.monotonic() - animation_start_time
        sys.stdout.write(f'\r{label}... {chars[idx % len(chars)]} ({elapsed_time:.1f}s) ')
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * (len(label) + 12 + 7) + '\r') # Adjusted for timer
    sys.stdout.flush()

def run_autopilot_simulation(sim_id, num_turns=10, turn_delay_seconds=5):
    print(f"Starting autopilot simulation for Sim ID: {sim_id} for {num_turns} turns.")
    total_llm_response_time_seconds = 0.0
    llm_calls_count = 0

    # Load scenarios
    try:
        with open('scenarios.json', 'r') as f:
            scenarios = json.load(f)
    except FileNotFoundError:
        logging.error("scenarios.json not found. Please create it.")
        return
    except json.JSONDecodeError:
        logging.error("Error decoding scenarios.json. Please ensure it's valid JSON.")
        return

    # Select a scenario (e.g., the first one or a specific one by key)
    # For now, let's hardcode to use "default_horace_apartment"
    scenario_key = "default_horace_apartment"
    if scenario_key not in scenarios:
        logging.error(f"Scenario '{scenario_key}' not found in scenarios.json.")
        return
    
    scenario_data = scenarios[scenario_key]
    # The sim_id for the simulation is now determined by the scenario
    # This function's sim_id parameter will be set by the caller based on this.
    # However, initialize_game_world will use the sim_id from scenario_data.

    with flask_app.app_context():
        initialize_game_world(scenario_data) # Pass scenario data
        print(f"Game world initialized with scenario: {scenario_data.get('description', scenario_key)}.")

        for turn in range(1, num_turns + 1):
            print(f"\n--- Turn {turn}/{num_turns} for {sim_id} ---")

            sim_state_for_display, objects_in_zone_display, _, _ = get_current_game_state(sim_id)
            if sim_state_for_display:
                print(f"Current state for {sim_state_for_display['name']}:")
                print(f"  Location: {sim_state_for_display['location']}")
                print(f"  Mood: {sim_state_for_display['mood']}")
                print(f"  Needs: {sim_state_for_display['needs']}")
                inventory_list = sim_state_for_display.get('inventory', [])
                inventory_str = ", ".join(inventory_list) if inventory_list else "empty"
                print(f"  Inventory: {inventory_str}")
                
                # Display objects in the current zone
                print(f"  Objects in {sim_state_for_display['location']}:")
                if objects_in_zone_display:
                    for obj in objects_in_zone_display:
                        obj_state_desc = obj.get('states', {}).get(obj.get('current_state_key', ''), 'state unknown')
                        print(f"    - {obj['name']} ({obj_state_desc}) [{obj['_id']}]")
                else:
                    print("    (nothing notable)")
            else:
                print(f"Could not fetch current state for Sim {sim_id}.")

            stop_animation_event.clear()
            animation_thread = None
            action_info = None # Will be a dict {"action": ..., "reason": ...} or None
            
            llm_call_start_time = time.monotonic()
            animation_start_time_suggest = time.monotonic()
            try:
                animation_thread = threading.Thread(target=animate, args=("Horace is deciding what to do", animation_start_time_suggest))
                animation_thread.start()
                action_info = get_llm_suggested_action(sim_id)
            finally:
                stop_animation_event.set()
                if animation_thread:
                    animation_thread.join()
            llm_call_duration = time.monotonic() - llm_call_start_time
            if action_info and action_info.get("action"):
                total_llm_response_time_seconds += llm_call_duration
                llm_calls_count += 1

            if not action_info or not action_info.get("action"):
                print(f"[{sim_id}] LLM did not suggest a valid action. Skipping turn.")
                time.sleep(turn_delay_seconds)
                continue

            suggested_action_str = action_info["action"]
            reason_str = action_info.get("reason", "No reason provided by LLM.")
            print(f"Horace chose action: {suggested_action_str}")
            print(f"Reasoning: {reason_str}")

            action_result_data = None
            status_code = None
            stop_animation_event.clear()
            animation_thread = None
            is_go_to_action = suggested_action_str.lower().startswith("go")

            llm_call_start_time_process = time.monotonic()
            animation_start_time_process = time.monotonic()
            try:
                animation_thread = threading.Thread(target=animate, args=("Game is processing the action", animation_start_time_process))
                animation_thread.start()
                action_result_data, status_code = process_sim_action(sim_id, suggested_action_str)
            finally:
                stop_animation_event.set()
                if animation_thread:
                    animation_thread.join()
            
            llm_call_duration_process = time.monotonic() - llm_call_start_time_process
            if not is_go_to_action and status_code == 200:
                total_llm_response_time_seconds += llm_call_duration_process
                llm_calls_count += 1
            
            if status_code == 200 and action_result_data:
                narrative = action_result_data.get("narrative", "No narrative provided.")
                print(f"Narrative: {narrative}")
            else:
                error_message = action_result_data.get("error", "Unknown error processing action.") if action_result_data else "Unknown error"
                print(f"Error processing action '{suggested_action_str}'. Status: {status_code}. Error: {error_message}")

            print(f"--- End of Turn {turn} ---")
            if turn < num_turns:
                time.sleep(turn_delay_seconds)

    print(f"\nAutopilot simulation for {sim_id} finished after {num_turns} turns.")
    if llm_calls_count > 0:
        average_llm_time = total_llm_response_time_seconds / llm_calls_count
        print(f"Average LLM response time over {llm_calls_count} calls: {average_llm_time:.2f} seconds.")
    else:
        print("No LLM calls were made during the simulation to calculate average time.")

if __name__ == "__main__":
    # Load scenarios to get the sim_id for the default scenario
    try:
        with open('scenarios.json', 'r') as f:
            scenarios_for_main = json.load(f)
        default_scenario_key = "default_horace_apartment" # Ensure this key exists
        if default_scenario_key in scenarios_for_main:
            sim_id_to_run = scenarios_for_main[default_scenario_key]["sim_config"]["sim_id"]
            run_autopilot_simulation(sim_id_to_run, num_turns=365, turn_delay_seconds=3)
        else:
            print(f"Error: Default scenario key '{default_scenario_key}' not found in scenarios.json.")
            # Fallback or exit if necessary. For now, just printing an error.
            # If you want to ensure it runs even if the key is missing, you might need a different approach
            # or ensure DEFAULT_SIM_ID is available as a fallback from app.py if imported.
            # For this refactor, we assume the scenario and sim_id will be correctly loaded.
    except FileNotFoundError:
        print("Error: scenarios.json not found. Autopilot cannot start.")
    except json.JSONDecodeError:
        print("Error: Could not decode scenarios.json. Autopilot cannot start.")
    # Original call: run_autopilot_simulation(DEFAULT_SIM_ID, num_turns=5, turn_delay_seconds=3) 