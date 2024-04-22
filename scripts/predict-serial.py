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

from preprocess import preprocess

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


def predict(image: Image) -> str:
    img_tensor = ToTensor()(image)
    mask = torch.zeros_like(img_tensor, dtype=torch.bool)
    hyp = model.approximate_joint_search(img_tensor.unsqueeze(0), mask)[0]
    pred_latex = vocab.indices2label(hyp.seq)
    return pred_latex


image_path, preprocessing_calibration_str = sys.argv[1:]
preprocessing_calibration = json.loads(preprocessing_calibration_str)
image = Image.open(image_path)
rows = preprocess(
    image,
    preprocessing_calibration["num_rows"],
    preprocessing_calibration["black_white_thresh"],
    preprocessing_calibration["rotation_deg"],
    preprocessing_calibration["crop_coords"],
    preprocessing_calibration["trim_sizes_px"],
)
for i, row in enumerate(rows):
    before = datetime.datetime.now()
    prediction = predict(row)
    prediction_time = datetime.datetime.now() - before

    print(
        json.dumps(
            {
                "type": "prediction-result",
                "data": {
                    "index": i,
                    "latex": predict(row),
                    "time": str(prediction_time),
                },
            },
        )
    )
