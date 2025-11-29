# DING Implementation Plan

## Project Overview

`ding` is a web-based application that allows authenticated users to send messages and images to an ESC/POS receipt printer connected to the server. The project features a retro 80's aesthetic and is designed to be mobile-responsive and appealing to Gen Z users.

**"To ding something"** = "To send something to the printer"

---

## Tech Stack

- **Backend API**: FastAPI (REST endpoints)
- **Frontend UI**: Streamlit (user-facing interface)
- **Database**: SQLite with SQLAlchemy ORM
- **Email**: SendGrid API
- **Printer**: python-escpos
- **Image Processing**: Pillow (PIL)
- **Text Processing**:
  - `emoji` library (emoji to text conversion)
  - `unidecode` or python-escpos built-in (UTF-8 to ESC/POS encoding)
  - `cowsay` (Linux CLI tool via subprocess)
- **Additional**: python-dotenv, requests, pydantic

---

## Project Structure

```
ding/
├── api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── auth.py                 # API key authentication middleware
│   ├── endpoints/
│   │   ├── __init__.py
│   │   ├── users.py            # User CRUD operations
│   │   ├── config.py           # Configuration management
│   │   └── jobs.py             # Job queries and retry
├── ui/
│   ├── __init__.py
│   ├── app.py                  # Streamlit application
│   ├── pages/
│   │   ├── login.py            # Login page
│   │   └── ding.py             # Main ding screen
│   └── styles/
│       └── retro.css           # 80's retro styling
├── core/
│   ├── __init__.py
│   ├── models.py               # SQLAlchemy database models
│   ├── database.py             # Database session management
│   ├── config.py               # Application configuration
│   └── security.py             # PIN generation, validation, sessions
├── services/
│   ├── __init__.py
│   ├── printer.py              # ESC/POS printer service
│   ├── email.py                # SendGrid integration
│   ├── image.py                # Image processing (resize, rotate, GIF)
│   └── text.py                 # Text processing (emoji, cowsay, encoding)
├── store/                      # Printer job images (resized)
├── postman/
│   └── ding-api.postman_collection.json
├── docs/
│   └── DING_IMPLEMENTATION_PLAN.md
├── .env                        # Environment variables
├── .env.example
├── requirements.txt
├── README.md
└── docker-compose.yml          # Optional: for easy deployment
```

---

## Database Schema

### Table: `users`
| Column      | Type      | Constraints           | Description                    |
|-------------|-----------|-----------------------|--------------------------------|
| id          | Integer   | PK, Auto-increment    | User ID                        |
| username    | String    | Unique, Not Null      | Username for login             |
| email       | String    | Not Null              | Email for PIN delivery         |
| is_active   | Boolean   | Default: True         | User active status             |
| created_at  | DateTime  | Default: now()        | Creation timestamp             |
| updated_at  | DateTime  | Default: now()        | Last update timestamp          |

### Table: `auth_pins`
| Column      | Type      | Constraints           | Description                    |
|-------------|-----------|-----------------------|--------------------------------|
| id          | Integer   | PK, Auto-increment    | PIN ID                         |
| user_id     | Integer   | FK(users.id)          | User reference                 |
| pin         | String(4) | Not Null              | 4-digit numeric PIN            |
| expires_at  | DateTime  | Not Null              | PIN expiration time            |
| created_at  | DateTime  | Default: now()        | PIN creation time              |
| used        | Boolean   | Default: False        | Whether PIN was used           |

**Notes**:
- New PIN request invalidates all previous unused PINs for the user
- PINs expire after 10 minutes (configurable)

### Table: `user_sessions`
| Column        | Type      | Constraints           | Description                    |
|---------------|-----------|-----------------------|--------------------------------|
| id            | Integer   | PK, Auto-increment    | Session ID                     |
| user_id       | Integer   | FK(users.id), Unique  | User reference (1 session/user)|
| session_token | String    | Unique, Not Null      | Session token                  |
| expires_at    | DateTime  | Not Null              | Session expiration             |
| last_activity | DateTime  | Default: now()        | Last activity timestamp        |
| created_at    | DateTime  | Default: now()        | Session creation time          |

**Notes**:
- Only one active session per user
- Activity extends the session timeout
- Default timeout: 180 minutes

### Table: `app_config`
| Column      | Type      | Constraints           | Description                    |
|-------------|-----------|-----------------------|--------------------------------|
| key         | String    | PK                    | Configuration parameter name   |
| value       | String    | Not Null              | Configuration value (JSON)     |
| updated_at  | DateTime  | Default: now()        | Last update timestamp          |

### Table: `ding_jobs`
| Column         | Type      | Constraints           | Description                         |
|----------------|-----------|-----------------------|-------------------------------------|
| id             | Integer   | PK, Auto-increment    | Job ID                              |
| user_id        | Integer   | FK(users.id)          | User who created the job            |
| job_type       | String    | Not Null              | text/image/text_with_image          |
| content_type   | String    | Not Null              | plain/cowsay/banner                 |
| text_content   | Text      | Nullable              | Text message content                |
| image_path     | String    | Nullable              | Path to resized image in store/     |
| font_size      | String    | Nullable              | small/medium/large                  |
| status         | String    | Default: pending      | pending/processing/success/failed   |
| error_message  | Text      | Nullable              | Error details if failed             |
| created_at     | DateTime  | Default: now()        | Job creation time                   |
| completed_at   | DateTime  | Nullable              | Job completion time                 |

---

## Configuration Parameters

Stored in `app_config` table as key-value pairs:

### Session & Authentication
- `session_timeout_minutes`: 180 (default)
- `session_warning_minutes`: 5 (warn user before timeout)
- `pin_rate_limit_minutes`: 1 (minimum time between PIN requests)
- `pin_expiry_minutes`: 10

### Printer Settings
- `printer_dots_per_line`: 384 (default)
- `feed_before_lines`: 1
- `feed_after_lines`: 3
- `cut_paper`: true

### Font Sizes & Text Layout
For each font size (`small`, `medium`, `large`):
- `text_chars_per_line_small`: 48
- `text_chars_per_line_medium`: 32
- `text_chars_per_line_large`: 24
- `cowsay_chars_per_line_small`: 40
- `cowsay_chars_per_line_medium`: 28
- `cowsay_chars_per_line_large`: 20

---

## API Endpoints (FastAPI)

All management endpoints require Bearer API key authentication (stored in `API_KEY` environment variable).

### User Management

#### `POST /api/users`
Create a new user.
```json
{
  "username": "string",
  "email": "string"
}
```
**Response**: User object with ID

#### `GET /api/users`
List all users (with pagination).

#### `GET /api/users/{user_id}`
Get user details by ID.

#### `PUT /api/users/{user_id}`
Update user information.
```json
{
  "username": "string",
  "email": "string",
  "is_active": true
}
```

#### `DELETE /api/users/{user_id}`
Delete (or deactivate) a user.

### Configuration Management

#### `GET /api/config`
Get all configuration parameters.

#### `GET /api/config/{key}`
Get specific configuration value.

#### `PUT /api/config/{key}`
Update configuration value.
```json
{
  "value": "string"
}
```

### Job Management

#### `GET /api/jobs`
Query printer jobs with filters.
**Query params**:
- `username`: Filter by username
- `start_date`: ISO datetime
- `end_date`: ISO datetime
- `status`: Filter by status

#### `GET /api/jobs/{job_id}`
Get job details.

#### `GET /api/jobs/{job_id}/image`
Download the job's image file (if exists).

#### `POST /api/jobs/{job_id}/retry`
Retry a failed job.

---

## Authentication Flow

### 1. User Login (Streamlit UI)
```
User enters username
    ↓
System checks if user exists and is active
    ↓
Rate-limit check (1 minute since last PIN request)
    ↓
Generate 4-digit PIN (0000-9999)
    ↓
Invalidate all previous unused PINs for user
    ↓
Store PIN in auth_pins table (expires in 10 minutes)
    ↓
Send PIN via SendGrid email
    ↓
User enters PIN in UI
    ↓
Validate PIN (correct, not used, not expired)
    ↓
Invalidate all existing sessions for user
    ↓
Create new session with token
    ↓
Store session token in Streamlit session state
    ↓
Redirect to Ding screen
```

### 2. Session Management
- Session token stored in Streamlit `st.session_state`
- Every user action updates `last_activity` in database
- Session expires after N minutes of inactivity (extends on activity)
- Warning shown 5 minutes before expiration
- Only one active session per user (new login invalidates old session)

### 3. Logout
- Delete session from database
- Clear Streamlit session state
- Redirect to login page

---

## Printer Service Implementation

### Printer Connection
```python
from escpos.printer import Usb, File

# Option 1: USB
p = Usb(0x0416, 0x5011)

# Option 2: File device
p = File("/dev/usb/lp0")
```

### Job Processing Pipeline

#### Text Jobs (Plain)
1. Convert emojis to text: `emoji.demojize("Hello 😀")` → `"Hello :grinning_face:"`
2. Handle UTF-8 to ESC/POS encoding (unidecode or python-escpos)
3. Set font size based on user selection
4. Apply text wrapping based on `text_chars_per_line_{size}`
5. Send to printer with feed_before/feed_after
6. Cut paper if configured

#### Text Jobs (Cowsay)
1. Convert emojis to text
2. Wrap text based on `cowsay_chars_per_line_{size}`
3. Run: `cowsay -W {max_width} "{text}"`
4. Capture output
5. Set font size
6. Send cowsay output to printer
7. Feed and cut

#### Image Jobs (Normal)
1. Accept: JPG, PNG, GIF
2. If GIF: Extract first frame only using Pillow
3. Resize image to fit `printer_dots_per_line` width
4. Convert to black & white if needed
5. Send to printer using `p.image()`
6. If caption provided: print caption below image
7. Feed and cut

#### Image Jobs (Banner Mode)
1. Process image as above
2. Rotate image 90 degrees (for banner orientation)
3. Send to printer
4. No caption in banner mode
5. Feed and cut

### Error Handling
- Catch printer connection errors
- Catch paper out / hardware errors
- Update job status to `failed` with error message
- Log errors for debugging

### Job Status Updates
- Update database job status: `pending` → `processing` → `success`/`failed`
- Provide real-time feedback via polling (every 1-2 seconds from Streamlit)

---

## Streamlit UI Implementation

### Theme: 80's Retro / 8-bit Style

**Color Palette**:
- Primary: Electric Blue (#00FFFF, cyan)
- Background: Dark Blue (#000033) / Black (#000000)
- Accent: Hot Pink (#FF10F0)
- Text: Cyan, White, Green (#00FF00)

**Typography**:
- Monospace fonts: 'VT323', 'Press Start 2P', 'Courier New'
- Pixelated UI elements
- ASCII art decorations

**Visual Effects**:
- CRT screen effect (optional scanlines)
- Neon glow on buttons/borders
- Retro terminal aesthetic
- Pixelated icons

**Responsive Design**:
- Mobile-first approach
- Touch-friendly buttons (large tap targets)
- Vertical layout for mobile
- Tested on iPhone/Android screens

### Page: Login (`ui/pages/login.py`)

```
+----------------------------------+
|         🖨️  D I N G  🖨️         |
|    [ Retro Receipt Printer ]    |
+----------------------------------+
|                                  |
|  Username: [_____________]       |
|                                  |
|  [ SEND PIN ]                    |
|                                  |
|  4-Digit PIN: [____]             |
|                                  |
|  [ LOGIN ]                       |
|                                  |
+----------------------------------+
```

**Flow**:
1. User enters username
2. Click "Send PIN" → API call → Email sent → Success message
3. User enters PIN
4. Click "Login" → Validate → Redirect to ding screen

**Features**:
- Rate limiting feedback ("Wait 1 minute before requesting new PIN")
- Error messages (user not found, invalid PIN, expired PIN)
- Loading states during API calls

### Page: Ding Screen (`ui/pages/ding.py`)

```
+----------------------------------+
|  🖨️  DING  |  Session: 2:45:00  |
|             |  [LOGOUT]          |
+----------------------------------+
|  [ TEXT ]  [ IMAGE ]             |
+----------------------------------+
|                                  |
|  Message:                        |
|  [____________________________]  |
|  [____________________________]  |
|                                  |
|  Font Size: ( ) S (•) M ( ) L    |
|  Format: (•) Plain ( ) Cowsay    |
|                                  |
|  [ 🚀 SEND TO PRINTER ]          |
|                                  |
|  Status: ⏳ Sending...           |
+----------------------------------+
```

**Tabs**:

#### Tab 1: Text Message
- Multi-line text area
- Font size radio buttons: Small / Medium / Large
- Format radio buttons: Plain / Cowsay
- Character counter (based on selected font size)

#### Tab 2: Image
- File uploader (JPG, PNG, GIF)
- Optional text caption field
- Banner mode checkbox
- Font size for caption (if banner mode is off)
- Image preview (thumbnail)

**Features**:
- Session timer countdown in header
- Warning modal 5 minutes before expiration
- Job status polling and display:
  - ⏳ Sending...
  - ✅ Success! (with job ID)
  - ❌ Failed (with error message)
- History of recent dings (last 5 jobs)
- Logout button

---

## Services Implementation

### `services/email.py` - SendGrid Integration
```python
def send_pin_email(email: str, pin: str, username: str):
    """Send PIN via SendGrid API"""
    # Template email with retro styling
    # Subject: "Your DING Login Code"
    # Body: ASCII art + PIN + expiration time
```

### `services/text.py` - Text Processing
```python
def convert_emojis_to_text(text: str) -> str:
    """Convert emojis to text representation"""
    return emoji.demojize(text)

def wrap_text_for_printer(text: str, max_width: int) -> str:
    """Wrap text based on character limit"""
    # textwrap.wrap or custom implementation

def generate_cowsay(text: str, max_width: int) -> str:
    """Generate cowsay output"""
    # subprocess.run(['cowsay', '-W', str(max_width), text])

def encode_for_escpos(text: str) -> str:
    """Convert UTF-8 to ESC/POS compatible encoding"""
    # Use unidecode or python-escpos built-in
```

### `services/image.py` - Image Processing
```python
def process_image(
    image_path: str,
    output_path: str,
    max_width: int = 384,
    rotate: bool = False
) -> str:
    """
    Resize and optionally rotate image for printer
    If GIF: extract first frame only
    """
    from PIL import Image

    img = Image.open(image_path)

    # If GIF, get first frame
    if img.format == 'GIF':
        img.seek(0)
        img = img.convert('RGB')

    # Resize
    wpercent = (max_width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((max_width, hsize), Image.Resampling.LANCZOS)

    # Rotate if banner mode
    if rotate:
        img = img.rotate(90, expand=True)

    # Convert to black & white (1-bit)
    img = img.convert('1')

    img.save(output_path)
    return output_path
```

### `services/printer.py` - Printer Service
```python
class PrinterService:
    def __init__(self):
        # Initialize printer connection
        self.printer = self._connect()

    def _connect(self):
        """Connect to ESC/POS printer"""
        try:
            return Usb(0x0416, 0x5011)
        except:
            return File("/dev/usb/lp0")

    def print_job(self, job_id: int):
        """Process and print a job"""
        # Load job from database
        # Update status to 'processing'
        # Process based on job_type
        # Handle errors
        # Update status to 'success' or 'failed'

    def print_text(self, text: str, font_size: str, is_cowsay: bool):
        """Print text message"""

    def print_image(self, image_path: str, caption: str = None):
        """Print image with optional caption"""

    def _feed_and_cut(self):
        """Apply feed_before, feed_after, and cut_paper settings"""
```

---

## Deployment Architecture

### Running the Application

**Terminal 1: FastAPI**
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8508 --reload
```

**Terminal 2: Streamlit**
```bash
streamlit run ui/app.py --server.port 8501
```

### Reverse Proxy (Nginx) Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://localhost:8508;
    }

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Environment Variables (`.env`)
```
# API Authentication
API_KEY=your-secret-api-key-here

# Database
DATABASE_URL=sqlite:///./ding.db

# SendGrid
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@your-domain.com

# Printer
PRINTER_VENDOR_ID=0x0416
PRINTER_PRODUCT_ID=0x5011
PRINTER_DEVICE_PATH=/dev/usb/lp0

# App
APP_NAME=DING
APP_URL=http://your-domain.com
```

---

## Testing Strategy

### Unit Tests
- Text processing functions (emoji conversion, wrapping)
- Image processing functions (resize, rotate, GIF first frame)
- PIN generation and validation
- Session management

### Integration Tests
- API endpoints (user CRUD, config, jobs)
- Database operations
- Email sending (mock SendGrid)

### Manual Testing
- End-to-end user flow (login → send message → verify print)
- Printer connectivity and error handling
- Mobile responsiveness
- Session timeout and warnings

---

## Postman Collection

Located in `postman/ding-api.postman_collection.json`

**Includes**:
- Environment variables setup (API_KEY, base_url)
- All user management endpoints
- Configuration endpoints
- Job query and retry endpoints
- Example requests with sample data

---

## Initial Setup Checklist

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Install system dependencies: `sudo apt install cowsay`
3. ✅ Copy `.env.example` to `.env` and configure
4. ✅ Initialize database: `python -m core.database`
5. ✅ Create initial admin user via API
6. ✅ Configure app settings via API
7. ✅ Test printer connection
8. ✅ Start FastAPI server
9. ✅ Start Streamlit UI
10. ✅ Test end-to-end flow

---

## Future Enhancements (Out of Scope for v1)

- Multiple printer support
- Custom cowsay characters selection
- Image filters and effects before printing
- Scheduled dings
- QR code generation and printing
- Webhook notifications for job status
- Admin dashboard for monitoring
- Multi-language support
- Dark/light theme toggle (beyond retro theme)

---

## Development Timeline Estimate

1. **Core Setup** (1 day)
   - Project structure
   - Database models
   - Configuration system

2. **API Development** (2 days)
   - User management endpoints
   - Config endpoints
   - Job endpoints
   - Authentication middleware

3. **Authentication System** (1 day)
   - PIN generation
   - Email integration
   - Session management

4. **Printer Service** (2 days)
   - Text processing (emoji, cowsay, wrapping)
   - Image processing (resize, rotate, GIF)
   - ESC/POS integration
   - Error handling

5. **Streamlit UI** (2 days)
   - Login page
   - Ding screen
   - Session management
   - Job status polling

6. **Styling & UX** (1 day)
   - Retro 80's CSS
   - Mobile responsiveness
   - Polish and refinements

7. **Testing & Documentation** (1 day)
   - Integration testing
   - Postman collection
   - README and setup docs

**Total**: ~10 days

---

## Success Criteria

- ✅ Users can authenticate via email PIN
- ✅ Users can send text messages (plain and cowsay) with font size selection
- ✅ Users can send images (JPG, PNG, GIF) with optional captions
- ✅ Banner mode rotates images correctly
- ✅ Emojis are converted to text representation
- ✅ GIF images print first frame only
- ✅ Session management works (timeout, warnings, single session per user)
- ✅ Real-time job status updates via polling
- ✅ All API endpoints functional and documented
- ✅ Mobile-responsive retro UI
- ✅ Printer jobs can be queried and retried
- ✅ Error handling for printer failures

---

**Project Start Date**: 2025-11-27
**Target Completion**: 2025-12-07
