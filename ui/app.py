"""Main Streamlit application for DING."""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from datetime import datetime, timedelta

from core.database import get_db
from core.security import validate_session, get_session_expiry
from core.config import settings

# Page config
st.set_page_config(
    page_title="DING - Retro Printer",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom CSS
css_path = Path(__file__).parent / "styles" / "retro.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def check_session():
    """Check if user has valid session."""
    if "session_token" not in st.session_state:
        return None

    db = next(get_db())
    user = validate_session(
        db=db,
        session_token=st.session_state.session_token,
        extend=True,
        timeout_minutes=int(st.session_state.get("session_timeout_minutes", 180))
    )

    # Extract user data before closing session
    if user:
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active
        }
        db.close()
        return user_data

    db.close()
    return None


def show_session_timer(user):
    """Display session timer and warning."""
    if "session_token" not in st.session_state:
        return

    db = next(get_db())
    expires_at = get_session_expiry(db, st.session_state.session_token)
    db.close()

    if expires_at:
        time_left = expires_at - datetime.utcnow()
        minutes_left = int(time_left.total_seconds() / 60)

        # Show warning if less than 5 minutes
        warning_minutes = int(st.session_state.get("session_warning_minutes", 5))
        if minutes_left <= warning_minutes and minutes_left > 0:
            st.warning(f"⚠️ Session expires in {minutes_left} minutes!")

        # Display timer
        hours = minutes_left // 60
        mins = minutes_left % 60
        st.sidebar.markdown(f"### ⏰ Session: {hours}:{mins:02d}")


def logout():
    """Logout user."""
    from core.security import delete_session

    if "session_token" in st.session_state:
        db = next(get_db())
        delete_session(db, st.session_state.session_token)
        db.close()

    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


def main():
    """Main application entry point."""
    # Check if user is logged in
    user = check_session()

    if user:
        # User is logged in - show ding page
        st.session_state.user = user

        # Sidebar with session info and logout
        with st.sidebar:
            st.markdown(f"### 👤 {user['username']}")
            show_session_timer(user)

            if st.button("🚪 LOGOUT", use_container_width=True):
                logout()

        # Import and show ding page
        from ui.pages.ding import show_ding_page
        show_ding_page()

    else:
        # User not logged in - show login page
        from ui.pages.login import show_login_page
        show_login_page()


if __name__ == "__main__":
    main()
