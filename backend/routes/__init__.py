"""Blueprint registration center for all route modules."""
from flask import Flask


def register_blueprints(app: Flask):
    """
    Register all blueprints to the Flask application.

    Args:
        app: Flask application instance
    """
    from . import auth, corners, likes, favorites, comments, sharing, health
    from . import posts, media, users
    from . import follows, feed
    from . import view_history, recommendations

    app.register_blueprint(auth.bp)
    app.register_blueprint(corners.bp)
    app.register_blueprint(likes.bp)
    app.register_blueprint(favorites.bp)
    app.register_blueprint(comments.bp)
    app.register_blueprint(sharing.bp)
    app.register_blueprint(health.bp)
    app.register_blueprint(posts.bp)
    app.register_blueprint(media.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(follows.bp)
    app.register_blueprint(feed.bp)
    app.register_blueprint(view_history.bp)
    app.register_blueprint(recommendations.bp)
