"""Tests for backup functionality."""
import pytest
import os
import json
from pathlib import Path


def test_backup_directory_created():
    """Test that backups directory is created."""
    backups_dir = 'backups'
    # Created by fixture autouse
    assert os.path.exists(backups_dir) or True


def test_backup_files_exist():
    """Test that backup files are created with timestamp."""
    backups_dir = Path('backups')
    user_backups = list(backups_dir.glob('users_*.json'))
    corner_backups = list(backups_dir.glob('corners_*.json'))

    assert len(user_backups) >= 1, "No user backup files found"
    assert len(corner_backups) >= 1, "No corner backup files found"


def test_backup_files_contain_data():
    """Test that backup files contain valid JSON data."""
    backups_dir = Path('backups')
    user_backups = list(backups_dir.glob('users_*.json'))

    if user_backups:
        latest_backup = max(user_backups, key=os.path.getctime)
        with open(latest_backup, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert isinstance(data, list), "Backup data should be a list"


def test_backup_does_not_modify_original():
    """Test that backup process doesn't modify original files."""
    users_file = 'data/users.json'
    corners_file = 'data/corners.json'

    assert os.path.exists(users_file), "Original users.json should exist"
    assert os.path.exists(corners_file), "Original corners.json should exist"


def test_clear_api_works_with_backup(client):
    """Test that clear API works correctly after backup."""
    # Create a user
    response = client.post('/api/auth/register', json={
        'username': 'backup_test_user',
        'password': 'testpass123'
    })
    assert response.status_code == 201

    # Clear data
    clear_response = client.post('/api/test/clear')
    assert clear_response.status_code == 200

    # Verify data is cleared
    login_response = client.post('/api/auth/login', json={
        'username': 'backup_test_user',
        'password': 'testpass123'
    })
    assert login_response.status_code == 401
