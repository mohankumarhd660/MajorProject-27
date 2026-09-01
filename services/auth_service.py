from werkzeug.security import check_password_hash, generate_password_hash

from models.user import User
from utils.db import get_db_session
from services.firebase_service import (
    init_firebase, 
    create_firebase_user, 
    get_user_by_email,
    sign_in_with_email_password,
    is_firebase_available
)


def create_user(username: str, password: str, role: str, email: str = None) -> User:
    db = get_db_session()
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise ValueError("Username already exists")

    if email:
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            raise ValueError("Email already registered")

    if role not in {"student", "teacher"}:
        raise ValueError("Invalid role")

    firebase_uid = None
    
    # Try to create Firebase user if available
    if is_firebase_available() and email:
        try:
            fb_user = create_firebase_user(email, password, display_name=username)
            firebase_uid = fb_user['uid']
        except ValueError as e:
            # If Firebase user already exists, try to get the UID
            if "already registered" in str(e):
                existing_fb = get_user_by_email(email)
                if existing_fb:
                    firebase_uid = existing_fb['uid']
            else:
                raise e

    user = User(
        username=username, 
        password_hash=generate_password_hash(password), 
        role=role,
        email=email,
        firebase_uid=firebase_uid
    )
    db.add(user)
    
    from sqlalchemy.exc import IntegrityError
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Database error: Unique constraint failed. Email or username already exists.")
        
    db.refresh(user)
    return user


def authenticate(username: str, password: str) -> User | None:
    db = get_db_session()
    identifier = username.strip()

    # Local auth by username first
    user = db.query(User).filter(User.username == identifier).first()
    if user and check_password_hash(user.password_hash, password) and user.is_active:
        return user

    # Local auth by email as a fallback
    user = db.query(User).filter(User.email == identifier).first()
    if user and check_password_hash(user.password_hash, password) and user.is_active:
        return user

    # Firebase auth with email/password if available
    if is_firebase_available() and "@" in identifier:
        try:
            fb_user = sign_in_with_email_password(identifier, password)
        except ValueError:
            return None
        if not fb_user:
            return None
        user = authenticate_by_firebase(fb_user.get("email"), fb_user["uid"])
        if user and user.is_active:
            return user

    return None


def authenticate_by_firebase(email: str, firebase_uid: str, name: str = None) -> User | None:
    """Authenticate or create user based on Firebase credentials."""
    db = get_db_session()
    
    # Try to find user by Firebase UID
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if user:
        return user
    
    # Try to find by email and link Firebase UID
    if email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.firebase_uid = firebase_uid
            db.commit()
            return user
            
        # If no user exists, create a new one automatically
        import secrets
        from werkzeug.security import generate_password_hash
        
        username = name.replace(" ", "").lower() if name else email.split("@")[0]
        base_username = username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}{counter}"
            counter += 1
            
        random_pass = secrets.token_hex(16)
        user = User(
            username=username,
            password_hash=generate_password_hash(random_pass),
            role="student",
            email=email,
            firebase_uid=firebase_uid
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    return None
