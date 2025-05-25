from flask import Flask, request, jsonify
from pymongo import MongoClient
from langchain_ollama.llms import OllamaLLM
# from langchain_core.prompts import ChatPromptTemplate # We'll craft prompts directly for JSON
import os
import json # For parsing LLM JSON responses
import re # For stripping <think> tags
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# MongoDB Setup
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/sims_mud_db") # Changed DB name
client = MongoClient(MONGO_URI)
db = client.get_database()
sims_collection = db.sims
environment_collection = db.environment_objects # More specific collection name
apartment_layout_collection = db.apartment_layout # Will store the layout from scenario

# Ollama Setup
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b") # User changed this recently
ollama_llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
app.logger.info(f"Initialized Ollama with model: {OLLAMA_MODEL} at {OLLAMA_BASE_URL}")

# --- Game Constants and Initial State ---
DEFAULT_SIM_ID = "sim_horace" # This might become obsolete or just a fallback if no scenario specifies an ID
RECOGNIZED_VERBS = [
    "go", "walk", "run", "move", # Movement
    "look", "examine", "inspect", "read", # Observation
    "take", "get", "pick up", "grab", # Acquisition
    "drop", "place", "put", # Relinquishing
    "use", "activate", "operate", "interact with", # Interaction
    "open", "close", # State changes
    "eat", "drink", # Consuming
    "sleep", "rest", # Needs recovery
    "talk to", "say", "ask", # Communication (even if to self for now)
    "peel", "combine" # Crafting/preparation
]

def initialize_game_world(scenario_data):
    app.logger.info(f"Initializing game world with scenario: {scenario_data.get('description', 'No description')}")

    sim_config = scenario_data["sim_config"]
    env_config = scenario_data["environment_config"]
    layout_data = env_config["layout"]
    object_definitions = env_config["objects"]
    sim_id_for_inventory = sim_config["sim_id"]

    # Clear existing collections
    apartment_layout_collection.delete_many({})
    sims_collection.delete_many({})
    environment_collection.delete_many({})

    # Initialize layout
    apartment_layout_collection.insert_one(layout_data)
    app.logger.info(f"Initialized layout: {layout_data.get('_id', 'N/A')}")

    # Initialize Sim
    sim_doc_to_insert = sim_config.copy()
    if "sim_id" in sim_doc_to_insert:
        sim_doc_to_insert["_id"] = sim_doc_to_insert.pop("sim_id")
    else:
        # This case should ideally not happen if scenarios are well-formed
        app.logger.warning("Sim config in scenario is missing 'sim_id'. MongoDB will generate an _id.")
        # If an _id is already present, MongoDB will use it. If not, it will generate one.

    sims_collection.insert_one(sim_doc_to_insert)
    app.logger.info(f"Initialized Sim: {sim_doc_to_insert['_id']}") # Log the actual _id used

    # Initialize Environment Objects (with special handling for inventory)
    objects_to_insert = []
    # Use the _id that was actually inserted for the sim for inventory zone consistency
    actual_sim_id_for_inventory = sim_doc_to_insert['_id'] 
    sim_inventory_ids = sim_config.get("inventory", []) # Original sim_config still has inventory list by original object _ids
    
    for obj_def in object_definitions:
        obj_copy = obj_def.copy() # Work on a copy
        if obj_copy["_id"] in sim_inventory_ids:
            obj_copy["zone"] = f"inventory_{actual_sim_id_for_inventory}" # Assign to Sim's inventory zone
        objects_to_insert.append(obj_copy)
    
    if objects_to_insert:
        environment_collection.insert_many(objects_to_insert)
        app.logger.info(f"Initialized {len(objects_to_insert)} environment objects.")
    else:
        app.logger.info("No environment objects defined in scenario to load.")

# --- Helper Functions ---
def get_current_game_state(sim_id):
    sim_state = sims_collection.find_one({"_id": sim_id})
    if not sim_state: # Important check if sim_id from scenario is not found
        app.logger.error(f"Sim state not found for sim_id: {sim_id}")
        return None, None, None, None

    # Fetch objects in the Sim's current zone and inventory
    # Ensure sim_state["location"] exists before querying
    objects_in_zone = []
    if sim_state.get("location"):
        objects_in_zone = list(environment_collection.find({"zone": sim_state["location"]}))
    else:
        app.logger.warning(f"Sim {sim_id} has no location set.")

    inventory_ids = [item_id for item_id in sim_state.get("inventory", [])]
    objects_in_inventory = []
    if inventory_ids:
        # Fetch objects whose _id is in inventory_ids AND their zone indicates they are in this sim's inventory
        # This ensures we only fetch objects that are *truly* in this sim's inventory per their current state in the DB.
        # The scenario initialization should have set their zone to inventory_<sim_id>.
        objects_in_inventory = list(environment_collection.find({
            "_id": {"$in": inventory_ids},
            "zone": f"inventory_{sim_id}"
        }))
    
    # The layout ID might come from the scenario, or we assume a single layout doc for now.
    # For simplicity, let's assume the layout inserted by initialize_game_world is the one to use.
    # If multiple layouts were possible, we'd need a way to identify which one is active.
    layout = apartment_layout_collection.find_one({}) # Finds the currently loaded layout
    if not layout:
        app.logger.error("No apartment layout found in the database.")

    return sim_state, objects_in_zone, objects_in_inventory, layout

def validate_llm_json_response(llm_json):
    if not isinstance(llm_json, dict):
        return False, "LLM response is not a JSON object."
    if "narrative" not in llm_json or not isinstance(llm_json["narrative"], str):
        return False, "LLM JSON missing or invalid 'narrative' field."
    if "sim_state_updates" not in llm_json or not isinstance(llm_json["sim_state_updates"], dict):
        return False, "LLM JSON missing or invalid 'sim_state_updates' field."
    if "environment_updates" not in llm_json or not isinstance(llm_json["environment_updates"], list):
        return False, "LLM JSON missing or invalid 'environment_updates' field."
    # Add more checks as needed for specific fields within updates
    return True, "Valid JSON structure."

def generate_sim_decision_prompt(sim_state, objects_in_zone, objects_in_inventory, apartment_layout):
    sim_name = sim_state['name']
    sim_location = sim_state['location']
    zone_description = apartment_layout['zones'][sim_location]['description']
    sim_mood = sim_state['mood']
    needs = sim_state['needs']
    current_activity = sim_state['current_activity']
    
    inventory_details = [f"{obj['name']} ({obj['states'][obj['current_state_key']]}) [{obj['_id']}]" for obj in objects_in_inventory]
    inventory_str = ", ".join(inventory_details) if inventory_details else "nothing"

    zone_object_details = [f"{obj['name']} ({obj['states'][obj['current_state_key']]}) [{obj['_id']}]" for obj in objects_in_zone]
    zone_objects_str = ", ".join(zone_object_details) if zone_object_details else "nothing notable"
    
    available_object_ids = [obj['_id'] for obj in objects_in_zone + objects_in_inventory]
    
    current_zone_connections = apartment_layout['zones'][sim_location].get('connections', [])
    connections_str = ", ".join(current_zone_connections) if current_zone_connections else "nowhere"

    prompt = (
        f"You are an AI controlling a character named {sim_name} in a simulated world.\\n"
        f"Your task is to decide what {sim_name} does next and provide a brief reason for that choice. Consider their needs, mood, and what's around them.\\n\\n"
        f"CURRENT SITUATION FOR {sim_name.upper()}:\\n"
        f"- Location: In the {sim_location} ({zone_description}).\\n"
        f"- Mood: {sim_mood}.\\n"
        f"- Needs: Hunger {needs['hunger']}/100, Energy {needs['energy']}/100, Fun {needs['fun']}/100, Social {needs['social']}/100.\\n"
        f"- Current Activity: {current_activity}.\\n"
        f"- Inventory: {inventory_str}.\\n"
        f"- Objects in {sim_location}: {zone_objects_str}.\\n"
        f"- Available Object IDs for interaction: {str(available_object_ids)}.\\n"
        f"- Can move from {sim_location} to: {connections_str}.\\n\\n"
        f"PRIORITIZE ACTIONS BASED ON NEEDS. For example:\\n"
        f"- If hunger is low (e.g., < 40), try to find and eat food.\\n"
        f"- If energy is low (e.g., < 40), try to sleep or rest.\\n"
        f"- If fun or social is low, try to do something enjoyable or interact.\\n"
        f"- Otherwise, explore, examine things, or maintain the environment.\\n\\n"
        f"RESPONSE FORMAT: Respond ONLY with a valid JSON object following this exact structure:\\n"
        f'{{\\n'
        f'  "action": "(string, the chosen action phrase for {sim_name}, e.g., \\\\"eat obj_banana\\\\", \\\\"go to Sleeping Area\\\\")",\\n'
        f'  "reason": "(string, a brief explanation for why this action was chosen, e.g., \\\\"Horace is hungry and a banana is available.\\\\")"\\n'
        f'}}\\n'
        f"CRITICAL: Ensure the JSON is complete and well-formed. Your response MUST start with \'{{\' and end with \'}}\'. ABSOLUTELY NO TEXT OR EXPLANATION BEFORE OR AFTER THE JSON OBJECT.\\n\\n"
        f"What does {sim_name} do next and why?"
    )
    return prompt

def get_llm_suggested_action(sim_id):
    sim_state, objects_in_zone, objects_in_inventory, apartment_layout = get_current_game_state(sim_id)
    
    if not sim_state:
        # app.logger.error(f"Cannot generate action for non-existent sim_id: {sim_id}") # Already WARNING in autopilot
        return None

    prompt = generate_sim_decision_prompt(sim_state, objects_in_zone, objects_in_inventory, apartment_layout)
    # app.logger.debug(f"Action Generation Prompt for {sim_id}:\\n{prompt}") # Commented out

    try:
        raw_llm_response = ollama_llm.invoke(prompt)
        # app.logger.debug(f"Raw LLM Action Suggestion for {sim_id}: {raw_llm_response}") # Commented out

        # Remove <think>...</think> blocks first
        cleaned_response_no_think = re.sub(r"<think>.*?</think>", "", raw_llm_response, flags=re.DOTALL).strip()

        # Attempt to find and parse a JSON block from the cleaned response
        json_string = None
        try:
            json_start_index = cleaned_response_no_think.find('{')
            json_end_index = cleaned_response_no_think.rfind('}')
            
            if json_start_index != -1 and json_end_index != -1 and json_start_index < json_end_index:
                json_string = cleaned_response_no_think[json_start_index : json_end_index + 1]
                parsed_json = json.loads(json_string)
                if isinstance(parsed_json, dict) and "action" in parsed_json and "reason" in parsed_json:
                    action = str(parsed_json["action"]).strip()
                    reason = str(parsed_json["reason"]).strip()
                    if action: # Ensure action is not empty
                        app.logger.info(f"LLM suggested action for {sim_id}: '{action}' because '{reason}'")
                        return {"action": action, "reason": reason}
            
            # If direct JSON block parsing failed or didn't find the right keys
            app.logger.warning(f"Could not parse valid action/reason JSON from LLM response for {sim_id} after stripping think tags. Cleaned response: {cleaned_response_no_think}. Extracted JSON string: {json_string}")
            return None

        except json.JSONDecodeError as e:
            app.logger.warning(f"JSONDecodeError for action suggestion {sim_id}: {e}. Cleaned response after stripping think tags: {cleaned_response_no_think}. Extracted JSON string: '{json_string if json_string else 'N/A'}'.")
            return None

    except Exception as e:
        # app.logger.error(f"Error invoking LLM for action suggestion: {e}") # Already WARNING in autopilot
        return None

# --- API Endpoints ---
@app.route('/')
def home():
    return "Welcome to the Sims MUD API - Evolved!"

@app.route('/game/full_state', methods=['GET'])
def get_full_game_state_api(): # Renamed from /game/state for clarity
    sim_state = sims_collection.find_one({"_id": DEFAULT_SIM_ID})
    all_objects = list(environment_collection.find({}))
    layout = apartment_layout_collection.find_one({"_id": "studio_apartment"})
    if not sim_state or not layout:
        return jsonify(error="Game state not found. Initialize first."), 404
    return jsonify(sim=sim_state, all_objects=all_objects, layout=layout)

def process_sim_action(sim_id, player_action_text):
    app.logger.info(f"Processing action for Sim {sim_id}: '{player_action_text}'")

    sim_state, objects_in_zone, objects_in_inventory, apartment_layout = get_current_game_state(sim_id)

    if not sim_state or not apartment_layout:
        app.logger.error(f"Game state not found for Sim {sim_id} or apartment layout missing.")
        return {"error": "Game state not found for Sim or apartment layout missing."}, 500

    # Handle 'go to' action (case-insensitive for target zone)
    first_word_action = player_action_text.split(" ", 1)[0].lower()
    if first_word_action == "go" or player_action_text.lower().startswith("go to "):
        previous_activity = sim_state.get("current_activity", "")
        previous_location_name = sim_state.get("location", "") # For finding the object Sim was using
        environment_updates_for_go = []

        if player_action_text.lower().startswith("go to "):
            target_zone_input = player_action_text[len("go to "):].strip()
        elif len(player_action_text.split()) > 1:
            target_zone_input = player_action_text.split(" ", 1)[1].strip()
        else:
            return {"narrative": "Where do you want to go? Specify a location, like 'go to Kitchenette'"}, 200
            
        current_zone_name = sim_state["location"]
        current_zone_details = apartment_layout["zones"].get(current_zone_name)

        if not current_zone_details:
            app.logger.error(f"Sim's current zone '{current_zone_name}' not found in layout!")
            return {"error": "Sim's current location is invalid."}, 500

        matched_zone_name = None
        for zone_name_in_layout in apartment_layout["zones"].keys():
            if zone_name_in_layout.lower() == target_zone_input.lower():
                matched_zone_name = zone_name_in_layout
                break
        
        if matched_zone_name and matched_zone_name in current_zone_details.get("connections", []):
            # Check if Sim was using an object that needs to be vacated
            # Example: If activity was "sitting on obj_sofa"
            activity_match = re.search(r"(obj_[a-zA-Z0-9_]+)", previous_activity) # General object ID extraction
            if activity_match:
                interacted_obj_id = activity_match.group(1)
                # Ensure object is in the Sim's previous location before trying to update it
                obj_to_vacate = environment_collection.find_one({"_id": interacted_obj_id, "zone": previous_location_name})
                
                if obj_to_vacate:
                    app.logger.debug(f"Sim {sim_id} was using {interacted_obj_id} ({obj_to_vacate.get('name')}) with activity: {previous_activity}")
                    # Specific logic for Sofa
                    if obj_to_vacate.get("name") == "Sofa" and obj_to_vacate.get("current_state_key") == "occupied":
                        environment_collection.update_one({"_id": interacted_obj_id}, {"$set": {"current_state_key": "empty"}})
                        environment_updates_for_go.append({
                            "object_id": interacted_obj_id, 
                            "new_state_key": "empty", 
                            "new_zone": None, 
                            "add_to_contains": None, 
                            "remove_from_contains": None
                        })
                        app.logger.info(f"Sofa {interacted_obj_id} vacated by {sim_id} upon moving.")
                    # Add more object-specific vacating logic here (e.g., for beds)

            new_sim_activity = f"moving to {matched_zone_name}"
            sims_collection.update_one({"_id": sim_id}, {"$set": {"location": matched_zone_name, "current_activity": new_sim_activity}})
            return {
                "narrative": f"{sim_state['name']} walks from the {current_zone_name} to the {matched_zone_name}.",
                "sim_state_updates": {"location": matched_zone_name, "current_activity": new_sim_activity},
                "environment_updates": environment_updates_for_go, # Include updates for vacated objects
                "available_actions": [f"look around in {matched_zone_name}", f"examine <object in {matched_zone_name}>"],
            }, 200
        else:
            return {"narrative": f"You can't go directly to {target_zone_input} from {current_zone_name}. Possible exits: {', '.join(current_zone_details.get('connections',[]))}"}, 200
    
    # --- Construct Prompt for LLM (demanding JSON) ---
    objects_in_zone_str = ", ".join([f"{obj['name']} ({obj['states'][obj['current_state_key']]}) [{obj['_id']}]" for obj in objects_in_zone]) if objects_in_zone else "nothing notable"
    objects_in_inventory_str = ", ".join([f"{obj['name']} ({obj['states'][obj['current_state_key']]}) [{obj['_id']}]" for obj in objects_in_inventory]) if objects_in_inventory else "empty"
    available_object_ids_str = str([obj['_id'] for obj in objects_in_zone + objects_in_inventory])

    prompt_context = (
        f"The Sim, {sim_state['name']}, is in the {sim_state['location']}.\n"
        f"Description of current zone ({sim_state['location']}): {apartment_layout['zones'][sim_state['location']]['description']}.\n"
        f"Sim's current mood: {sim_state['mood']}. Needs: Hunger {sim_state['needs']['hunger']}, Energy {sim_state['needs']['energy']}.\n"
        f"Objects in this zone (object_name (current_state) [object_id]): [{objects_in_zone_str}].\n"
        f"Sim's inventory (object_name (current_state) [object_id]): [{objects_in_inventory_str}].\n"
        f"Available object IDs in current context (zone and inventory): {available_object_ids_str}.\n\n"
        f"Player action: '{player_action_text}'\n\n"
        f"Your primary goal is to determine the outcome of this action. Respond in a narrative-driven way.\n"
        f"1. For sensible actions: Describe a realistic outcome and make appropriate state changes (mood, needs, object states, inventory) consistent with the Sim's abilities and object properties.\n"
        f"2. For actions that are illogical or interact with objects in unintended ways (e.g., 'talk to lamp', 'peel the fridge'): Describe the Sim's attempt, perhaps humorously. State changes should be minimal (e.g., mood change to 'confused' or 'amused', slight energy use). Do NOT change fundamental object states or Sim needs in ways that defy logic (e.g., hunger decreasing from 'eating' a computer).\n"
        f"3. For actions that are truly impossible due to game rules you should infer (e.g., trying to move into a wall, 'eat sofa' if sofa is clearly not food): The narrative should describe the Sim realizing they can't do that, or briefly attempting and failing. Propose no significant state changes, or only a slight mood change (e.g., 'frustrated').\n"
        f"Focus on maintaining a believable simulation overall, but allow for some characterful quirks in how the Sim interacts with the world when actions are odd. Use the object properties and descriptions provided.\n\n"
        f"Respond ONLY with a valid JSON object following this exact structure:\n"
        f"{{\n"
        f"  \"narrative\": \"A concise, present-tense description of what happens. If the action is absurd, describe the attempt and outcome creatively.\",\n"
        f"  \"sim_state_updates\": {{\n"
        f"    \"location\": \"(string, new zone name if changed, otherwise null)\",\n"
        f"    \"mood\": \"(string, new mood if changed, otherwise null)\",\n"
        f"    \"needs_delta\": {{ \"hunger\": <int>, \"energy\": <int>, \"fun\": <int> }} (changes to needs, e.g. hunger: -10 means less hungry; only include needs that changed, 0 if no change to a specific need but other needs changed),\n"
        f"    \"inventory_add\": \"(string, ID of object added, e.g., obj_banana, MUST be from 'Available object IDs' list or a newly created/transformed object ID, otherwise null)\",\n"
        f"    \"inventory_remove\": \"(string, ID of object removed, e.g., obj_banana_peel, MUST be from 'Available object IDs' list, otherwise null)\",\n"
        f"    \"current_activity\": \"(string, brief description of new activity, otherwise null)\"\n"
        f"  }},\n"
        f"  \"environment_updates\": [\n"
        f"    // For each object affected by the action:\n"
        f"    {{ \n"
        f"      \"object_id\": \"(string, ID of object affected, e.g., obj_fridge, MUST be from 'Available object IDs' list)\", \n"
        f"      \"new_state_key\": \"(string, key of new state for the object, from its defined states, otherwise null)\", \n"
        f"      \"new_zone\": \"(string, new zone ID if object moved, e.g., inventory_{sim_id} or another zone ID, otherwise null)\", \n"
        f"      \"add_to_contains\": \"(string, ID of object to add to this object's container, MUST be from 'Available object IDs' or new, otherwise null)\", \n"
        f"      \"remove_from_contains\": \"(string, ID of object to remove from this object's container, MUST be from 'Available object IDs', otherwise null)\" \n"
        f"    }}\n"
        f"    // ... more objects if affected. Only include objects that actually change.\n"
        f"  ],\n"
        f"  \"available_actions\": [\"(string, suggested action 1, should be a plausible next action for the Sim)\", \"(string, suggested action 2)\", \"(string, suggested action 3)\"]\n"
        f"}}\n"
        f"CRITICAL: Ensure the JSON is complete and well-formed. No other text before or after the JSON.\n"
        f"Object ID Usage: When updating `sim_state_updates` (inventory) or `environment_updates` (object_id, add_to_contains, remove_from_contains), YOU MUST use the exact object IDs (e.g., `obj_banana`, `obj_fridge`) provided in the 'Objects in this zone' or 'Sim\'s inventory' lists, or a new ID if an object is created/transformed. Do NOT use object names.\n\n"
        f"Example of correct Object ID usage if Hoarace takes Banana (obj_banana) from Fridge (obj_fridge):\n"
        f"  \"sim_state_updates\": {{ ... \"inventory_add\": \"obj_banana\" ... }},\n"
        f"  \"environment_updates\": [\n"
        f"    {{ \"object_id\": \"obj_fridge\", \"new_state_key\": null, \"new_zone\": null, \"add_to_contains\": null, \"remove_from_contains\": \"obj_banana\" }}, // Fridge contents changed\n"
        f"    {{ \"object_id\": \"obj_banana\", \"new_state_key\": null, \"new_zone\": \"inventory_{sim_id}\", \"add_to_contains\": null, \"remove_from_contains\": null }}  // Banana location changed\n"
        f"  ]\n\n"
        f"If an action is valid but has no major effect (e.g., \"look at wall\"), the narrative should reflect that, and state_updates can be minimal or null.\n"
        f"Now, process the action: '{player_action_text}'"
    )

    # app.logger.debug(f"LLM Prompt:\n{prompt_context}") # Commented out for cleaner autopilot

    # --- Send to LLM and Get JSON Response ---
    try:
        raw_llm_response = ollama_llm.invoke(prompt_context)
        # app.logger.debug(f"Raw LLM Response:\n{raw_llm_response}") # Commented out for cleaner autopilot
        
        # Remove <think>...</think> blocks first, similar to get_llm_suggested_action
        cleaned_response_no_think = re.sub(r"<think>.*?</think>", "", raw_llm_response, flags=re.DOTALL).strip()
        # app.logger.debug(f"Cleaned LLM Response (no think tags):\\n{cleaned_response_no_think}")

        # Extract JSON block from the cleaned response
        json_string = None
        try:
            json_start_index = cleaned_response_no_think.find('{')
            json_end_index = cleaned_response_no_think.rfind('}')
            
            if json_start_index != -1 and json_end_index != -1 and json_start_index < json_end_index:
                json_string = cleaned_response_no_think[json_start_index : json_end_index + 1]
                # app.logger.debug(f"Extracted JSON String:\\n{json_string}") # Commented out for cleaner autopilot
                llm_json = json.loads(json_string)
            else:
                app.logger.error(f"Could not find valid JSON block in cleaned LLM response. Cleaned response: {cleaned_response_no_think}")
                return {"error": "Could not find valid JSON block in cleaned LLM response.", "llm_raw": raw_llm_response, "cleaned_response": cleaned_response_no_think}, 500
        except json.JSONDecodeError as e:
            app.logger.error(f"LLM response (after cleaning think tags) was not valid JSON: {e}. Extracted string: '{json_string if json_string else 'N/A'}'. Cleaned response: {cleaned_response_no_think}")
            return {"error": "LLM response (after cleaning) was not valid JSON.", "llm_raw": raw_llm_response, "cleaned_response": cleaned_response_no_think, "attempted_parse": json_string if json_string else None}, 500

        is_valid, validation_msg = validate_llm_json_response(llm_json)
        if not is_valid:
            app.logger.error(f"LLM JSON failed validation: {validation_msg}. JSON: {llm_json}")
            return {"error": f"LLM JSON failed validation: {validation_msg}", "llm_json": llm_json}, 500

    except Exception as e:
        app.logger.error(f"Error invoking LLM or processing its response: {e}")
        return {"error": f"Error communicating with LLM: {str(e)}"}, 500

    # --- Apply State Updates from LLM JSON ---
    sim_updates = llm_json.get("sim_state_updates", {})
    db_sim_update_ops = {}
    if sim_updates.get("location"):
        db_sim_update_ops["location"] = sim_updates["location"]
    if sim_updates.get("mood"):
        db_sim_update_ops["mood"] = sim_updates["mood"]
    if sim_updates.get("current_activity"):
        db_sim_update_ops["current_activity"] = sim_updates["current_activity"]
    
    needs_delta = sim_updates.get("needs_delta", {})
    for need, delta in needs_delta.items():
        if isinstance(delta, int) and need in sim_state["needs"]:
            current_need_value = sims_collection.find_one({"_id": sim_id}, {f"needs.{need}": 1})["needs"][need]
            db_sim_update_ops[f"needs.{need}"] = max(0, min(100, current_need_value + delta))

    if sim_updates.get("inventory_add"):
        obj_id_to_add = sim_updates["inventory_add"]
        sims_collection.update_one({"_id": sim_id}, {"$addToSet": {"inventory": obj_id_to_add}})
        app.logger.info(f"Added {obj_id_to_add} to {sim_id} inventory per LLM.")

    if sim_updates.get("inventory_remove"):
        obj_id_to_remove = sim_updates["inventory_remove"]
        sims_collection.update_one({"_id": sim_id}, {"$pull": {"inventory": obj_id_to_remove}})
        app.logger.info(f"Removed {obj_id_to_remove} from {sim_id} inventory per LLM.")

    if db_sim_update_ops:
        sims_collection.update_one({"_id": sim_id}, {"$set": db_sim_update_ops})
        app.logger.debug(f"Applied Sim updates for {sim_id}: {db_sim_update_ops}")

    env_updates = llm_json.get("environment_updates", [])
    for update_info in env_updates:
        obj_id = update_info.get("object_id")
        if not obj_id:
            app.logger.warning(f"Skipping env update with no object_id: {update_info}")
            continue
        
        target_object = environment_collection.find_one({"_id": obj_id})
        if not target_object:
            app.logger.warning(f"Skipping env update for unknown object_id: {obj_id}. Update info: {update_info}")
            continue
            
        db_env_update_ops = {}
        new_state_key_from_llm = update_info.get("new_state_key")
        if new_state_key_from_llm:
            if new_state_key_from_llm in target_object.get("states", {}):
                db_env_update_ops["current_state_key"] = new_state_key_from_llm
            else:
                app.logger.warning(f"LLM proposed invalid state '{new_state_key_from_llm}' for object {obj_id} ('{target_object.get('name')}'). Valid states: {list(target_object.get('states', {}).keys())}. State not changed.")

        if update_info.get("new_zone"):
            db_env_update_ops["zone"] = update_info["new_zone"]
        
        if update_info.get("add_to_contains"):
            environment_collection.update_one({"_id": obj_id}, {"$addToSet": {"contains": update_info["add_to_contains"]}})
        if update_info.get("remove_from_contains"):
            environment_collection.update_one({"_id": obj_id}, {"$pull": {"contains": update_info["remove_from_contains"]}})

        if db_env_update_ops:
            environment_collection.update_one({"_id": obj_id}, {"$set": db_env_update_ops})
            app.logger.debug(f"Applied Env object update for {obj_id}: {db_env_update_ops}")

    return llm_json, 200

@app.route('/game/action', methods=['POST'])
def handle_action():
    data = request.get_json()
    if not data or 'action' not in data or 'sim_id' not in data:
        return jsonify(error="'action' and 'sim_id' are required"), 400

    player_action_text = data['action'].strip()
    sim_id = data['sim_id']
    
    result_data, status_code = process_sim_action(sim_id, player_action_text)
    
    return jsonify(result_data), status_code

if __name__ == '__main__':
    # app.run() is for the Flask server. 
    # Direct initialization for testing here would need a default scenario_data.
    # For now, initialization is primarily handled by autopilot.py or a direct call with scenario data.
    # Example: 
    # with open('scenarios.json', 'r') as f:
    #     scenarios = json.load(f)
    # default_scenario = scenarios["default_horace_apartment"]
    # with app.app_context():
    # initialize_game_world(default_scenario)
    app.run(debug=True, host='0.0.0.0', port=5001) 