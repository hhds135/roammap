"""
Urban Canvas Backend Application

Main entry point for the Flask application.
Initializes the app, registers blueprints, and sets up error handlers.
"""
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from routes import register_blueprints
from utils import generate_token, decode_token, jwt_required, jwt_optional, allowed_file


def create_app():
    """
    Application factory function.

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Enable CORS
    CORS(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    return app


def register_error_handlers(app):
    """Register global error handlers."""

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500


# Create the Flask application
app = create_app()


if __name__ == '__main__':
    print("Starting Urban Canvas Backend...")
    print("Data storage: MongoDB")
    print("Server: http://localhost:5200")
    app.run(debug=True, host='0.0.0.0', port=5200)
