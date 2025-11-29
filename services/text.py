"""Text processing service for emoji conversion and cowsay generation."""
import emoji
import subprocess
import textwrap
import shutil
import os
from typing import Optional
from unidecode import unidecode


def convert_emojis_to_text(text: str) -> str:
    """
    Convert emojis in text to their text representation.

    Args:
        text: Text containing emojis

    Returns:
        Text with emojis converted to text (e.g., 😀 -> :grinning_face:)
    """
    return emoji.demojize(text)


def encode_for_escpos(text: str) -> str:
    """
    Convert UTF-8 text to ESC/POS compatible encoding.
    Uses unidecode to handle special characters.

    Args:
        text: UTF-8 text

    Returns:
        ESC/POS compatible text
    """
    # First convert emojis to text
    text = convert_emojis_to_text(text)

    # Then handle special characters
    return unidecode(text)


def wrap_text_for_printer(text: str, max_width: int) -> str:
    """
    Wrap text for printer based on character limit per line.

    Args:
        text: Text to wrap
        max_width: Maximum characters per line

    Returns:
        Wrapped text
    """
    lines = []
    for paragraph in text.split('\n'):
        if paragraph.strip():
            wrapped = textwrap.fill(paragraph, width=max_width)
            lines.append(wrapped)
        else:
            lines.append('')

    return '\n'.join(lines)


def find_cowsay_command() -> Optional[str]:
    """
    Find cowsay command in system PATH and common locations.

    Returns:
        Full path to cowsay executable or None if not found
    """
    # Try shutil.which first (searches PATH)
    cowsay_path = shutil.which('cowsay')
    if cowsay_path:
        return cowsay_path

    # Check common locations where cowsay might be installed
    # Use file existence check instead of running commands
    common_paths = [
        '/usr/games/cowsay',
        '/usr/local/bin/cowsay',
        '/usr/bin/cowsay',
        '/bin/cowsay',
    ]

    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    return None


def generate_cowsay(text: str, max_width: int) -> Optional[str]:
    """
    Generate cowsay output for text.

    Args:
        text: Text to convert to cowsay
        max_width: Maximum width for cowsay text bubble

    Returns:
        Cowsay output or None if cowsay command fails
    """
    try:
        # Find cowsay command
        cowsay_cmd = find_cowsay_command()
        if not cowsay_cmd:
            print("❌ Cowsay command not found. Please install cowsay: sudo apt install cowsay")
            print("   Common locations checked: /usr/games/cowsay, /usr/bin/cowsay, /usr/local/bin/cowsay")
            return None

        # Encode text for printing first
        encoded_text = encode_for_escpos(text)

        # Run cowsay command with full path
        result = subprocess.run(
            [cowsay_cmd, '-W', str(max_width), encoded_text],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return result.stdout
        else:
            print(f"⚠️  Cowsay command failed: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        print("⚠️  Cowsay command timed out")
        return None
    except Exception as e:
        print(f"❌ Error generating cowsay: {e}")
        return None


def prepare_text_for_print(text: str, max_width: int, use_cowsay: bool = False) -> str:
    """
    Prepare text for printing by encoding and optionally wrapping/cowsay.

    Args:
        text: Text to prepare
        max_width: Maximum characters per line
        use_cowsay: Whether to use cowsay format

    Returns:
        Prepared text ready for printing
    """
    if use_cowsay:
        cowsay_output = generate_cowsay(text, max_width)
        if cowsay_output:
            return cowsay_output
        else:
            # Fallback to regular text if cowsay fails
            print("⚠️  Falling back to regular text")
            text = encode_for_escpos(text)
            return wrap_text_for_printer(text, max_width)
    else:
        text = encode_for_escpos(text)
        return wrap_text_for_printer(text, max_width)
