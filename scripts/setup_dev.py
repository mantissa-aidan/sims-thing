#!/usr/bin/env python3
"""
Development setup script for Sims Thing
Sets up the development environment and validates configuration
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import pymongo
        import langchain_ollama
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_ollama():
    """Check if Ollama is running and has the required model"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            if "gemma3:12b" in model_names:
                print("✅ Ollama is running with gemma3:12b model")
                return True
            else:
                print("❌ gemma3:12b model not found")
                print("Run: ollama pull gemma3:12b")
                return False
        else:
            print("❌ Ollama is not responding")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("Make sure Ollama is running: ollama serve")
        return False

def check_mongodb():
    """Check if MongoDB is accessible"""
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        client.server_info()
        print("✅ MongoDB is accessible")
        return True
    except Exception as e:
        print(f"❌ Cannot connect to MongoDB: {e}")
        print("Make sure MongoDB is running")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# Database
MONGODB_URI=mongodb://localhost:27017/sims_mud_db

# AI Model
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:12b

# Flask
FLASK_APP=app_clean.py
FLASK_DEBUG=1
"""
        env_file.write_text(env_content)
        print("✅ Created .env file")
    else:
        print("✅ .env file already exists")

def main():
    """Main setup function"""
    print("🚀 Setting up Sims Thing development environment...\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Ollama", check_ollama),
        ("MongoDB", check_mongodb),
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"Checking {name}...")
        if not check_func():
            all_passed = False
        print()
    
    create_env_file()
    
    if all_passed:
        print("🎉 Development environment is ready!")
        print("\nNext steps:")
        print("1. Run the application: python app_clean.py")
        print("2. Test the API: curl http://localhost:5001/api/v1/health")
        print("3. Run autopilot: python scripts/run_autopilot.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
