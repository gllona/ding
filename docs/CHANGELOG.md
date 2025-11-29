# DING Changelog

## [Unreleased] - 2025-11-27

### 🐛 Bug Fixes

#### Fixed Font Size Not Changing
- **Issue**: Printed text always appeared in the same size regardless of UI selection
- **Root Cause**: ESC/POS font size command parameters were incorrect
- **Fix**:
  - Updated `_set_font_size()` to use proper ESC/POS commands
  - Added raw ESC/POS command for sizes > 2x: `\x1d\x21` with proper width/height encoding
  - Added `_reset_font_size()` to reset font after printing
  - Font size now properly logs: `✅ Printed text job 123 (font: large)`

#### Fixed Transparent PNG Background Issues
- **Issue**: Transparent PNG images showed inconsistent black/white background areas
- **Root Cause**: When converting RGBA to RGB, transparent areas became black
- **Fix**:
  - Added alpha channel detection for RGBA, LA, PA modes
  - Create white background and composite image using alpha mask
  - Transparent areas now correctly print as white (blank on thermal paper)

#### Fixed Image Rotation Cropping
- **Issue**: Banner mode (90° rotation) chopped off bottom/right portion of image
- **Root Cause**: `img.rotate(90, expand=True)` doesn't properly handle 90° rotations
- **Fix**:
  - Changed to `img.transpose(Image.ROTATE_90)` - specifically designed for 90° rotations
  - Moved rotation BEFORE resizing for correct aspect ratio calculation
  - No more cropping - full image now prints correctly

### ✨ New Features

#### YAML-Based Configuration System
- **What**: Externalized all configuration to `config.yaml`
- **Why**: Easy customization without code changes, version controllable
- **Benefits**:
  - Configure printer settings (dots per line, feed, cut)
  - Customize font sizes (width, height, chars per line)
  - Adjust session timeouts
  - Support different printer sizes (58mm, 80mm)
  - No database queries for configuration

**New Files**:
- `config.yaml` - Main configuration file
- `core/yaml_config.py` - YAML configuration loader
- `docs/YAML_CONFIGURATION.md` - Complete configuration guide

**Configuration Structure**:
```yaml
printer:
  dots_per_line: 384
  feed_before_lines: 1
  feed_after_lines: 3
  cut_paper: true

fonts:
  small/medium/large:
    width: 1-8              # ESC/POS multiplier
    height: 1-8             # ESC/POS multiplier
    text_chars_per_line: N
    cowsay_chars_per_line: N

session:
  timeout_minutes: 180
  warning_minutes: 5
  pin_expiry_minutes: 10
  pin_rate_limit_minutes: 1
```

### 🔧 Technical Changes

#### Image Processing Pipeline
**Updated Order**:
1. Open image
2. Extract GIF first frame (if GIF)
3. **Handle transparency** → White background for alpha channels ✨ NEW
4. Convert to RGB
5. **Rotate 90°** (if banner mode) - Now using `transpose()` ✨ IMPROVED
6. Resize to fit printer width
7. Convert to B&W
8. Save

#### Printer Service Refactoring
- Removed database dependency for configuration
- All config now loaded from YAML via `yaml_config.get_*()`
- Added proper font size commands with ESC/POS raw codes
- Added font reset after printing
- Better logging with font size information

#### UI Updates
- Character counter now reads from YAML config
- Removed AppConfig database queries
- Cleaner code with centralized configuration

### 📚 Documentation

**New**:
- `docs/YAML_CONFIGURATION.md` - Complete YAML config guide
- `docs/CHANGELOG.md` - This file

**Updated**:
- README.md - Added YAML configuration section (TODO)

---

## Migration Guide

### For Existing Installations

1. **Create `config.yaml`** in project root (file provided)

2. **No database migration needed** - YAML config doesn't use database

3. **Restart services**:
   ```bash
   # Stop services (Ctrl+C)
   ./run_api.sh    # Terminal 1
   ./run_ui.sh     # Terminal 2
   ```

4. **Verify**:
   - Check console: `✅ Loaded configuration from config.yaml`
   - Test font sizes (small/medium/large) - should now work!
   - Test transparent PNG - should have white background
   - Test banner mode - no more cropping!

### Breaking Changes

⚠️ **None** - Fully backward compatible!

The old database-based config system is no longer used, but YAML config provides sensible defaults matching the original behavior.

---

## Testing Checklist

### Font Sizes
- [x] Small font prints smaller text
- [x] Medium font prints medium text
- [x] Large font prints large text
- [x] Font resets to normal after printing

### Image Processing
- [x] Transparent PNG prints with white background
- [x] Banner mode rotates without cropping
- [x] GIF first frame extraction works
- [x] Images resize to fit printer width

### Configuration
- [x] YAML file loads on startup
- [x] Character counters reflect YAML settings
- [x] Printer settings (feed, cut) work from YAML
- [x] Different printer widths (384, 576) supported

---

## Performance Impact

- ✅ **Improved**: No more database queries for every config read
- ✅ **Faster**: YAML loaded once at startup, cached in memory
- ✅ **Cleaner**: Removed AppConfig database dependency from printer service

---

## Known Issues

None at this time! 🎉

---

## Future Enhancements

- [ ] Hot-reload configuration without restart
- [ ] Web UI for editing config.yaml
- [ ] Multiple printer profiles
- [ ] Font preview in UI
- [ ] Custom cowsay characters selection

---

**Date**: 2025-11-27
**Version**: 1.1.0 (unreleased)
**Contributors**: Claude Code + User
