#ifndef BITMAP_HPP
#define BITMAP_HPP

#include <cstdint>
#include <array>

template <uint16_t pixel_data_size>
struct Bitmap {
  //* ════════════════════════════════════════════════════════════════════════════════════════════════════
  uint8_t width;
  uint8_t height;
  uint16_t size;
  bool transparency;
  uint8_t transparent_pixel_designator;
  bool compressed;
  std::array<uint8_t, pixel_data_size> pixel_data;
};

#endif  // BITMAP_HPP