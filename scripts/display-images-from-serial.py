import sys
import serial
import base64
import binascii
from tkinter import Tk, Label
from PIL import Image, ImageTk
from io import BytesIO

# Initial setup for Tkinter
root = Tk()
img_label = Label(root)
img_label.pack()


# Function to update the image displayed from base64 data
def update_image_display_from_base64(image_jpeg_base64):
    image_data = base64.b64decode(image_jpeg_base64)
    image = Image.open(BytesIO(image_data))
    image = image.resize((640, 480), Image.LANCZOS)  # Resize if necessary
    try:
        tk_image = ImageTk.PhotoImage(image)
    except OSError as e:
        print(e)
        return
    img_label.config(image=tk_image)
    img_label.image = tk_image  # Keep a reference!
    root.update()
    print("image displayed successfully!")


# Start the GUI in a non-blocking way
root.update_idletasks()
root.update()

# Serial connection setup
port = sys.argv[1]  # Example: "/dev/ttyS3"
baud_rate = int(sys.argv[2])  # Example: 115200


while True:
    print(f"Connecting to port {port} with baud rate {baud_rate}")
    with serial.Serial(port, baud_rate) as serial_conn:
        print("connected.")
        serial_conn.setDTR(False)
        serial_conn.setRTS(False)
        while serial_conn.is_open:
            line = serial_conn.readline()
            try:
                line_str = line.decode("utf8")
                if line_str.strip() == "goodbye, world!":
                    break
                if line_str.startswith("image_jpeg_base64:"):
                    _, image_jpeg_base64 = line_str.split(":", 1)
                    # Update image display directly from base64 data
                    try:
                        update_image_display_from_base64(image_jpeg_base64)
                    except binascii.Error as e:
                        print(e)
                else:
                    print(f"decoded line: '{line_str}'")

            except UnicodeDecodeError as e:
                print(f"Error decoding line: {e}")

print("Serial connection closed!")
