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


image_path = sys.argv[1]
image = Image.open(image_path)
for i, segment in enumerate(preprocess(image)):
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
