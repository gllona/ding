# 🖨️ DING - Retro Receipt Printer

**DING** is a web-based application that allows authenticated users to send messages and images to an ESC/POS thermal receipt printer. Features a retro 80's aesthetic with 8-bit styling.

**"To ding something"** = "To send something to the printer"

---

## ✨ Features

### 🔐 Authentication
- Email-based PIN authentication (no passwords!)
- 4-digit PIN sent via SendGrid
- Rate-limited PIN requests (prevent abuse)
- Session management with timeout and warnings
- One active session per user

### 📝 Text Messages
- Plain text or Cowsay format
- Multiple font sizes (small/medium/large)
- Automatic emoji to text conversion (😀 → `:grinning_face:`)
- UTF-8 to ESC/POS encoding
- Configurable text wrapping per font size

### 🖼️ Images
- Support for JPG, PNG, GIF formats
- GIF support (first frame only)
- Automatic resizing to fit printer width
- Optional text captions
- Banner mode (90° rotation)

### 🎨 UI/UX
- Retro 80's / 8-bit design
- Electric blue and hot pink color scheme
- CRT scanline effects
- Mobile-responsive
- Real-time job status updates

### 🔧 Management
- REST API for user management (CRUD)
- Configuration management via API
- Job querying and retry functionality
- Postman collection included

---

## 🏗️ Architecture

### Tech Stack
- **Backend API**: FastAPI
- **Frontend UI**: Streamlit
- **Database**: SQLite + SQLAlchemy
- **Email**: SendGrid
- **Printer**: python-escpos
- **Image Processing**: Pillow
- **Text Processing**: emoji, unidecode, cowsay

### Project Structure
```
ding/
├── api/                    # FastAPI REST API
│   ├── endpoints/          # API endpoints
│   └── main.py            # FastAPI app
├── ui/                     # Streamlit UI
│   ├── pages/             # UI pages
│   ├── styles/            # CSS styling
│   └── app.py             # Streamlit app
├── core/                   # Core functionality
│   ├── models.py          # Database models
│   ├── database.py        # DB management
│   ├── config.py          # Configuration
│   └── security.py        # Auth & sessions
├── services/               # Business logic
│   ├── email.py           # SendGrid integration
│   ├── text.py            # Text processing
│   ├── image.py           # Image processing
│   └── printer.py         # Printer service
├── store/                  # Uploaded images
├── postman/               # Postman collection
└── docs/                  # Documentation
```

---

## 🚀 Quick Start

> See also the [Raspberry Pi Full Setup Guide](docs/RASPBERRY_PI_FULL_SETUP.md)!

### Prerequisites
- Python 3.10+
- ESC/POS thermal printer (USB or /dev/usb/lp0)
- SendGrid API key
- cowsay installed: `sudo apt install cowsay`

### Installation

1. **Clone the repository**
```bash
cd /home/gorka/printers/repos/ding
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source .venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install system dependencies**
```bash
sudo apt install cowsay  # Linux/Mac
```

5. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

Required environment variables:
- `API_KEY`: Secret key for API authentication
- `SENDGRID_API_KEY`: Your SendGrid API key
- `SENDGRID_FROM_EMAIL`: Email address for sending PINs
- `PRINTER_VENDOR_ID`: USB vendor ID (default: 0x0416)
- `PRINTER_PRODUCT_ID`: USB product ID (default: 0x5011)
- `PRINTER_DEVICE_PATH`: File device path (default: /dev/usb/lp0)

6. **Initialize database**
```bash
python -m core.database
```

This will:
- Create all database tables
- Initialize default configuration parameters

---

## 🎮 Running the Application

### Start FastAPI Backend (Terminal 1)
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8508 --reload
```

API will be available at:
- API: http://localhost:8508
- API Docs: http://localhost:8508/docs
- Health Check: http://localhost:8508/health

### Start Streamlit UI (Terminal 2)
```bash
streamlit run ui/app.py --server.port 8501
```

UI will be available at:
- http://localhost:8501

---

## 👥 User Management

### Create Users via API

Use the Postman collection in `postman/ding-api.postman_collection.json` or use curl:

```bash
# Set your API key
export API_KEY="your-secret-api-key-here"

# Create a user
curl -X POST http://localhost:8508/api/users \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "johndoe@example.com"
  }'

# List users
curl -X GET http://localhost:8508/api/users \
  -H "Authorization: Bearer $API_KEY"
```

### User Login Flow

1. User enters username on login page
2. Click "SEND PIN"
3. User receives 4-digit PIN via email
4. User enters PIN
5. User is logged in for 180 minutes (configurable)

---

## 🎨 Using DING

### Send Text Message
1. Log in with username and PIN
2. Go to "TEXT MESSAGE" tab
3. Type your message
4. Select font size (small/medium/large)
5. Choose format (Plain or Cowsay)
6. Click "SEND TO PRINTER"

### Send Image
1. Log in with username and PIN
2. Go to "IMAGE" tab
3. Upload image (JPG, PNG, or GIF)
4. Optionally add a caption
5. Enable banner mode for 90° rotation
6. Click "SEND TO PRINTER"

### Job Status
- Jobs are processed asynchronously
- Real-time status updates via polling
- View recent jobs at bottom of page
- Statuses: pending → processing → success/failed

---

## 🔧 Configuration

All configuration parameters are stored in the database and can be managed via API:

### View Current Configuration
```bash
curl -X GET http://localhost:8508/api/config \
  -H "Authorization: Bearer $API_KEY"
```

### Update Configuration
```bash
curl -X PUT http://localhost:8508/api/config/session_timeout_minutes \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"value": "120"}'
```

### Available Parameters

**Session & Authentication**
- `session_timeout_minutes`: 180 (3 hours)
- `session_warning_minutes`: 5
- `pin_rate_limit_minutes`: 1
- `pin_expiry_minutes`: 10

**Printer Settings**
- `printer_dots_per_line`: 384
- `feed_before_lines`: 1
- `feed_after_lines`: 3
- `cut_paper`: true

**Font Sizes - Text**
- `text_chars_per_line_small`: 48
- `text_chars_per_line_medium`: 32
- `text_chars_per_line_large`: 24

**Font Sizes - Cowsay**
- `cowsay_chars_per_line_small`: 40
- `cowsay_chars_per_line_medium`: 28
- `cowsay_chars_per_line_large`: 20

---

## 📡 API Endpoints

### Health Check
```
GET /health
```

### User Management
```
POST   /api/users          # Create user
GET    /api/users          # List users
GET    /api/users/{id}     # Get user
PUT    /api/users/{id}     # Update user
DELETE /api/users/{id}     # Delete user
```

### Configuration
```
GET /api/config            # Get all config
GET /api/config/{key}      # Get config by key
PUT /api/config/{key}      # Update config
```

### Jobs
```
GET  /api/jobs                  # Query jobs (with filters)
GET  /api/jobs/{id}             # Get job details
GET  /api/jobs/{id}/image       # Download job image
POST /api/jobs/{id}/retry       # Retry failed job
```

**Query Parameters for /api/jobs:**
- `username`: Filter by username
- `start_date`: ISO 8601 datetime
- `end_date`: ISO 8601 datetime
- `status`: pending/processing/success/failed

All management endpoints require Bearer token authentication with `API_KEY`.

---

## 🖨️ Printer Setup

### Supported Printers
Any ESC/POS compatible thermal receipt printer should work. Tested with:
- 58mm thermal printers
- 80mm thermal printers
- Standard: 384 dots-per-line

### Connection Methods

#### USB Connection
```python
# Default vendor/product IDs in .env
PRINTER_VENDOR_ID=0x0416
PRINTER_PRODUCT_ID=0x5011
```

Find your printer IDs:
```bash
lsusb
# Example output: Bus 001 Device 005: ID 0416:5011 Printer
# Example output: Bus 001 Device 089: ID 0416:5011 Winbond Electronics Corp. Virtual Com Port
```

#### File Device Connection
```bash
# Check if device exists
ls -l /dev/usb/lp0

# Set in .env
PRINTER_DEVICE_PATH=/dev/usb/lp0
```

### Permissions
```bash
# Add user to lp group (printer access)
sudo usermod -a -G lp $USER

# Reload groups
newgrp lp
```

---

## 🐛 Troubleshooting

### Printer Not Found
- Check USB connection: `lsusb`
- Verify vendor/product IDs in .env
- Check permissions: `ls -l /dev/usb/lp0`
- Try file device method instead of USB

### Email Not Sending
- Verify SendGrid API key is valid
- Check SendGrid sender authentication
- Verify `SENDGRID_FROM_EMAIL` is authorized in SendGrid

### Cowsay Not Working
- Install cowsay: `sudo apt install cowsay`
- Verify installation: `which cowsay`

### Session Expires Too Quickly
- Increase `session_timeout_minutes` via API
- Check that activity is extending session

### Database Issues
- Delete `ding.db` and reinitialize: `python -m core.database`
- Check file permissions on database file

---

## 📋 Development

### Run Tests
```bash
pytest tests/
```

### Code Style
```bash
black .
flake8 .
```

### Database Migrations
```bash
# After model changes
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

---

## 🔒 Security Notes

- **API Key**: Keep `API_KEY` secret. Use strong random value in production.
- **SendGrid**: Protect your SendGrid API key. Use environment variables.
- **HTTPS**: In production, use HTTPS for both API and UI.
- **Rate Limiting**: PIN requests are rate-limited to prevent abuse.
- **Session Security**: Sessions expire and are invalidated on logout.

---

## 📦 Deployment

### Using systemd

**FastAPI service** (`/etc/systemd/system/ding-api.service`):
```ini
[Unit]
Description=DING API
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/ding
Environment="PATH=/path/to/ding/venv/bin"
ExecStart=/path/to/ding/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8508
Restart=always

[Install]
WantedBy=multi-user.target
```

**Streamlit service** (`/etc/systemd/system/ding-ui.service`):
```ini
[Unit]
Description=DING UI
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/ding
Environment="PATH=/path/to/ding/venv/bin"
ExecStart=/path/to/ding/venv/bin/streamlit run ui/app.py --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ding-api ding-ui
sudo systemctl start ding-api ding-ui
```

### Using Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /api {
        proxy_pass http://localhost:8508;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 📝 License

This project is provided as-is for educational and personal use.

---

## 🙏 Acknowledgments

- **python-escpos**: ESC/POS printer library
- **Streamlit**: Amazing web UI framework
- **FastAPI**: Modern Python web framework
- **SendGrid**: Email delivery service
- **cowsay**: Classic Unix utility

---

## 🎯 Roadmap

- [ ] Support for multiple printers
- [ ] Custom cowsay characters
- [ ] Image filters and effects
- [ ] Scheduled dings
- [ ] QR code generation
- [ ] Admin dashboard
- [ ] Docker deployment
- [ ] Multi-language support

---

**Happy Dinging! 🖨️✨**
