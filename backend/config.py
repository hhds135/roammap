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

    # MongoDB settings
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'conner_db')

    # Preset tags
    PRESET_TAGS = [
        'Food', 'Travel', 'Sports', 'Art', 'Photography',
        'Reading', 'Music', 'Movies', 'Pets', 'Nature'
    ]

    # Recommendation algorithm settings
    RECOMMENDATION_WEIGHTS = {
        'geo': 0.4,
        'interest': 0.3,
        'social': 0.2,
        'behavior': 0.1
    }

    # Geographic search settings
    DEFAULT_SEARCH_RADIUS_METERS = 10000  # 10km
    MAX_SEARCH_RADIUS_METERS = 100000  # 100km

    # Recommendation cache TTL in seconds (5 minutes)
    RECOMMENDATION_CACHE_TTL = 300

    # View history TTL in days
    VIEW_HISTORY_TTL_DAYS = 30
