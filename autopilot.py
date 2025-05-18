import time
import logging
import sys
import threading
from app import get_llm_suggested_action, process_sim_action, initialize_game_world, DEFAULT_SIM_ID, app as flask_app, get_current_game_state

# Configure basic logging for the root logger (e.g., for this script's own direct logging)
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# Explicitly set the Flask app's logger level to WARNING to suppress its DEBUG messages
if flask_app:
    flask_app.logger.setLevel(logging.WARNING)

# --- Animation for waiting ---
stop_animation_event = threading.Event()

def animate(label="Thinking", animation_start_time=None):
    chars = "-\\\|/"
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

    with flask_app.app_context():
        initialize_game_world()
        print("Game world initialized.")

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
    run_autopilot_simulation(DEFAULT_SIM_ID, num_turns=5, turn_delay_seconds=3) 