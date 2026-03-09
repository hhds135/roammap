"""Blueprint registration center for all route modules."""
from flask import Flask


def register_blueprints(app: Flask):
    """
    Register all blueprints to the Flask application.

    Args:
        app: Flask application instance
    """
    from . import auth, corners, likes, favorites, comments, friends, sharing, health
    from . import posts, media, users

    app.register_blueprint(auth.bp)
    app.register_blueprint(corners.bp)
    app.register_blueprint(likes.bp)
    app.register_blueprint(favorites.bp)
    app.register_blueprint(comments.bp)
    app.register_blueprint(friends.bp)
    app.register_blueprint(sharing.bp)
    app.register_blueprint(health.bp)
    app.register_blueprint(posts.bp)
    app.register_blueprint(media.bp)
    app.register_blueprint(users.bp)
