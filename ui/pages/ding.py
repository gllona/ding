"""Main ding page for sending messages and images to printer."""
import streamlit as st
import time
from pathlib import Path
from datetime import datetime

from core.database import get_db
from core.models import DingJob
from core.config import settings
from core.yaml_config import yaml_config
from services.image import validate_image, process_image
from services.printer import printer_service
from services.text_renderer import get_banner_char_limit


def show_ding_page():
    """Display main ding page."""
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h1 style='font-size: 3rem; color: #00FFFF; text-shadow: 0 0 10px #00FFFF;'>
            🖨️ D I N G 🖨️
        </h1>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Tabs for different ding types
    tab1, tab2 = st.tabs(["📝 TEXT MESSAGE", "🖼️ IMAGE"])

    with tab1:
        show_text_tab()

    with tab2:
        show_image_tab()

    # Show recent jobs
    st.markdown("---")
    show_recent_jobs()


def show_text_tab():
    """Show text message tab."""
    st.markdown("### 📝 Send Text Message")

    # Text input
    text_content = st.text_area(
        "Message",
        height=200,
        placeholder="Type your message here...",
        help="Emojis will be converted to text 😀 -> :grinning_face:"
    )

    # Font size selector first
    font_size = st.radio(
        "Font Size",
        options=["small", "medium", "large", "banner"],
        index=1,
        horizontal=True,
        help="Banner mode renders large vertical text - perfect for signs!"
    )

    # Format selector (only for non-banner modes)
    if font_size == "banner":
        use_cowsay = False
        st.info("🎌 Banner mode renders text vertically - perfect for signs and announcements!")
    else:
        # Format selector for regular text
        use_cowsay = st.radio(
            "Format",
            options=["Plain", "Cowsay"],
            index=0,
            horizontal=True,
            help="Cowsay mode always uses small font for best readability"
        ) == "Cowsay"

        # Override font size for cowsay
        if use_cowsay:
            font_size = "small"
            st.info("ℹ️ Cowsay mode always uses small font for best readability")

    # Character counter
    if font_size == "banner":
        # Get banner character limit
        dots_per_line = yaml_config.get_int("printer.dots_per_line", 384)
        max_chars = get_banner_char_limit(dots_per_line)
        char_count = len(text_content)
        st.caption(f"Characters: {char_count} (max ~{max_chars} for banner)")
        if char_count > max_chars:
            st.warning(f"⚠️ Text may be too long for banner mode (max ~{max_chars} chars)")
    else:
        prefix = "cowsay" if use_cowsay else "text"
        config_key = f"fonts.{font_size}.{prefix}_chars_per_line"
        max_chars = yaml_config.get_int(config_key, 32)
        char_count = len(text_content)
        st.caption(f"Characters: {char_count} (approx. {max_chars} chars per line)")

    st.markdown("<br>", unsafe_allow_html=True)

    # Send button
    if st.button("🚀 SEND TO PRINTER", use_container_width=True, type="primary", key="send_text"):
        if not text_content.strip():
            st.error("⚠️ Please enter a message")
            return

        # Create job
        db = next(get_db())
        job = DingJob(
            user_id=st.session_state.user["id"],
            job_type="text",
            content_type="cowsay" if use_cowsay else "plain",
            text_content=text_content,
            font_size=font_size,
            status="pending"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id
        db.close()

        # Process job asynchronously
        printer_service.process_job_async(job_id)

        st.success(f"✅ Job #{job_id} submitted!")

        # Show job status
        show_job_status(job_id)


def show_image_tab():
    """Show image upload tab."""
    st.markdown("### 🖼️ Send Image")

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Image",
        type=["jpg", "jpeg", "png", "gif"],
        help="Supported formats: JPG, PNG, GIF (first frame only)"
    )

    if uploaded_file:
        # Show preview
        st.image(uploaded_file, caption="Preview", use_container_width=True)

        # Banner mode checkbox
        is_banner = st.checkbox(
            "🎌 Banner Mode (rotate 90°)",
            help="Rotate image 90 degrees for banner printing"
        )

        # Caption input (disabled in banner mode)
        caption = None
        font_size = "medium"

        if not is_banner:
            caption = st.text_input(
                "Caption (optional)",
                placeholder="Add text below the image..."
            )

            if caption:
                font_size = st.radio(
                    "Caption Font Size",
                    options=["small", "medium", "large"],
                    index=1,
                    horizontal=True,
                    key="image_font_size"
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # Send button
        if st.button("🚀 SEND TO PRINTER", use_container_width=True, type="primary", key="send_image"):
            # Save uploaded file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{st.session_state.user['username']}_{timestamp}_{uploaded_file.name}"
            file_path = settings.store_path / filename

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Validate image
            if not validate_image(str(file_path)):
                st.error("❌ Invalid image file")
                file_path.unlink()
                return

            # Create job
            db = next(get_db())

            job_type = "text_with_image" if caption else "image"
            content_type = "banner" if is_banner else "plain"

            job = DingJob(
                user_id=st.session_state.user["id"],
                job_type=job_type,
                content_type=content_type,
                text_content=caption,
                image_path=str(file_path),
                font_size=font_size if caption else None,
                status="pending"
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            job_id = job.id
            db.close()

            # Process job asynchronously
            printer_service.process_job_async(job_id)

            st.success(f"✅ Job #{job_id} submitted!")

            # Show job status
            show_job_status(job_id)


def show_job_status(job_id: int, max_wait: int = 30):
    """
    Show real-time job status with polling.

    Args:
        job_id: Job ID to monitor
        max_wait: Maximum seconds to wait
    """
    status_placeholder = st.empty()
    progress_bar = st.progress(0)

    start_time = time.time()
    poll_interval = 1  # seconds

    while time.time() - start_time < max_wait:
        # Get job status
        db = next(get_db())
        job = db.query(DingJob).filter(DingJob.id == job_id).first()
        db.close()

        if not job:
            status_placeholder.error("❌ Job not found")
            break

        # Update progress
        elapsed = time.time() - start_time
        progress = min(elapsed / max_wait, 1.0)
        progress_bar.progress(progress)

        # Display status
        if job.status == "pending":
            status_placeholder.info("⏳ Waiting to process...")
        elif job.status == "processing":
            status_placeholder.info("🖨️ Printing...")
        elif job.status == "success":
            status_placeholder.success("✅ Successfully printed!")
            progress_bar.progress(1.0)
            break
        elif job.status == "failed":
            status_placeholder.error(f"❌ Failed: {job.error_message}")
            progress_bar.progress(1.0)
            break

        time.sleep(poll_interval)

    else:
        # Timeout
        status_placeholder.warning("⚠️ Status check timed out. Job is still processing in background.")


def show_recent_jobs():
    """Show recent jobs for current user."""
    st.markdown("### 📋 Recent Dings")

    db = next(get_db())
    jobs = db.query(DingJob).filter(
        DingJob.user_id == st.session_state.user["id"]
    ).order_by(DingJob.created_at.desc()).limit(5).all()
    db.close()

    if not jobs:
        st.info("No recent dings. Send something to the printer!")
        return

    for job in jobs:
        with st.expander(f"Job #{job.id} - {job.job_type.upper()} - {job.status.upper()}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Type:** {job.job_type}")
                st.write(f"**Format:** {job.content_type}")

            with col2:
                st.write(f"**Status:** {job.status}")
                st.write(f"**Created:** {job.created_at.strftime('%Y-%m-%d %H:%M')}")

            with col3:
                if job.font_size:
                    st.write(f"**Font:** {job.font_size}")
                if job.completed_at:
                    st.write(f"**Completed:** {job.completed_at.strftime('%H:%M:%S')}")

            if job.text_content:
                st.text(f"Text: {job.text_content[:100]}{'...' if len(job.text_content) > 100 else ''}")

            if job.error_message:
                st.error(f"Error: {job.error_message}")
