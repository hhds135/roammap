"""Pytest configuration and fixtures for the test suite."""
import pytest
import sys

# Add backend directory to path to import app
BASE_DIR = sys.path[0] if '__file__' not in locals() else '/Volumes/extra/ueassignments/zj0304-01/project/backend'
sys.path.insert(0, BASE_DIR)
from app import app as flask_app

# Import fixtures from fixtures directory
from tests.fixtures.auth_fixtures import (
    sample_token,
    auth_headers,
    registered_user,
    multiple_registered_users,
)
from tests.fixtures.data_fixtures import (
    sample_corner_data,
    sample_corner_with_friends,
    sample_private_corner,
    image_file,
)
from tests.fixtures.api_fixtures import (
    api_client,
    clear_data,
)


@pytest.fixture(scope='session')
def app():
    """
    Create the Flask app for testing.

    Returns:
        Flask: The Flask application instance
    """
    app = flask_app
    app.config['TESTING'] = True
    # Flask 3.x requires this for file uploads in test client
    app.config['WTF_CSRF_ENABLED'] = False
    yield app


@pytest.fixture(scope='function')
def client(app):
    """
    Create a test client for the Flask app.

    Args:
        app: Flask application fixture

    Yields:
        Flask test client configured for testing
    """
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


def make_test_file_upload(image_file, field_name='image'):
    """
    Create a file upload for Flask 3.x test client.
    
    In Flask 3.x, the test client doesn't support the 'files' parameter directly.
    We need to use werkzeug's FormParser or create the data manually.
    
    Args:
        image_file: FileStorage object with image data
        field_name: Name of the form field
        
    Returns:
        tuple: (data, content_type) for the POST request
    """
    import io
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    
    # Read file content
    image_file.stream.seek(0)
    file_content = image_file.stream.read()
    
    # Create multipart form data
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    body = (
        f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
        f'Content-Disposition: form-data; name="{field_name}"; filename="{image_file.filename}"\r\n'
        f'Content-Type: {image_file.content_type}\r\n\r\n'
    ).encode('utf-8') + file_content + b'\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'
    
    content_type = f'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    return body, content_type


def make_multipart_form_data(data_dict, image_file=None, image_field_name='image'):
    """
    Create multipart form data for Flask 3.x test client.
    
    Args:
        data_dict: Dictionary of form fields
        image_file: Optional FileStorage object with image data
        image_field_name: Name of the image form field
        
    Returns:
        tuple: (data, content_type) for the POST request
    """
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = b''
    
    # Add form fields
    for key, value in data_dict.items():
        body += (
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
            f'{value}\r\n'
        ).encode('utf-8')
    
    # Add file if provided
    if image_file:
        image_file.stream.seek(0)
        file_content = image_file.stream.read()
        body += (
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            f'Content-Disposition: form-data; name="{image_field_name}"; filename="{image_file.filename}"\r\n'
            f'Content-Type: {image_file.content_type}\r\n\r\n'
        ).encode('utf-8') + file_content + b'\r\n'
    
    # Add closing boundary
    body += b'------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'
    
    content_type = f'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    return body, content_type


@pytest.fixture
def multipart_form_data():
    """
    Fixture for creating multipart form data for file uploads in Flask 3.x.
    
    Returns:
        function: Function that creates multipart form data
    """
    return make_multipart_form_data


def pytest_configure(config):
    """
    Pytest hook for configuration.

    This runs at the start of the test session.

    Args:
        config: Pytest config object
    """
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# Storage fixtures
@pytest.fixture
def corner_store():
    """Corner store fixture for tests."""
    from storage.corner_store import CornerStore
    return CornerStore()


@pytest.fixture
def user_store():
    """User store fixture for tests."""
    from storage.user_store import UserStore
    return UserStore()


@pytest.fixture
def post_store():
    """Post store fixture for tests."""
    from storage.post_store import PostStore
    return PostStore()


@pytest.fixture
def view_history_store():
    """View history store fixture for tests."""
    from storage.view_history_store import ViewHistoryStore
    return ViewHistoryStore()


@pytest.fixture
def like_store():
    """Like store fixture for tests."""
    from storage.like_store import LikeStore
    return LikeStore()


@pytest.fixture
def favorite_store():
    """Favorite store fixture for tests."""
    from storage.favorite_store import FavoriteStore
    return FavoriteStore()


@pytest.fixture(scope='function')
def cleanup_test_data():
    """
    Fixture to clean up test data before and after each test.
    
    This ensures tests don't fail due to duplicate keys or leftover data.
    """
    from storage.corner_store import CornerStore
    from storage.post_store import PostStore
    from storage.user_store import UserStore
    from storage.view_history_store import ViewHistoryStore
    from storage.like_store import LikeStore
    from storage.favorite_store import FavoriteStore
    from storage.comment_store import CommentStore
    from bson import ObjectId
    
    corner_store = CornerStore()
    post_store = PostStore()
    user_store = UserStore()
    view_history_store = ViewHistoryStore()
    like_store = LikeStore()
    favorite_store = FavoriteStore()
    comment_store = CommentStore()
    
    # Clean up before test
    _cleanup_all_data(
        corner_store, post_store, user_store,
        view_history_store, like_store, favorite_store, comment_store
    )
    
    yield
    
    # Clean up after test
    _cleanup_all_data(
        corner_store, post_store, user_store,
        view_history_store, like_store, favorite_store, comment_store
    )


def _cleanup_all_data(corner_store, post_store, user_store,
                      view_history_store, like_store, favorite_store, comment_store):
    """
    Clean up all test data from collections.
    
    Args:
        corner_store: CornerStore instance
        post_store: PostStore instance
        user_store: UserStore instance
        view_history_store: ViewHistoryStore instance
        like_store: LikeStore instance
        favorite_store: FavoriteStore instance
        comment_store: CommentStore instance
    """
    # Clear view history
    try:
        view_history_store.collection.delete_many({})
    except Exception:
        pass
    
    # Clear comments
    try:
        comment_store.collection.delete_many({})
    except Exception:
        pass
    
    # Clear likes
    try:
        like_store.collection.delete_many({})
    except Exception:
        pass
    
    # Clear favorites
    try:
        favorite_store.collection.delete_many({})
    except Exception:
        pass
    
    # Clear posts
    try:
        post_store.collection.delete_many({})
    except Exception:
        pass
    
    # Clear corners (excluding preset ones if any)
    try:
        corner_store.collection.delete_many({})
    except Exception:
        pass
    
    # Clear users (be careful with this in production)
    try:
        # Only delete test users (those with 'test' in username)
        user_store.collection.delete_many({'username': {'$regex': 'test', '$options': 'i'}})
    except Exception:
        pass
