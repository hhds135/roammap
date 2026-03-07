"""Pytest configuration and fixtures for the test suite."""
import pytest
import os
import shutil
import sys
from datetime import datetime

# Absolute paths to data files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, 'data')
BACKUPS_DIR = os.path.join(BACKEND_DIR, 'backups')

USERS_FILE = os.path.join(DATA_DIR, 'users.json')
CORNERS_FILE = os.path.join(DATA_DIR, 'corners.json')

# Add backend directory to path to import app
sys.path.insert(0, BACKEND_DIR)
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


@pytest.fixture(scope='session', autouse=True)
def backup_before_tests():
    """
    Session-scoped fixture that automatically backs up data files before running tests.

    This fixture runs automatically before all tests:
    - Creates backups/ directory if it doesn't exist
    - Backs up data/users.json and data/corners.json with timestamp
    - Creates empty files if they don't exist
    - Prints backup confirmation

    Yields:
        None: Control returns to tests after backup is complete
    """
    # Create backups directory if it doesn't exist
    if not os.path.exists(BACKUPS_DIR):
        os.makedirs(BACKUPS_DIR)
        print(f"\n[BACKUP] Created backups directory: {BACKUPS_DIR}")

    # Generate timestamp for backup files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Backup users.json
    if os.path.exists(USERS_FILE):
        users_backup = os.path.join(BACKUPS_DIR, f'users_{timestamp}.json')
        shutil.copy2(USERS_FILE, users_backup)
        print(f"[BACKUP] Backed up users.json -> {users_backup}")
    else:
        # Create empty users.json if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(USERS_FILE, 'w') as f:
            f.write('[]')
        print(f"[BACKUP] Created empty users.json: {USERS_FILE}")

    # Backup corners.json
    if os.path.exists(CORNERS_FILE):
        corners_backup = os.path.join(BACKUPS_DIR, f'corners_{timestamp}.json')
        shutil.copy2(CORNERS_FILE, corners_backup)
        print(f"[BACKUP] Backed up corners.json -> {corners_backup}")
    else:
        # Create empty corners.json if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CORNERS_FILE, 'w') as f:
            f.write('[]')
        print(f"[BACKUP] Created empty corners.json: {CORNERS_FILE}")

    print(f"[BACKUP] Test data backup completed at {datetime.now()}\n")

    # Yield control to tests
    yield

    # Cleanup after all tests complete (optional)
    print(f"\n[BACKUP] Test session completed at {datetime.now()}")


@pytest.fixture
def clean_test_data():
    """
    Function-scoped fixture for optional test cleanup.

    This fixture can be used in tests that want to clean up data
    after each test. It's not automatically used - tests must
    explicitly request it.

    Example usage:
        def test_something(clean_test_data):
            # perform test
            clean_test_data()

    Returns:
        function: Function that clears test data when called
    """
    def _clean():
        """
        Clear all test data by resetting data files to empty arrays.

        Returns:
            None
        """
        with open(USERS_FILE, 'w') as f:
            f.write('[]')

        with open(CORNERS_FILE, 'w') as f:
            f.write('[]')

    return _clean


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
