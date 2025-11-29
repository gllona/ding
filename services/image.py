"""Image processing service for resizing, rotating, and GIF handling."""
from PIL import Image
from pathlib import Path
from typing import Optional


def process_image(
    image_path: str,
    output_path: str,
    max_width: int = 384,
    rotate: bool = False,
    convert_to_bw: bool = True
) -> str:
    """
    Process image for thermal printer.
    - Extracts first frame if GIF
    - Resizes to fit printer width
    - Optionally rotates for banner mode
    - Converts to black & white

    Args:
        image_path: Path to input image
        output_path: Path to save processed image
        max_width: Maximum width in dots (printer capability)
        rotate: Whether to rotate 90 degrees (banner mode)
        convert_to_bw: Whether to convert to black & white

    Returns:
        Path to processed image

    Raises:
        ValueError: If image processing fails
    """
    try:
        # Open image
        img = Image.open(image_path)

        # If GIF, extract first frame
        if img.format == 'GIF':
            img.seek(0)  # Go to first frame
            # Convert to RGB (GIFs might be in palette mode)
            img = img.convert('RGB')
            print("📸 Extracted first frame from GIF")

        # Handle transparency (PNG with alpha channel)
        if img.mode in ('RGBA', 'LA', 'PA'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            # Paste the image on the white background using alpha channel as mask
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
            elif img.mode == 'LA':
                background.paste(img, mask=img.split()[1])  # 1 is the alpha channel
            else:  # PA mode
                background.paste(img, mask=img.split()[1])
            img = background
            print("🎨 Converted transparent image with white background")

        # Ensure image is in RGB mode before processing
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        # Rotate BEFORE resizing if banner mode (to maintain aspect ratio correctly)
        if rotate:
            # Use transpose for proper 90-degree rotation (counterclockwise)
            img = img.transpose(Image.ROTATE_90)
            print("🔄 Rotated image 90 degrees for banner mode")

        # Resize to fit printer width while maintaining aspect ratio
        original_width, original_height = img.size
        if original_width > max_width:
            wpercent = max_width / float(original_width)
            hsize = int(float(original_height) * wpercent)
            img = img.resize((max_width, hsize), Image.Resampling.LANCZOS)
            print(f"📐 Resized image: {original_width}x{original_height} -> {max_width}x{hsize}")
        else:
            print(f"📐 Image already fits: {original_width}x{original_height}")

        # Convert to black & white (1-bit) for thermal printer
        if convert_to_bw:
            img = img.convert('1')
            print("⚫⚪ Converted to black & white")

        # Save processed image
        img.save(output_path)
        print(f"✅ Processed image saved to: {output_path}")

        return output_path

    except Exception as e:
        raise ValueError(f"Error processing image: {e}")


def validate_image(image_path: str) -> bool:
    """
    Validate that file is a supported image format.

    Args:
        image_path: Path to image file

    Returns:
        True if valid image, False otherwise
    """
    try:
        img = Image.open(image_path)
        # Check if format is supported
        supported_formats = ['JPEG', 'PNG', 'GIF', 'BMP']
        if img.format in supported_formats:
            return True
        else:
            print(f"⚠️  Unsupported image format: {img.format}")
            return False
    except Exception as e:
        print(f"❌ Invalid image file: {e}")
        return False


def get_image_info(image_path: str) -> Optional[dict]:
    """
    Get image information (format, size, etc.).

    Args:
        image_path: Path to image file

    Returns:
        Dictionary with image info or None if invalid
    """
    try:
        img = Image.open(image_path)
        return {
            "format": img.format,
            "mode": img.mode,
            "width": img.size[0],
            "height": img.size[1],
            "is_animated": hasattr(img, 'n_frames') and img.n_frames > 1
        }
    except Exception as e:
        print(f"❌ Error getting image info: {e}")
        return None
