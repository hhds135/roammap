"""Tests for the health check endpoint."""


def test_health_check_returns_200(client):
    """Test that health check returns 200 status."""
    response = client.get('/api/health')
    assert response.status_code == 200


def test_health_check_returns_json(client):
    """Test that health check returns JSON response."""
    response = client.get('/api/health')
    assert response.content_type.startswith('application/json')


def test_health_check_contains_status(client):
    """Test that health check contains status field."""
    response = client.get('/api/health')
    data = response.get_json()
    assert 'status' in data
    assert data['status'] == 'healthy'


def test_health_check_contains_message(client):
    """Test that health check contains message field."""
    response = client.get('/api/health')
    data = response.get_json()
    assert 'message' in data
    assert 'running' in data['message'].lower()
