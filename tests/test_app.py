import pytest
import json
from app import app as flask_app # Import your Flask app instance
from app import initialize_game_world, DEFAULT_SIM_ID, sims_collection, environment_collection, apartment_layout_collection, ollama_llm

@pytest.fixture
def client():
    # flask_app.config['TESTING'] = True # Standard practice, though might not be strictly needed for all our tests yet
    # Reset database before each test for isolation
    with flask_app.app_context():
        # Clear existing data - adjust if specific collections should persist or be handled differently
        sims_collection.delete_many({})
        environment_collection.delete_many({})
        apartment_layout_collection.delete_many({})
        initialize_game_world() # Ensure a clean state for each test
    
    with flask_app.test_client() as client:
        yield client

def test_home_endpoint(client):
    """Test the home endpoint."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Welcome to the Sims MUD API - Evolved!" in response.data

def test_initialize_game_world(client):
    """Test if the game world initializes correctly."""
    # The client fixture already calls initialize_game_world()
    # We can assert that the collections are populated
    with flask_app.app_context(): # Need app context to access db directly
        assert sims_collection.count_documents({"_id": DEFAULT_SIM_ID}) == 1, "Default Sim should be initialized"
        assert apartment_layout_collection.count_documents({}) > 0, "Apartment layout should be initialized"
        assert environment_collection.count_documents({}) > 0, "Environment objects should be initialized"
        
        sim_state = sims_collection.find_one({"_id": DEFAULT_SIM_ID})
        assert sim_state is not None
        assert sim_state["name"] == "Alex"
        assert "Kitchenette" in apartment_layout_collection.find_one({})["zones"], "Kitchenette should be a zone"
        assert environment_collection.find_one({"name": "Banana"}) is not None, "Banana object should exist"

def test_get_full_game_state_api(client):
    """Test the /game/full_state endpoint."""
    response = client.get('/game/full_state')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
    data = json.loads(response.data)
    
    assert "sim" in data, "Response should contain sim data"
    assert "all_objects" in data, "Response should contain all_objects data"
    assert "layout" in data, "Response should contain layout data"
    
    assert data["sim"]["_id"] == DEFAULT_SIM_ID
    assert data["sim"]["name"] == "Alex"
    assert len(data["all_objects"]) > 0
    assert data["layout"]["_id"] == "studio_apartment"
    assert "Kitchenette" in data["layout"]["zones"]

def test_action_go_to_kitchenette(client):
    """Test the 'go to Kitchenette' action which is handled by Python."""
    action_payload = {"sim_id": DEFAULT_SIM_ID, "action": "go to Kitchenette"}
    response = client.post('/game/action', json=action_payload)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "narrative" in data
    assert "Kitchenette" in data["narrative"]
    assert data["sim_state_updates"]["location"] == "Kitchenette"
    
    # Verify actual DB state change
    with flask_app.app_context():
        sim = sims_collection.find_one({"_id": DEFAULT_SIM_ID})
        assert sim["location"] == "Kitchenette"

def test_action_invalid_verb(client):
    """Test an action that starts with an unrecognized verb."""
    action_payload = {"sim_id": DEFAULT_SIM_ID, "action": "teleport to Kitchenette"}
    response = client.post('/game/action', json=action_payload)
    assert response.status_code == 200 # The server handles this as a valid game interaction
    data = json.loads(response.data)
    assert "narrative" in data
    assert "doesn\'t seem to start with a clear action verb" in data["narrative"]

def test_llm_action_sim_need_change(client, mocker):
    """Test an action processed by LLM that changes a Sim's needs."""
    mock_llm_response = {
        "narrative": "Alex eats the banana. It's quite satisfying!",
        "sim_state_updates": {
            "location": None,
            "mood": "content",
            "needs_delta": {"hunger": 30, "energy": 5, "fun": 0}, # Hunger increases (less hungry)
            "inventory_add": None,
            "inventory_remove": "obj_banana_peeled", # Assuming a peeled banana object ID
            "current_activity": "eating banana"
        },
        "environment_updates": [
            {"object_id": "obj_banana_peeled", "new_state_key": "eaten", "new_zone": "inventory_sim_alex"} # or disappears
        ],
        "available_actions": ["look around", "go to Living Area"]
    }
    mocker.patch('app.OllamaLLM.invoke', return_value=json.dumps(mock_llm_response))

    action_payload = {"sim_id": DEFAULT_SIM_ID, "action": "eat banana"} # Assume banana is in inventory and peeled
    
    # Get initial hunger to compare against
    with flask_app.app_context():
        initial_sim_state = sims_collection.find_one({"_id": DEFAULT_SIM_ID})
        initial_hunger = initial_sim_state["needs"]["hunger"]
        initial_energy = initial_sim_state["needs"]["energy"]

    response = client.post('/game/action', json=action_payload)
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data["narrative"] == mock_llm_response["narrative"]
    assert data["sim_state_updates"]["mood"] == "content"

    with flask_app.app_context():
        updated_sim_state = sims_collection.find_one({"_id": DEFAULT_SIM_ID})
        # Hunger increases (less hungry), so new value is initial + delta (max 100)
        expected_hunger = min(100, initial_hunger + mock_llm_response["sim_state_updates"]["needs_delta"]["hunger"])
        assert updated_sim_state["needs"]["hunger"] == expected_hunger
        expected_energy = min(100, initial_energy + mock_llm_response["sim_state_updates"]["needs_delta"]["energy"])
        assert updated_sim_state["needs"]["energy"] == expected_energy
        assert updated_sim_state["mood"] == "content"
        assert "obj_banana_peeled" not in updated_sim_state.get("inventory", [])

def test_llm_action_env_object_state_change(client, mocker):
    """Test an action processed by LLM that changes an environment object's state."""
    mock_llm_response = {
        "narrative": "Alex turns on the computer. The screen flickers to life.",
        "sim_state_updates": {
            "location": None, "mood": None, "needs_delta": {},
            "inventory_add": None, "inventory_remove": None,
            "current_activity": "using computer"
        },
        "environment_updates": [
            {"object_id": "obj_computer", "new_state_key": "on", "new_zone": None} # Assume obj_computer ID
        ],
        "available_actions": ["work on computer", "browse web"]
    }
    mocker.patch('app.OllamaLLM.invoke', return_value=json.dumps(mock_llm_response))

    action_payload = {"sim_id": DEFAULT_SIM_ID, "action": "use computer"}
    
    # Need to ensure sim is in Desk Area for this test to be logical
    with flask_app.app_context():
        sims_collection.update_one({"_id": DEFAULT_SIM_ID}, {"$set": {"location": "Desk Area"}})
        # And find the computer object's ID (assuming it exists and is named Computer)
        computer_obj = environment_collection.find_one({"name": "Computer"})
        assert computer_obj is not None, "Test requires a Computer object in the initial environment state"
        mock_llm_response["environment_updates"][0]["object_id"] = computer_obj["_id"] # Use actual ID

    response = client.post('/game/action', json=action_payload)
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data["narrative"] == mock_llm_response["narrative"]

    with flask_app.app_context():
        computer_obj_after = environment_collection.find_one({"_id": mock_llm_response["environment_updates"][0]["object_id"]})
        assert computer_obj_after["current_state_key"] == "on"

def test_llm_action_inventory_change_take_item(client, mocker):
    """Test an action (take banana) processed by LLM that adds an item to inventory."""
    # Assuming banana (obj_banana) is in the Kitchenette, in the Fridge (obj_fridge)
    banana_id = "obj_banana"
    fridge_id = "obj_fridge"

    mock_llm_response = {
        "narrative": "Alex opens the fridge and takes the banana.",
        "sim_state_updates": {
            "location": None, "mood": None, "needs_delta": {},
            "inventory_add": banana_id, 
            "inventory_remove": None,
            "current_activity": "taking banana from fridge"
        },
        "environment_updates": [
            {"object_id": fridge_id, "new_state_key": "open", "remove_from_contains": banana_id}, # Fridge is opened and banana removed from its contents
            {"object_id": banana_id, "new_zone": f"inventory_{DEFAULT_SIM_ID}"} # Banana moves to sim's inventory zone
        ],
        "available_actions": ["peel banana", "close fridge"]
    }
    mocker.patch('app.OllamaLLM.invoke', return_value=json.dumps(mock_llm_response))

    # Ensure Sim is in Kitchenette
    with flask_app.app_context():
        sims_collection.update_one({"_id": DEFAULT_SIM_ID}, {"$set": {"location": "Kitchenette"}})
        # Ensure banana is in fridge for the test setup
        environment_collection.update_one({"_id": fridge_id}, {"$addToSet": {"contains": banana_id}})
        environment_collection.update_one({"_id": banana_id}, {"$set": {"zone": fridge_id}}) # Banana is physically in fridge

    action_payload = {"sim_id": DEFAULT_SIM_ID, "action": "take banana from fridge"}
    response = client.post('/game/action', json=action_payload)
    assert response.status_code == 200
    data = json.loads(response.data)

    assert data["narrative"] == mock_llm_response["narrative"]
    assert data["sim_state_updates"]["inventory_add"] == banana_id

    with flask_app.app_context():
        updated_sim_state = sims_collection.find_one({"_id": DEFAULT_SIM_ID})
        assert banana_id in updated_sim_state.get("inventory", [])
        
        fridge_obj_after = environment_collection.find_one({"_id": fridge_id})
        assert banana_id not in fridge_obj_after.get("contains", [])
        # The banana object itself should now have its zone updated
        banana_obj_after = environment_collection.find_one({"_id": banana_id})
        assert banana_obj_after["zone"] == f"inventory_{DEFAULT_SIM_ID}"

def test_llm_json_parsing_error_handling(client, mocker):
    """Test that server handles LLM response that isn't valid JSON."""
    mocker.patch('app.OllamaLLM.invoke', return_value="This is not JSON.")
    action_payload = {"sim_id": DEFAULT_SIM_ID, "action": "look around"}
    response = client.post('/game/action', json=action_payload)
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data
    assert "Could not find valid JSON block in LLM response." in data["error"]

def test_llm_json_validation_error_handling(client, mocker):
    """Test that server handles LLM JSON that is missing required fields."""
    mock_llm_invalid_json = {
        "narrative": "Something happened.",
        # Missing sim_state_updates and environment_updates
    }
    mocker.patch('app.OllamaLLM.invoke', return_value=json.dumps(mock_llm_invalid_json))
    action_payload = {"sim_id": DEFAULT_SIM_ID, "action": "look around"}
    response = client.post('/game/action', json=action_payload)
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data
    assert "LLM JSON failed validation" in data["error"]

# TODO: Add tests for LLM interactions (these will be more complex and might require mocking the LLM call)
# For example:
# - Test successful LLM JSON parsing
# - Test LLM response leading to sim need changes
# - Test LLM response leading to object state changes
# - Test LLM response leading to inventory changes 