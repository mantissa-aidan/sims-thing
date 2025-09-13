"""
Full Game Engine module for Sims Thing
Complete AI integration with all original functionality
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from langchain_ollama.llms import OllamaLLM

from src.config import Config
from src.database import sims_collection, environment_collection, apartment_layout_collection
from src.utils.validation import validate_sim_id, validate_action

class GameEngine:
    """Complete game engine with full AI functionality"""
    
    def __init__(self):
        self.ollama_llm = OllamaLLM(
            model=Config.OLLAMA_MODEL,
            base_url=Config.OLLAMA_BASE_URL
        )
    
    def normalize_location_name(self, location_name, apartment_layout):
        """Normalize location names to match the case used in apartment layout"""
        if not location_name or not apartment_layout or 'zones' not in apartment_layout:
            return None
        
        for zone_name in apartment_layout['zones'].keys():
            if zone_name.lower() == location_name.lower():
                return zone_name
        return None
    
    def get_detailed_object_info(self, objects_in_zone, objects_in_inventory):
        """Get detailed object information for AI prompts"""
        detailed_info = []
        
        for obj in objects_in_zone + objects_in_inventory:
            obj_info = {
                "id": obj['_id'],
                "name": obj['name'],
                "current_state": obj['states'][obj['current_state_key']],
                "available_states": list(obj['states'].keys()),
                "interactions": obj.get('interactions', []),
                "properties": obj.get('properties', {})
            }
            detailed_info.append(obj_info)
        
        return detailed_info
    
    def validate_action_objects(self, player_action_text, objects_in_zone, objects_in_inventory):
        """Validate that action references existing objects"""
        # Extract object IDs from action text
        object_ids = re.findall(r'obj_[a-zA-Z0-9_]+', player_action_text)
        
        available_object_ids = [obj['_id'] for obj in objects_in_zone + objects_in_inventory]
        
        missing_objects = []
        for obj_id in object_ids:
            if obj_id not in available_object_ids:
                missing_objects.append(obj_id)
        
        return len(missing_objects) == 0, missing_objects, available_object_ids
    
    def get_action_history(self, sim_id, limit=10):
        """Get action history for a Sim"""
        try:
            sim = sims_collection.find_one({"_id": sim_id}, {"action_history": 1})
            if sim and "action_history" in sim:
                return sim["action_history"][-limit:]
            return []
        except Exception as e:
            return []
    
    def add_action_to_history(self, sim_id, action, reason, narrative):
        """Add an action to the Sim's history"""
        try:
            action_entry = {
                "action": action,
                "reason": reason,
                "narrative": narrative,
                "timestamp": datetime.now().isoformat()
            }
            
            sims_collection.update_one(
                {"_id": sim_id},
                {
                    "$push": {"action_history": {"$each": [action_entry], "$slice": -Config.MAX_ACTION_HISTORY}}
                }
            )
        except Exception as e:
            pass  # Don't fail if history update fails
    
    def format_action_history_for_prompt(self, action_history):
        """Format action history for AI prompt"""
        if not action_history:
            return "No recent actions"
        
        formatted = []
        for entry in action_history[-5:]:  # Last 5 actions
            formatted.append(f"- {entry['action']} (reason: {entry['reason']})")
        
        return "\\n".join(formatted)
    
    def generate_sim_decision_prompt(self, sim_state, objects_in_zone, objects_in_inventory, apartment_layout, action_history=None):
        """Generate AI prompt for decision making"""
        sim_name = sim_state['name']
        sim_location = sim_state['location']
        
        # Normalize location name
        normalized_location = self.normalize_location_name(sim_location, apartment_layout)
        if not normalized_location:
            raise ValueError(f"Invalid location '{sim_location}'. Valid locations: {list(apartment_layout['zones'].keys())}")
        
        zone_description = apartment_layout['zones'][normalized_location]['description']
        sim_mood = sim_state['mood']
        needs = sim_state['needs']
        current_activity = sim_state['current_activity']
        
        inventory_details = [f"{obj['name']} ({obj['states'][obj['current_state_key']]}) [{obj['_id']}]" for obj in objects_in_inventory]
        inventory_str = ", ".join(inventory_details) if inventory_details else "nothing"
        
        zone_object_details = [f"{obj['name']} ({obj['states'][obj['current_state_key']]}) [{obj['_id']}]" for obj in objects_in_zone]
        zone_objects_str = ", ".join(zone_object_details) if zone_object_details else "nothing notable"
        
        available_object_ids = [obj['_id'] for obj in objects_in_zone + objects_in_inventory]
        current_zone_connections = apartment_layout['zones'][normalized_location].get('connections', [])
        connections_str = ", ".join(current_zone_connections) if current_zone_connections else "nowhere"
        
        # Format action history
        history_text = ""
        if action_history:
            history_text = f"\\n\\nRECENT ACTION HISTORY (learn from these):\\n{self.format_action_history_for_prompt(action_history)}\\n"
        
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
            f"- Can move from {sim_location} to: {connections_str}.\\n{history_text}"
            
            f"CRITICAL RULES - READ CAREFULLY:\\n"
            f"1. VALID LOCATION NAMES (use EXACTLY as shown): {', '.join(apartment_layout['zones'].keys())}\\n"
            f"2. ONLY interact with objects that are ACTUALLY PRESENT in the current location or inventory\\n"
            f"3. If no food objects are visible, you CANNOT eat anything - look for food in other locations first\\n"
            f"4. If no bed/sofa is visible, you CANNOT sleep - find a suitable location first\\n"
            f"5. Object IDs must be EXACTLY as shown in the 'Available Object IDs' list\\n"
            f"6. DO NOT invent objects that don't exist - if you want to eat something, first check if food is available\\n"
            f"7. If no suitable objects are available for your desired action, choose a different action\\n\\n"
            
            f"PRIORITIZE ACTIONS BASED ON NEEDS. For example:\\n"
            f"- If hunger is high (>70), look for food or go to kitchen\\n"
            f"- If energy is low (<30), look for a bed or sofa to rest\\n"
            f"- If fun is low (<30), look for entertainment like computer or TV\\n"
            f"- If social is low (<30), consider going to areas with other people\\n\\n"
            
            f"RESPOND WITH VALID JSON ONLY:\\n"
            f"{{\\n"
            f'  "action": "your suggested action here",\\n'
            f'  "reason": "brief explanation of why this action makes sense"\\n'
            f"}}\\n\\n"
            
            f"Examples of good actions:\\n"
            f"- 'go to Kitchenette' (if hungry and kitchen is connected)\\n"
            f"- 'examine obj_fridge' (if fridge is present and you want to see what's inside)\\n"
            f"- 'eat obj_banana_scenario' (if banana is in inventory or current location)\\n"
            f"- 'turn on obj_computer' (if computer is present and you want entertainment)\\n"
            f"- 'sit on obj_sofa' (if sofa is present and you want to rest)\\n"
        )
        
        return prompt
    
    def get_llm_suggested_action(self, sim_id: str) -> Optional[Dict[str, str]]:
        """Get AI-suggested action for a Sim"""
        if not validate_sim_id(sim_id):
            return None
        
        try:
            sim_state = sims_collection.find_one({"_id": sim_id})
            if not sim_state:
                return None
            
            # Get objects in current zone
            objects_in_zone = list(environment_collection.find({"zone": sim_state["location"]}))
            
            # Get objects in inventory
            inventory_ids = sim_state.get("inventory", [])
            objects_in_inventory = []
            if inventory_ids:
                objects_in_inventory = list(environment_collection.find({
                    "_id": {"$in": inventory_ids},
                    "zone": f"inventory_{sim_id}"
                }))
            
            # Get apartment layout
            apartment_layout = apartment_layout_collection.find_one({})
            if not apartment_layout:
                return None
            
            # Get action history for context
            action_history = self.get_action_history(sim_id)
            
            # Generate prompt
            prompt = self.generate_sim_decision_prompt(sim_state, objects_in_zone, objects_in_inventory, apartment_layout, action_history)
            
            # Get AI response
            raw_llm_response = self.ollama_llm.invoke(prompt)
            
            # Clean response
            cleaned_response = re.sub(r"<think>.*?</think>", "", raw_llm_response, flags=re.DOTALL).strip()
            
            # Parse JSON
            json_string = None
            try:
                json_start_index = cleaned_response.find('{')
                json_end_index = cleaned_response.rfind('}')
                
                if json_start_index != -1 and json_end_index != -1 and json_start_index < json_end_index:
                    json_string = cleaned_response[json_start_index:json_end_index + 1]
                    parsed_json = json.loads(json_string)
                    
                    if isinstance(parsed_json, dict) and "action" in parsed_json and "reason" in parsed_json:
                        action = str(parsed_json["action"]).strip()
                        reason = str(parsed_json["reason"]).strip()
                        
                        if action:
                            # Validate action objects
                            is_valid, missing_objects, available_object_ids = self.validate_action_objects(action, objects_in_zone, objects_in_inventory)
                            
                            if not is_valid:
                                # Return fallback action
                                available_objects = [obj['name'] for obj in objects_in_zone + objects_in_inventory]
                                
                                if available_objects:
                                    fallback_action = f"examine {available_objects[0]}"
                                    fallback_reason = f"Looking at available objects since {', '.join(missing_objects)} don't exist"
                                    
                                    # Record fallback action
                                    self.add_action_to_history(sim_id, fallback_action, fallback_reason, "Fallback action taken due to invalid object reference")
                                    
                                    return {"action": fallback_action, "reason": fallback_reason}
                                else:
                                    fallback_action = f"go to {list(apartment_layout['zones'].keys())[0]}"
                                    fallback_reason = "No objects available in current location, moving to explore"
                                    
                                    # Record fallback action
                                    self.add_action_to_history(sim_id, fallback_action, fallback_reason, "Fallback action taken - no objects available")
                                    
                                    return {"action": fallback_action, "reason": fallback_reason}
                            
                            # Record successful action
                            self.add_action_to_history(sim_id, action, reason, "AI-suggested action")
                            
                            return {"action": action, "reason": reason}
            
            except json.JSONDecodeError:
                pass
            
            # If we get here, JSON parsing failed
            return {"action": "look around", "reason": "Exploring the current location"}
            
        except Exception as e:
            return {"action": "look around", "reason": "Exploring the current location"}
    
    def process_sim_action(self, sim_id: str, action: str) -> Dict[str, Any]:
        """Process an action for a Sim with full AI integration"""
        if not validate_sim_id(sim_id) or not validate_action(action):
            raise ValueError("Invalid sim_id or action")
        
        try:
            sim_state = sims_collection.find_one({"_id": sim_id})
            if not sim_state:
                raise ValueError("Sim not found")
            
            # Get objects in current zone
            objects_in_zone = list(environment_collection.find({"zone": sim_state["location"]}))
            
            # Get objects in inventory
            inventory_ids = sim_state.get("inventory", [])
            objects_in_inventory = []
            if inventory_ids:
                objects_in_inventory = list(environment_collection.find({
                    "_id": {"$in": inventory_ids},
                    "zone": f"inventory_{sim_id}"
                }))
            
            # Get apartment layout
            apartment_layout = apartment_layout_collection.find_one({})
            if not apartment_layout:
                raise ValueError("Apartment layout not found")
            
            # Handle 'go to' action
            if action.lower().startswith("go to "):
                return self._handle_go_to_action(sim_id, action, sim_state, apartment_layout)
            
            # Pre-validate action objects
            is_valid, missing_objects, available_object_ids = self.validate_action_objects(action, objects_in_zone, objects_in_inventory)
            
            if not is_valid:
                available_objects_str = ", ".join([f"{obj['name']} [{obj['_id']}]" for obj in objects_in_zone + objects_in_inventory])
                narrative = f"{sim_state['name']} looks around but can't find {', '.join(missing_objects)}. Available objects: {available_objects_str if available_objects_str else 'none'}."
                
                # Record failed action
                self.add_action_to_history(sim_id, action, f"Failed - objects {missing_objects} not found", narrative)
                
                return {
                    "narrative": narrative,
                    "sim_state_updates": {"mood": "confused"},
                    "environment_updates": [],
                    "available_actions": [f"look around in {sim_state['location']}", f"examine <available object>"]
                }
            
            # Process with AI
            return self._process_action_with_ai(sim_id, action, sim_state, objects_in_zone, objects_in_inventory, apartment_layout)
            
        except Exception as e:
            raise Exception(f"Error processing action: {str(e)}")
    
    def _handle_go_to_action(self, sim_id, action, sim_state, apartment_layout):
        """Handle movement actions"""
        target_zone_input = action[len("go to "):].strip()
        current_zone_name = sim_state["location"]
        current_zone_details = apartment_layout["zones"].get(current_zone_name)
        
        if not current_zone_details:
            raise ValueError(f"Sim's current zone '{current_zone_name}' not found in layout!")
        
        # Find matching zone
        matched_zone_name = None
        for zone_name_in_layout in apartment_layout["zones"].keys():
            if zone_name_in_layout.lower() == target_zone_input.lower():
                matched_zone_name = zone_name_in_layout
                break
        
        if matched_zone_name and matched_zone_name in current_zone_details.get("connections", []):
            # Update sim location
            new_sim_activity = f"moving to {matched_zone_name}"
            sims_collection.update_one({"_id": sim_id}, {"$set": {"location": matched_zone_name, "current_activity": new_sim_activity}})
            
            narrative = f"{sim_state['name']} walks from the {current_zone_name} to the {matched_zone_name}."
            
            # Record movement
            self.add_action_to_history(sim_id, action, f"Successfully moved to {matched_zone_name}", narrative)
            
            return {
                "narrative": narrative,
                "sim_state_updates": {"location": matched_zone_name, "current_activity": new_sim_activity},
                "environment_updates": [],
                "available_actions": [f"look around in {matched_zone_name}", f"examine <object in {matched_zone_name}>"]
            }
        else:
            return {
                "narrative": f"You can't go directly to {target_zone_input} from {current_zone_name}. Possible exits: {', '.join(current_zone_details.get('connections',[]))}",
                "sim_state_updates": {},
                "environment_updates": [],
                "available_actions": [f"look around in {current_zone_name}", f"go to <connected location>"]
            }
    
    def _process_action_with_ai(self, sim_id, action, sim_state, objects_in_zone, objects_in_inventory, apartment_layout):
        """Process action using AI"""
        # Create detailed prompt for AI
        objects_in_zone_str = ", ".join([f"{obj['name']} ({obj['states'][obj['current_state_key']]}) [{obj['_id']}]" for obj in objects_in_zone]) if objects_in_zone else "nothing notable"
        objects_in_inventory_str = ", ".join([f"{obj['name']} ({obj['states'][obj['current_state_key']]}) [{obj['_id']}]" for obj in objects_in_inventory]) if objects_in_inventory else "empty"
        available_object_ids_str = str([obj['_id'] for obj in objects_in_zone + objects_in_inventory])
        
        # Normalize location name
        normalized_location = self.normalize_location_name(sim_state['location'], apartment_layout)
        if not normalized_location:
            normalized_location = sim_state['location']
        
        # Get action history
        action_history = self.get_action_history(sim_id)
        history_text = ""
        if action_history:
            history_text = f"\\n\\nRECENT ACTION HISTORY:\\n{self.format_action_history_for_prompt(action_history)}\\n"
        
        prompt = (
            f"You are processing the action '{action}' for {sim_state['name']} in a simulated world.\\n\\n"
            
            f"CURRENT SITUATION:\\n"
            f"- Sim: {sim_state['name']} (mood: {sim_state['mood']})\\n"
            f"- Location: {sim_state['location']}\\n"
            f"- Needs: Hunger {sim_state['needs']['hunger']}/100, Energy {sim_state['needs']['energy']}/100, Fun {sim_state['needs']['fun']}/100, Social {sim_state['needs']['social']}/100\\n"
            f"- Current Activity: {sim_state['current_activity']}\\n"
            f"- Objects in current location: {objects_in_zone_str}\\n"
            f"- Objects in inventory: {objects_in_inventory_str}\\n"
            f"- Available Object IDs: {available_object_ids_str}\\n{history_text}"
            
            f"CRITICAL RULES:\\n"
            f"1. Use EXACT object IDs from the Available Object IDs list\\n"
            f"2. Only reference objects that are ACTUALLY PRESENT\\n"
            f"3. If an object is consumed (like food), set 'consumed': true\\n"
            f"4. Update needs realistically (eating reduces hunger, sleeping increases energy)\\n"
            f"5. Use valid state keys for objects\\n\\n"
            
            f"RESPOND WITH VALID JSON ONLY:\\n"
            f"{{\\n"
            f'  "narrative": "detailed description of what happens",\\n'
            f'  "sim_state_updates": {{\\n'
            f'    "location": null,\\n'
            f'    "mood": "new_mood_or_null",\\n'
            f'    "needs_delta": {{"hunger": 0, "energy": 0, "fun": 0, "social": 0}},\\n'
            f'    "inventory_add": null,\\n'
            f'    "inventory_remove": null,\\n'
            f'    "current_activity": "new_activity_or_null"\\n'
            f'  }},\\n'
            f'  "environment_updates": [\\n'
            f'    {{"object_id": "obj_id", "new_state_key": "new_state", "new_zone": null, "consumed": false}}\\n'
            f'  ],\\n'
            f'  "available_actions": ["action1", "action2"]\\n'
            f"}}\\n"
        )
        
        try:
            # Get AI response
            raw_llm_response = self.ollama_llm.invoke(prompt)
            
            # Clean response
            cleaned_response = re.sub(r"<think>.*?</think>", "", raw_llm_response, flags=re.DOTALL).strip()
            
            # Parse JSON
            json_string = None
            try:
                json_start_index = cleaned_response.find('{')
                json_end_index = cleaned_response.rfind('}')
                
                if json_start_index != -1 and json_end_index != -1 and json_start_index < json_end_index:
                    json_string = cleaned_response[json_start_index:json_end_index + 1]
                    parsed_json = json.loads(json_string)
                    
                    if isinstance(parsed_json, dict) and "narrative" in parsed_json:
                        # Process the AI response
                        return self._apply_ai_response(sim_id, action, parsed_json, sim_state)
            
            except json.JSONDecodeError:
                pass
            
            # Fallback if JSON parsing fails
            return {
                "narrative": f"{sim_state['name']} attempts to {action} but nothing notable happens.",
                "sim_state_updates": {},
                "environment_updates": [],
                "available_actions": ["look around", "examine objects"]
            }
            
        except Exception as e:
            return {
                "narrative": f"{sim_state['name']} attempts to {action} but something goes wrong.",
                "sim_state_updates": {},
                "environment_updates": [],
                "available_actions": ["look around", "examine objects"]
            }
    
    def _apply_ai_response(self, sim_id, action, ai_response, sim_state):
        """Apply AI response to game state"""
        narrative = ai_response.get("narrative", f"{sim_state['name']} performs the action.")
        sim_updates = ai_response.get("sim_state_updates", {})
        environment_updates = ai_response.get("environment_updates", [])
        available_actions = ai_response.get("available_actions", ["look around", "examine objects"])
        
        # Apply sim state updates
        if sim_updates:
            update_data = {}
            
            # Handle location update
            if "location" in sim_updates and sim_updates["location"]:
                update_data["location"] = sim_updates["location"]
            
            # Handle mood update
            if "mood" in sim_updates and sim_updates["mood"]:
                update_data["mood"] = sim_updates["mood"]
            
            # Handle needs delta
            if "needs_delta" in sim_updates:
                needs_delta = sim_updates["needs_delta"]
                current_needs = sim_state["needs"]
                new_needs = {}
                for need, delta in needs_delta.items():
                    if need in current_needs:
                        new_value = max(0, min(100, current_needs[need] + delta))
                        new_needs[need] = new_value
                    else:
                        new_needs[need] = current_needs.get(need, 50)
                
                update_data["needs"] = new_needs
            
            # Handle inventory changes
            if "inventory_add" in sim_updates and sim_updates["inventory_add"]:
                sims_collection.update_one({"_id": sim_id}, {"$addToSet": {"inventory": sim_updates["inventory_add"]}})
            
            if "inventory_remove" in sim_updates and sim_updates["inventory_remove"]:
                sims_collection.update_one({"_id": sim_id}, {"$pull": {"inventory": sim_updates["inventory_remove"]}})
            
            # Handle current activity
            if "current_activity" in sim_updates and sim_updates["current_activity"]:
                update_data["current_activity"] = sim_updates["current_activity"]
            
            # Apply updates
            if update_data:
                sims_collection.update_one({"_id": sim_id}, {"$set": update_data})
        
        # Apply environment updates
        for env_update in environment_updates:
            obj_id = env_update.get("object_id")
            if not obj_id:
                continue
            
            update_data = {}
            
            # Handle state change
            if "new_state_key" in env_update and env_update["new_state_key"]:
                update_data["current_state_key"] = env_update["new_state_key"]
            
            # Handle zone change
            if "new_zone" in env_update and env_update["new_zone"]:
                update_data["zone"] = env_update["new_zone"]
            
            # Handle consumption
            if env_update.get("consumed"):
                environment_collection.delete_one({"_id": obj_id})
                continue
            
            # Apply updates
            if update_data:
                environment_collection.update_one({"_id": obj_id}, {"$set": update_data})
        
        # Record action in history
        self.add_action_to_history(sim_id, action, "Player action", narrative)
        
        return {
            "narrative": narrative,
            "sim_state_updates": sim_updates,
            "environment_updates": environment_updates,
            "available_actions": available_actions
        }
    
    # Keep the existing methods for compatibility
    def get_all_sims(self) -> List[Dict[str, Any]]:
        """Get all available Sims"""
        try:
            sims = list(sims_collection.find({}, {"_id": 1, "name": 1, "location": 1, "mood": 1, "needs": 1}))
            return [{"sim_id": sim["_id"], **sim} for sim in sims]
        except Exception as e:
            raise Exception(f"Error fetching Sims: {str(e)}")
    
    def get_sim_details(self, sim_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific Sim"""
        if not validate_sim_id(sim_id):
            return None
        
        try:
            sim = sims_collection.find_one({"_id": sim_id})
            if sim:
                return {"sim_id": sim["_id"], **sim}
            return None
        except Exception as e:
            raise Exception(f"Error fetching Sim details: {str(e)}")
    
    def get_current_game_state(self, sim_id: str) -> Optional[Dict[str, Any]]:
        """Get current game state for a Sim"""
        if not validate_sim_id(sim_id):
            return None
        
        try:
            sim_state = sims_collection.find_one({"_id": sim_id})
            if not sim_state:
                return None
            
            # Get objects in current zone
            objects_in_zone = list(environment_collection.find({"zone": sim_state["location"]}))
            
            # Get objects in inventory
            inventory_ids = sim_state.get("inventory", [])
            objects_in_inventory = []
            if inventory_ids:
                objects_in_inventory = list(environment_collection.find({
                    "_id": {"$in": inventory_ids},
                    "zone": f"inventory_{sim_id}"
                }))
            
            # Get apartment layout
            apartment_layout = apartment_layout_collection.find_one({})
            
            return {
                "sim_state": sim_state,
                "objects_in_zone": objects_in_zone,
                "objects_in_inventory": objects_in_inventory,
                "apartment_layout": apartment_layout
            }
        except Exception as e:
            raise Exception(f"Error fetching game state: {str(e)}")
    
    def get_action_history(self, sim_id: str) -> List[Dict[str, Any]]:
        """Get action history for a Sim"""
        if not validate_sim_id(sim_id):
            return []
        
        try:
            sim = sims_collection.find_one({"_id": sim_id}, {"action_history": 1})
            if sim and "action_history" in sim:
                return sim["action_history"][-Config.ACTION_HISTORY_DISPLAY_LIMIT:]
            return []
        except Exception as e:
            raise Exception(f"Error fetching action history: {str(e)}")
    
    def get_available_scenarios(self) -> List[Dict[str, str]]:
        """Get available scenarios"""
        try:
            with open('scenarios.json', 'r') as f:
                scenarios = json.load(f)
            
            return [
                {
                    "id": scenario_id,
                    "name": scenario_data.get("description", scenario_id),
                    "description": scenario_data.get("description", "")
                }
                for scenario_id, scenario_data in scenarios.items()
            ]
        except Exception as e:
            raise Exception(f"Error fetching scenarios: {str(e)}")
    
    def initialize_game_world(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a scenario with the provided scenario data"""
        try:
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

            # Initialize Sim
            sim_doc_to_insert = sim_config.copy()
            if "sim_id" in sim_doc_to_insert:
                sim_doc_to_insert["_id"] = sim_doc_to_insert.pop("sim_id")
            
            sims_collection.insert_one(sim_doc_to_insert)
            actual_sim_id_for_inventory = sim_doc_to_insert['_id']
            sim_inventory_ids = sim_config.get("inventory", [])

            # Initialize Environment Objects (with special handling for inventory)
            objects_to_insert = []
            for obj_def in object_definitions:
                obj_copy = obj_def.copy()
                if obj_copy["_id"] in sim_inventory_ids:
                    obj_copy["zone"] = f"inventory_{actual_sim_id_for_inventory}"
                objects_to_insert.append(obj_copy)
            
            if objects_to_insert:
                environment_collection.insert_many(objects_to_insert)
            
            return {
                "message": "Scenario initialized successfully",
                "sim_id": actual_sim_id_for_inventory,
                "scenario": "initialized"
            }
        except Exception as e:
            raise Exception(f"Error initializing scenario: {str(e)}")
