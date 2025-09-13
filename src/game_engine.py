"""
Game Engine module for Sims Thing
Core game logic and AI integration
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
    """Core game engine handling AI interactions and game state"""
    
    def __init__(self):
        self.ollama_llm = OllamaLLM(
            model=Config.OLLAMA_MODEL,
            base_url=Config.OLLAMA_BASE_URL
        )
    
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
    
    def process_sim_action(self, sim_id: str, action: str) -> Dict[str, Any]:
        """Process an action for a Sim"""
        if not validate_sim_id(sim_id) or not validate_action(action):
            raise ValueError("Invalid sim_id or action")
        
        # This would integrate with the existing process_sim_action logic
        # For now, return a placeholder response
        return {
            "narrative": f"Action '{action}' processed for {sim_id}",
            "sim_state_updates": {},
            "environment_updates": [],
            "available_actions": ["look around", "examine objects"]
        }
    
    def get_llm_suggested_action(self, sim_id: str) -> Optional[Dict[str, str]]:
        """Get AI-suggested action for a Sim"""
        if not validate_sim_id(sim_id):
            return None
        
        try:
            # This would integrate with the existing get_llm_suggested_action logic
            # For now, return a placeholder response
            return {
                "action": "look around",
                "reason": "Exploring the current location"
            }
        except Exception as e:
            raise Exception(f"Error generating suggestion: {str(e)}")
    
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
    
    def initialize_game_world(self, scenario_id: str) -> Dict[str, Any]:
        """Initialize a scenario"""
        try:
            with open('scenarios.json', 'r') as f:
                scenarios = json.load(f)
            
            if scenario_id not in scenarios:
                raise ValueError(f"Scenario '{scenario_id}' not found")
            
            scenario_data = scenarios[scenario_id]
            
            # This would integrate with the existing initialize_game_world logic
            # For now, return a placeholder response
            return {
                "message": "Scenario initialized successfully",
                "sim_id": scenario_data["sim_config"]["sim_id"],
                "scenario": scenario_id
            }
        except Exception as e:
            raise Exception(f"Error initializing scenario: {str(e)}")
