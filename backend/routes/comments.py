"""Comment endpoints for posts."""
from flask import Blueprint, request, jsonify
from bson import ObjectId

from storage.comment_store import CommentStore
from storage.post_store import PostStore
from storage.user_store import UserStore
from utils import jwt_required, check_post_visibility, is_following_user

bp = Blueprint('comments', __name__)

comment_store = CommentStore()
post_store = PostStore()
user_store = UserStore()


@bp.route('/api/posts/<post_id>/comments', methods=['POST'])
@jwt_required
def add_comment(post_id):
    """Add a comment to a post."""
    user_id = request.user_id
    data = request.get_json()

    if not data or not data.get('content'):
        return jsonify({'error': 'Comment content required'}), 400

    content = data['content'].strip()
    if not content:
        return jsonify({'error': 'Comment content required'}), 400

    try:
        post_id_obj = ObjectId(post_id)
    except Exception:
        return jsonify({'error': 'Invalid post ID'}), 400

    # Get post
    post = post_store.get_post_by_id(post_id_obj)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Check visibility
    if not check_post_visibility(user_id, post, is_following_user):
        return jsonify({'error': 'Access denied'}), 403

    # Get user info
    user = user_store.get_user_by_id(ObjectId(user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404

    username = user.get('username', '')

    # Create comment
    try:
        comment_id = comment_store.create_comment(
            post_id=post_id_obj,
            user_id=ObjectId(user_id),
            username=username,
            content=content
        )
    except Exception as e:
        return jsonify({'error': f'Failed to create comment: {str(e)}'}), 500

    # Update post stats
    try:
        post_store.increment_stat(post_id_obj, 'comments_count')
    except Exception:
        pass

    # Get created comment
    comment = comment_store.get_comment_by_id(comment_id)

    # Convert ObjectIds to strings
    comment['_id'] = str(comment['_id'])
    comment['user_id'] = str(comment['user_id'])
    comment['post_id'] = str(comment['post_id'])

    return jsonify({
        'success': True,
        'data': comment
    }), 201


@bp.route('/api/posts/<post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    """Get comments for a post."""
    try:
        post_id_obj = ObjectId(post_id)
    except Exception:
        return jsonify({'error': 'Invalid post ID'}), 400

    # Get post
    post = post_store.get_post_by_id(post_id_obj)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Get pagination params
    try:
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)
    except ValueError:
        limit = 20

    try:
        skip = int(request.args.get('skip', 0))
        if skip < 0:
            skip = 0
    except ValueError:
        skip = 0

    # Get comments
    comments = comment_store.get_comments_by_post(post_id_obj, limit=limit)

    # Convert ObjectIds to strings
    for comment in comments:
        comment['_id'] = str(comment['_id'])
        comment['user_id'] = str(comment['user_id'])
        comment['post_id'] = str(comment['post_id'])

    # Get total count
    total = comment_store.count_comments_by_post(post_id_obj)

    return jsonify({
        'success': True,
        'data': {
            'comments': comments,
            'total': total,
            'limit': limit,
            'skip': skip
        }
    })


@bp.route('/api/posts/<post_id>/comments/<comment_id>', methods=['PUT'])
@jwt_required
def update_comment(post_id, comment_id):
    """Update a comment."""
    user_id = request.user_id
    data = request.get_json()

    if not data or not data.get('content'):
        return jsonify({'error': 'Comment content required'}), 400

    content = data['content'].strip()
    if not content:
        return jsonify({'error': 'Comment content required'}), 400

    try:
        post_id_obj = ObjectId(post_id)
        comment_id_obj = ObjectId(comment_id)
    except Exception:
        return jsonify({'error': 'Invalid ID'}), 400

    # Get comment
    comment = comment_store.get_comment_by_id(comment_id_obj)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    # Check if comment belongs to post
    if comment.get('post_id') != post_id_obj:
        return jsonify({'error': 'Comment not found for this post'}), 404

    # Check if user is the comment author
    if str(comment.get('user_id')) != user_id:
        return jsonify({'error': 'Access denied'}), 403

    # Update comment
    try:
        if not comment_store.update_comment(comment_id_obj, content):
            return jsonify({'error': 'Failed to update comment'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to update comment: {str(e)}'}), 500

    # Get updated comment
    updated_comment = comment_store.get_comment_by_id(comment_id_obj)

    # Convert ObjectIds to strings
    updated_comment['_id'] = str(updated_comment['_id'])
    updated_comment['user_id'] = str(updated_comment['user_id'])
    updated_comment['post_id'] = str(updated_comment['post_id'])

    return jsonify({
        'success': True,
        'data': updated_comment
    })


@bp.route('/api/posts/<post_id>/comments/<comment_id>', methods=['DELETE'])
@jwt_required
def delete_comment(post_id, comment_id):
    """Delete a comment."""
    user_id = request.user_id

    try:
        post_id_obj = ObjectId(post_id)
        comment_id_obj = ObjectId(comment_id)
    except Exception:
        return jsonify({'error': 'Invalid ID'}), 400

    # Get comment
    comment = comment_store.get_comment_by_id(comment_id_obj)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    # Check if comment belongs to post
    if comment.get('post_id') != post_id_obj:
        return jsonify({'error': 'Comment not found for this post'}), 404

    # Check if user is the comment author
    if str(comment.get('user_id')) != user_id:
        return jsonify({'error': 'Access denied'}), 403

    # Delete comment
    try:
        if not comment_store.delete_comment(comment_id_obj):
            return jsonify({'error': 'Failed to delete comment'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to delete comment: {str(e)}'}), 500

    # Update post stats
    try:
        post_store.decrement_stat(post_id_obj, 'comments_count')
    except Exception:
        pass

    return jsonify({
        'success': True,
        'message': 'Comment deleted'
    })


@bp.route('/api/users/<user_id>/comments', methods=['GET'])
def get_user_comments(user_id):
    """Get comments by a user."""
    try:
        user_id_obj = ObjectId(user_id)
    except Exception:
        return jsonify({'error': 'Invalid user ID'}), 400

    # Get pagination params
    try:
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)
    except ValueError:
        limit = 20

    try:
        skip = int(request.args.get('skip', 0))
        if skip < 0:
            skip = 0
    except ValueError:
        skip = 0

    # Get comments
    comments = comment_store.get_comments_by_user(user_id_obj, limit=limit)

    # Get total count
    total = len(comments)

    return jsonify({
        'success': True,
        'data': {
            'comments': comments,
            'total': total,
            'limit': limit,
            'skip': skip
        }
    })