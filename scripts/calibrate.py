import tkinter as tk
from tkinter import ttk, Canvas, Scrollbar, Scale
from PIL import Image, ImageTk
import numpy as np
import cv2
import sys
import json
from preprocess import preprocess

# required for nodejs to parse in real time
sys.stdout.reconfigure(line_buffering=True, write_through=True)


class SelectCoordinates:
    def __init__(self, master, image: Image, initial_calibration: dict = None):
        self.master = master
        self.canvas = tk.Canvas(master, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        if initial_calibration is not None:
            self.load_image(image, initial_calibration["crop_coords"])
        else:
            self.load_image(image)
        self.dragging_point = None
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def load_image(self, image: Image, starting_points: list = None):
        self.image = image
        self.cv_image = cv2.cvtColor(np.array(self.image), cv2.COLOR_RGB2BGR)
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.set_initial_points(starting_points)

    def set_initial_points(self, starting_points: list = None):
        width, height = self.image.size
        if starting_points == None:
            self.points = [
                (width * 0.25, height * 0.25),
                (width * 0.75, height * 0.25),
                (width * 0.75, height * 0.75),
                (width * 0.25, height * 0.75),
            ]
        else:
            self.points = starting_points
        self.draw_points_and_lines()

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

    def on_release(self, event):
        self.dragging_point = None


class CalibrationOptions:
    def __init__(self, parent, initial_calibration: dict = None):
        self.parent = parent
        self.num_rows_slider = Scale(
            parent, from_=1, to=15, orient=tk.HORIZONTAL, label="number of rows"
        )
        self.num_rows_slider.pack(fill=tk.X)
        self.num_rows_slider.set(10)

        self.black_white_thresh_slider = Scale(
            parent,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            label="black/white threshold",
        )
        self.black_white_thresh_slider.set(145)
        self.black_white_thresh_slider.pack(fill=tk.X)

        self.rotation_deg_options = ["90", "180", "270"]
        self.rotation_deg_label = ttk.Label(parent, text="rotation")
        self.rotation_deg_label.pack(fill=tk.X)
        self.rotation_deg_combobox = ttk.Combobox(
            parent, values=self.rotation_deg_options
        )
        self.rotation_deg_combobox.set("270")
        self.rotation_deg_combobox.pack(fill=tk.X)

        self.trim_left_slider = Scale(
            parent,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            label="trim pixels left",
        )
        self.trim_left_slider.set(5)
        self.trim_left_slider.pack(fill=tk.X)
        self.trim_right_slider = Scale(
            parent,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            label="trim pixels right",
        )
        self.trim_right_slider.set(5)
        self.trim_right_slider.pack(fill=tk.X)
        self.trim_top_slider = Scale(
            parent, from_=0, to=255, orient=tk.HORIZONTAL, label="trim pixels top"
        )
        self.trim_top_slider.set(5)
        self.trim_top_slider.pack(fill=tk.X)
        self.trim_bottom_slider = Scale(
            parent,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            label="trim pixels bottom",
        )
        self.trim_bottom_slider.set(5)
        self.trim_bottom_slider.pack(fill=tk.X)
        if initial_calibration is not None:
            self.num_rows_slider.set(initial_calibration["num_rows"])
            self.black_white_thresh_slider.set(
                initial_calibration["black_white_thresh"]
            )
            self.rotation_deg_combobox.set(initial_calibration["rotation_deg"])
            self.trim_left_slider.set(initial_calibration["trim_sizes_px"]["left"])
            self.trim_right_slider.set(initial_calibration["trim_sizes_px"]["right"])
            self.trim_top_slider.set(initial_calibration["trim_sizes_px"]["top"])
            self.trim_bottom_slider.set(initial_calibration["trim_sizes_px"]["bottom"])
        else:
            self.num_rows_slider.set(10)
            self.black_white_thresh_slider.set(145)
            self.rotation_deg_combobox.set("270")
            self.trim_left_slider.set(5)
            self.trim_right_slider.set(5)
            self.trim_top_slider.set(5)
            self.trim_bottom_slider.set(5)


class ScrollableImageFrame:
    def __init__(self, root):
        self.root = root
        self.canvas = Canvas(root)
        self.scrollbar = Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def add_image(self, image):
        photo_img = ImageTk.PhotoImage(image)
        label = tk.Label(self.scrollable_frame, image=photo_img)
        label.image = photo_img  # Keep a reference!
        label.pack()

    def clear(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    image = Image.open(sys.argv[1])
    if len(sys.argv) > 2:
        initial_calibration = json.loads(sys.argv[2])
        if initial_calibration == dict():
            initial_calibration = None
    else:
        initial_calibration = None

    print(f"given initial calibration: {initial_calibration}")

    root = tk.Tk()
    root.withdraw()  # This hides the root window

    def close_all_windows():
        print("Closing all windows...")
        root.destroy()

    buttons_window = tk.Toplevel(root)
    buttons_window.title("Calibration")
    buttons_window.geometry("200x55")
    buttons_window.attributes("-topmost", True)
    buttons_window.protocol("WM_DELETE_WINDOW", close_all_windows)

    select_coords_window = tk.Toplevel(root)
    select_coords_window.title("Select Points")
    select_coords_window.geometry(f"{image.size[0]}x{image.size[1]}")
    select_coords_window.protocol("WM_DELETE_WINDOW", close_all_windows)

    options_window = tk.Toplevel(root)
    options_window.title("Options")
    options_window.geometry("300x450")
    options_window.protocol("WM_DELETE_WINDOW", close_all_windows)
    options_window.attributes("-topmost", True)

    images_window = tk.Toplevel(root)
    images_window.title("Preprocessing Output")
    images_window.geometry("640x360")
    images_window.protocol("WM_DELETE_WINDOW", close_all_windows)

    coordinate_selection = SelectCoordinates(
        select_coords_window, image, initial_calibration
    )

    options = CalibrationOptions(options_window, initial_calibration)

    output_image_frame = ScrollableImageFrame(images_window)

    def run_preprocessing():
        output_image_frame.clear()
        preprocessing_output = preprocess(
            image,
            options.num_rows_slider.get(),
            options.black_white_thresh_slider.get(),
            int(options.rotation_deg_combobox.get()),
            coordinate_selection.points,
            {
                "left": int(options.trim_left_slider.get()),
                "right": int(options.trim_right_slider.get()),
                "top": int(options.trim_top_slider.get()),
                "bottom": int(options.trim_bottom_slider.get()),
            },
        )
        for output_image in preprocessing_output:
            output_image_frame.add_image(output_image)

    test_button = ttk.Button(buttons_window, text="Test", command=run_preprocessing)
    test_button.pack(fill=tk.X)

    def export_exit():
        print(
            json.dumps(
                {
                    "calibration": {
                        "num_rows": int(options.num_rows_slider.get()),
                        "black_white_thresh": int(
                            options.black_white_thresh_slider.get()
                        ),
                        "rotation_deg": int(options.rotation_deg_combobox.get()),
                        "crop_coords": coordinate_selection.points,
                        "trim_sizes_px": {
                            "left": int(options.trim_left_slider.get()),
                            "right": int(options.trim_right_slider.get()),
                            "top": int(options.trim_top_slider.get()),
                            "bottom": int(options.trim_bottom_slider.get()),
                        },
                    }
                }
            )
        )
        root.destroy()
        quit()

    export_exit_button = ttk.Button(
        buttons_window, text="Save & Exit", command=export_exit
    )
    export_exit_button.pack(fill=tk.X)

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
