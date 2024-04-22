#!/usr/bin/env python
import os
import sys
import json
import torch
from PIL import Image, ImageOps
from torchvision.transforms import ToTensor
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime

from preprocess import preprocess
from comer.datamodule import vocab
from comer.lit_comer import LitCoMER

sys.stdout.reconfigure(line_buffering=True, write_through=True)
ckpt = "./lightning_logs/version_0/checkpoints/epoch=151-step=57151-val_ExpRate=0.6365.ckpt"
model = LitCoMER.load_from_checkpoint(ckpt)
model = model.eval()
device = torch.device("cpu")
model = model.to(device)


def filter_result(result: str) -> str:
    output = result
    # common mistakes by prediction
    if " n " in output:
        output = output.replace(" n ", " 1 1 ")
    if " a " in output:
        output = output.replace(" a ", " 2 ")
    if "=" in output:
        output = output.replace("=", "-")
    return output


def predict(image: Image, index: int, start_time: datetime.datetime) -> dict:
    img_tensor = ToTensor()(image)
    mask = torch.zeros_like(img_tensor, dtype=torch.bool)

    hyp = model.approximate_joint_search(img_tensor.unsqueeze(0), mask)[0]
    pred_latex = vocab.indices2label(hyp.seq)
    prediction_time = datetime.datetime.now() - start_time
    pred_latex = filter_result(pred_latex)
    return {"index": index, "latex": pred_latex, "time": str(prediction_time)}


if __name__ == "__main__":
    image_path, preprocessing_calibration_str = sys.argv[1:]
    assert os.path.isfile(image_path)
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

    # Execute predictions in parallel
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {
            executor.submit(predict, row, i, datetime.datetime.now()): i
            for i, row in enumerate(rows)
        }

        for future in as_completed(futures):
            index = futures[future]
            try:
                result = future.result()
                print(json.dumps({"type": "prediction-result", "data": result}))
            except Exception as exc:
                print(f"Prediction generated an exception for index {index}: {exc}")
