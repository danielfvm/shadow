#!/bin/bash

import tkinter
from tkinter import ttk as tk
from tkinter import filedialog

class PictureElement:
    def __init__(self, image_path):
        self.image_path = image_path

class PictureListApp:
    def __init__(self):
        self.picture_list = []
        self.selected_index = -1

        # Create the UI
        self.root = tkinter.tk.Tk()
        self.root.title("Picture List App")

        self.picture_list_frame = tk.Frame(self.root)
        self.picture_list_frame.pack(side="left", fill="both", expand=True)

        self.picture_list_box = tk.Listbox(self.picture_list_frame, selectmode="single")
        self.picture_list_box.pack(side="left", fill="both", expand=True)

        self.picture_detail_frame = tk.Frame(self.root)
        self.picture_detail_frame.pack(side="left", fill="both", expand=True)

        self.picture_detail_label = tk.Label(self.picture_detail_frame, text="No picture selected")
        self.picture_detail_label.pack(pady=10)

        self.apply_button = tk.Button(self.picture_detail_frame, text="Apply", command=self.apply_action)
        self.apply_button.pack(pady=10)

        self.remove_button = tk.Button(self.picture_detail_frame, text="Remove", command=self.remove_picture)
        self.remove_button.pack(pady=10)

        self.add_button = tk.Button(self.root, text="Add", command=self.add_picture)
        self.add_button.pack(side="bottom", pady=10)

    def add_picture(self):
        # Open a file dialog to select a picture file
        #file_path = filedialog.askopenfilename(title="Select a picture", filetypes=(("Image files", "*.jpg;*.jpeg;*.png")))
        file_path = filedialog.askopenfilename(initialdir="/", title="Select An Image", filetypes=(("jpeg files", "*.jpg"), ("gif files", "*.gif*"), ("png files", "*.png")))
        if file_path:
            # Create a PictureElement instance with the selected picture file
            picture_element = PictureElement(file_path)
            self.picture_list.append(picture_element)

            # Add the picture element to the list box
            self.picture_list_box.insert("end", file_path)

    def remove_picture(self):
        if self.selected_index >= 0:
            # Remove the selected picture element from the list and list box
            del self.picture_list[self.selected_index]
            self.picture_list_box.delete(self.selected_index)

            # Clear the picture detail label
            self.picture_detail_label.config(text="No picture selected")
            self.selected_index = -1

    def apply_action(self):
        if self.selected_index >= 0:
            # Do some action with the selected picture element
            picture_element = self.picture_list[self.selected_index]
            # ...
            pass

    def run(self):
        self.root.mainloop()

def main():
    print("test")
    app = PictureListApp()
    app.run()

if __name__ == "__main__":
    main()
