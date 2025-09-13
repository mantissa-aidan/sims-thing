#!/usr/bin/env python3
"""
Health check script for Sims Thing
Checks all system components and dependencies
"""

import sys
import requests
import json
from datetime import datetime

def check_api_health():
    """Check if the API is responding"""
    try:
        response = requests.get("http://localhost:5001/api/v1/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Health: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ API Health: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Health: {e}")
        return False

def check_database_connection():
    """Check database connectivity"""
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        client.server_info()
        print("✅ Database: Connected")
        return True
    except Exception as e:
        print(f"❌ Database: {e}")
        return False

def check_ollama_connection():
    """Check Ollama connectivity"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            if "gemma3:12b" in model_names:
                print("✅ Ollama: Connected with gemma3:12b")
                return True
            else:
                print("❌ Ollama: Connected but gemma3:12b not found")
                return False
        else:
            print(f"❌ Ollama: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama: {e}")
        return False

def check_sims_available():
    """Check if Sims are available"""
    try:
        response = requests.get("http://localhost:5001/api/v1/sims", timeout=5)
        if response.status_code == 200:
            data = response.json()
            sims = data.get("sims", [])
            print(f"✅ Sims: {len(sims)} available")
            return True
        else:
            print(f"❌ Sims: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Sims: {e}")
        return False

def main():
    """Run all health checks"""
    print("🏥 Sims Thing Health Check")
    print("=" * 40)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    checks = [
        ("API Health", check_api_health),
        ("Database", check_database_connection),
        ("Ollama", check_ollama_connection),
        ("Sims Available", check_sims_available),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"Checking {name}...")
        result = check_func()
        results.append(result)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 40)
    print(f"Health Check Summary: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All systems healthy!")
        sys.exit(0)
    else:
        print("⚠️  Some systems need attention")
        sys.exit(1)

if __name__ == "__main__":
    main()
