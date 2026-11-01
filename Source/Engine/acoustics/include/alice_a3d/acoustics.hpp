/* v0.5.0 SOURCE COMMENTARY — Geometry-acoustics public structures
 * Defines geometry, audio-material and ray/reflection interfaces for independent
 * testing; keep floating-point coordinate units consistent with A3D scene submission.
 */
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace alicea3d {
constexpr double kSoundSpeed = 343.0;
struct Vec3 {
    double x=0, y=0, z=0;
    Vec3 operator+(Vec3 b) const { return {x+b.x,y+b.y,z+b.z}; }
    Vec3 operator-(Vec3 b) const { return {x-b.x,y-b.y,z-b.z}; }
    Vec3 operator*(double s) const { return {x*s,y*s,z*s}; }
    Vec3 operator/(double s) const { return {x/s,y/s,z/s}; }
};
double dot(Vec3 a, Vec3 b);
Vec3 cross(Vec3 a, Vec3 b);
double length(Vec3 v);
Vec3 normalized(Vec3 v);

struct Surface {
    Vec3 a, b, c;
    double absorption = 0.25; // illustrative broadband, NOT measured material coefficients
    std::string material = "unknown";
};

enum class PathKind { Direct, Occluded, FirstReflection };
struct AcousticPath {
    PathKind kind = PathKind::Direct;
    Vec3 arrival_from;          // listener -> source or reflection point, world coordinates
    Vec3 bounce_point;          // valid for reflections
    double metres = 0.0;
    double delay_seconds = 0.0;
    double amplitude = 0.0;     // simplified broadband gain
    double lowpass_hz = 18000.0;
    int reflector = -1;
    std::size_t blockers = 0;
};

class Scene {
public:
    void add(Surface s);
    void clear();
    const std::vector<Surface>& surfaces() const { return surfaces_; }
    bool blocked(Vec3 from, Vec3 to, int ignore = -1) const;
    std::size_t blocking_count(Vec3 from, Vec3 to, int ignore = -1) const;
    std::vector<AcousticPath> trace(Vec3 source, Vec3 listener,
                                    std::size_t max_reflections=16) const;
private:
    struct BvhNode {
        Vec3 lo,hi;
        int left=-1,right=-1;
        std::size_t begin=0,end=0;
    };
    void ensure_bvh() const;
    int build_node(std::size_t begin,std::size_t end) const;
    std::vector<Surface> surfaces_;
    mutable bool accel_dirty_=true;
    mutable std::vector<std::size_t> order_;
    mutable std::vector<BvhNode> tree_;
};

// Offline diagnostic audition. Stereo is only a crude ITD/ILD approximation:
// there is NO individualized or measured HRTF in this prototype.
void render_diagnostic_wav(const std::string& path,
                           const std::vector<AcousticPath>& paths,
                           Vec3 listener_right={1,0,0},
                           unsigned sample_rate=48000);
std::string path_kind_name(PathKind kind);
} // namespace alicea3d
