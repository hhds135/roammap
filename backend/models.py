"""Data access layer for managing users and corners."""
import json
import os
import uuid
from config import Config


def init_data_files():
    """Initialize data files if they don't exist."""
    os.makedirs(Config.DATA_FOLDER, exist_ok=True)
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    if not os.path.exists(Config.USERS_FILE):
        with open(Config.USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)

    if not os.path.exists(Config.CORNERS_FILE):
        with open(Config.CORNERS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    else:
        # Add share_id to existing corners if not present
        corners = load_corners()
        updated = False
        for corner in corners:
            if 'share_id' not in corner:
                corner['share_id'] = str(uuid.uuid4())
                updated = True
        if updated:
            save_corners(corners)


# Data read operations
def load_users():
    """Load users from JSON file."""
    try:
        with open(Config.USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def load_corners():
    """Load corners from JSON file."""
    try:
        with open(Config.CORNERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


# Data save operations
def save_users(users):
    """Save users to JSON file."""
    with open(Config.USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def save_corners(corners):
    """Save corners to JSON file."""
    with open(Config.CORNERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(corners, f, ensure_ascii=False, indent=2)


# User lookup functions
def find_user_by_username(username):
    """Find user by username."""
    users = load_users()
    return next((user for user in users if user['username'] == username), None)


def find_user_by_id(user_id):
    """Find user by ID."""
    users = load_users()
    return next((user for user in users if user['id'] == user_id), None)


# Friend system functions
def get_user_friends(user_id):
    """Get user's friend list."""
    user = find_user_by_id(user_id)
    if user:
        return user.get('friends', [])
    return []


def add_friend_request(sender_id, receiver_id):
    """
    Send a friend request.

    Args:
        sender_id: ID of the user sending the request
        receiver_id: ID of the user receiving the request

    Returns:
        tuple: (success: bool, message: str)
    """
    users = load_users()

    # Check if users exist
    sender = find_user_by_id(sender_id)
    receiver = find_user_by_id(receiver_id)

    if not sender or not receiver:
        return False, 'User not found'

    # Check if already friends
    if receiver_id in sender.get('friends', []):
        return False, 'Already friends'

    # Check if request already sent
    for user in users:
        if user['id'] == receiver_id:
            friend_requests = user.get('friend_requests', [])
            if sender_id in friend_requests:
                return False, 'Friend request already sent'

    # Add friend request
    for user in users:
        if user['id'] == receiver_id:
            if 'friend_requests' not in user:
                user['friend_requests'] = []
            if sender_id not in user['friend_requests']:
                user['friend_requests'].append(sender_id)

    save_users(users)
    return True, 'Friend request sent'


def accept_friend_request(receiver_id, sender_id):
    """
    Accept a friend request.

    Args:
        receiver_id: ID of the user receiving the request
        sender_id: ID of the user who sent the request

    Returns:
        tuple: (success: bool, message: str)
    """
    users = load_users()

    # Check if users exist
    receiver = find_user_by_id(receiver_id)
    sender = find_user_by_id(sender_id)

    if not receiver or not sender:
        return False, 'User not found'

    # Check if friend request exists
    friend_requests = receiver.get('friend_requests', [])
    if sender_id not in friend_requests:
        return False, 'Friend request not found'

    # Add friends bidirectionally
    for user in users:
        if user['id'] == receiver_id:
            user['friend_requests'].remove(sender_id)
            if 'friends' not in user:
                user['friends'] = []
            if sender_id not in user['friends']:
                user['friends'].append(sender_id)
        elif user['id'] == sender_id:
            if 'friends' not in user:
                user['friends'] = []
            if receiver_id not in user['friends']:
                user['friends'].append(receiver_id)

    save_users(users)
    return True, 'Friend request accepted'


def reject_friend_request(receiver_id, sender_id):
    """
    Reject a friend request.

    Args:
        receiver_id: ID of the user receiving the request
        sender_id: ID of the user who sent the request

    Returns:
        tuple: (success: bool, message: str)
    """
    users = load_users()

    # Check if user exists
    receiver = find_user_by_id(receiver_id)
    if not receiver:
        return False, 'User not found'

    # Check if friend request exists
    friend_requests = receiver.get('friend_requests', [])
    if sender_id not in friend_requests:
        return False, 'Friend request not found'

    # Remove friend request
    for user in users:
        if user['id'] == receiver_id:
            user['friend_requests'].remove(sender_id)

    save_users(users)
    return True, 'Friend request rejected'


def remove_friend(user_id, friend_id):
    """
    Remove a friend.

    Args:
        user_id: ID of the user removing the friend
        friend_id: ID of the friend to remove

    Returns:
        tuple: (success: bool, message: str)
    """
    users = load_users()

    # Check if users exist
    user = find_user_by_id(user_id)
    friend = find_user_by_id(friend_id)

    if not user or not friend:
        return False, 'User not found'

    # Check if friends
    if friend_id not in user.get('friends', []):
        return False, 'Not friends'

    # Remove friend bidirectionally
    for user in users:
        if user['id'] == user_id:
            user['friends'].remove(friend_id)
        elif user['id'] == friend_id:
            user['friends'].remove(user_id)

    save_users(users)
    return True, 'Friend removed'


def get_friend_requests(user_id):
    """
    Get user's friend request list.

    Args:
        user_id: ID of the user

    Returns:
        list: List of sender IDs
    """
    user = find_user_by_id(user_id)
    if user:
        return user.get('friend_requests', [])
    return []


def is_friend(user_id1, user_id2):
    """
    Check if two users are friends.

    Args:
        user_id1: ID of user 1
        user_id2: ID of user 2

    Returns:
        bool: True if users are friends, False otherwise
    """
    users = load_users()
    user1 = find_user_by_id(user_id1)
    user2 = find_user_by_id(user_id2)

    if not user1 or not user2:
        return False

    # Check if user1 is in user2's friend list and vice versa
    friends1 = user1.get('friends', [])
    friends2 = user2.get('friends', [])

    return user_id2 in friends1 and user_id1 in friends2


def can_access_corner(user_id, corner):
    """
    Check if a user can access a corner.

    Args:
        user_id: ID of the user
        corner: Corner object

    Returns:
        bool: True if user can access the corner, False otherwise
    """
    # Corner creator can always access
    if user_id == corner.get('user_id'):
        return True

    # Get visibility strategy
    visibility = corner.get('visibility', 'public')

    if visibility == 'public':
        # Public: visible to everyone
        return True
    elif visibility == 'private':
        # Private: only visible to creator
        return False
    elif visibility == 'friends':
        # Friends only: check if user is a friend
        return is_friend(user_id, corner.get('user_id'))
    elif visibility == 'specific_friends':
        # Specific friends: check if user is a friend and in the list
        specific_friends = corner.get('specific_friends', [])
        return is_friend(user_id, corner.get('user_id')) and user_id in specific_friends
    elif visibility == 'exclude_friends':
        # Exclude friends: check if user is a friend but not in exclude list
        exclude_friends = corner.get('exclude_friends', [])
        return is_friend(user_id, corner.get('user_id')) and user_id not in exclude_friends
    else:
        # Default: public
        return True
