"""Login page for DING Streamlit UI."""
import streamlit as st
from datetime import datetime

from core.database import get_db
from core.models import User, AppConfig
from core.security import create_pin_for_user, validate_pin, can_request_pin, create_session
from services.email import send_pin_email


def show_login_page():
    """Display login page."""
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 4rem; color: #00FFFF; text-shadow: 0 0 10px #00FFFF;'>
            🖨️ D I N G 🖨️
        </h1>
        <p style='font-size: 1.2rem; color: #00FF00;'>
            [ Retro Receipt Printer ]
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Initialize session state
    if "login_step" not in st.session_state:
        st.session_state.login_step = "username"
    if "login_username" not in st.session_state:
        st.session_state.login_username = ""
    if "pin_sent_message" not in st.session_state:
        st.session_state.pin_sent_message = ""

    # Step 1: Enter username
    if st.session_state.login_step == "username":
        show_username_step()
    # Step 2: Enter PIN
    elif st.session_state.login_step == "pin":
        show_pin_step()


def show_username_step():
    """Show username input step."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 👤 Enter Username")

        username = st.text_input(
            "Username",
            value=st.session_state.login_username,
            placeholder="your_username",
            key="username_input",
            label_visibility="collapsed"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📧 SEND PIN", use_container_width=True, type="primary"):
            if not username:
                st.error("⚠️ Please enter a username")
                return

            # Validate user exists
            db = next(get_db())
            user = db.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()

            if not user:
                db.close()
                st.error("❌ User not found or inactive")
                return

            # Check rate limit
            config = db.query(AppConfig).filter(AppConfig.key == "pin_rate_limit_minutes").first()
            rate_limit_minutes = int(config.value) if config else 1

            if not can_request_pin(db, user.id, rate_limit_minutes):
                db.close()
                st.error(f"⚠️ Please wait {rate_limit_minutes} minute(s) before requesting a new PIN")
                return

            # Get PIN expiry config
            config = db.query(AppConfig).filter(AppConfig.key == "pin_expiry_minutes").first()
            pin_expiry_minutes = int(config.value) if config else 10

            # Create PIN
            pin = create_pin_for_user(db, user.id, pin_expiry_minutes)

            # Send email
            email_sent = send_pin_email(user.email, pin, user.username)

            db.close()

            if email_sent:
                st.session_state.login_username = username
                st.session_state.login_step = "pin"
                st.session_state.pin_sent_message = f"✅ PIN sent to {user.email}"
                st.rerun()
            else:
                st.error("❌ Failed to send PIN email. Please try again.")

        # Show message if any
        if st.session_state.pin_sent_message:
            st.info(st.session_state.pin_sent_message)


def show_pin_step():
    """Show PIN input step."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(f"### 🔐 Enter PIN")
        st.info(f"📧 PIN sent to the email registered for **{st.session_state.login_username}**")

        pin = st.text_input(
            "4-Digit PIN",
            max_chars=4,
            placeholder="0000",
            type="password",
            key="pin_input",
            label_visibility="collapsed"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("🔙 BACK", use_container_width=True):
                st.session_state.login_step = "username"
                st.session_state.pin_sent_message = ""
                st.rerun()

        with col_b:
            if st.button("🚀 LOGIN", use_container_width=True, type="primary"):
                if not pin or len(pin) != 4:
                    st.error("⚠️ Please enter a 4-digit PIN")
                    return

                # Validate PIN
                db = next(get_db())
                user = validate_pin(db, st.session_state.login_username, pin)

                if not user:
                    db.close()
                    st.error("❌ Invalid or expired PIN")
                    return

                # Get session timeout config
                config = db.query(AppConfig).filter(AppConfig.key == "session_timeout_minutes").first()
                session_timeout = int(config.value) if config else 180

                # Get session warning config
                config = db.query(AppConfig).filter(AppConfig.key == "session_warning_minutes").first()
                session_warning = int(config.value) if config else 5

                # Create session
                session_token = create_session(db, user.id, session_timeout)

                # Extract user data before closing session
                user_data = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active
                }

                db.close()

                # Store in session state
                st.session_state.session_token = session_token
                st.session_state.session_timeout_minutes = session_timeout
                st.session_state.session_warning_minutes = session_warning
                st.session_state.user = user_data

                # Clear login state
                st.session_state.login_step = "username"
                st.session_state.login_username = ""
                st.session_state.pin_sent_message = ""

                st.success("✅ Login successful!")
                st.rerun()
