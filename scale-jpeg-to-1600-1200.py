import os
import sys
from PIL import Image
import numpy as np

TARGET_WIDTH = 1200
TARGET_HEIGHT = 1600

input_path, output_path = sys.argv[1:]

image = Image.open(input_path)
bw_array = np.array(image)

current_height, current_width, _ = bw_array.shape
height_ratio = TARGET_HEIGHT / current_height
width_ratio = TARGET_WIDTH / current_width

if height_ratio * current_width <= TARGET_WIDTH:
    new_height = TARGET_HEIGHT
    new_width = int(current_width * height_ratio)
else:
    new_width = TARGET_WIDTH
    new_height = int(current_height * width_ratio)

scale_dim = (new_width, new_height)
resized_image = Image.fromarray(bw_array).resize(scale_dim)
resized_array = np.array(resized_image)

horizontal_padding = (TARGET_WIDTH - new_width) // 2
vertical_padding = (TARGET_HEIGHT - new_height) // 2
padded_array = np.pad(
    resized_array,
    (
        (vertical_padding, vertical_padding),
        (horizontal_padding, horizontal_padding),
        (0, 0),
    ),
    "constant",
    constant_values=255,
)

final_image = Image.fromarray(padded_array)
final_image.save(output_path)
print(output_path)
