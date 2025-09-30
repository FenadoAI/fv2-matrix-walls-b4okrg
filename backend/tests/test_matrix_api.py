"""Test Matrix social network API endpoints."""

import os
import time

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API URL from environment
API_BASE = os.getenv("BACKEND_API_URL", "http://localhost:8001")
API_URL = f"{API_BASE}/api"

print(f"Testing API at: {API_URL}")


def test_register_and_login():
    """Test user registration and login flow."""
    timestamp = int(time.time())
    test_user = {"username": f"neo_{timestamp}", "password": "followthewhiterabbit"}

    # Test registration
    print("\n1. Testing user registration...")
    response = requests.post(f"{API_URL}/register", json=test_user)
    print(f"   Status: {response.status_code}")

    if response.status_code != 200:
        print(f"   ERROR: {response.text}")
        raise AssertionError(f"Registration failed: {response.text}")

    data = response.json()
    assert "access_token" in data, "No access token in response"
    assert data["user"]["username"] == test_user["username"], "Username mismatch"
    print(f"   ✓ User registered: {data['user']['username']}")

    token = data["access_token"]

    # Test login
    print("\n2. Testing user login...")
    response = requests.post(f"{API_URL}/login", json=test_user)
    print(f"   Status: {response.status_code}")

    if response.status_code != 200:
        print(f"   ERROR: {response.text}")
        raise AssertionError(f"Login failed: {response.text}")

    data = response.json()
    assert "access_token" in data, "No access token in login response"
    print(f"   ✓ Login successful")

    return test_user["username"], token


def test_post_on_own_wall(username, token):
    """Test posting on own wall."""
    print("\n3. Testing post on own wall...")

    post_data = {"wall_owner": username, "content": "Wake up, Neo... The Matrix has you..."}

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/posts", json=post_data, headers=headers)
    print(f"   Status: {response.status_code}")

    if response.status_code != 200:
        print(f"   ERROR: {response.text}")
        raise AssertionError(f"Failed to create post: {response.text}")

    post = response.json()
    assert post["author"] == username, "Author mismatch"
    assert post["wall_owner"] == username, "Wall owner mismatch"
    assert post["content"] == post_data["content"], "Content mismatch"
    print(f"   ✓ Post created on {username}'s wall")

    return post


def test_get_wall_posts(username):
    """Test retrieving wall posts."""
    print(f"\n4. Testing get wall posts for {username}...")

    response = requests.get(f"{API_URL}/posts/{username}")
    print(f"   Status: {response.status_code}")

    if response.status_code != 200:
        print(f"   ERROR: {response.text}")
        raise AssertionError(f"Failed to get posts: {response.text}")

    posts = response.json()
    assert isinstance(posts, list), "Posts should be a list"
    assert len(posts) > 0, "Should have at least one post"
    print(f"   ✓ Retrieved {len(posts)} post(s)")

    return posts


def test_post_on_another_wall(wall_owner, author_username, author_token):
    """Test posting on another user's wall."""
    print(f"\n5. Testing post on {wall_owner}'s wall by {author_username}...")

    post_data = {"wall_owner": wall_owner, "content": "I know kung fu."}

    headers = {"Authorization": f"Bearer {author_token}"}
    response = requests.post(f"{API_URL}/posts", json=post_data, headers=headers)
    print(f"   Status: {response.status_code}")

    if response.status_code != 200:
        print(f"   ERROR: {response.text}")
        raise AssertionError(f"Failed to post on another wall: {response.text}")

    post = response.json()
    assert post["author"] == author_username, "Author should be the poster"
    assert post["wall_owner"] == wall_owner, "Wall owner should be the target user"
    print(f"   ✓ {author_username} posted on {wall_owner}'s wall")


def test_get_users():
    """Test getting list of users."""
    print("\n6. Testing get users list...")

    response = requests.get(f"{API_URL}/users")
    print(f"   Status: {response.status_code}")

    if response.status_code != 200:
        print(f"   ERROR: {response.text}")
        raise AssertionError(f"Failed to get users: {response.text}")

    users = response.json()
    assert isinstance(users, list), "Users should be a list"
    assert len(users) > 0, "Should have at least one user"
    print(f"   ✓ Retrieved {len(users)} user(s)")

    return users


def test_duplicate_registration():
    """Test that duplicate registration fails."""
    print("\n7. Testing duplicate registration (should fail)...")

    test_user = {"username": "morpheus_test", "password": "redpill"}

    # First registration should succeed
    response1 = requests.post(f"{API_URL}/register", json=test_user)
    if response1.status_code == 200:
        print(f"   ✓ First registration succeeded")
    else:
        # User might already exist from previous test runs
        print(f"   → User already exists from previous test")

    # Second registration should fail
    response2 = requests.post(f"{API_URL}/register", json=test_user)
    print(f"   Status: {response2.status_code}")

    if response2.status_code == 400:
        print(f"   ✓ Duplicate registration properly rejected")
    else:
        raise AssertionError(f"Duplicate registration should fail with 400, got {response2.status_code}")


if __name__ == "__main__":
    print("=" * 60)
    print("MATRIX SOCIAL NETWORK API TESTS")
    print("=" * 60)

    try:
        # Test authentication
        user1, token1 = test_register_and_login()

        # Test posting on own wall
        test_post_on_own_wall(user1, token1)

        # Test getting wall posts
        test_get_wall_posts(user1)

        # Create second user and test cross-wall posting
        user2, token2 = test_register_and_login()
        test_post_on_another_wall(user1, user2, token2)

        # Test get users
        test_get_users()

        # Test duplicate registration
        test_duplicate_registration()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)

    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 60)
        exit(1)
    except requests.exceptions.ConnectionError:
        print("\n" + "=" * 60)
        print("✗ CONNECTION ERROR: Is the backend server running on port 8001?")
        print("Start it with: cd backend && uvicorn server:app --reload --port 8001")
        print("=" * 60)
        exit(1)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ UNEXPECTED ERROR: {e}")
        print("=" * 60)
        raise