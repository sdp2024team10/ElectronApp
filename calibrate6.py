import tkinter as tk
from tkinter import ttk, Canvas, Scrollbar, Scale
from tkinter import filedialog, Toplevel
from PIL import Image, ImageTk
import numpy as np
import cv2
import sys
import json
from preprocess import preprocess


sys.argv = ["", "image.jpeg"]

CALIBRATION = {
    "crop_coords": [None, None, None, None],
    "black_white_thresh": None,
    "trim_sizes_px": {"left": None, "right": None, "top": None, "bottom": None},
    "num_rows": None,
}


class SelectCoordinates:
    def __init__(self, master, path: str):
        self.master = master
        self.canvas = tk.Canvas(master, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.load_image(path)
        self.dragging_point = None

    def load_image(self, path: str):
        self.master.filename = path
        self.image = Image.open(self.master.filename)
        self.cv_image = cv2.cvtColor(np.array(self.image), cv2.COLOR_RGB2BGR)
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.set_initial_points()

    def set_initial_points(self):
        width, height = self.image.size
        self.points = [
            (width * 0.25, height * 0.25),
            (width * 0.75, height * 0.25),
            (width * 0.75, height * 0.75),
            (width * 0.25, height * 0.75),
        ]
        CALIBRATION["crop_coords"] = self.points
        self.draw_points_and_lines()
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def draw_points_and_lines(self):
        self.canvas.delete("all")  # Clear existing drawing
        self.canvas.create_image(
            0, 0, anchor=tk.NW, image=self.tk_image
        )  # Redraw the image
        for point in self.points:
            self.canvas.create_oval(
                point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5, fill="red"
            )
        # Draw lines between the points to form a quadrilateral
        for i in range(len(self.points)):
            next_index = (i + 1) % len(self.points)
            self.canvas.create_line(
                self.points[i][0],
                self.points[i][1],
                self.points[next_index][0],
                self.points[next_index][1],
                fill="green",
            )

    def on_click(self, event):
        for i, point in enumerate(self.points):
            if abs(point[0] - event.x) < 10 and abs(point[1] - event.y) < 10:
                self.dragging_point = i
                return

    def on_drag(self, event):
        if self.dragging_point is not None:
            width, height = self.image.size
            # Ensure the new position is within the image boundaries
            new_x = min(max(event.x, 0), width)
            new_y = min(max(event.y, 0), height)
            self.points[self.dragging_point] = (new_x, new_y)
            self.draw_points_and_lines()
            CALIBRATION["crop_coords"] = self.points

    def on_release(self, event):
        self.dragging_point = None


class CalibrationOptions:
    def __init__(self, parent):
        self.parent = parent
        self.num_rows_slider = Scale(
            parent, from_=1, to=15, orient=tk.HORIZONTAL, label="Num Rows"
        )
        self.num_rows_slider.pack(fill=tk.X)

        self.black_white_thresh_slider = Scale(
            parent,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            label="Black-White Threshold",
        )
        self.black_white_thresh_slider.pack(fill=tk.X)

        self.rotation_deg_options = ["90", "180", "270"]  # Rotation options
        self.rotation_deg_label = ttk.Label(parent, text="Rotation Degrees")
        self.rotation_deg_label.pack(fill=tk.X)
        self.rotation_deg_combobox = ttk.Combobox(
            parent, values=self.rotation_deg_options
        )
        self.rotation_deg_combobox.set("90")  # Default value
        self.rotation_deg_combobox.pack(fill=tk.X)

        self.trim_left_slider = Scale(
            parent,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            label="trim pixels left",
        )
        self.trim_left_slider.pack(fill=tk.X)
        self.trim_right_slider = Scale(
            parent,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            label="trim pixels right",
        )
        self.trim_right_slider.pack(fill=tk.X)
        self.trim_top_slider = Scale(
            parent, from_=0, to=255, orient=tk.HORIZONTAL, label="trim pixels top"
        )
        self.trim_top_slider.pack(fill=tk.X)
        self.trim_bottom_slider = Scale(
            parent,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            label="trim pixels bottom",
        )
        self.trim_bottom_slider.pack(fill=tk.X)

        self.apply_button = ttk.Button(parent, text="Apply", command=self.apply_changes)
        self.apply_button.pack(fill=tk.X)

    def apply_changes(self):
        CALIBRATION["num_rows"] = self.num_rows_slider.get()
        CALIBRATION["black_white_thresh"] = self.black_white_thresh_slider.get()
        CALIBRATION["rotation_deg"] = self.rotation_deg_combobox.get()
        CALIBRATION["trim_sizes_px"] = {
            "left": int(self.trim_left_slider.get()),
            "right": int(self.trim_right_slider.get()),
            "top": int(self.trim_top_slider.get()),
            "bottom": int(self.trim_bottom_slider.get()),
        }
        print(json.dumps(CALIBRATION))

        # Here, call your function that processes these values and returns a list of image paths
        # For example: image_paths = process_images(num_rows_val, black_white_thresh_val, ...)

        # Then, clear existing images from the right pane and add new ones
        # This part of the code will be dependent on how you've implemented image loading


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Calibration")
    root.geometry("200x10")

    select_coords_window = tk.Toplevel(root)
    select_coords_window.title("Select Points")
    select_coords_window.geometry("640x360")  # Adjust size as needed

    options_window = tk.Toplevel(root)
    options_window.title("Options")
    options_window.geometry("640x360")  # Adjust size as needed

    images_window = tk.Toplevel(root)
    images_window.title("Images")
    images_window.geometry("640x360")  # Adjust size as needed

    app = SelectCoordinates(select_coords_window, sys.argv[1])

    options = CalibrationOptions(options_window)

    # Creating a frame within the canvas for the images
    images_frame = ttk.Frame(images_window)

    images_canvas = Canvas(images_frame)
    images_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar_images = Scrollbar(
        images_window, orient=tk.VERTICAL, command=images_canvas.yview
    )
    scrollbar_images.pack(side=tk.RIGHT, fill=tk.Y)
    images_canvas.configure(yscrollcommand=scrollbar_images.set)
    images_canvas.bind(
        "<Configure>",
        lambda e: images_canvas.configure(scrollregion=images_canvas.bbox("all")),
    )

    images_canvas.create_window((0, 0), window=images_frame, anchor="nw")

    root.mainloop()
