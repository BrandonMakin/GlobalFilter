import tkinter as tk
from tkinter import messagebox, ttk
import platform
import cv2

import controller
import model
from gui import SingleImagePreviewer, TabbedImagePreviewer, ImageSource, HeatmapAdjustments

blank_image_path = 'C:/Users/bmicm/OneDrive/Documents/GitHub/EyeTrackingBlurring/gui/blank.bmp'
observers_to_refresh = [] # (observer design pattern) a list of the functions to call whenever refresh_settings() is called

def change_state_of_all_widgets(root, state): # states: tk.ENABLED, tk.DISABLED, tk.NORMAL
    if "state" in root.config():
        root["state"] = state
    for child in root.winfo_children():
        change_state_of_all_widgets(child, state)


def main():
    # hidpi support on windows
    if (platform.system() == "Windows"):
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)

    # initialize gui
    root = tk.Tk()
    root.winfo_toplevel().title("Global Filter")
    controller.view = View(root)
    controller.view.pack()
    root.mainloop()

#############################
# View
# The whole gui of the program
#
class View(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.previews = SaveLoadAndPreviews(self)
        self.previews.pack()

        self.settings = FiltersAndSettings(self)
        self.settings.pack()

        # allow direct access to the tk.messagebox
        self.messagebox = tk.messagebox

        # reload preview images whenever view.refresh is called
        observers_to_refresh.append(lambda: self.preview_image(0))

    def get_selected_filter_index_from_available(self):
        return self.settings.available.selected_filter_from_available.get()

    def get_selected_filter_index_from_active(self):
        return self.settings.active.selected_filter_from_active.get()

    def preview_image(self, index):
        if index < len(controller.image_filenames):
            self.__set_preview_input(controller.image_filenames[index])
        if index < len(controller.heatmap_filenames):
            self.__set_preview_heatmap(controller.heatmap_filenames[index])
            self.__update_preview_modified_heatmap(controller.heatmap_filenames[index])
        if index < len(controller.image_filenames) and index < len(controller.heatmap_filenames):
            self.__set_preview_result(controller.image_filenames[index], controller.heatmap_filenames[index])

    def __set_preview_input(self, filename):
        self.previews.image_input.set(filename, ImageSource.FILEPATH)

    def __set_preview_heatmap(self, filename):
        self.previews.image_heatmap.set(filename, ImageSource.FILEPATH)

    def __update_preview_modified_heatmap(self, filename):
        heatmap = cv2.imread(filename, cv2.IMREAD_GRAYSCALE).astype("float32") * model.NORMALIZED
        model.set_input_heatmap(heatmap)
        heatmap = (model.get_remapped_heatmap() / model.NORMALIZED).astype("uint8")
        self.previews.image_heatmap_adjusted.set(heatmap, ImageSource.ARRAY)

    def __set_preview_result(self, image, heatmap):
        model.run(image, heatmap, controller.active_filters)
        self.previews.image_result.set(model.get_output_image(), ImageSource.ARRAY)

    def refresh(self):
        for func in observers_to_refresh:
            func()

    def change_state(self, state):
        change_state_of_all_widgets(self, state)


class SaveLoadAndPreviews(ttk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, highlightbackground="black", highlightthickness="1p")
        ttk.Label(self, text="Preview").grid(row=0, column=0, sticky=tk.W)

        ttk.Label(self, text="Images   ").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(self, text="Heatmaps (original)   ").grid(row=1, column=1, sticky=tk.W)
        ttk.Label(self, text="(adjusted)   ").grid(row=1, column=2, sticky=tk.W)
        ttk.Label(self, text="Result").grid(row=1, column=3, sticky=tk.W)

        max_size = "2i" # 2 inches

        self.image_input = SingleImagePreviewer(self, image_source=blank_image_path, source=ImageSource.FILEPATH, max_width=max_size, max_height=max_size)
        self.image_input.grid(row=2, column=0, sticky=tk.W)

        # image_heatmap = TabbedImagePreviewer(self)
        self.image_heatmap = SingleImagePreviewer(self, image_source=blank_image_path, source=ImageSource.FILEPATH, max_width=max_size, max_height=max_size)
        self.image_heatmap.grid(row=2, column=1, sticky=tk.W)

        self.image_heatmap_adjusted = SingleImagePreviewer(self, image_source=blank_image_path, source=ImageSource.FILEPATH, max_width=max_size, max_height=max_size)
        self.image_heatmap_adjusted.grid(row=2, column=2, sticky=tk.W)

        self.image_result = SingleImagePreviewer(self, image_source=blank_image_path, source=ImageSource.FILEPATH, max_width=max_size, max_height=max_size)
        self.image_result.grid(row=2, column=3, sticky=tk.W)


        button_load_image = ttk.Button(self, text="Load Images", command=controller.on_button_pressed_load_image)
        button_load_image.grid(row=3, column=0, sticky=tk.W)

        button_load_heatmap = ttk.Button(self, text="Load Heatmaps", command=controller.on_button_pressed_load_heatmap)
        button_load_heatmap.grid(row=3, column=1, sticky=tk.W)

        button_choose_save_location = ttk.Button(self, text="Choose Save Location", command=controller.on_button_pressed_choose_save_location)
        button_choose_save_location.grid(row=3, column=3, sticky=tk.W)

class Previews(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        tabs = ttk.Notebook(self)
        tabs.pack(expand=1, fill='both')
        tabs.add(ttk.Frame(tabs), text="Your Images")
        tabs.add(ttk.Frame(tabs), text="Example Image")

class FiltersAndSettings(ttk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, highlightbackground="black", highlightthickness="1p")
        # ttk.Label(self, text="Filters").grid(row=0, column=0)
        ttk.Label(self, text="Available Filters   ").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(self, text="Active Filters   ").grid(row=1, column=2, sticky=tk.W)
        ttk.Label(self, text="Filter Settings   ").grid(row=1, column=3, sticky=tk.W)
        ttk.Label(self, text="Heatmap Adjustments").grid(row=1, column=4, sticky=tk.W)

        self.available = AvailableFilters(self)
        self.available.grid(row=2, column=0)
        SwapFilters(self).grid(row=2, column=1)
        self.active = ActiveFilters(self)
        self.active.grid(row=2, column=2)
        FilterSettings(self).grid(row=2, column=3)
        HeatmapAdjustments(self, controller.on_heatmap_adjustments_updated).grid(row=2, column=4)
        RunButton(self).grid(row=3, column=5, sticky=tk.W)

class AvailableFilters(ttk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, highlightbackground="black", highlightthickness="1p")
        self.selected_filter_from_available = tk.IntVar()
        for i, filter in enumerate(controller.available_filters):
            tk.Radiobutton(self, text=filter.name, value=i, variable=self.selected_filter_from_available, indicator = 0, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

class SwapFilters(ttk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, highlightbackground="black", highlightthickness="1p")
        ttk.Button(self, text="Add", command = controller.on_button_pressed_filter_add).pack(fill=tk.X)
        ttk.Button(self, text="Remove", command = controller.on_button_pressed_filter_remove).pack(fill=tk.X)
        ttk.Button(self, text="Remove  All", command = controller.on_button_pressed_filter_remove_all).pack(fill=tk.X)
        ttk.Button(self, text="▲", command = controller.on_button_pressed_filter_move_up).pack(fill=tk.X)
        ttk.Button(self, text="▼", command = controller.on_button_pressed_filter_move_down).pack(fill=tk.X)

class ActiveFilters(ttk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, highlightbackground="black", highlightthickness="1p")
        self.selected_filter_from_active = tk.IntVar()
        observers_to_refresh.append(self.refresh)

    def refresh(self): # make sure that the visible list of active filters is up to date
        for child in self.winfo_children():
            child.destroy()
        for i, filter in enumerate(controller.active_filters):
            tk.Radiobutton(self, text=filter.name, value=i, variable=self.selected_filter_from_active, indicator = 0, anchor=tk.W).pack(side=tk.TOP, fill=tk.X)

class FilterSettings(ttk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, highlightbackground="black", highlightthickness="1p")

class RunButton(ttk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        tk.Button(self, text="▶ Run", bg="green", command=controller.on_button_pressed_run).pack()

if __name__ == "__main__":
    main()
