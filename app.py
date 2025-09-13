"""
Sims Thing - Emergent AI Simulation
Clean, organized main application file
"""

from flask import Flask, jsonify
from src.config import Config
from src.api.routes import api

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Register API blueprint
    app.register_blueprint(api)
    
    # Root endpoint
    @app.route('/')
    def home():
        return jsonify({
            "name": Config.APP_NAME,
            "version": Config.VERSION,
            "status": "running",
            "endpoints": {
                "health": "/api/v1/health",
                "sims": "/api/v1/sims",
                "scenarios": "/api/v1/scenarios"
            }
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        debug=Config.FLASK_DEBUG,
        host='0.0.0.0',
        port=5001
    )
