import tkinter as tk
import queue
from tkinter import ttk, Canvas, Scrollbar, Scale
from PIL import Image, ImageTk
import numpy as np
import cv2
import sys
import json
import threading
import math
from preprocess import preprocess

# required for nodejs to parse in real time
sys.stdout.reconfigure(line_buffering=True, write_through=True)


class PageCornerLocationError(Exception):
    pass


class SelectCoordinates:
    def __init__(
        self,
        master,
        image: Image,
        initial_calibration: dict = None,
        call_func_on_update=None,
    ):
        self.master = master

        self.call_func_on_update = call_func_on_update

        # TODO screen dimensions global
        # screen_width = master.winfo_screenwidth()
        # screen_height = master.winfo_screenheight()
        # master.geometry(f"{screen_width}x{screen_height}")
        self.image = image
        self.cv_image = cv2.cvtColor(np.array(self.image), cv2.COLOR_RGB2BGR)
        self.tk_image = ImageTk.PhotoImage(self.image)

        self.canvas = tk.Canvas(master, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        self.points = [None, None, None, None]
        if initial_calibration is not None:
            self.set_initial_points(initial_calibration["crop_coords"])
        else:
            self.set_initial_points()

        self.dragging_point = None

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    # TODO replace reference to this function
    # def reset_image(self):
    #     self.set_initial_points()

    def set_initial_points(self, starting_points: list = None):
        width, height = self.image.size
        if starting_points is not None:
            self.points = starting_points
        else:
            try:
                self.points = self.locate_page_corners()
                print("successfully located page corners", file=sys.stderr)
            except PageCornerLocationError as e:
                print("failed to locate page corners!", file=sys.stderr)
                print(e, file=sys.stderr)
                self.points = [
                    (width * 0.25, height * 0.25),
                    (width * 0.75, height * 0.25),
                    (width * 0.75, height * 0.75),
                    (width * 0.25, height * 0.75),
                ]
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
        if self.call_func_on_update is not None:
            self.call_func_on_update()

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

    def locate_page_corners(self):
        grayscale_img = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2GRAY)
        length, width = grayscale_img.shape
        image_area = length * width
        # I am blindly copying these magic numbers from opencv documentation
        binary_img = cv2.adaptiveThreshold(
            grayscale_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        contours, _ = cv2.findContours(
            binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        # assume that page contour must be > 60% of the total area and less thn the entire area
        contours = [
            x
            for x in contours
            if cv2.contourArea(x) > 0.6 * image_area
            and cv2.contourArea(x) < 0.95 * image_area
        ]
        # Sort contours based on area in descending order
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        # in my testing this was not the case, the first contour was the one I wanted
        page_corners = None
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approximated_polygon = cv2.approxPolyDP(contour, 0.02 * peri, True)
            # If our approximated contour has four points, we can assume we have found the paper
            if len(approximated_polygon) == 4:
                page_corners = approximated_polygon
                break
        if page_corners is not None:
            page_corner_coordinates = [
                (int(x[0][0]), int(x[0][1])) for x in page_corners
            ]

            # sort the coordinates based on their distance from the top left corner
            def hypotnuse(lengths):
                return math.sqrt(lengths[0] ** 2 + lengths[1] ** 2)

            sorted_coords = sorted(page_corner_coordinates, key=hypotnuse)
            # the page is turned on its side
            top_left, bottom_left, top_right, bottom_right = sorted_coords

            # print(
            #     json.dumps(
            #         {
            #             "sorted_coords": sorted_coords,
            #             "top left": top_left,
            #             "bottom left": bottom_left,
            #             "top right": top_right,
            #             "bottom right": bottom_right,
            #         }
            #     )
            # )
            if not (
                top_left[0] < top_right[0]
                and bottom_left[0] < bottom_right[0]
                and top_left[1] < bottom_left[1]
                and top_right[1] < bottom_right[1]
            ):
                raise PageCornerLocationError("page corners are out of order!")
            return [top_left, top_right, bottom_right, bottom_left]
        else:
            raise PageCornerLocationError("No quadrilateral contour detected.")


class CalibrationOptions:
    def __init__(
        self, parent, initial_calibration: dict = None, call_func_on_update=None
    ):
        self.parent = parent
        self.call_func_on_update = call_func_on_update
        self.black_white_thresh_slider = Scale(
            parent,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            label="black/white threshold",
            command=self.call_func_on_update,
        )
        self.black_white_thresh_slider.set(145)
        self.black_white_thresh_slider.pack(fill=tk.X)
        if initial_calibration is not None:
            self.black_white_thresh_slider.set(
                initial_calibration["black_white_thresh"]
            )
        else:
            self.black_white_thresh_slider.set(145)
        # the save/exit button is added to here from outside
        # it's quick and dirty


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
        sys.exit(1)

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

    output_image_frame = ScrollableImageFrame(images_window)

    def run_preprocessing():
        output_image_frame.clear()
        preprocessing_output = preprocess(
            image,
            options.black_white_thresh_slider.get(),
            coordinate_selection.points,
        )
        for output_image in preprocessing_output:
            output_image_frame.add_image(output_image)

    preprocessing_task_queue = queue.Queue(maxsize=2)

    def add_job_to_preprocess_queue(x=None):
        try:
            preprocessing_task_queue.put_nowait(x)
        except queue.Full:
            pass

    def service_preprocess_queue():
        while True:
            preprocessing_task_queue.get()  # wait for item in queue
            run_preprocessing()
            preprocessing_task_queue.task_done()

    preprocess_queue_servicer_thread = threading.Thread(target=service_preprocess_queue)
    preprocess_queue_servicer_thread.daemon = True
    preprocess_queue_servicer_thread.start()

    coordinate_selection = SelectCoordinates(
        select_coords_window,
        image,
        initial_calibration,
        call_func_on_update=add_job_to_preprocess_queue,
    )

    options = CalibrationOptions(
        options_window,
        initial_calibration,
        call_func_on_update=add_job_to_preprocess_queue,
    )

    # TODO do we really need this?
    # reset_image_button = ttk.Button(
    #     buttons_window, text="Reset Image", command=coordinate_selection.reset_image
    # )
    # reset_image_button.pack(fill=tk.X, pady=5)

    def export_exit():
        print(
            json.dumps(
                {
                    "calibration": {
                        "black_white_thresh": int(
                            options.black_white_thresh_slider.get()
                        ),
                        "crop_coords": coordinate_selection.points,
                    }
                }
            )
        )
        root.destroy()
        quit()

    export_exit_button = ttk.Button(
        options_window, text="Save & Exit", command=export_exit
    )
    # TODO what does pady accomplish?
    # export_exit_button.pack(fill=tk.X, pady=5)
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
