"""SQLAlchemy database models for DING application."""
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """User model for authentication and job tracking."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    auth_pins = relationship("AuthPin", back_populates="user", cascade="all, delete-orphan")
    session = relationship("UserSession", back_populates="user", uselist=False, cascade="all, delete-orphan")
    jobs = relationship("DingJob", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class AuthPin(Base):
    """Authentication PIN model for email-based login."""

    __tablename__ = "auth_pins"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    pin = Column(String(4), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    used = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="auth_pins")

    def __repr__(self):
        return f"<AuthPin(id={self.id}, user_id={self.user_id}, used={self.used})>"


class UserSession(Base):
    """User session model for maintaining login state."""

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="session")

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"


class AppConfig(Base):
    """Application configuration parameters."""

    __tablename__ = "app_config"

    key = Column(String(100), primary_key=True)
    value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AppConfig(key='{self.key}', value='{self.value}')>"


class DingJob(Base):
    """Printer job model for tracking dings."""

    __tablename__ = "ding_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_type = Column(String(50), nullable=False)  # text, image, text_with_image
    content_type = Column(String(50), nullable=False)  # plain, cowsay, banner
    text_content = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)
    font_size = Column(String(20), nullable=True)  # small, medium, large
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, processing, success, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="jobs")

    def __repr__(self):
        return f"<DingJob(id={self.id}, type='{self.job_type}', status='{self.status}')>"
