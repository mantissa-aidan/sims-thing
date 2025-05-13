from flask import Flask, request, jsonify
from pymongo import MongoClient
from langchain_ollama.llms import OllamaLLM
# from langchain_core.prompts import ChatPromptTemplate # We'll craft prompts directly for JSON
import os
import json # For parsing LLM JSON responses
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# MongoDB Setup
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/sims_mud_db") # Changed DB name
client = MongoClient(MONGO_URI)
db = client.get_database()
sims_collection = db.sims
environment_collection = db.environment_objects # More specific collection name
apartment_layout_collection = db.apartment_layout

# Ollama Setup
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b") # User changed this recently
ollama_llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
app.logger.info(f"Initialized Ollama with model: {OLLAMA_MODEL} at {OLLAMA_BASE_URL}")

# --- Game Constants and Initial State ---
DEFAULT_SIM_ID = "sim_alex"
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

def get_initial_apartment_layout():
    return {
        "_id": "studio_apartment",
        "name": "Alex's Studio Apartment",
        "zones": {
            "Sleeping Area": {
                "description": "A cozy corner with a neatly made bed and a nightstand.",
                "connections": ["Living Area"],
                "coordinates": {"x": 1, "y": 1} # Example, if we go grid-based later
            },
            "Living Area": {
                "description": "A comfortable area with a sofa, a coffee table, and a bookshelf.",
                "connections": ["Sleeping Area", "Kitchenette", "Desk Area"],
                "coordinates": {"x": 2, "y": 1}
            },
            "Kitchenette": {
                "description": "A small but functional kitchenette with a fridge, a counter, and a sink.",
                "connections": ["Living Area"],
                "coordinates": {"x": 3, "y": 1}
            },
            "Desk Area": {
                "description": "A tidy desk with a computer, a lamp, and an office chair.",
                "connections": ["Living Area"],
                "coordinates": {"x": 2, "y": 2}
            }
            # Bathroom could be added later
        }
    }

def get_initial_sim_state():
    return {
        "_id": DEFAULT_SIM_ID,
        "name": "Alex",
        "location": "Living Area", # Starting zone
        "mood": "neutral",
        "needs": {"hunger": 50, "energy": 70, "social": 60, "fun": 40},
        "inventory": [],
        "current_activity": "idle"
    }

def get_initial_environment_objects():
    return [
        # Sleeping Area Objects
        {"_id": "obj_bed", "name": "Bed", "zone": "Sleeping Area", "current_state_key": "made",
         "states": {"made": "The bed is neatly made.", "unmade": "The bed is unmade, covers rumpled."}, 
         "interactions": ["sleep in", "make bed", "sit on"]},
        # Kitchenette Objects
        {"_id": "obj_fridge", "name": "Fridge", "zone": "Kitchenette", "current_state_key": "closed",
         "states": {"closed": "The fridge is closed.", "open": "The fridge is open, a cool light emanating from within."},
         "interactions": ["open", "close", "look inside", "take item from"],
         "contains": ["obj_milk", "obj_banana"] # IDs of other objects
        },
        {"_id": "obj_banana", "name": "Banana", "zone": "Fridge", "current_state_key": "whole", # Initial location is *inside* fridge
         "states": {
             "whole": "a ripe, yellow banana.", 
             "peeled": "a peeled banana, ready to eat.",
             "eaten": "the banana peel."
         },
         "interactions": ["take", "peel", "eat", "examine"], # take will move it to inventory/hand
         "properties": {"edible": True, "requires_peeling": True}
        },
        {"_id": "obj_milk", "name": "Milk Carton", "zone": "Fridge", "current_state_key": "sealed",
         "states": {"sealed": "a sealed carton of milk.", "open": "an open carton of milk."}, 
         "interactions": ["take", "open", "pour", "drink from"], 
         "properties": {"drinkable": True, "capacity_ml": 1000, "current_ml": 1000}
        },
        # Living Area Objects
        {"_id": "obj_sofa", "name": "Sofa", "zone": "Living Area", "current_state_key": "empty",
         "states": {"empty": "The sofa looks inviting.", "occupied": "Someone is sitting on the sofa."},
         "interactions": ["sit on", "lie down on", "get up from"]},
        # Desk Area Objects
        {"_id": "obj_computer", "name": "Computer", "zone": "Desk Area", "current_state_key": "off",
         "states": {"off": "The computer is off.", "on": "The computer screen is glowing." },
         "interactions": ["use computer", "turn on computer", "turn off computer", "check email", "browse web"]},
        {"_id": "obj_desk_lamp", "name": "Desk Lamp", "zone": "Desk Area", "current_state_key": "off",
         "states": {"off": "The desk lamp is off.", "on": "The desk lamp brightly illuminates the desk."},
         "interactions": ["turn on", "turn off"]} # Added a desk lamp too for more interaction
    ]

def initialize_game_world():
    if not apartment_layout_collection.count_documents({}):
        apartment_layout_collection.insert_one(get_initial_apartment_layout())
        app.logger.info("Initialized apartment layout.")
    
    if not sims_collection.count_documents({}):
        sims_collection.insert_one(get_initial_sim_state())
        app.logger.info(f"Initialized Sim: {DEFAULT_SIM_ID}")

    # Clear and re-initialize objects for simplicity during dev
    environment_collection.delete_many({})
    initial_objects = get_initial_environment_objects()
    if initial_objects:
        environment_collection.insert_many(initial_objects)
        app.logger.info(f"Initialized {len(initial_objects)} environment objects.")
    else:
        app.logger.info("No initial environment objects to load.")


# --- Helper Functions ---
def get_current_game_state(sim_id):
    sim_state = sims_collection.find_one({"_id": sim_id})
    # Fetch objects in the Sim's current zone and inventory
    objects_in_zone = list(environment_collection.find({"zone": sim_state["location"]}))
    inventory_ids = [item_id for item_id in sim_state.get("inventory", [])]
    objects_in_inventory = []
    if inventory_ids:
        objects_in_inventory = list(environment_collection.find({"_id": {"$in": inventory_ids}}))
    
    apartment_layout = apartment_layout_collection.find_one({"_id": "studio_apartment"})
    return sim_state, objects_in_zone, objects_in_inventory, apartment_layout

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

@app.route('/game/action', methods=['POST'])
def handle_action():
    data = request.get_json()
    if not data or 'action' not in data or 'sim_id' not in data:
        return jsonify(error="'action' and 'sim_id' are required"), 400

    player_action_text = data['action'].strip()
    sim_id = data['sim_id']
    app.logger.info(f"Sim {sim_id} action received: '{player_action_text}'")

    sim_state, objects_in_zone, objects_in_inventory, apartment_layout = get_current_game_state(sim_id)

    if not sim_state or not apartment_layout:
        return jsonify(error="Game state not found for Sim or apartment layout missing."), 500

    # --- Action Pre-validation (Python-side) ---
    action_verb = player_action_text.split(" ", 1)[0].lower()
    verb_recognized = any(action_verb == verb or player_action_text.lower().startswith(verb + " ") for verb in RECOGNIZED_VERBS)

    if not verb_recognized:
        app.logger.warning(f"Action '{player_action_text}' does not start with a recognized verb.")
        return jsonify({
            "narrative": f"Hmm, '{player_action_text}' doesn't seem to start with a clear action verb. Try starting your command with a verb like 'go', 'look', 'take', 'use', etc.",
            "sim_state_updates": {},
            "environment_updates": [],
            "available_actions": [] # Could suggest some common verbs here
        }), 200 # Return 200 as it's a parsable game response, not a server error

    # Example: 'go to Kitchenette' - Specific handling for 'go' verb
    if action_verb == "go" or player_action_text.lower().startswith("go to "):
        # Extract target zone more carefully
        if player_action_text.lower().startswith("go to "):
            target_zone = player_action_text[len("go to "):].strip()
        elif len(player_action_text.split()) > 1:
            target_zone = player_action_text.split(" ", 1)[1].strip()
        else:
            return jsonify({"narrative": "Where do you want to go? Specify a location, like 'go to Kitchenette'"}), 200
            
        current_zone_name = sim_state["location"]
        current_zone_details = apartment_layout["zones"].get(current_zone_name)

        if not current_zone_details:
            app.logger.error(f"Sim's current zone '{current_zone_name}' not found in layout!")
            return jsonify(error="Sim's current location is invalid."), 500

        if target_zone in current_zone_details.get("connections", []):
            sims_collection.update_one({"_id": sim_id}, {"$set": {"location": target_zone, "current_activity": f"going to {target_zone}"}})
            # Get updated sim_state to reflect the change immediately if needed for available_actions by LLM
            # For now, just return direct python response
            return jsonify({
                "narrative": f"{sim_state['name']} walks from the {current_zone_name} to the {target_zone}.",
                "sim_state_updates": {"location": target_zone, "current_activity": f"going to {target_zone}"},
                "environment_updates": [],
                "available_actions": [f"look around in {target_zone}", f"examine <object in {target_zone}>"] # Simple python-generated suggestions
            }), 200
        else:
            return jsonify({"narrative": f"You can't go directly to {target_zone} from {current_zone_name}. Possible exits: {', '.join(current_zone_details.get('connections',[]))}"}), 200
    
    # --- Construct Prompt for LLM (demanding JSON) ---
    prompt_context = f"""
The Sim, {sim_state['name']}, is in the {sim_state['location']}. 
Description of current zone ({sim_state['location']}): {apartment_layout['zones'][sim_state['location']]['description']}.
Sim's current mood: {sim_state['mood']}. Needs: Hunger {sim_state['needs']['hunger']}, Energy {sim_state['needs']['energy']}.
Objects in this zone: [{', '.join([obj['name'] + ' (' + obj['states'][obj['current_state_key']] + ')' for obj in objects_in_zone]) if objects_in_zone else 'nothing notable' }].
Sim's inventory: [{', '.join([obj['name'] + ' (' + obj['states'][obj['current_state_key']] + ')' for obj in objects_in_inventory]) if objects_in_inventory else 'empty'}].

Player action: '{player_action_text}' (This action has been validated to start with a recognized verb: '{action_verb}').

Consider the Sim's state, the environment, and the action. 
Respond ONLY with a valid JSON object following this structure:
{{
  "narrative": "A concise, present-tense description of what happens as a result of the action. If the action is impossible or doesn't make sense given the current context (even if it starts with a verb), explain why in the narrative.",
  "sim_state_updates": {{
    "location": "(string, new zone name if changed, otherwise null)",
    "mood": "(string, new mood if changed, otherwise null)",
    "needs_delta": {{"hunger": <int>, "energy": <int>, "fun": <int>}} (changes to needs, e.g. hunger: -10 means less hungry, only include changed needs),
    "inventory_add": "(string, ID of object added if any, e.g., obj_banana, otherwise null)",
    "inventory_remove": "(string, ID of object removed if any, e.g., obj_banana_peel, otherwise null)",
    "current_activity": "(string, brief description of new activity, otherwise null)"
  }},
  "environment_updates": [
    {{ "object_id": "(string, ID of object affected, e.g., obj_fridge)", "new_state_key": "(string, key of new state for the object)", "new_zone": "(string, new zone if object moved, e.g., to inventory_sim_alex or another zone, otherwise null)", "add_to_contains": "(string, ID of object to add to container, otherwise null)", "remove_from_contains": "(string, ID of object to remove from container, otherwise null)" }}
    // ... more objects if affected
  ],
  "available_actions": ["(string, suggested action 1)", "(string, suggested action 2)", "(string, suggested action 3)"] // LLM should suggest 3 contextually relevant actions that start with a verb.
}}
Ensure the JSON is complete and well-formed. No other text before or after the JSON. 
If an action is valid but has no major effect, the narrative should reflect that, and state_updates can be minimal or null.
Make sure object IDs (like obj_banana, obj_fridge) are used in sim_state_updates (inventory) and environment_updates (object_id, add_to_contains, remove_from_contains).
For example, if Alex takes the Banana (obj_banana) from the Fridge (obj_fridge):
  "sim_state_updates": {{ ... "inventory_add": "obj_banana" ... }},
  "environment_updates": [
    {{ "object_id": "obj_fridge", "remove_from_contains": "obj_banana" }},
    {{ "object_id": "obj_banana", "new_zone": "inventory_sim_alex" }}
  ]
Now, process the action: '{player_action_text}'
"""

    app.logger.debug(f"LLM Prompt:\n{prompt_context}")

    # --- Send to LLM and Get JSON Response ---
    try:
        raw_llm_response = ollama_llm.invoke(prompt_context)
        app.logger.debug(f"Raw LLM Response:\n{raw_llm_response}")
        
        # Extract JSON block from the raw response
        try:
            # Find the start and end of the main JSON object
            json_start_index = raw_llm_response.find('{')
            json_end_index = raw_llm_response.rfind('}')
            
            if json_start_index != -1 and json_end_index != -1 and json_start_index < json_end_index:
                json_string = raw_llm_response[json_start_index : json_end_index + 1]
                app.logger.debug(f"Extracted JSON String:\n{json_string}")
                llm_json = json.loads(json_string)
            else:
                app.logger.error(f"Could not find valid JSON block in LLM response. Response: {raw_llm_response}")
                return jsonify(error="Could not find valid JSON block in LLM response.", llm_raw=raw_llm_response), 500
        except json.JSONDecodeError as e:
            app.logger.error(f"LLM response was not valid JSON: {e}. Extracted string: '{json_string if 'json_string' in locals() else 'N/A'}'. Raw response: {raw_llm_response}")
            return jsonify(error="LLM response was not valid JSON.", llm_raw=raw_llm_response, attempted_parse=json_string if 'json_string' in locals() else None), 500

        is_valid, validation_msg = validate_llm_json_response(llm_json)
        if not is_valid:
            app.logger.error(f"LLM JSON failed validation: {validation_msg}. JSON: {llm_json}")
            return jsonify(error=f"LLM JSON failed validation: {validation_msg}", llm_json=llm_json), 500

    except Exception as e:
        app.logger.error(f"Error invoking LLM or processing its response: {e}")
        return jsonify(error=f"Error communicating with LLM: {e}"), 500

    # --- Apply State Updates from LLM JSON ---
    # Needs significant rework to use IDs instead of names for inventory and object updates
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
            # Ensure current_need_value is fetched fresh if multiple needs update or for $inc
            current_need_value = sims_collection.find_one({"_id": sim_id}, {f"needs.{need}": 1})["needs"][need]
            db_sim_update_ops[f"needs.{need}"] = max(0, min(100, current_need_value + delta))

    if sim_updates.get("inventory_add"):
        obj_id_to_add = sim_updates["inventory_add"] # LLM now provides ID
        sims_collection.update_one({"_id": sim_id}, {"$addToSet": {"inventory": obj_id_to_add}})
        # The object itself should be updated by an environment_update to set its zone
        app.logger.info(f"Added {obj_id_to_add} to {sim_id} inventory per LLM.")

    if sim_updates.get("inventory_remove"):
        obj_id_to_remove = sim_updates["inventory_remove"] # LLM now provides ID
        sims_collection.update_one({"_id": sim_id}, {"$pull": {"inventory": obj_id_to_remove}})
        # The object itself might be updated by an environment_update (e.g. to a zone like 'floor')
        app.logger.info(f"Removed {obj_id_to_remove} from {sim_id} inventory per LLM.")

    if db_sim_update_ops:
        sims_collection.update_one({"_id": sim_id}, {"$set": db_sim_update_ops})
        app.logger.debug(f"Applied Sim updates for {sim_id}: {db_sim_update_ops}")

    env_updates = llm_json.get("environment_updates", [])
    for update_info in env_updates:
        obj_id = update_info.get("object_id") # LLM provides ID
        if not obj_id:
            app.logger.warning(f"Skipping env update with no object_id: {update_info}")
            continue
            
        db_env_update_ops = {}
        if update_info.get("new_state_key"):
            db_env_update_ops["current_state_key"] = update_info["new_state_key"]
        if update_info.get("new_zone"):
            db_env_update_ops["zone"] = update_info["new_zone"]
        
        # Handling contains (for containers like Fridge)
        # Note: This is a simplified $addToSet and $pull. Real inventory/container logic can be complex.
        if update_info.get("add_to_contains"):
            environment_collection.update_one({"_id": obj_id}, {"$addToSet": {"contains": update_info["add_to_contains"]}})
        if update_info.get("remove_from_contains"):
            environment_collection.update_one({"_id": obj_id}, {"$pull": {"contains": update_info["remove_from_contains"]}})

        if db_env_update_ops: # These are $set operations
            environment_collection.update_one({"_id": obj_id}, {"$set": db_env_update_ops})
            app.logger.debug(f"Applied Env object update for {obj_id}: {db_env_update_ops}")

    # Return the LLM's JSON response (which includes narrative and state changes)
    return jsonify(llm_json), 200

if __name__ == '__main__':
    with app.app_context():
        initialize_game_world() # Initialize game state on startup
    app.run(debug=True, host='0.0.0.0', port=5001) 