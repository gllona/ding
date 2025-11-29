"""Text rendering service for converting text to images (banner mode)."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import Optional


def find_monospace_font(size: int) -> ImageFont.FreeTypeFont:
    """
    Find and load a monospace font.

    Args:
        size: Font size in pixels

    Returns:
        ImageFont object
    """
    # Common monospace font paths on Linux
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
        "/System/Library/Fonts/Courier.dfont",  # macOS
        "C:\\Windows\\Fonts\\cour.ttf",  # Windows
    ]

    for font_path in font_paths:
        if Path(font_path).exists():
            try:
                return ImageFont.truetype(font_path, size)
            except Exception as e:
                print(f"⚠️  Failed to load font {font_path}: {e}")
                continue

    # Fallback to default PIL font
    print("⚠️  No monospace font found, using default")
    return ImageFont.load_default()


def calculate_font_size(text: str, target_height: int, max_iterations: int = 20) -> int:
    """
    Calculate optimal font size to fill target height.

    Args:
        text: Text to render
        target_height: Target height in pixels (70% of dots_per_line)
        max_iterations: Maximum number of binary search iterations

    Returns:
        Optimal font size
    """
    # Binary search for optimal font size
    min_size = 10
    max_size = 500
    best_size = 50

    for _ in range(max_iterations):
        mid_size = (min_size + max_size) // 2
        font = find_monospace_font(mid_size)

        # Get text bounding box
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_height = bbox[3] - bbox[1]

        if text_height < target_height:
            min_size = mid_size + 1
            best_size = mid_size
        elif text_height > target_height:
            max_size = mid_size - 1
        else:
            return mid_size

    return best_size


def render_text_banner(
    text: str,
    output_path: str,
    dots_per_line: int = 384
) -> str:
    """
    Render text as a horizontal image for banner printing.

    Args:
        text: Text to render (single line)
        output_path: Path to save rendered image
        dots_per_line: Printer width in dots

    Returns:
        Path to rendered image

    Raises:
        ValueError: If text is empty or rendering fails
    """
    if not text.strip():
        raise ValueError("Text cannot be empty")

    # Target height is 70% of printer width for margins
    target_height = int(dots_per_line * 0.7)

    # Calculate optimal font size
    font_size = calculate_font_size(text, target_height)
    font = find_monospace_font(font_size)

    print(f"  🎨 Rendering banner with font size: {font_size}px")

    # Create dummy image to measure text dimensions
    dummy_img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Add small margins
    margin_x = 20
    margin_y = (dots_per_line - text_height) // 2

    # Create final image
    img_width = text_width + (2 * margin_x)
    img_height = dots_per_line

    image = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(image)

    # Draw text in black, centered vertically
    draw.text((margin_x, margin_y), text, fill='black', font=font)

    # Convert to black & white (1-bit) for thermal printer
    image = image.convert('1')

    # Save image
    image.save(output_path)

    print(f"  ✅ Banner rendered: {img_width}x{img_height} px")
    print(f"     Text: '{text}' ({len(text)} chars)")

    return output_path


def get_banner_char_limit(dots_per_line: int = 384) -> int:
    """
    Estimate maximum characters for banner mode.

    Args:
        dots_per_line: Printer width in dots

    Returns:
        Approximate maximum characters
    """
    # Very rough estimate: ~30 pixels per character at optimal size
    # This is conservative to ensure text fits
    target_height = int(dots_per_line * 0.7)
    font_size = calculate_font_size("M", target_height)  # Use 'M' as reference

    # Test with sample text
    font = find_monospace_font(font_size)
    dummy_img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(dummy_img)

    # Measure single character
    bbox = draw.textbbox((0, 0), "M", font=font)
    char_width = bbox[2] - bbox[0]

    # Maximum banner length (conservative estimate)
    # Assume maximum print length of ~10x printer width
    max_length_pixels = dots_per_line * 10
    max_chars = int(max_length_pixels / char_width) if char_width > 0 else 50

    return max_chars
