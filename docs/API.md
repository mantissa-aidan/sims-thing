# Sims Thing API Documentation

## Overview
The Sims Thing API provides endpoints for interacting with an emergent AI simulation system. The API allows you to manage Sims, process actions, and retrieve game state information.

## Base URL
```
http://localhost:5001/api/v1
```

## Authentication
Currently no authentication is required. All endpoints are publicly accessible.

## Endpoints

### Health Check
```http
GET /api/v1/health
```
Returns the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "service": "Sims Thing API",
  "version": "1.0.0"
}
```

### Get All Sims
```http
GET /api/v1/sims
```
Returns a list of all available Sims in the system.

**Response:**
```json
{
  "sims": [
    {
      "sim_id": "sim_horace",
      "name": "Horace",
      "location": "Living Area",
      "mood": "neutral",
      "needs": {
        "hunger": 50,
        "energy": 70,
        "social": 60,
        "fun": 40
      }
    }
  ]
}
```

### Get Sim Details
```http
GET /api/v1/sims/{sim_id}
```
Returns detailed information about a specific Sim.

**Parameters:**
- `sim_id` (string): The unique identifier for the Sim

**Response:**
```json
{
  "sim_id": "sim_horace",
  "name": "Horace",
  "location": "Living Area",
  "mood": "neutral",
  "needs": {
    "hunger": 50,
    "energy": 70,
    "social": 60,
    "fun": 40
  },
  "inventory": [],
  "current_activity": "idle"
}
```

### Get Sim State
```http
GET /api/v1/sims/{sim_id}/state
```
Returns the current game state for a Sim, including objects in the current location.

**Parameters:**
- `sim_id` (string): The unique identifier for the Sim

**Response:**
```json
{
  "sim_state": {
    "sim_id": "sim_horace",
    "name": "Horace",
    "location": "Living Area",
    "mood": "neutral",
    "needs": {
      "hunger": 50,
      "energy": 70,
      "social": 60,
      "fun": 40
    },
    "inventory": [],
    "current_activity": "idle"
  },
  "objects_in_zone": [
    {
      "_id": "obj_sofa",
      "name": "Sofa",
      "current_state_key": "empty",
      "states": {
        "empty": "The sofa looks inviting.",
        "occupied": "Someone is sitting on the sofa."
      }
    }
  ],
  "objects_in_inventory": [],
  "apartment_layout": {
    "zones": {
      "Living Area": {
        "description": "A comfortable area with a sofa, a coffee table, and a bookshelf.",
        "connections": ["Sleeping Area", "Kitchenette", "Desk Area"]
      }
    }
  }
}
```

### Process Action
```http
POST /api/v1/sims/{sim_id}/action
```
Process an action for a Sim and return the result.

**Parameters:**
- `sim_id` (string): The unique identifier for the Sim

**Request Body:**
```json
{
  "action": "sit on obj_sofa"
}
```

**Response:**
```json
{
  "narrative": "Horace sits down on the sofa, feeling comfortable.",
  "sim_state_updates": {
    "location": "Living Area",
    "mood": "neutral",
    "needs_delta": {
      "energy": 10
    },
    "current_activity": "sitting on sofa"
  },
  "environment_updates": [
    {
      "object_id": "obj_sofa",
      "new_state_key": "occupied",
      "new_zone": null,
      "add_to_contains": null,
      "remove_from_contains": null,
      "consumed": null
    }
  ],
  "available_actions": [
    "get up from obj_sofa",
    "look around",
    "go to Kitchenette"
  ]
}
```

### Get Suggested Action
```http
GET /api/v1/sims/{sim_id}/suggest
```
Get an AI-suggested action for a Sim.

**Parameters:**
- `sim_id` (string): The unique identifier for the Sim

**Response:**
```json
{
  "action": "go to Kitchenette",
  "reason": "Horace is hungry and the Kitchenette is likely to have food available."
}
```

### Get Action History
```http
GET /api/v1/sims/{sim_id}/history
```
Get the action history for a Sim.

**Parameters:**
- `sim_id` (string): The unique identifier for the Sim

**Response:**
```json
{
  "history": [
    {
      "action": "go to Kitchenette",
      "reason": "Looking for food",
      "narrative": "Horace walks from the Living Area to the Kitchenette.",
      "timestamp": "2025-09-13T08:00:00"
    },
    {
      "action": "eat obj_banana_scenario",
      "reason": "Horace is hungry and a banana is available",
      "narrative": "Horace peels the banana and eats it.",
      "timestamp": "2025-09-13T08:01:00"
    }
  ]
}
```

### Get Scenarios
```http
GET /api/v1/scenarios
```
Get available scenarios for initialization.

**Response:**
```json
{
  "scenarios": [
    {
      "id": "default_horace_apartment",
      "name": "Horace's Studio Apartment",
      "description": "Horace, a regular Sim, in his usual studio apartment."
    }
  ]
}
```

### Initialize Scenario
```http
POST /api/v1/scenarios/{scenario_id}/initialize
```
Initialize a scenario with a Sim and environment.

**Parameters:**
- `scenario_id` (string): The unique identifier for the scenario

**Response:**
```json
{
  "message": "Scenario initialized successfully",
  "sim_id": "sim_horace",
  "scenario": "default_horace_apartment"
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (Sim or scenario not found)
- `500`: Internal Server Error

## Action Format

Actions should be natural language strings describing what the Sim should do. Examples:
- `"sit on obj_sofa"`
- `"go to Kitchenette"`
- `"eat obj_banana_scenario"`
- `"examine obj_fridge"`
- `"open obj_fridge"`

## Object IDs

Objects in the system have unique IDs that start with `obj_`. Examples:
- `obj_sofa`
- `obj_fridge`
- `obj_banana_scenario`
- `obj_milk_carton`

## Location Names

Valid location names include:
- `"Living Area"`
- `"Kitchenette"`
- `"Sleeping Area"`
- `"Desk Area"`
