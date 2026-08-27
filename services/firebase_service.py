import os
from pathlib import Path

import firebase_admin
import requests
from firebase_admin import auth, credentials

# Global Firebase app instance
_firebase_app = None


def init_firebase():
    """Initialize Firebase Admin SDK with service account credentials."""
    global _firebase_app
    
    if _firebase_app is not None:
        return _firebase_app
    
    cred_env = os.getenv("FIREBASE_CREDENTIALS", "firebase_key.json")
    
    try:
        if cred_env.strip().startswith('{'):
            # It's a JSON string from environment variables
            import json
            cred_dict = json.loads(cred_env)
            cred = credentials.Certificate(cred_dict)
        else:
            # It's a file path
            if not Path(cred_env).exists():
                print(f"Warning: Firebase credentials file not found at {cred_env}")
                print("Firebase authentication will be disabled.")
                return None
            cred = credentials.Certificate(cred_env)
            
        _firebase_app = firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully")
        return _firebase_app
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return None


def create_firebase_user(email: str, password: str, display_name: str = None) -> dict:
    """Create a new user in Firebase Authentication."""
    app = init_firebase()
    if app is None:
        raise ValueError("Firebase not initialized")
    
    user_properties = {
        'email': email,
        'password': password,
    }
    
    if display_name:
        user_properties['display_name'] = display_name
    
    try:
        user = auth.create_user(**user_properties)
        return {
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name,
        }
    except auth.EmailAlreadyExistsError:
        raise ValueError("Email already registered")
    except Exception as e:
        raise ValueError(f"Failed to create user: {str(e)}")


def verify_firebase_token(id_token: str) -> dict:
    """Verify Firebase ID token and return user info."""
    app = init_firebase()
    if app is None:
        raise ValueError("Firebase not initialized")
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        return {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
        }
    except Exception as e:
        raise ValueError(f"Invalid token: {str(e)}")


def sign_in_with_email_password(email: str, password: str) -> dict:
    """Sign in with Firebase email/password via Identity Toolkit API."""
    api_key = os.getenv("FIREBASE_API_KEY")
    if not api_key:
        raise ValueError("FIREBASE_API_KEY is not configured")

    endpoint = (
        "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
        f"?key={api_key}"
    )
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True,
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=10)
        data = response.json()
    except requests.RequestException as e:
        raise ValueError(f"Firebase sign-in request failed: {str(e)}")

    if response.status_code != 200:
        error_message = data.get("error", {}).get("message", "UNKNOWN")
        if error_message in {"EMAIL_NOT_FOUND", "INVALID_PASSWORD", "INVALID_LOGIN_CREDENTIALS"}:
            return None
        raise ValueError(f"Firebase sign-in failed: {error_message}")

    return {
        "uid": data.get("localId"),
        "email": data.get("email"),
        "id_token": data.get("idToken"),
    }


def get_user_by_email(email: str) -> dict:
    """Get Firebase user by email."""
    app = init_firebase()
    if app is None:
        raise ValueError("Firebase not initialized")
    
    try:
        user = auth.get_user_by_email(email)
        return {
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name,
        }
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        raise ValueError(f"Error fetching user: {str(e)}")


def delete_firebase_user(uid: str):
    """Delete a user from Firebase Authentication."""
    app = init_firebase()
    if app is None:
        raise ValueError("Firebase not initialized")
    
    try:
        auth.delete_user(uid)
        return True
    except Exception as e:
        raise ValueError(f"Failed to delete user: {str(e)}")


def is_firebase_available() -> bool:
    """Check if Firebase is available and initialized."""
    return _firebase_app is not None
