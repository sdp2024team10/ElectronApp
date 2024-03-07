import os
import sys
import json
import serial
import base64
import tempfile

# required for nodejs to parse in real time
sys.stdout.reconfigure(line_buffering=True, write_through=True)

print(json.dumps({"image_path": "../hand-math.jpeg"}))
quit()


PREFIX = os.getenv("TMP", "/tmp/")

port = sys.argv[1]  # "/dev/ttyS3"
baud_rate = int(sys.argv[2])  # 115200

print(f"connecting to port {port} with baud rate {baud_rate}")
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
            print(json.dumps({"image_path": my_tempfile.name}))
    except UnicodeDecodeError:
        print(line)

print("serial connection closed!")
