Hello! We will implement `ding`, a funny python project providing a web interface to send, from the web, messages and images to a ESC/POS receipt printer connected to the server where ding runs.

These are the requirements:

Overview:

- An authenticated user, from the web, can send messages, images or both to the ESC/POS printer connected to the server.

Web UI:

- The user browsers to a public URL (which is directed to the server), where a python process provides a web UI to: 1. Authenticate the user; 2. Enter the content to send to the printer (message, image or both); 3. The server prints the content in the local printer.
- After that, the user remains logged by N minutes and is redirected to the screen where them can send other content to the printer.
- The user can logout, then the UI goes to the login page.

Authentication:

- All users are registered by CRUD REST endpoints. These user management CRUD endpoints are authenticated by an bearer API key.
- In the login screen, the user enters its username, then an email is send to the user (the email associated to each user is stored in DB). The email contains a 4-digits numeric PIN (which is valid for 10 minutes). Then the user enters the PIN in the login screen. After the user is validated, the flow directs to the `send to printer` screen.

Configuration:

- Users can be managed using the REST user management endpoints.
- Application parameters are also configured by REST endpoints:
- Number of minutes to remain logged in after entering a valid PIN.
- Maximum width of text per printer line, in characters.
- Maximum width of each printer line, in dots.
- Maximum width of text per line in a `cowsay` message.
- `feed_before` and `feed_after` printer values.
- `cut_paper` printer parameter (boolean telling if cut the paper after each print job).
- REST endpoints to query for printer jobs (dings) (including downloading a printer job image) and to retry a printer job. These queries can be filtered by username and by timestamp range.

UX/UI:

- The UX/UI should be retro-like, '80's style, 8-bit style, blue and black tones.
- The UX/UI should be responsive to be used in a mobile phone.
- The app name is `ding`.
- `To ding something` means `To send something to the printer`.
- UX/UI should be appealing to Gen Z users.

Ding screen:

- Enter a text message only. User can select if send it in plain or send it as a cowsay message.
- Upload an image. The user can type an additional text caption that will be printer just below the image.
- Upload an image and select banner mode (no additional caption available). In this case the image will be rotated after being sent to the printer.

Implementation details:

- What to do if the user send emojis? Would them be rendered by the thermal printer fonts?
- For `cowsay` text messages, the input text needs to be formatted in several lines (each one of them with a maximum length) before sending it to `cowsay`.
- Images need to be resized so their width is below the configurable printer's dots-per-line value.
- Images need to be rotated if the users selected banner mode.
- The printer support font sizes according to the ESC/POS standard.

Printer:

- The printer is a 384 dots-per-line black and white thermal POS, that can be used in two ways:
- `python-escpos`: `p = Usb(0x0416, 0x5011)` or `p = File("/dev/usb/lp0")`.
- Linux CLI: `cowsay "Hello printer!" > /dev/usb/lp0`.
- For cowsay, another option is to run `cowsay` and redirect the output to a file, read the file contents from python, and send the contents to the printer using `python-escpos`.
- Support only 1 concurrent login per user.
- Try to give feedback to the web user about the status of each printer job (sending / success / failed).
- Some configurable paper feed should be sent to the printer before and after each message or image (`feed_bafore` and `feed_after` parameters).

Database:

- User management table.
- User authentication table (expirable PIN's).
- Printer jobs table.
- Dings table (table registering messages sent to the printer) (images can be stored off-database, in the `store/` project subdirectory).

Tech Stack:

- Python.
- Streamlit for rendering the UI.
- SendGrid to send authentication emails to the users.
- python-escpos to format the content and send it to the printer.
- Linux cowsay to send specially formatted text messages to the printer.
- Pillow for image manipulation.
- SQLite for database.
- Other available dependencies are in `requirements.txt`.

Initial Parameters:

- Printer: 384 dost-per-inch.
- Minutes before being logged out: 180.

Code example (just for reference):

```
from escpos.printer import Usb


def resize_image(image_path, resized_path, base_width):
  from PIL import Image

  img = Image.open(image_path)
  wpercent = (base_width / float(img.size[0]))
  hsize = int((float(img.size[1]) * float(wpercent)))
  img = img.resize((base_width, hsize), Image.Resampling.LANCZOS)
  img.save(resized_path)


resize_image("rocky.jpg", "rocky_dog.jpg", 384)

# p = Usb(0x0416, 0x5011, 0, profile="TM-T88III")
p = Usb(0x0416, 0x5011)
#p.text("Hello World\n")
p.image("rocky_dog.jpg")
#p.barcode('4006381333931', 'EAN13', 64, 2, '', '')
p.cut()
```

Please ask any relevant question. After your questions are answered by me, let's proceed to the implementation plan. 
