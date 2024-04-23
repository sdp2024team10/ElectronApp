from PIL import Image, ImageFilter
import numpy as np
from typing import List
import sys
import cv2

ROTATION_DEG = 270
NUM_ROWS = 11
GAUSSIAN_BLUR_KERNEL_SIZE = 17


def convert_black_white(image: Image, threshold=150):
    return image.convert("L").point(lambda x: 255 if x < threshold else 0, "1")
    # cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    # cv_img = cv2.GaussianBlur(cv_img, (19, 19), 0)
    # binary_cv_img = cv2.adaptiveThreshold(
    #     cv_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    # )
    # return Image.fromarray(binary_cv_img)


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


def equalizeHist(image) -> Image:
    # image_array = np.array(image).astype("uint8")
    grayscale_cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    equalized_grayscale_cv_image = cv2.equalizeHist(grayscale_cv_image)
    equalized_cv_image = cv2.cvtColor(
        np.array(equalized_grayscale_cv_image), cv2.COLOR_GRAY2BGR
    )
    return Image.fromarray(equalized_cv_image)


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
    black_white_thresh: int,
    crop_coords,
):
    # image = image.filter(ImageFilter.SHARPEN)
    image = crop(image, crop_coords)
    image = equalizeHist(image)
    image = image.rotate(ROTATION_DEG, expand=True)
    image = convert_black_white(image, black_white_thresh)
    output = []
    for i, segment in enumerate(split_rows(image, NUM_ROWS)):
        extrema = segment.convert("L").getextrema()
        if extrema[0] == extrema[1] == 0:
            print(
                f"found empty row at index {i}, skipping all following rows",
                file=sys.stderr,
            )
            break
        output.append(strip_black_edges(segment))
    return output


# this is not usually the case, this is just an example
if __name__ == "__main__":
    segments = preprocess(
        Image.open(sys.argv[1]),
        [(57, 82), (960, 67), (949, 723), (75, 735)],
        black_white_thresh,
    )
    for i, segment in enumerate(segments):
        segment.save(f"segment{i}.bmp")
