# DING YAML Configuration Guide

## Overview

DING now uses a centralized `config.yaml` file for all application settings, making it easy to customize the printer behavior, font sizes, session timeouts, and more without touching the code.

## Configuration File Location

```
/home/gorka/printers/repos/ding/config.yaml
```

## Configuration Structure

### Printer Settings

```yaml
printer:
  dots_per_line: 384          # Maximum width in dots (58mm = 384, 80mm = 576)
  vendor_id: "0x0416"         # USB vendor ID
  product_id: "0x5011"        # USB product ID
  device_path: "/dev/usb/lp0" # File device path (fallback)

  feed_before_lines: 1        # Lines to feed before printing
  feed_after_lines: 3         # Lines to feed after printing
  cut_paper: true             # Whether to cut paper after printing
```

**Common Printer Widths:**
- 58mm thermal printer: 384 dots
- 80mm thermal printer: 576 dots

### Font Size Configuration

Each font size has configurable width/height multipliers and character limits:

```yaml
fonts:
  small:
    width: 1                  # ESC/POS width multiplier (1-8)
    height: 1                 # ESC/POS height multiplier (1-8)
    text_chars_per_line: 48   # Max characters for plain text
    cowsay_chars_per_line: 40 # Max characters for cowsay bubble

  medium:
    width: 2
    height: 2
    text_chars_per_line: 32
    cowsay_chars_per_line: 28

  large:
    width: 3
    height: 3
    text_chars_per_line: 24
    cowsay_chars_per_line: 20
```

**Width/Height Values:**
- `1`: Normal size (1x)
- `2`: Double size (2x)
- `3`: Triple size (3x)
- Up to `8`: 8x size (very large!)

**Character Limits:**
- `text_chars_per_line`: Maximum characters per line for plain text
- `cowsay_chars_per_line`: Maximum characters per line for cowsay text bubble

### Session & Authentication

```yaml
session:
  timeout_minutes: 180        # Session duration (3 hours)
  warning_minutes: 5          # Warn user N minutes before expiry
  pin_expiry_minutes: 10      # PIN validity duration
  pin_rate_limit_minutes: 1   # Minimum time between PIN requests
```

### Database

```yaml
database:
  url: "sqlite:///./ding.db"  # Database connection string
```

**Alternative database URLs:**
- PostgreSQL: `postgresql://user:pass@localhost/ding`
- MySQL: `mysql://user:pass@localhost/ding`

### Application

```yaml
app:
  name: "DING"
  url: "http://localhost:8501"
  store_path: "store"         # Directory for uploaded images
```

---

## How to Modify Configuration

### 1. Edit the YAML File

```bash
nano config.yaml
# or
vim config.yaml
```

### 2. Restart the Services

Configuration is loaded on startup, so restart both services:

```bash
# Stop both services (Ctrl+C)

# Restart API
./run_api.sh

# Restart UI (in another terminal)
./run_ui.sh
```

### 3. Verify Changes

Check the console output when starting the services to see:
```
✅ Loaded configuration from config.yaml
```

---

## Common Configuration Examples

### Example 1: 80mm Printer

```yaml
printer:
  dots_per_line: 576          # 80mm printer

fonts:
  small:
    width: 1
    height: 1
    text_chars_per_line: 72   # More characters on wider printer
    cowsay_chars_per_line: 60

  medium:
    width: 2
    height: 2
    text_chars_per_line: 48
    cowsay_chars_per_line: 42

  large:
    width: 3
    height: 3
    text_chars_per_line: 36
    cowsay_chars_per_line: 30
```

### Example 2: Longer Session Timeout

```yaml
session:
  timeout_minutes: 480        # 8 hours
  warning_minutes: 10         # Warn 10 minutes before
```

### Example 3: More Paper Feed

```yaml
printer:
  feed_before_lines: 2        # More space before
  feed_after_lines: 5         # More space after
  cut_paper: false            # Don't auto-cut (manual cutting)
```

### Example 4: Extra Large Font

```yaml
fonts:
  large:
    width: 4                  # 4x width
    height: 4                 # 4x height
    text_chars_per_line: 12   # Fewer chars per line
    cowsay_chars_per_line: 10
```

---

## Font Size Configuration Guide

### Calculating Characters Per Line

The formula for calculating max characters per line:

```
chars_per_line = printer_dots_per_line / (char_width_in_dots * width_multiplier)
```

For standard ESC/POS fonts:
- Character width: ~8 dots
- 58mm printer (384 dots):
  - 1x: 384 / 8 = 48 chars
  - 2x: 384 / 16 = 24 chars
  - 3x: 384 / 24 = 16 chars

**Tip**: Leave some margin, so use slightly fewer characters than the theoretical maximum.

### Cowsay Character Limits

Cowsay needs narrower text because of the speech bubble borders:

```
 _____________
< Hello DING! >
 -------------
        \   ^__^
         \  (oo)\_______
```

The bubble adds ~8 characters of border, so:
```
cowsay_chars = text_chars - 8
```

---

## Troubleshooting

### Configuration Not Loading

**Error**: `FileNotFoundError: Configuration file not found: config.yaml`

**Solution**: Ensure `config.yaml` exists in the project root:
```bash
ls -l config.yaml
```

### Font Size Not Changing

**Check**:
1. Verify font configuration in `config.yaml`
2. Restart both services
3. Check console output for font size logging:
   ```
   ✅ Printed text job 123 (font: large)
   ```

### Characters Getting Cut Off

**Problem**: Text wraps unexpectedly or gets truncated

**Solution**: Reduce `chars_per_line` values in config:
```yaml
fonts:
  medium:
    text_chars_per_line: 30  # Reduced from 32
```

### Paper Not Cutting

**Check**: `cut_paper` setting:
```yaml
printer:
  cut_paper: true  # Should be true
```

---

## Advanced: Dynamic Configuration Reloading

To reload configuration without restarting:

```python
from core.yaml_config import yaml_config

# Reload configuration
yaml_config.reload()
```

*Note: This feature is not exposed in the UI yet but can be added.*

---

## Configuration Validation

The YAML loader validates:
- File exists
- Valid YAML syntax
- Type conversions (int, bool, str)

If configuration is invalid, the application will fail to start with an error message indicating the problem.

---

## Environment Variables Override

Sensitive settings (API keys, database credentials) should still use environment variables in `.env`:

```bash
# .env
API_KEY=your-secret-key
SENDGRID_API_KEY=your-sendgrid-key
SENDGRID_FROM_EMAIL=noreply@example.com
```

These take precedence over `config.yaml`.

---

## Summary

- ✅ All printer settings in one YAML file
- ✅ Easy to customize without code changes
- ✅ Font sizes fully configurable
- ✅ Session timeouts adjustable
- ✅ Works with different printer sizes (58mm, 80mm)
- ✅ Version controllable (can commit to git)

**Happy configuring! 🖨️✨**
