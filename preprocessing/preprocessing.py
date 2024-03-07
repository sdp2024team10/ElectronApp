import sys
import os
from PIL import Image

input_path = sys.argv[1]
image = Image.open(input_path)
gray_image = image.convert("L")
threshold = 150  # Define the threshold (can be adjusted)
bw_image = gray_image.point(lambda x: 255 if x < threshold else 0, "1")
output_path = os.path.basename(input_path).rsplit(".", 1)[0] + ".bmp"
bw_image.save(output_path, "BMP")
print(output_path)
