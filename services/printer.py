"""Printer service for ESC/POS thermal printer integration."""
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from escpos.printer import Usb, File as PrinterFile

from core.config import settings
from core.database import SessionLocal
from core.models import DingJob
from core.yaml_config import yaml_config
from services.text import prepare_text_for_print
from services.image import process_image
from services.text_renderer import render_text_banner


class PrinterService:
    """Service for managing thermal printer operations."""

    def __init__(self):
        """Initialize printer service."""
        self._lock = threading.Lock()

    def _connect_printer(self):
        """
        Connect to ESC/POS printer.
        Tries USB connection first, then falls back to file device.
        Always creates a fresh connection to avoid stale connections.

        Returns:
            Printer object (Usb or File)
        """
        try:
            # Parse hex vendor and product IDs
            vendor_id = int(settings.printer_vendor_id, 16)
            product_id = int(settings.printer_product_id, 16)

            # Try USB connection
            printer = Usb(vendor_id, product_id)
            print(f"✅ Connected to printer via USB ({settings.printer_vendor_id}:{settings.printer_product_id})")
            return printer

        except Exception as e:
            print(f"⚠️  USB connection failed: {e}, trying file device...")

            try:
                # Fallback to file device
                printer = PrinterFile(settings.printer_device_path)
                print(f"✅ Connected to printer via file device ({settings.printer_device_path})")
                return printer

            except Exception as e2:
                print(f"❌ File device connection failed: {e2}")
                raise ConnectionError(f"Failed to connect to printer: USB failed ({e}), File failed ({e2})")

    def _close_printer(self, printer):
        """
        Close printer connection and release resources.

        Args:
            printer: Printer object to close
        """
        try:
            if printer:
                printer.close()
                print(f"  🔌 Printer connection closed")
        except Exception as e:
            print(f"  ⚠️  Error closing printer: {e}")

    def _feed_and_cut(self, printer):
        """
        Apply feed_before, feed_after, and cut_paper settings from YAML.

        Args:
            printer: Printer object to use
        """
        feed_after = yaml_config.get_int("printer.feed_after_lines", 3)
        cut_paper = yaml_config.get_bool("printer.cut_paper", True)

        # Feed after content
        for _ in range(feed_after):
            printer.text("\n")

        # Cut paper if configured
        if cut_paper:
            printer.cut()

    def _get_font_size_config(self, font_size: str, is_cowsay: bool = False) -> int:
        """Get character limit for font size from YAML."""
        prefix = "cowsay" if is_cowsay else "text"
        config_key = f"fonts.{font_size}.{prefix}_chars_per_line"
        return yaml_config.get_int(config_key, 32)

    def _set_font_size(self, printer, font_size: str):
        """
        Set ESC/POS font size using YAML configuration.

        Args:
            printer: Printer object to use
            font_size: Font size name (small/medium/large)
        """
        width = yaml_config.get_int(f"fonts.{font_size}.width", 1)
        height = yaml_config.get_int(f"fonts.{font_size}.height", 1)

        # ALWAYS reset first to ensure clean state
        printer._raw(b'\x1d\x21\x00')  # Reset to normal (1x1)

        # ESC/POS GS ! n command: width and height from 0-7 (representing 1-8x)
        # Bit 0-2: width-1, Bit 4-6: height-1
        size_byte = ((width - 1) << 4) | (height - 1)
        printer._raw(b'\x1d\x21' + bytes([size_byte]))

        print(f"  📏 Set font size: {font_size} ({width}x{height})")

    def _reset_font_size(self, printer):
        """
        Reset font to normal size.

        Args:
            printer: Printer object to use
        """
        printer._raw(b'\x1d\x21\x00')  # Reset to 1x1
        print(f"  📏 Reset font to normal")

    def print_text(
        self,
        db: Session,
        job_id: int,
        text: str,
        font_size: str = "medium",
        use_cowsay: bool = False
    ):
        """
        Print text message.

        Args:
            db: Database session
            job_id: Job ID
            text: Text to print
            font_size: Font size (small/medium/large/banner)
            use_cowsay: Whether to use cowsay format
        """
        printer = None
        try:
            # Banner mode: render text as image
            if font_size == "banner":
                self._print_text_banner(db, job_id, text)
                return

            # Regular text printing
            # Connect to printer (fresh connection each time)
            printer = self._connect_printer()

            # Feed before
            feed_before = yaml_config.get_int("printer.feed_before_lines", 1)
            for _ in range(feed_before):
                printer.text("\n")

            # Get character limit for font size
            max_width = self._get_font_size_config(font_size, use_cowsay)

            # Prepare text
            prepared_text = prepare_text_for_print(text, max_width, use_cowsay)

            # Set font size
            self._set_font_size(printer, font_size)

            # Print text
            printer.text(prepared_text)
            printer.text("\n")

            # Reset font size
            self._reset_font_size(printer)

            # Feed and cut
            self._feed_and_cut(printer)

            print(f"✅ Printed text job {job_id} (font: {font_size})")

        except Exception as e:
            raise Exception(f"Error printing text: {e}")
        finally:
            # Always close the printer connection
            self._close_printer(printer)

    def _print_text_banner(self, db: Session, job_id: int, text: str):
        """
        Print text in banner mode (rendered as rotated image).

        Args:
            db: Database session
            job_id: Job ID
            text: Text to print as banner
        """
        printer = None
        try:
            # Get printer width
            dots_per_line = yaml_config.get_int("printer.dots_per_line", 384)

            # Render text to horizontal image
            temp_path = str(Path(settings.store_path) / f"banner_temp_{job_id}.png")
            render_text_banner(text, temp_path, dots_per_line)

            # Process image: rotate 90° counterclockwise
            processed_path = str(Path(settings.store_path) / f"banner_{job_id}.png")
            from PIL import Image
            img = Image.open(temp_path)
            img = img.transpose(Image.Transpose.ROTATE_90)
            img.save(processed_path)

            print(f"  🔄 Rotated banner 90° counterclockwise")

            # Print as image (fresh connection)
            printer = self._connect_printer()

            # Feed before
            feed_before = yaml_config.get_int("printer.feed_before_lines", 1)
            for _ in range(feed_before):
                printer.text("\n")

            # Print the rotated banner image
            printer.image(processed_path)

            # Feed and cut
            self._feed_and_cut(printer)

            print(f"✅ Printed banner job {job_id}")

            # Clean up temp files
            Path(temp_path).unlink(missing_ok=True)
            # Keep processed_path for retry functionality

        except Exception as e:
            raise Exception(f"Error printing banner: {e}")
        finally:
            # Always close the printer connection
            self._close_printer(printer)

    def print_image(
        self,
        db: Session,
        job_id: int,
        image_path: str,
        caption: Optional[str] = None,
        font_size: str = "medium",
        is_banner: bool = False
    ):
        """
        Print image with optional caption.

        Args:
            db: Database session
            job_id: Job ID
            image_path: Path to image file
            caption: Optional text caption
            font_size: Font size for caption
            is_banner: Whether to rotate image for banner mode
        """
        printer = None
        try:
            # Connect to printer (fresh connection)
            printer = self._connect_printer()

            # Feed before
            feed_before = yaml_config.get_int("printer.feed_before_lines", 1)
            for _ in range(feed_before):
                printer.text("\n")

            # Process image
            max_width = yaml_config.get_int("printer.dots_per_line", 384)
            processed_path = str(Path(image_path).parent / f"processed_{Path(image_path).name}")

            process_image(
                image_path=image_path,
                output_path=processed_path,
                max_width=max_width,
                rotate=is_banner
            )

            # Print image
            printer.image(processed_path)

            # Print caption if provided (not in banner mode)
            if caption and not is_banner:
                printer.text("\n")
                self._set_font_size(printer, font_size)

                max_chars = self._get_font_size_config(font_size, False)
                prepared_caption = prepare_text_for_print(caption, max_chars, False)
                printer.text(prepared_caption)
                printer.text("\n")

                # Reset font size
                self._reset_font_size(printer)

            # Feed and cut
            self._feed_and_cut(printer)

            print(f"✅ Printed image job {job_id}")

        except Exception as e:
            raise Exception(f"Error printing image: {e}")
        finally:
            # Always close the printer connection
            self._close_printer(printer)

    def process_job(self, job_id: int):
        """
        Process a print job from the database.

        Args:
            job_id: Job ID to process
        """
        db = SessionLocal()

        try:
            # Acquire lock to prevent concurrent printing
            with self._lock:
                # Get job
                job = db.query(DingJob).filter(DingJob.id == job_id).first()
                if not job:
                    raise ValueError(f"Job {job_id} not found")

                # Update status to processing
                job.status = "processing"
                db.commit()

                # Process based on job type
                if job.job_type == "text":
                    use_cowsay = job.content_type == "cowsay"
                    self.print_text(
                        db=db,
                        job_id=job_id,
                        text=job.text_content,
                        font_size=job.font_size or "medium",
                        use_cowsay=use_cowsay
                    )

                elif job.job_type == "image":
                    is_banner = job.content_type == "banner"
                    self.print_image(
                        db=db,
                        job_id=job_id,
                        image_path=job.image_path,
                        caption=None,
                        font_size=job.font_size or "medium",
                        is_banner=is_banner
                    )

                elif job.job_type == "text_with_image":
                    self.print_image(
                        db=db,
                        job_id=job_id,
                        image_path=job.image_path,
                        caption=job.text_content,
                        font_size=job.font_size or "medium",
                        is_banner=False
                    )

                # Update status to success
                job.status = "success"
                job.completed_at = datetime.utcnow()
                db.commit()

        except Exception as e:
            # Update status to failed
            job = db.query(DingJob).filter(DingJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()

            print(f"❌ Job {job_id} failed: {e}")

        finally:
            db.close()

    def process_job_async(self, job_id: int):
        """
        Process a print job asynchronously in a background thread.

        Args:
            job_id: Job ID to process
        """
        thread = threading.Thread(target=self.process_job, args=(job_id,))
        thread.daemon = True
        thread.start()


# Global printer service instance
printer_service = PrinterService()
