"""Health check endpoint."""
from flask import Blueprint, jsonify

bp = Blueprint('health', __name__)


@bp.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Urban Canvas API is running'
    })
