"""Media upload and management endpoints."""
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from bson import ObjectId
from io import BytesIO

from storage.media_store import MediaStore
from storage.connection import MongoDBConnection, get_db
from utils import jwt_required
from config import Config

bp = Blueprint('media', __name__)

# Initialize MongoDB connection if not already connected
# This ensures the database is connected when the blueprint is loaded
try:
    if get_db() is None:
        conn = MongoDBConnection()
        conn.connect()
except Exception:
    pass  # Connection will be attempted lazily by MediaStore

# File size limits
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi'}

# MIME type mapping
IMAGE_MIME_TYPES = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'webp': 'image/webp'
}

VIDEO_MIME_TYPES = {
    'mp4': 'video/mp4',
    'mov': 'video/quicktime',
    'avi': 'video/x-msvideo'
}

media_store = MediaStore(bucket_name="media")


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    if '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()


def get_mime_type(extension: str, media_type: str) -> str:
    """Get MIME type from extension and media type."""
    if media_type == 'image':
        return IMAGE_MIME_TYPES.get(extension, 'image/jpeg')
    elif media_type == 'video':
        return VIDEO_MIME_TYPES.get(extension, 'video/mp4')
    return 'application/octet-stream'


def validate_file(file, media_type: str):
    """
    Validate uploaded file.
    
    Args:
        file: File object from request
        media_type: Expected media type ('image' or 'video')
        
    Returns:
        tuple: (success, extension, error_message)
    """
    if not file or file.filename == '':
        return False, None, 'No file provided'
    
    extension = get_file_extension(file.filename)
    
    if media_type == 'image':
        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            return False, extension, f'Invalid image type. Allowed: {ALLOWED_IMAGE_EXTENSIONS}'
        max_size = MAX_IMAGE_SIZE
    elif media_type == 'video':
        if extension not in ALLOWED_VIDEO_EXTENSIONS:
            return False, extension, f'Invalid video type. Allowed: {ALLOWED_VIDEO_EXTENSIONS}'
        max_size = MAX_VIDEO_SIZE
    else:
        return False, extension, 'Invalid media_type. Must be "image" or "video"'
    
    # Read file to check size
    file.seek(0, 2)  # Seek to end
    file_length = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_length > max_size:
        return False, extension, f'File too large. Max size: {max_size} bytes ({max_size // 1024 // 1024}MB)'
    
    if file_length == 0:
        return False, extension, 'Empty file'
    
    return True, extension, None


@bp.route('/api/media/upload', methods=['POST'])
@jwt_required
def upload_media():
    """
    Upload a media file (image or video).
    
    Request:
        - file: The media file (multipart/form-data)
        - media_type: 'image' or 'video'
        
    Returns:
        JSON with file_id and metadata
    """
    user_id = request.user_id
    
    # Get media type from form
    media_type = request.form.get('media_type')
    if not media_type:
        return jsonify({'error': 'media_type is required (image or video)'}), 400
    
    if media_type not in ['image', 'video']:
        return jsonify({'error': 'media_type must be "image" or "video"'}), 400
    
    # Get uploaded file
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Validate file
    is_valid, extension, error = validate_file(file, media_type)
    if not is_valid:
        return jsonify({'error': error}), 400 if 'type' in error else 413
    
    # Get MIME type
    content_type = get_mime_type(extension, media_type)
    
    # Read file data
    file_data = file.read()
    
    # Generate unique filename
    original_filename = file.filename
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    
    # Prepare metadata
    metadata = {
        'media_type': media_type,
        'user_id': user_id,
        'content_type': content_type,
        'original_filename': original_filename,
        'upload_date': datetime.utcnow().isoformat()
    }
    
    # Save to GridFS
    try:
        file_id = media_store.save_file(
            file_data=file_data,
            filename=unique_filename,
            content_type=content_type,
            metadata=metadata
        )
    except Exception as e:
        return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
    
    # Get file info
    file_doc = media_store.get_file(file_id)
    
    return jsonify({
        'success': True,
        'data': {
            'file_id': str(file_id),
            'filename': unique_filename,
            'original_filename': original_filename,
            'length': file_doc.get('length', 0),
            'content_type': content_type,
            'media_type': media_type,
            'upload_date': metadata['upload_date']
        }
    }), 201


@bp.route('/api/media/<file_id>', methods=['GET'])
def get_media(file_id):
    """
    Get a media file by ID.
    
    Args:
        file_id: GridFS file ObjectId
        
    Returns:
        File content with appropriate Content-Type header
    """
    try:
        file_obj = ObjectId(file_id)
    except Exception:
        return jsonify({'error': 'Invalid file ID'}), 400
    
    # Get file metadata
    file_doc = media_store.get_file(file_obj)
    if not file_doc:
        return jsonify({'error': 'File not found'}), 404
    
    # Get file stream
    file_stream = media_store.get_file_stream(file_obj)
    if not file_stream:
        return jsonify({'error': 'File not found'}), 404
    
    # Get content type from metadata
    content_type = file_doc.get('metadata', {}).get('contentType', 'application/octet-stream')
    
    # Create response with file content
    response = send_file(
        file_stream,
        mimetype=content_type,
        as_attachment=False,
        download_name=file_doc.get('filename', 'file')
    )
    
    return response


@bp.route('/api/media/<file_id>', methods=['DELETE'])
@jwt_required
def delete_media(file_id):
    """
    Delete a media file.
    
    Only the user who uploaded the file can delete it.
    
    Args:
        file_id: GridFS file ObjectId
        
    Returns:
        Success message
    """
    try:
        file_obj = ObjectId(file_id)
    except Exception:
        return jsonify({'error': 'Invalid file ID'}), 400
    
    # Get file metadata
    file_doc = media_store.get_file(file_obj)
    if not file_doc:
        return jsonify({'error': 'File not found'}), 404
    
    # Check if user owns the file
    file_user_id = file_doc.get('metadata', {}).get('user_id')
    current_user_id = request.user_id
    
    if file_user_id != current_user_id:
        return jsonify({'error': 'Access denied. You can only delete your own files'}), 403
    
    # Delete file
    try:
        if media_store.delete_file(file_obj):
            return jsonify({
                'success': True,
                'message': 'File deleted successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to delete file'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to delete file: {str(e)}'}), 500


@bp.route('/api/media/<file_id>/info', methods=['GET'])
def get_media_info(file_id):
    """
    Get media file metadata without downloading the file.
    
    Args:
        file_id: GridFS file ObjectId
        
    Returns:
        JSON with file metadata
    """
    try:
        file_obj = ObjectId(file_id)
    except Exception:
        return jsonify({'error': 'Invalid file ID'}), 400
    
    # Get file metadata
    file_doc = media_store.get_file(file_obj)
    if not file_doc:
        return jsonify({'error': 'File not found'}), 404
    
    metadata = file_doc.get('metadata', {})
    
    return jsonify({
        'success': True,
        'data': {
            'file_id': str(file_id),
            'filename': file_doc.get('filename', ''),
            'original_filename': metadata.get('original_filename', ''),
            'length': file_doc.get('length', 0),
            'content_type': metadata.get('content_type', ''),
            'media_type': metadata.get('media_type', ''),
            'upload_date': metadata.get('upload_date', ''),
            'user_id': metadata.get('user_id', '')
        }
    })
