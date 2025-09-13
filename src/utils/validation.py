"""
Validation utilities for Sims Thing
Input validation and sanitization
"""

import re
from typing import Optional

def validate_sim_id(sim_id: str) -> bool:
    """Validate Sim ID format"""
    if not sim_id or not isinstance(sim_id, str):
        return False
    
    # Sim IDs should start with 'sim_' and contain only alphanumeric characters and underscores
    pattern = r'^sim_[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, sim_id))

def validate_action(action: str) -> bool:
    """Validate action format"""
    if not action or not isinstance(action, str):
        return False
    
    # Actions should be non-empty strings with reasonable length
    return 1 <= len(action.strip()) <= 200

def validate_object_id(object_id: str) -> bool:
    """Validate object ID format"""
    if not object_id or not isinstance(object_id, str):
        return False
    
    # Object IDs should start with 'obj_' and contain only alphanumeric characters and underscores
    pattern = r'^obj_[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, object_id))

def validate_location_name(location: str) -> bool:
    """Validate location name format"""
    if not location or not isinstance(location, str):
        return False
    
    # Location names should be non-empty strings with reasonable length
    return 1 <= len(location.strip()) <= 50

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', text)
    return sanitized.strip()
