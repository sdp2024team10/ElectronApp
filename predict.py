#!/usr/bin/env python
import os
import sys
import json
import torch
import datetime
import numpy as np
from PIL import Image
from typing import List
from IPython.display import display
from torchvision.transforms import ToTensor

# nodejs spawns this process in the appropriate directory
sys.path.append(os.getcwd())

from comer.datamodule import vocab
from comer.lit_comer import LitCoMER

print("hello, world!")

# required for nodejs to parse in real time
sys.stdout.reconfigure(line_buffering=True, write_through=True)

ckpt = "./lightning_logs/version_0/checkpoints/epoch=151-step=57151-val_ExpRate=0.6365.ckpt"
model = LitCoMER.load_from_checkpoint(ckpt)
model = model.eval()
device = torch.device("cpu")
model = model.to(device)


def convert_black_white(image: Image, threshold=150):
    return image.convert("L").point(lambda x: 255 if x < threshold else 0, "1")


def split_rows(image: Image, num_segments: int) -> List[Image]:
    output = []
    width, height = image.size
    segment_height = int(height / num_segments)
    for i in range(num_segments):
        top = i * segment_height
        bottom = (
            (i + 1) * segment_height if i < num_segments - 1 else height
        )  # Ensure last segment goes to the edge
        output.append(image.crop((0, top, width, bottom)))
    return output


def strip_black_edges(image: Image, padding=10) -> Image:
    bw_array = np.array(image)

    def find_non_white_edges(arr):
        rows = np.where(~np.all(arr == False, axis=1))[0]
        cols = np.where(~np.all(arr == False, axis=0))[0]
        return rows[0], rows[-1], cols[0], cols[-1]

    first_row, last_row, first_col, last_col = find_non_white_edges(bw_array)
    first_row = max(0, first_row - padding)
    last_row = min(bw_array.shape[0], last_row + padding)
    first_col = max(0, first_col - padding)
    last_col = min(bw_array.shape[1], last_col + padding)

    stripped_arr = bw_array[first_row : last_row + 1, first_col : last_col + 1]
    return Image.fromarray(stripped_arr)


def predict(image: Image) -> str:
    img_tensor = ToTensor()(image)
    mask = torch.zeros_like(img_tensor, dtype=torch.bool)
    hyp = model.approximate_joint_search(img_tensor.unsqueeze(0), mask)[0]
    pred_latex = vocab.indices2label(hyp.seq)
    return pred_latex


image_path = sys.argv[1]
image = Image.open(image_path)
image = convert_black_white(image)
for i, segment in enumerate(split_rows(image, 11)):
    segment = strip_black_edges(segment)
    segment.save(f"{i}.bmp")
    if i == 0:
        continue
    before = datetime.datetime.now()
    prediction = predict(segment)
    prediction_time = datetime.datetime.now() - before

    print(
        json.dumps(
            {
                "type": "prediction-result",
                "data": {
                    "index": i,
                    "latex": predict(segment),
                    "time": str(prediction_time),
                },
            },
        )
    )
