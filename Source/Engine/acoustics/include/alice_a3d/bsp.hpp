/* v0.5.0 SOURCE COMMENTARY — BSP loader structures
 * Describes independent Quake-style BSP parsing APIs. Only the formats explicitly
 * implemented by the parser are supported; do not infer that all Quake/Alice levels can
 * be read.
 */
#pragma once
#include "alice_a3d/acoustics.hpp"
#include <cstddef>
#include <string>

namespace alicea3d {
struct BspReport {
    int version=0;
    std::string format;
    std::size_t faces=0, triangles=0, patches=0, skipped_faces=0;
    std::size_t textures=0;
    double units_to_metres=0.0254;
};
// Quake III IBSP version 46: visual faces, not a complete collision scene.
// Unit scale is user-controlled; the 0.0254 default is a starting assumption.
// Alice uses FAKK BSP version 42 (not Quake III's IBSP 46).
BspReport load_fakk42(const std::string& filename, Scene& scene,
                      double units_to_metres=0.0254,
                      int patch_subdivisions=4);
// Autodetect only these supported variants; reject others rather than guess.
BspReport load_bsp(const std::string& filename, Scene& scene,
                   double units_to_metres=0.0254,
                   int patch_subdivisions=4);
BspReport load_ibsp46(const std::string& filename, Scene& scene,
                      double units_to_metres=0.0254,
                      int patch_subdivisions=4);
}
