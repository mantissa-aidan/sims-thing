"""
Database module for Sims Thing
Handles MongoDB connections and collections
"""

from pymongo import MongoClient
from src.config import Config

class Database:
    """Database connection and collection management"""
    
    def __init__(self):
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client.get_database()
        
        # Collections
        self.sims = self.db[Config.SIMS_COLLECTION]
        self.environment = self.db[Config.ENVIRONMENT_COLLECTION]
        self.apartment_layouts = self.db[Config.APARTMENT_LAYOUT_COLLECTION]
    
    def get_collections(self):
        """Get all collections for easy access"""
        return {
            'sims': self.sims,
            'environment': self.environment,
            'apartment_layouts': self.apartment_layouts
        }

# Global database instance
db = Database()
sims_collection = db.sims
environment_collection = db.environment
apartment_layout_collection = db.apartment_layouts
