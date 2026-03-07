"""Configuration management for the Flask application."""
import os
from datetime import timedelta


class Config:
    """Application configuration class."""

    # Application settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

    # JWT settings
    JWT_EXPIRATION_DELTA = timedelta(days=1)
    JWT_ALGORITHM = 'HS256'

    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Data storage paths
    DATA_FOLDER = 'data'
    USERS_FILE = os.path.join(DATA_FOLDER, 'users.json')
    CORNERS_FILE = os.path.join(DATA_FOLDER, 'corners.json')

    # MongoDB settings
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://192.168.0.222:27017/')
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'conner_db')

    # Preset tags
    PRESET_TAGS = [
        'Food', 'Travel', 'Sports', 'Art', 'Photography',
        'Reading', 'Music', 'Movies', 'Pets', 'Nature'
    ]
