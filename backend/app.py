"""
Urban Canvas Backend Application

Main entry point for the Flask application.
Initializes the app, registers blueprints, and sets up error handlers.
"""
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from models import init_data_files
from routes import register_blueprints

# Re-export for backward compatibility with tests
from utils import generate_token, decode_token, jwt_required, jwt_optional, allowed_file
from models import (
    load_users, save_users, load_corners, save_corners,
    find_user_by_username, find_user_by_id,
    can_access_corner, is_friend
)


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

    # Initialize data files
    init_data_files()

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register test utility endpoints
    register_test_endpoints(app)

    return app


def register_error_handlers(app):
    """Register global error handlers."""

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500


def register_test_endpoints(app):
    """Register test utility endpoints."""
    import os
    import json
    from config import Config

    @app.route('/api/test/clear', methods=['POST'])
    def clear_test_data():
        """Clear all test data - testing only, no auth required."""
        try:
            # Clear users.json
            with open(Config.USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)

            # Clear corners.json
            with open(Config.CORNERS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)

            return jsonify({
                'message': 'Test data cleared successfully',
                'cleared_files': [Config.USERS_FILE, Config.CORNERS_FILE]
            }), 200
        except Exception as e:
            return jsonify({'error': f'Failed to clear data: {str(e)}'}), 500


# Create the Flask application
app = create_app()


if __name__ == '__main__':
    print("Starting Urban Canvas Backend...")
    print("Data storage: JSON files")
    print("Server: http://localhost:5200")
    app.run(debug=True, host='0.0.0.0', port=5200)
