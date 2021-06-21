import os

import numpy as np
from PIL import Image, ImageDraw
import numpy


class RLE4Bit:
    # def __init__(self):

    _TRANSPARENT_PIXEL_DESIGNATOR = 0x1  # This should be treated more as a constant than a variable, determines what pixels should not be drawn
    _image_width = 0  # The number of pixels wide the image is
    _image_height = 0  # The number of pixels tall the image is
    _pixel_data = numpy.empty(1, dtype = numpy.uint8)  # The array to hold the pixel values that is read in from a bitmap

    def change_transparent_pixel_designator(self, new_designator):
        self._TRANSPARENT_PIXEL_DESIGNATOR = new_designator

    def _uncompressed_convert(self, pixel_data):
        uncompressed_pixel_data = numpy.empty(1, dtype = numpy.uint8)  # Create the array that will hold the uncompressed data

        odd_pixel_data = self._pixel_data_2d # Create a copy of the data
        if self._image_width % 2 == 1: # If the bitmap is an odd size
            # Add a column full of transparent pixels to make it an even width
            padding = np.ones((self._image_height, self._image_width + 1))
            padding = padding * self._TRANSPARENT_PIXEL_DESIGNATOR
            padding[:, :-1] = odd_pixel_data # Thanks: https://stackoverflow.com/questions/8486294/how-to-add-an-extra-column-to-a-numpy-array
            odd_pixel_data = padding

        # Next because the data is still in a 2D array, flatten it to the 1D array that is used when storing the data
        odd_pixel_data = odd_pixel_data.flatten()
        odd_pixel_data = odd_pixel_data.astype(numpy.uint8) # Make sure it is in the right datatype for doing the bitwise operations

        uncompressed_index = 0  # This keeps track of the last checked index in the raw (input) array
        for index in range(0, odd_pixel_data.size, 2):  # As each pixel must be translated from 0000gggg 0000GGGG to ggggGGGG format, go in increments of 2 to capture both at the same time
            uncompressed_pixel_data.resize(uncompressed_index + 1, refcheck = False)  # Increase the output array size by 1 byte to accommodate the new pixels
            # Set the newly allocated byte equal to the combined ggggGGGG format, but if there are bytes that have only a single pixel (eg for the byte at the end of a bitmap that has an
            # odd number of pixels as a width), use the transparent pixel value
            # uncompressed_pixel_data[uncompressed_index] = (odd_pixel_data[index] << 4) | (odd_pixel_data[index + 1] if index != odd_pixel_data.size - 1 else self._TRANSPARENT_PIXEL_DESIGNATOR)
            uncompressed_pixel_data[uncompressed_index] = (odd_pixel_data[index] << 4) | (odd_pixel_data[index + 1])
            # uncompressed_pixel_data[uncompressed_index] = (pixel_data[index] << 4) | (pixel_data[index + 1] if index != pixel_data.size - 1 else 0xF)
            uncompressed_index += 1  # Increment the uncompressed output array index as the array is now one byte large due to the new addition

        return uncompressed_pixel_data

    # Does the same thing as the _uncompressed_convert but increments a counter instead
    def uncompressed_size(self):
        size = 0
        for index in range(0, self._pixel_data.size, 2):
            size += 1
        return size

    def _compressed_convert(self, pixel_data):
        compressed_array_index = 0  # This keeps track of where in the last index in the compressed (output) index
        uncompressed_array_index = 0  # This keeps track of the last checked index in the raw (input) array
        compressed_pixel_data = numpy.empty(1, dtype = numpy.uint8)  # Create the array that will hold the compressed data
        while uncompressed_array_index < pixel_data.size:  # Keep compressing until the whole array has been read
            sequential_pixels = 1  # This keeps track of how many pixels in a row are the same, it starts at 1 as there must be a minimum of 1 pixel to generate a compressed byte
            # As the input data is stored like this: 0000gggg with the grayscale 'color' being the gggg, it must be shifted to the front of the byte as the compressed bytes have the
            # structure: ggggnnnn where gggg is the grayscale 'color' and nnnn is the number of sequential pixels that are that value
            grayscale_value = (pixel_data[uncompressed_array_index] << 4)
            # While we haven't reached the end of the uncompressed array and while the next pixel is the same 'color' as the one currently being compressed
            while (uncompressed_array_index < (pixel_data.size - 1)) and (pixel_data[uncompressed_array_index] == pixel_data[uncompressed_array_index + 1]):
                if sequential_pixels < 15:  # As there are only 4 bits for storing the number of sequential pixels, make sure it doesn't keep going if it reaches that limit
                    sequential_pixels += 1  # Since there are less than 15 current consecutive bytes, increment the sequential pixel variables to indicate another pixel of the same 'color'
                    uncompressed_array_index += 1  # Move onto the next pixel so that it can be checked if it is the same as the last
                else:  # There are more than 15 consecutive bytes, so start a new byte as the number portion of a byte is only 4 bits
                    break
            # Once the inner while loop breaks, we have either have a situation where more than 15 pixels are the same 'color', we have pixels that are different 'colors', or run out of pixels
            uncompressed_array_index += 1  # First increment this to move onto the next pixel in the raw input buffer
            compressed_pixel_data.resize(compressed_array_index + 1, refcheck = False)  # Increase the output array size by 1 byte to accommodate the new byte
            compressed_pixel_data[compressed_array_index] = (grayscale_value | sequential_pixels)  # Store the new byte in the same ggggnnnn pattern as mentioned above
            compressed_array_index += 1  # Increment the compressed array index as the array is now one byte large due to the new addition
        # Once the outer while loop breaks, we know we have run out of pixels to compress so the entire array is returned
        return compressed_pixel_data

    # This method does exactly what the _compressed_convert method does, but just keeps track of the number of pixels, so refer to that function for details
    def compressed_size(self):
        size = 0
        uncompressed_array_index = 0
        while uncompressed_array_index < self._pixel_data.size:
            sequential_pixels = 1
            while (uncompressed_array_index < (self._pixel_data.size - 1)) and (self._pixel_data[uncompressed_array_index] == self._pixel_data[uncompressed_array_index + 1]):
                if sequential_pixels < 15:
                    sequential_pixels += 1
                    uncompressed_array_index += 1
                else:  # There are more than 15 consecutive bytes, so start a new byte as the number portion of a byte is only 4 bits
                    break
            uncompressed_array_index += 1
            size += 1  # Instead of adding pixels to a buffer, the size variable is just incremented
        return size

    def open_image(self, input_image_name):
        self._image_width, self._image_height, self._pixel_data = self._open_image(input_image_name)  # Read all the data required from the file when opening it

    def uncompressed_pixel_data(self):
        return self._uncompressed_convert(self._pixel_data)

    def compressed_pixel_data(self):
        return self._compressed_convert(self._pixel_data)

    def convert_image(self, filepath, has_transparency, transparent_pixel_designator = 0x0, compress = True, save = True):
        if not save:
            if compress:
                print("Compressed size: " + str(self.compressed_size()))
                compressed_pixel_data = self._compressed_convert(self._pixel_data)
                return self._generate_output_string(image_width = self._image_width, image_height = self._image_height, pixel_data = compressed_pixel_data, file_path = filepath, transparency = has_transparency,
                                                    transparent_pixel_designator = transparent_pixel_designator, compress = True)
                # return compressed_pixel_data  # Return the compressed array in case it needs to be used elsewhere
            else:
                print("Uncompressed size: " + str(self.uncompressed_size()))
                uncompressed_pixel_data = self._uncompressed_convert(self._pixel_data)
                return self._generate_output_string(image_width = self._image_width, image_height = self._image_height, pixel_data = uncompressed_pixel_data, file_path = filepath, transparency = has_transparency,
                                                    transparent_pixel_designator = transparent_pixel_designator, compress = False)
                # return uncompressed_pixel_data  # Return the uncompressed array of pixels
        else:
            if compress:
                print("Compressed size: " + str(self.compressed_size()))
                compressed_pixel_data = self._compressed_convert(self._pixel_data)
                return self._write_to_hpp(image_width = self._image_width, image_height = self._image_height, pixel_data = compressed_pixel_data, file_path = filepath, transparency = has_transparency,
                                          transparent_pixel_designator = transparent_pixel_designator, compress = True)
                # return compressed_pixel_data  # Return the compressed array in case it needs to be used elsewhere
            else:
                print("Uncompressed size: " + str(self.uncompressed_size()))
                uncompressed_pixel_data = self._uncompressed_convert(self._pixel_data)
                return self._write_to_hpp(image_width = self._image_width, image_height = self._image_height, pixel_data = uncompressed_pixel_data, file_path = filepath, transparency = has_transparency,
                                          transparent_pixel_designator = transparent_pixel_designator, compress = False)
                # return uncompressed_pixel_data  # Return the uncompressed array of pixels

    def _generate_image_from_array(self, image_width, image_height, pixel_data):
        rendered_image = Image.new("L", (image_width, image_height))  # This is a temporary image which is used to render a preview of the bitmap once it has been processed and reconstructed

        draw = ImageDraw.Draw(rendered_image)  # Create the object to draw the pixels

        # Draws a single pixel in 8 bit grayscale from a 4 bit grayscale input
        def DrawPixel(x, y, grayscale):
            shape = [(x, y), (x, y)]
            draw.rectangle(shape, fill = int(numpy.interp(grayscale, [0, 15], [0, 255])))

        for row in range(image_width):
            for column in range(image_height):
                DrawPixel(row, column, pixel_data[(column * 128) + row])  # Draw each pixel in the array to the temporary image

        # rendered_image.show()  # Display the temporary image
        return rendered_image

    def _generate_output_string(self, image_width, image_height, pixel_data, file_path, transparency, transparent_pixel_designator, compress):
        # This adds the required include guards, includes, and other struct members to the header file string
        # Thanks https://stackoverflow.com/questions/8384737/extract-file-name-from-path-no-matter-what-the-os-path-format
        # and https://stackoverflow.com/questions/904746/how-to-remove-all-characters-after-a-specific-character-in-python
        file_name, dot, extension = os.path.basename(file_path).partition('.')
        compressed_string = ""
        compressed_string += "#ifndef " + file_name.upper() + "_HPP" + "\n#define " + file_name.upper() + "_HPP\n"  # Include guard
        compressed_string += "#include \"Bitmap/Bitmap.hpp\"\n\n"  # Struct base defintion file
        compressed_string += "static const Bitmap<" + str(pixel_data.size) + "> " + file_name + "{\n"  # Struct instance definition with template filled in
        compressed_string += ".width = " + str(image_width) + ",\n"  # Picture width
        compressed_string += ".height = " + str(image_height) + ",\n"  # Picture height
        compressed_string += ".size = " + str(pixel_data.size) + ",\n"  # Number of bytes in the pixel_data array
        compressed_string += ".transparency = " + str(transparency).lower() + ",\n"  # Whether or not the bitmap uses transparency
        # compressed_string += ".transparent_pixel_designator = " + f"0x{transparent_pixel_designator:X}" + ",\n"  # What pixel is reserved for transparency
        compressed_string += ".transparent_pixel_designator = " + transparent_pixel_designator + ",\n"  # What pixel is reserved for transparency
        compressed_string += ".compressed = " + str(compress).lower() + ",\n"  # If the bitmap is compressed or not
        compressed_string += ".pixel_data = {\n"

        counter = 10  # Used for determining newlines on the outputted hex array
        for index in range(0, pixel_data.size):
            if pixel_data[index] > 0xF:  # If it's hex representation has 2 characters (eg 0xAA, 0x18)
                compressed_string += f"0x{pixel_data[index]:X}"  # Print the hex value with capital letters
            else:  # Else it's hex representation has only 1 characters (eg 0xA, 0x4) so a 0 will be added in front to maintain formatting
                compressed_string += f"0x0{pixel_data[index]:X}"

            if index != pixel_data.size - 1:  # Don't add a comma at the end of the array
                compressed_string += ", "  # There is another byte following the current one so place a comma
            else:  # We have reached the end of the file, place the closing sets of brackets and close the include guard
                compressed_string += "},\n};\n#endif // " + file_name.upper() + "_HPP"
            counter += 1

            # Determines if a newline will be placed at the end, in this case it is placed every 10 bytes
            if counter > 12 and counter % 10 == 0:
                compressed_string += '\n'
        return compressed_string

    def _write_to_hpp(self, image_width, image_height, pixel_data, file_path, transparency, transparent_pixel_designator, compress):
        outfile = open(str(file_path), "w")  # Open or create a header file to place the data into
        outfile.write(
            self._generate_output_string(image_width, image_height, pixel_data, file_path, transparency, transparent_pixel_designator, compress)
        )  # Copy the data in
        outfile.close()  # Save the file

    def _open_image(self, filepath):
        input_image = Image.open(filepath, 'r')  # Open the image in read only mode
        width, height = input_image.size  # Get the width and height of the picture

        self._pixel_data_2d = numpy.array(input_image)  # Get the data in a 2D representation

        pixel_values = list(input_image.getdata())  # Convert the pixel data to a 1D list
        pixel_values = numpy.array(pixel_values).reshape((width, height, 1))  # Create a numpy array with the x, y, and grayscale value (0-255)

        return width, height, pixel_values.flatten()  # Convert the 2D array to a 1D array
