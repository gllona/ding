"""Database session management and initialization."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from core.config import settings
from core.models import Base


# Create database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def init_default_config():
    """Initialize default configuration parameters."""
    from core.models import AppConfig

    db = SessionLocal()
    try:
        # Check if config already exists
        existing_config = db.query(AppConfig).first()
        if existing_config:
            print("⚠️  Configuration already exists, skipping initialization")
            return

        default_configs = {
            # Session & Authentication
            "session_timeout_minutes": "180",
            "session_warning_minutes": "5",
            "pin_rate_limit_minutes": "1",
            "pin_expiry_minutes": "10",

            # Printer Settings
            "printer_dots_per_line": "384",
            "feed_before_lines": "1",
            "feed_after_lines": "3",
            "cut_paper": "true",

            # Font Sizes - Text Characters Per Line
            "text_chars_per_line_small": "48",
            "text_chars_per_line_medium": "32",
            "text_chars_per_line_large": "24",

            # Font Sizes - Cowsay Characters Per Line
            "cowsay_chars_per_line_small": "40",
            "cowsay_chars_per_line_medium": "28",
            "cowsay_chars_per_line_large": "20",
        }

        for key, value in default_configs.items():
            config = AppConfig(key=key, value=value)
            db.add(config)

        db.commit()
        print(f"✅ Initialized {len(default_configs)} default configuration parameters")

    except Exception as e:
        db.rollback()
        print(f"❌ Error initializing configuration: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing DING database...")
    init_db()
    init_default_config()
    print("✅ Database initialization complete!")
