#!/usr/bin/env python3
import sys
from PIL import Image

img = Image.open(sys.argv[1])
print(f"w: {img.width} px")
print(f"h: {img.height} px")
