"""
API routes for Sims Thing
Clean, organized API endpoints for UI integration
"""

from flask import Blueprint, request, jsonify
from src.game_engine import GameEngine
from src.utils.validation import validate_sim_id, validate_action

# Create API blueprint
api = Blueprint('api', __name__, url_prefix='/api/v1')

# Initialize game engine
game_engine = GameEngine()

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Sims Thing API",
        "version": "1.0.0"
    })

@api.route('/sims', methods=['GET'])
def get_all_sims():
    """Get all available Sims"""
    try:
        sims = game_engine.get_all_sims()
        return jsonify({"sims": sims}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/sims/<sim_id>', methods=['GET'])
def get_sim(sim_id):
    """Get specific Sim details"""
    if not validate_sim_id(sim_id):
        return jsonify({"error": "Invalid sim_id"}), 400
    
    try:
        sim_data = game_engine.get_sim_details(sim_id)
        if not sim_data:
            return jsonify({"error": "Sim not found"}), 404
        return jsonify(sim_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/sims/<sim_id>/state', methods=['GET'])
def get_sim_state(sim_id):
    """Get current game state for a Sim"""
    if not validate_sim_id(sim_id):
        return jsonify({"error": "Invalid sim_id"}), 400
    
    try:
        state = game_engine.get_current_game_state(sim_id)
        if not state:
            return jsonify({"error": "Sim not found"}), 404
        return jsonify(state), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/sims/<sim_id>/action', methods=['POST'])
def process_action(sim_id):
    """Process an action for a Sim"""
    if not validate_sim_id(sim_id):
        return jsonify({"error": "Invalid sim_id"}), 400
    
    data = request.get_json()
    if not data or 'action' not in data:
        return jsonify({"error": "Action is required"}), 400
    
    action = data['action'].strip()
    if not validate_action(action):
        return jsonify({"error": "Invalid action format"}), 400
    
    try:
        result = game_engine.process_sim_action(sim_id, action)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/sims/<sim_id>/suggest', methods=['GET'])
def get_suggested_action(sim_id):
    """Get AI-suggested action for a Sim"""
    if not validate_sim_id(sim_id):
        return jsonify({"error": "Invalid sim_id"}), 400
    
    try:
        suggestion = game_engine.get_llm_suggested_action(sim_id)
        if not suggestion:
            return jsonify({"error": "Could not generate suggestion"}), 500
        return jsonify(suggestion), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/sims/<sim_id>/history', methods=['GET'])
def get_action_history(sim_id):
    """Get action history for a Sim"""
    if not validate_sim_id(sim_id):
        return jsonify({"error": "Invalid sim_id"}), 400
    
    try:
        history = game_engine.get_action_history(sim_id)
        return jsonify({"history": history}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/scenarios', methods=['GET'])
def get_scenarios():
    """Get available scenarios"""
    try:
        scenarios = game_engine.get_available_scenarios()
        return jsonify({"scenarios": scenarios}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/scenarios/<scenario_id>/initialize', methods=['POST'])
def initialize_scenario(scenario_id):
    """Initialize a scenario"""
    try:
        result = game_engine.initialize_game_world(scenario_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
