import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext, PhotoImage
from tkinter import ttk as ttk

import RLE4Bit


class UI:
    compressor = RLE4Bit.RLE4Bit()
    window = tk.Tk

    def __init__(self):
        # Create the root window
        self.window = tk.Tk()
        self.window.title('Bitmap Compressor')
        self.window.geometry("500x500")  # Set window size
        self.filename = ""

        self._generate_file_menu()
        self._generate_transparent_pixel_optionmenu()
        self._generate_transparent_pixel_checkbox()
        self._generate_data_size_labels()
        self._generate_compress_checkbox()
        self._generate_output_scolledtext()

        self.window.mainloop()

    def _import(self):
        self._browse_files()
        self._update_data_sizes()
        self._update_pixel_output_text()

    def _generate_transparent_pixel_optionmenu(self):
        # Create the transparent pixel designator selector
        transparent_pixel_designator_label = tk.Label(self.window, text = "Transparent Pixel Designator:")
        transparent_pixel_designator_label.grid(row = 2, column = 0, sticky = tk.W)

        # Thanks: https://stackoverflow.com/questions/45441885/how-can-i-create-a-dropdown-menu-from-a-list-in-tkinter
        transparent_pixel_options = ["0x0", "0x1", "0x2", "0x3", "0x4", "0x5", "0x6", "0x7", "0x8", "0x9", "0xA", "0xB", "0xC", "0xD", "0xE", "0xF"]
        self.transparent_pixel_designator_value = tk.StringVar(self.window)  # Create a new string variable for storing the choice of pixel designator
        self.transparent_pixel_designator_value.set(transparent_pixel_options[0])  # Set the string to be equal to the name that is chosen in the list TODO: Read this value from the INI file
        transparent_pixel_designator_combobox = tk.ttk.Combobox(self.window, textvariable = self.transparent_pixel_designator_value, values = transparent_pixel_options,
                                                                width = 4)  # Set up the optionmenu with the initial value and list of values
        transparent_pixel_designator_combobox.grid(row = 2, column = 1, sticky = tk.W)  # Add it to the grid next to the transparent pixel label
        transparent_pixel_designator_combobox.bind("<<ComboboxSelected>>", self._update_pixel_output_text)  # Thanks: https://stackoverflow.com/questions/35209522/how-to-make-a-ttk-combobox-callback

    def _generate_transparent_pixel_checkbox(self):
        self.transparency_checkbox_var = tk.BooleanVar()
        self.transparency_checkbox = tk.Checkbutton(self.window, text = "Transparency", variable = self.transparency_checkbox_var, onvalue = True, offvalue = False, command = self._update_pixel_output_text)
        self.transparency_checkbox.grid(row = 3, column = 0, sticky = tk.W)

    def _generate_compress_checkbox(self):
        self.compress_checkbox_var = tk.BooleanVar()
        self.compress_checkbox = tk.Checkbutton(self.window, text = "Compress", variable = self.compress_checkbox_var, onvalue = True, offvalue = False, command = self._update_pixel_output_text)
        self.compress_checkbox.grid(row = 3, column = 1, sticky = tk.W)

    def _generate_data_size_labels(self):
        self.uncompressed_size = tk.IntVar()  # Will be updated whenever an image is imported with the size of the image if compression is not chosen
        self.compressed_size = tk.IntVar()  # Will be updated whenever an image is imported with the size of the image if compression is chosen
        uncompress_size_label = tk.Label(self.window, text = "Uncompressed Size (Bytes): ")
        uncompress_size_data_label = tk.Label(self.window, textvariable = self.uncompressed_size)  # Bind the uncompressed_size variable to this label
        compress_size_label = tk.Label(self.window, text = "Compressed Size (Bytes): ")
        compress_size_data_label = tk.Label(self.window, textvariable = self.compressed_size)  # Bind the compressed_size variable to this label

        # Add each of the elements to the grid in the form Label: Size
        uncompress_size_label.grid(row = 0, column = 0, sticky = tk.W)
        uncompress_size_data_label.grid(row = 0, column = 1, sticky = tk.W)
        compress_size_label.grid(row = 1, column = 0, sticky = tk.W)
        compress_size_data_label.grid(row = 1, column = 1, sticky = tk.W)

    def _generate_output_scolledtext(self):
        self.output_scolledtext = scrolledtext.ScrolledText(self.window, wrap = tk.WORD, width = 60, height = 20)
        self.output_scolledtext.grid(row = 5, column = 0, sticky = tk.SW, columnspan = 4)

    def _browse_files(self):
        filename = filedialog.askopenfilename(initialdir = "/Quick access", title = "Select a 4 Bit BMP Image", filetypes = (("Bitmap files", "*.bmp*"), ("all files", "*.*")))
        if not filename:
            return
        self.compressor.open_image(filename)  # Load the pixel data into the RLE object
        self._display_image()
        self.filename = filename

    def _update_pixel_output_text(self, event = 0):
        if not self.filename:
            return
        self.compressor.change_transparent_pixel_designator(int(self.transparent_pixel_designator_value.get(), 16))
        self.output_scolledtext.delete('1.0', tk.END)
        self.output_scolledtext.insert('1.0', self.compressor.convert_image(filepath = self.filename,
                                                                            has_transparency = self.transparency_checkbox_var.get(),
                                                                            transparent_pixel_designator = self.transparent_pixel_designator_value.get(),
                                                                            compress = self.compress_checkbox_var.get(),
                                                                            save = False))
        self._display_image()

    def _update_data_sizes(self):
        self.uncompressed_size.set(self.compressor.uncompressed_size())
        self.compressed_size.set(self.compressor.compressed_size())

        # If the image is smaller compressed, set the compression checkbox to selected
        if self.compressed_size.get() < self.uncompressed_size.get():
            self.compress_checkbox_var.set(True)
        else:  # Otherwise since the data is smaller uncompressed, uncheck the box
            self.compress_checkbox_var.set(False)

    def _display_image(self):
        canvas = tk.Canvas(self.window, width = 128, height = 128, bg = "#000000")
        canvas.grid(row = 0, column = 2, sticky = tk.E, rowspan = 4, columnspan = 1, padx = 5)
        img = PhotoImage(width = 128, height = 128)
        self.window.img = img  # Prevent garbage collection
        canvas.create_image(128 / 2, 128 / 2, image = img, state = "normal")

        pixel_data = self.compressor.uncompressed_pixel_data()
        array_index = 0

        print(pixel_data.size)

        # Thanks: https://stackoverflow.com/questions/12284311/python-tkinter-how-to-work-with-pixels/12287117
        def _pixel(x, y, color):
            img.put(("#" + f"{color:X}" * 3), (x, y))

        for y in range(3, self.compressor._image_height + 3):
            # If the bitmap is an odd width, it must be draw like it was an even width bitmap so add 1 to the range for x to change it to an even number of columns
            for x in range(self.compressor._image_width + (self.compressor._image_width % 2)):
                if not x % 2 == 1:  # If it is an even pixel
                    grayscale = pixel_data[array_index] >> 4  # The data is stored in the upper 4 bits of the byte
                else:  # It is an odd pixel
                    grayscale = pixel_data[array_index] & 0b1111  # The data is stored in the lower 4 bits
                    array_index = array_index + 1  # Increment the index of the array being read in only when odd pixels are processed because there are 2 pixels per byte

                # If the image has transparency enabled and the current pixel being draw is the value of the transparent pixel designator
                if self.transparency_checkbox_var.get() and grayscale == int(self.transparent_pixel_designator_value.get(), 16):
                    img.put("#FF0000", (x, y))  # Draw the pixel in a different color to indicate that it will be transparent
                else:  # Otherwise if there is no transparency or the pixel is not the same value as the TPD
                    _pixel(x, y, grayscale)  # Draw it as normal

    def _generate_file_menu(self):
        menubar = tk.Menu(self.window)
        filemenu = tk.Menu(menubar, tearoff = 0)
        filemenu.add_command(label = "Import", command = self._import)
        filemenu.add_command(label = "Save As", command = self._save_file)
        filemenu.add_command(label = "Exit", command = self.window.quit)
        menubar.add_cascade(label = "File", menu = filemenu)

        viewmenu = tk.Menu(menubar, tearoff = 0)
        # viewmenu.add_checkbutton(label = "Dark Mode", command = self._dark_mode)
        menubar.add_cascade(label = "View", menu = viewmenu)

        self.window.config(menu = menubar)

    # From: https://realpython.com/python-gui-tkinter/
    def _save_file(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension = "hpp",
            filetypes = [("C++ Header", "*.hpp"), ("C Header", "*.h"), ("Text", "*.txt"), ("All Files", "*.*")],
        )

        if not filepath:
            return

        self.compressor.convert_image(filepath = filepath,
                                      has_transparency = self.transparency_checkbox_var.get(),
                                      transparent_pixel_designator = self.transparent_pixel_designator_value.get(),
                                      compress = self.compress_checkbox_var.get(),
                                      save = True)
