from PIL import Image, ImageFilter
import numpy as np
from typing import List
import sys
import cv2


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
    if np.all(bw_array == False):
        print(
            "warning: attempted to strip black edges from entirely black image!",
            file=sys.stderr,
        )
        return image

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


def trim(image: Image, trim_sizes_px: dict) -> Image:
    width, height = image.size
    left = trim_sizes_px["left"]
    upper = trim_sizes_px["top"]
    right = width - trim_sizes_px["right"]
    lower = height - trim_sizes_px["bottom"]
    # clamp image size bounds
    left = max(left, 0)
    upper = max(upper, 0)
    right = min(right, width)
    lower = min(lower, height)
    return image.crop((left, upper, right, lower))


def crop(image: Image, crop_coords) -> Image:
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    pts1 = np.float32(crop_coords)
    # distance between top left and top right
    width = int(crop_coords[1][0] - crop_coords[0][0])
    # distance between bottom left and top left
    height = int(crop_coords[3][1] - crop_coords[0][1])
    pts2 = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    result = cv2.warpPerspective(cv_image, matrix, (width, height))
    return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))


def preprocess(
    image: Image,
    num_rows: int,
    black_white_thresh: int,
    rotation_deg: int,
    crop_coords,
    trim_sizes_px={"left": 0, "right": 0, "top": 0, "bottom": 0},
):
    # image = image.filter(ImageFilter.SHARPEN)
    image = crop(image, crop_coords)
    assert rotation_deg % 90 == 0, "rotation must be a multiple of 90"
    image = image.rotate(rotation_deg, expand=True)
    image = trim(image, trim_sizes_px)
    image = convert_black_white(image, black_white_thresh)
    output = []
    for i, segment in enumerate(split_rows(image, num_rows)):
        extrema = segment.convert("L").getextrema()
        if extrema[0] == extrema[1] == 0:
            print(
                f"found empty row at index {i}, skipping all following rows",
                file=sys.stderr,
            )
            break
        output.append(strip_black_edges(segment))
    return output


if __name__ == "__main__":
    # trim_sizes_px = {"left": 80, "right": 40, "top": 0, "bottom": 0}
    trim_sizes_px = {"left": 10, "right": 10, "top": 0, "bottom": 0}
    num_rows = 10
    black_white_thresh = 100
    rotation_deg = 90
    crop_coords = [(57, 82), (960, 67), (949, 723), (75, 735)]
    segments = preprocess(
        Image.open(sys.argv[1]),
        num_rows,
        black_white_thresh,
        rotation_deg,
        crop_coords,
        trim_sizes_px,
    )
    for i, segment in enumerate(segments):
        segment.save(f"segment{i}.bmp")
