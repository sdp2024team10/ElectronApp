import os
import sys
import serial
import base64
import tempfile

PREFIX = os.getenv("TMP")

port = sys.argv[1]  # "/dev/ttyS3"
baud_rate = int(sys.argv[2])  # 115200

serial_conn = serial.Serial(port, baud_rate)
serial_conn.setDTR(False)
serial_conn.setRTS(False)

while serial_conn.is_open:
    line = serial_conn.readline()
    try:
        line_str = line.decode("utf8")
        if line_str.startswith("image_jpeg_base64:"):
            _, image_jpeg_base64 = line_str.split(":", 1)
            my_tempfile = tempfile.NamedTemporaryFile(
                mode="w+b",
                delete=False,
                prefix=PREFIX,
                suffix=".jpeg",
            )
            my_tempfile.write(base64.b64decode(image_jpeg_base64))
            my_tempfile.close()
            print(f"image written to {my_tempfile.name}")
    except UnicodeDecodeError:
        print(line)
