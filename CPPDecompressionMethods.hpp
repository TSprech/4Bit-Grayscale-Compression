/**
 * @brief Draws a 128 x 128 compressed bitmap to the @ref pixel_buffer "pixel buffer". This is only used for full screen bitmaps as it 
 * does not have bound checking and takes in no start coordinates. It is ~3 times faster than the other decompression for full screen bitmaps.
 * @tparam bitmap_instance The @ref Bitmap "Bitmap" struct instance which holds all bitmap data
 * @param bitmap The bitmap struct instance which contains all the data for an image
 */
template <typename bitmap_instance>
void Decompress(bitmap_instance bitmap) {
    uint_fast16_t output_array_index = 0;
    uint_fast8_t odd = 0;
    uint_fast16_t input_array_index = 0;
    uint_fast8_t current_compressed_byte = 0;
    uint_fast16_t top_limit = 0;

    while (output_array_index ^ pixel_buffer.size()) {
        current_compressed_byte = bitmap.pixel_data.at(input_array_index);
        top_limit = output_array_index + (current_compressed_byte & 0b1111);
        while (output_array_index < top_limit) {
        if (odd & 0b1) {
            pixel_buffer.at(output_array_index) = (current_compressed_byte >> 4) | (pixel_buffer.at(output_array_index) & 0b11110000);
            ++output_array_index;
        } else {
            pixel_buffer.at(output_array_index) = (current_compressed_byte & 0b11110000) | (pixel_buffer.at(output_array_index) & 0b1111);
            --top_limit;
        }
        odd = ~odd;
        }
        ++input_array_index;
    }
}

/**
 * @brief Draws any size compressed bitmap to the @ref pixel_buffer "pixel buffer"
 * @tparam bitmap_instance The @ref Bitmap "Bitmap" struct instance which holds all bitmap data
 * @param x The x coordinate which the top left of the bitmap will start to be drawn from
 * @param y The y coordinate which the top left of the bitmap will start to be drawn from
 * @param bitmap The bitmap struct instance which contains all the data for an image
 */
template <typename bitmap_instance>
void Decompress(uint8_t x, uint8_t y, bitmap_instance bitmap) {
    if (bitmap.transparency) {
        uint16_t input_array_index = 0;  // Holds the index of the array that contains all compressed pixel data for the bitmap
        uint8_t transparent_pixel_designator = bitmap.transparent_pixel_designator;

        for (uint8_t row = y; row < (y + bitmap.height); ++row) {   // For each row of pixels from the y offset to the bottom row of the bitmap
        for (uint8_t column = x; column < (x + bitmap.width);) {  // For each column from the x offset to the end of the bitmap | Note: column refers to individual pixels, not a pair
            uint8_t grayscale = bitmap.pixel_data.at(input_array_index) >> 4;
            for (uint8_t sequential_pixels = 0; sequential_pixels < (bitmap.pixel_data.at(input_array_index) & 0b1111);) {  // Extracts and runs for the number of pixels in a compressed byte
            uint8_t grayscale = bitmap.pixel_data.at(input_array_index) >> 4;
            if ((column - x) == bitmap.width) {  // If we have reached the last column of a bitmap
                column = x;                        // Reset the column back to the start x offset
                ++row;                             // Go to the next row to begin drawing
            }
            if (grayscale != transparent_pixel_designator) Pixel(column, row, grayscale);  // Shift the compressed byte over 4 to leave the color in bits 3-0 then write that grayscale at the current coordinates
            ++column;                                                                     // Move to the next pixel
            ++sequential_pixels;                                                          // Indicate that one of sequential pixel instances has been drawn
            }
            ++input_array_index;  // If a compressed byte has been fully decompressed and drawn, move to the next compressed byte
        }
        }
    } else {
        uint16_t input_array_index = 0;  // Holds the index of the array that contains all compressed pixel data for the bitmap

        for (uint8_t row = y; row < (y + bitmap.height); ++row) {                                                           // For each row of pixels from the y offset to the bottom row of the bitmap
        for (uint8_t column = x; column < (x + bitmap.width);) {                                                          // For each column from the x offset to the end of the bitmap | Note: column refers to individual pixels, not a pair
            for (uint8_t sequential_pixels = 0; sequential_pixels < (bitmap.pixel_data.at(input_array_index) & 0b1111);) {  // Extracts and runs for the number of pixels in a compressed byte
            if ((column - x) == bitmap.width) {                                                                           // If we have reached the last column of a bitmap
                column = x;                                                                                                 // Reset the column back to the start x offset
                ++row;                                                                                                      // Go to the next row to begin drawing
            }
            Pixel(column, row, (bitmap.pixel_data.at(input_array_index) >> 4));  // Shift the compressed byte over 4 to leave the color in bits 3-0 then write that grayscale at the current coordinates
            ++column;                                                            // Move to the next pixel
            ++sequential_pixels;                                                 // Indicate that one of sequential pixel instances has been drawn
            }
            ++input_array_index;  // If a compressed byte has been fully decompressed and drawn, move to the next compressed byte
        }
        }
    }
}

/**
 * @brief Draws a pixel into the pixel buffer THIS SHOULD BE CHANGED TO MATCH YOUR SETUP
 * @param x The x coordinate of the pixel
 * @param y The y coordinate of the pixel
 * @param grayscale_value The 4 bit grayscale value that the pixel will be drawn in
 */
void Pixel(uint8_t x, uint8_t y, uint8_t grayscale_value) {
    if ((x >= width_) || (y >= height_)) {
        return;
    }
    uint16_t index = (x / 2) + (y * 64);
    if (x & 0b1) {  // If this is an odd pixel, place it into the right side of the pixel pair
        pixel_buffer.at(index) = (pixel_buffer.at(index) & 0xF0) | (grayscale_value);
    } else {  // Put it in the left side
        pixel_buffer.at(index) = (pixel_buffer.at(index) & 0x0F) | (grayscale_value << 4);
    }
}