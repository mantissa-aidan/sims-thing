"""
Configuration module for Sims Thing
Handles environment variables and application settings
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Database
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/sims_mud_db")
    
    # Ollama LLM
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
    
    # Flask
    FLASK_APP = os.getenv("FLASK_APP", "app.py")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"
    
    # Application
    APP_NAME = "Sims Thing - Emergent AI Simulation"
    VERSION = "1.0.0"
    
    # Database Collections
    SIMS_COLLECTION = "sims"
    ENVIRONMENT_COLLECTION = "environment_objects"
    APARTMENT_LAYOUT_COLLECTION = "apartment_layouts"
    
    # Action History
    MAX_ACTION_HISTORY = 20
    ACTION_HISTORY_DISPLAY_LIMIT = 10
