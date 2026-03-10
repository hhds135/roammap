"""API client helper fixtures for testing API endpoints."""
import pytest
import json


class APIClient:
    """Helper class for making API requests with automatic JSON handling."""

    def __init__(self, client):
        """
        Initialize API client with Flask test client.

        Args:
            client: Flask test client
        """
        self.client = client
        self.token = None

    def set_token(self, token):
        """
        Set authentication token for requests.

        Args:
            token: JWT token string
        """
        self.token = token

    def get_headers(self, extra_headers=None):
        """
        Get headers for requests, including auth token if set.

        Args:
            extra_headers: Optional dict of additional headers

        Returns:
            dict: Headers dictionary
        """
        headers = {'Content-Type': 'application/json'}
        if extra_headers:
            headers.update(extra_headers)
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def post_json(self, endpoint, data, auth_token=None, extra_headers=None):
        """
        Make a POST request with JSON data.

        Args:
            endpoint: API endpoint path
            data: Dictionary of data to send as JSON
            auth_token: Optional JWT token for authentication
            extra_headers: Optional dict of additional headers

        Returns:
            tuple: (response, data) where response is the Flask response object
                   and data is the parsed JSON response
        """
        headers = self.get_headers(extra_headers)
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

        response = self.client.post(endpoint, json=data, headers=headers)
        response_data = response.get_json()
        return response, response_data

    def get_json(self, endpoint, auth_token=None, extra_headers=None, query_params=None):
        """
        Make a GET request expecting JSON response.

        Args:
            endpoint: API endpoint path
            auth_token: Optional JWT token for authentication
            extra_headers: Optional dict of additional headers
            query_params: Optional dict of query parameters

        Returns:
            tuple: (response, data) where response is the Flask response object
                   and data is the parsed JSON response
        """
        headers = self.get_headers(extra_headers)
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

        response = self.client.get(endpoint, headers=headers, query_string=query_params)
        response_data = response.get_json()
        return response, response_data

    def put_json(self, endpoint, data, auth_token=None, extra_headers=None):
        """
        Make a PUT request with JSON data.

        Args:
            endpoint: API endpoint path
            data: Dictionary of data to send as JSON
            auth_token: Optional JWT token for authentication
            extra_headers: Optional dict of additional headers

        Returns:
            tuple: (response, data) where response is the Flask response object
                   and data is the parsed JSON response
        """
        headers = self.get_headers(extra_headers)
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

        response = self.client.put(endpoint, json=data, headers=headers)
        response_data = response.get_json()
        return response, response_data

    def delete(self, endpoint, auth_token=None, extra_headers=None):
        """
        Make a DELETE request.

        Args:
            endpoint: API endpoint path
            auth_token: Optional JWT token for authentication
            extra_headers: Optional dict of additional headers

        Returns:
            tuple: (response, data) where response is the Flask response object
                   and data is the parsed JSON response
        """
        headers = self.get_headers(extra_headers)
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

        response = self.client.delete(endpoint, headers=headers)
        try:
            response_data = response.get_json()
        except Exception:
            response_data = None
        return response, response_data

    def post(self, endpoint, auth_token=None, extra_headers=None):
        """
        Make a POST request without JSON body.

        Args:
            endpoint: API endpoint path
            auth_token: Optional JWT token for authentication
            extra_headers: Optional dict of additional headers

        Returns:
            tuple: (response, data) where response is the Flask response object
                   and data is the parsed JSON response
        """
        headers = {}
        if extra_headers:
            headers.update(extra_headers)
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

        response = self.client.post(endpoint, headers=headers)
        try:
            response_data = response.get_json()
        except Exception:
            response_data = None
        return response, response_data

    def post_multipart(self, endpoint, data, files, auth_token=None, extra_headers=None):
        """
        Make a POST request with multipart/form-data (for file uploads).

        For Flask 3.x, we need to manually create the multipart form data
        and set the content type header.

        Args:
            endpoint: API endpoint path
            data: Dictionary of form data fields
            files: Dictionary of files to upload (e.g., {'file': FileStorage object})
            auth_token: Optional JWT token for authentication
            extra_headers: Optional dict of additional headers

        Returns:
            tuple: (response, data) where response is the Flask response object
                   and data is the parsed JSON response
        """
        # Import here to avoid circular import
        from tests.conftest import make_multipart_form_data

        headers = {}
        if extra_headers:
            headers.update(extra_headers)
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

        # For Flask 3.x, manually create multipart form data
        # Extract the file from the files dict
        file_obj = None
        file_field_name = 'file'
        if files:
            # Get the first (and usually only) file
            file_field_name, file_obj = list(files.items())[0]

        # Create multipart form data
        body, content_type = make_multipart_form_data(data, file_obj, file_field_name)
        headers['Content-Type'] = content_type

        response = self.client.post(
            endpoint,
            data=body,
            headers=headers
        )
        try:
            response_data = response.get_json()
        except Exception:
            response_data = None
        return response, response_data


@pytest.fixture
def api_client(client):
    """
    API client wrapper class with helper methods.

    Args:
        client: Flask test client fixture

    Returns:
        APIClient: Initialized API client instance
    """
    return APIClient(client)


@pytest.fixture
def clear_data(api_client):
    """
    Helper function to clear test data via clear API.

    Note: This requires a /admin/clear endpoint to be implemented
    in the application. If not available, tests should handle cleanup
    manually.

    Args:
        api_client: API client fixture

    Returns:
        function: Function that clears test data when called
    """
    def _clear(auth_token=None):
        """
        Clear test data from the application.

        Args:
            auth_token: Optional admin token for authentication

        Returns:
            bool: True if clear was successful, False otherwise
        """
        try:
            response, data = api_client.post_json('/admin/clear', {}, auth_token=auth_token)
            return response.status_code == 200
        except Exception:
            # If endpoint doesn't exist, return False
            return False

    return _clear
