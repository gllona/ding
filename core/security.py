"""Security utilities for PIN generation, validation, and session management."""
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from core.models import AuthPin, User, UserSession


def generate_pin() -> str:
    """Generate a random 4-digit PIN."""
    return ''.join(secrets.choice(string.digits) for _ in range(4))


def generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_urlsafe(32)


def create_pin_for_user(db: Session, user_id: int, expiry_minutes: int = 10) -> str:
    """
    Create a new PIN for user and invalidate all previous unused PINs.

    Args:
        db: Database session
        user_id: User ID
        expiry_minutes: PIN expiration time in minutes

    Returns:
        The generated PIN
    """
    # Invalidate all previous unused PINs for this user
    db.query(AuthPin).filter(
        AuthPin.user_id == user_id,
        AuthPin.used == False
    ).update({"used": True})

    # Generate new PIN
    pin = generate_pin()
    expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)

    # Create PIN record
    auth_pin = AuthPin(
        user_id=user_id,
        pin=pin,
        expires_at=expires_at,
        used=False
    )
    db.add(auth_pin)
    db.commit()
    db.refresh(auth_pin)

    return pin


def validate_pin(db: Session, username: str, pin: str) -> Optional[User]:
    """
    Validate a PIN for a user.

    Args:
        db: Database session
        username: Username
        pin: PIN to validate

    Returns:
        User object if PIN is valid, None otherwise
    """
    # Get user
    user = db.query(User).filter(
        User.username == username,
        User.is_active == True
    ).first()

    if not user:
        return None

    # Get PIN record
    auth_pin = db.query(AuthPin).filter(
        AuthPin.user_id == user.id,
        AuthPin.pin == pin,
        AuthPin.used == False,
        AuthPin.expires_at > datetime.utcnow()
    ).first()

    if not auth_pin:
        return None

    # Mark PIN as used
    auth_pin.used = True
    db.commit()

    return user


def can_request_pin(db: Session, user_id: int, rate_limit_minutes: int = 1) -> bool:
    """
    Check if user can request a new PIN (rate limiting).

    Args:
        db: Database session
        user_id: User ID
        rate_limit_minutes: Minimum minutes between PIN requests

    Returns:
        True if user can request PIN, False otherwise
    """
    # Get most recent PIN for user
    last_pin = db.query(AuthPin).filter(
        AuthPin.user_id == user_id
    ).order_by(AuthPin.created_at.desc()).first()

    if not last_pin:
        return True

    # Check if enough time has passed
    time_since_last = datetime.utcnow() - last_pin.created_at
    return time_since_last >= timedelta(minutes=rate_limit_minutes)


def create_session(db: Session, user_id: int, timeout_minutes: int = 180) -> str:
    """
    Create a new session for user. Invalidates any existing session.

    Args:
        db: Database session
        user_id: User ID
        timeout_minutes: Session timeout in minutes

    Returns:
        Session token
    """
    # Delete existing session for this user
    db.query(UserSession).filter(UserSession.user_id == user_id).delete()

    # Generate session token
    session_token = generate_session_token()
    expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)

    # Create session
    session = UserSession(
        user_id=user_id,
        session_token=session_token,
        expires_at=expires_at,
        last_activity=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return session_token


def validate_session(db: Session, session_token: str, extend: bool = True, timeout_minutes: int = 180) -> Optional[User]:
    """
    Validate a session token and optionally extend it.

    Args:
        db: Database session
        session_token: Session token to validate
        extend: Whether to extend session on activity
        timeout_minutes: Session timeout in minutes (for extension)

    Returns:
        User object if session is valid, None otherwise
    """
    # Get session
    session = db.query(UserSession).filter(
        UserSession.session_token == session_token,
        UserSession.expires_at > datetime.utcnow()
    ).first()

    if not session:
        return None

    # Get user
    user = db.query(User).filter(
        User.id == session.user_id,
        User.is_active == True
    ).first()

    if not user:
        return None

    # Extend session if requested
    if extend:
        session.last_activity = datetime.utcnow()
        session.expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)
        db.commit()

    return user


def delete_session(db: Session, session_token: str):
    """
    Delete a session (logout).

    Args:
        db: Database session
        session_token: Session token to delete
    """
    db.query(UserSession).filter(UserSession.session_token == session_token).delete()
    db.commit()


def get_session_expiry(db: Session, session_token: str) -> Optional[datetime]:
    """
    Get session expiry time.

    Args:
        db: Database session
        session_token: Session token

    Returns:
        Expiry datetime or None if session doesn't exist
    """
    session = db.query(UserSession).filter(
        UserSession.session_token == session_token
    ).first()

    return session.expires_at if session else None
