"""Test data generation fixtures for corners and images."""
import pytest
import io
from werkzeug.datastructures import FileStorage


def create_test_image_bytes():
    """Create a minimal valid PNG image bytes."""
    png_data = (
        b'\x89PNG\r\n\x1a\n'
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00'
        b'\x90wS\xde'
        b'\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01'
        b' \xf8\xa6\x05\x00'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return png_data


@pytest.fixture
def sample_corner_data():
    """
    Sample corner data with public visibility.

    Returns:
        dict: Corner data dictionary with public visibility
    """
    return {
        'title': 'Test Corner',
        'description': 'This is a test corner',
        'latitude': 35.6762,
        'longitude': 139.6503,
        'visibility': 'public',
        'tags': ['test', 'sample']
    }


@pytest.fixture
def sample_corner_with_friends():
    """
    Corner data with friends-only visibility.

    Returns:
        dict: Corner data dictionary with friends-only visibility
    """
    return {
        'title': 'Friends Corner',
        'description': 'Only friends can see this corner',
        'latitude': 35.6762,
        'longitude': 139.6503,
        'visibility': 'friends',
        'tags': ['friends', 'private']
    }


@pytest.fixture
def sample_private_corner():
    """
    Corner data with private visibility.

    Returns:
        dict: Corner data dictionary with private visibility
    """
    return {
        'title': 'Private Corner',
        'description': 'Only owner can see this corner',
        'latitude': 35.6762,
        'longitude': 139.6503,
        'visibility': 'private',
        'tags': ['private']
    }


@pytest.fixture
def image_file():
    """
    Test image file (werkzeug FileStorage).

    Returns:
        FileStorage: A FileStorage object containing test image data
    """
    png_data = create_test_image_bytes()
    file_obj = io.BytesIO(png_data)
    
    # Create a FileStorage object (compatible with Flask test client)
    file_storage = FileStorage(
        stream=file_obj,
        filename='test_image.png',
        content_type='image/png'
    )
    
    return file_storage
