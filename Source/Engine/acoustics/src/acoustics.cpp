/* v0.5.0 SOURCE COMMENTARY — Acoustic path and material model
 * Implements simplified ray intersection/occlusion and reflection estimation for the
 * experimental geometry backend. Results are acoustical approximations, not bit-exact
 * Aureal Wavetracing output.
 */
#include "alice_a3d/acoustics.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <limits>
#include <stdexcept>

namespace alicea3d {
double dot(Vec3 a,Vec3 b) { return a.x*b.x+a.y*b.y+a.z*b.z; }
Vec3 cross(Vec3 a,Vec3 b) { return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x}; }
double length(Vec3 v) { return std::sqrt(dot(v,v)); }
Vec3 normalized(Vec3 v) { double n=length(v); return n<1.e-10 ? Vec3{} : v/n; }

// Two-sided Moller-Trumbore test. The endpoint margin avoids a path hitting its
// originating/reflection triangle due to floating-point roundoff.
static double segment_hit_fraction(Vec3 a, Vec3 b, const Surface& tri) {
    Vec3 delta=b-a, e1=tri.b-tri.a,e2=tri.c-tri.a;
    Vec3 p=cross(delta,e2);
    double det=dot(e1,p);
    if (std::abs(det)<1.e-10) return -1;
    double inv=1.0/det;
    Vec3 t=a-tri.a;
    double u=dot(t,p)*inv;
    if (u < -1.e-8 || u > 1.0+1.e-8) return -1;
    double v=dot(delta,cross(t,e1))*inv;
    if (v < -1.e-8 || u+v > 1.0+1.e-8) return -1;
    double segment_fraction=dot(e2,cross(t,e1))*inv;
    return (segment_fraction > 1.e-5 && segment_fraction < 1.0-1.e-5) ? segment_fraction : -1.0;
}
static bool point_in_triangle(Vec3 p, const Surface& t) {
    Vec3 v0=t.b-t.a,v1=t.c-t.a,v2=p-t.a;
    double d00=dot(v0,v0),d01=dot(v0,v1),d11=dot(v1,v1);
    double d20=dot(v2,v0),d21=dot(v2,v1),denom=d00*d11-d01*d01;
    if (std::abs(denom)<1.e-16) return false;
    double u=(d11*d20-d01*d21)/denom;
    double v=(d00*d21-d01*d20)/denom;
    return u>=-1.e-6 && v>=-1.e-6 && u+v<=1.0+1.e-6;
}
void Scene::add(Surface s) {
    if (length(cross(s.b-s.a,s.c-s.a))<1.e-9) return;
    s.absorption=std::clamp(s.absorption,0.0,1.0);
    surfaces_.push_back(std::move(s));
    accel_dirty_=true;
}
void Scene::clear() { surfaces_.clear();tree_.clear();order_.clear();accel_dirty_=true; }
namespace {
double coordinate(Vec3 p,int axis){return axis==0?p.x:(axis==1?p.y:p.z);}
Vec3 vmin(Vec3 a,Vec3 b){return {std::min(a.x,b.x),std::min(a.y,b.y),std::min(a.z,b.z)};}
Vec3 vmax(Vec3 a,Vec3 b){return {std::max(a.x,b.x),std::max(a.y,b.y),std::max(a.z,b.z)};}
bool segment_box(Vec3 a,Vec3 b,Vec3 lo,Vec3 hi){
    Vec3 d=b-a;
    double near=0,far=1;
    for(int axis=0;axis<3;++axis){
        double origin=coordinate(a,axis),delta=coordinate(d,axis);
        double left=coordinate(lo,axis)-1e-7,right=coordinate(hi,axis)+1e-7;
        if(std::abs(delta)<1e-12){if(origin<left || origin>right) return false;}
        else {
            double t0=(left-origin)/delta,t1=(right-origin)/delta;
            if(t0>t1) std::swap(t0,t1);
            near=std::max(near,t0);far=std::min(far,t1);
            if(near>far) return false;
        }
    }
    return true;
}
} // namespace
void Scene::ensure_bvh() const {
    if(!accel_dirty_) return;
    order_.resize(surfaces_.size());
    for(std::size_t i=0;i<order_.size();++i) order_[i]=i;
    tree_.clear();
    if(!order_.empty()) build_node(0,order_.size());
    accel_dirty_=false;
}
int Scene::build_node(std::size_t begin,std::size_t end) const {
    const int current=static_cast<int>(tree_.size());
    tree_.push_back({});
    Vec3 lo{1e100,1e100,1e100},hi{-1e100,-1e100,-1e100};
    for(std::size_t k=begin;k<end;++k){
        const auto& s=surfaces_[order_[k]];
        lo=vmin(lo,vmin(s.a,vmin(s.b,s.c)));
        hi=vmax(hi,vmax(s.a,vmax(s.b,s.c)));
    }
    tree_[current].lo=lo;tree_[current].hi=hi;
    tree_[current].begin=begin;tree_[current].end=end;
    if(end-begin<=8) return current;
    Vec3 ext=hi-lo;
    int axis=ext.x>=ext.y && ext.x>=ext.z?0:(ext.y>=ext.z?1:2);
    const auto mid=begin+(end-begin)/2;
    std::nth_element(order_.begin()+begin,order_.begin()+mid,order_.begin()+end,
      [&](std::size_t ia,std::size_t ib){
        const auto& a=surfaces_[ia];const auto& b=surfaces_[ib];
        return coordinate((a.a+a.b+a.c)/3,axis) < coordinate((b.a+b.b+b.c)/3,axis);
      });
    int left=build_node(begin,mid);
    int right=build_node(mid,end);
    tree_[current].left=left;tree_[current].right=right;
    return current;
}
std::size_t Scene::blocking_count(Vec3 a, Vec3 b, int ignore) const {
    ensure_bvh();
    std::vector<double> intersections;
    if(tree_.empty()) return 0;
    std::vector<int> stack{0};
    while(!stack.empty()){
        int index=stack.back();stack.pop_back();
        const auto& node=tree_[index];
        if(!segment_box(a,b,node.lo,node.hi)) continue;
        if(node.left>=0){stack.push_back(node.left);stack.push_back(node.right);}
        else for(std::size_t k=node.begin;k<node.end;++k){
            const auto id=order_[k];
            if(static_cast<int>(id)==ignore) continue;
            double t=segment_hit_fraction(a,b,surfaces_[id]);
            if(t>=0) intersections.push_back(t);
        }
    }
    // Two triangles of a planar quad may meet at the same ray parameter.
    std::sort(intersections.begin(),intersections.end());
    std::size_t count=0;
    double last=-1;
    for(double t:intersections){if(!count || t-last>1e-5){++count;last=t;}}
    return count;
}
bool Scene::blocked(Vec3 a,Vec3 b,int ignore) const {
    ensure_bvh();
    if(tree_.empty()) return false;
    std::vector<int> stack{0};
    while(!stack.empty()){
        int index=stack.back();stack.pop_back();
        const auto& node=tree_[index];
        if(!segment_box(a,b,node.lo,node.hi)) continue;
        if(node.left>=0){stack.push_back(node.left);stack.push_back(node.right);}
        else for(std::size_t k=node.begin;k<node.end;++k){
            const auto id=order_[k];
            if(static_cast<int>(id)!=ignore && segment_hit_fraction(a,b,surfaces_[id])>=0)
                return true;
        }
    }
    return false;
}
static double distance_gain(double metres) {
    // Perceptual audition convenience, not an AU8830 attenuation law.
    return 1.0/(1.0+0.25*metres);
}
std::vector<AcousticPath> Scene::trace(Vec3 source,Vec3 listener,std::size_t max_reflections) const {
    std::vector<AcousticPath> out;
    double direct_len=length(source-listener);
    std::size_t obstructions=blocking_count(listener,source);
    AcousticPath direct;
    direct.kind=obstructions?PathKind::Occluded:PathKind::Direct;
    direct.arrival_from=normalized(source-listener);
    direct.metres=direct_len;
    direct.delay_seconds=direct_len/kSoundSpeed;
    direct.blockers=obstructions;
    direct.amplitude=distance_gain(direct_len)* (obstructions?0.25:1.0);
    direct.lowpass_hz=obstructions?1350.0:18000.0;
    out.push_back(direct);

    if(max_reflections==0) return out;
    std::vector<AcousticPath> candidates;
    for (std::size_t i=0;i<surfaces_.size();++i) {
        const Surface& s=surfaces_[i];
        Vec3 n=normalized(cross(s.b-s.a,s.c-s.a));
        double sd=dot(source-s.a,n), ld=dot(listener-s.a,n);
        // Specular reflection is defined when source and listener are on the
        // same side; normal winding is irrelevant.
        if (sd*ld <= 1.e-8) continue;
        Vec3 image_source=source-n*(2.0*sd);
        Vec3 ray=image_source-listener;
        double denominator=dot(ray,n);
        if (std::abs(denominator)<1.e-10) continue;
        double fraction=dot(s.a-listener,n)/denominator;
        if (fraction<=1.e-6 || fraction>=1.0-1.e-6) continue;
        Vec3 bounce=listener+ray*fraction;
        if (!point_in_triangle(bounce,s)) continue;
        double metres=length(listener-bounce)+length(bounce-source);
        AcousticPath p;
        p.kind=PathKind::FirstReflection;
        p.bounce_point=bounce;
        p.arrival_from=normalized(bounce-listener);
        p.metres=metres;
        p.delay_seconds=metres/kSoundSpeed;
        p.reflector=static_cast<int>(i);
        p.amplitude=0.65*std::sqrt(std::max(0.0,1.0-s.absorption))*distance_gain(metres);
        p.lowpass_hz=6000.0;
        candidates.push_back(p);
    }
    // Sort without shadow rays, then run occlusion BVH checks on the strongest
    // candidates. This keeps large BSP scenes usable for offline diagnostics.
    // Candidate budget is a heuristic: not yet an exhaustive reflection solver.
    std::sort(candidates.begin(),candidates.end(),[](const AcousticPath&a,const AcousticPath&b){
        return a.amplitude>b.amplitude;
    });
    std::size_t budget=std::min(candidates.size(),std::max<std::size_t>(2048,max_reflections*64));
    for(std::size_t i=0;i<budget && out.size()<max_reflections+1;++i) {
        auto& p=candidates[i];
        if(!blocked(listener,p.bounce_point,p.reflector) &&
           !blocked(p.bounce_point,source,p.reflector)) out.push_back(p);
    }
    return out;
}
std::string path_kind_name(PathKind kind) {
    switch(kind) {
        case PathKind::Direct:return "direct";
        case PathKind::Occluded:return "occluded";
        case PathKind::FirstReflection:return "first-reflection";
    }
    return "unknown";
}
static void write16(std::ofstream& o,std::uint16_t v) {
    char bytes[2]={static_cast<char>(v),static_cast<char>(v>>8)};
    o.write(bytes,2);
}
static void write32(std::ofstream& o,std::uint32_t v) {
    char bytes[4]={static_cast<char>(v),static_cast<char>(v>>8),static_cast<char>(v>>16),static_cast<char>(v>>24)};
    o.write(bytes,4);
}
void render_diagnostic_wav(const std::string& filename,
                           const std::vector<AcousticPath>& paths,
                           Vec3 listener_right, unsigned sample_rate) {
    if(sample_rate<8000 || sample_rate>192000) throw std::runtime_error("Invalid rate");
    const std::size_t samples=static_cast<std::size_t>(sample_rate)*2;
    std::vector<double> left(samples,0),right(samples,0);
    const Vec3 ear_right=normalized(listener_right);
    const double pi=3.14159265358979323846;
    // Short 850Hz+1700Hz pulse repeated every 0.4s. Paths have physical flight time.
    // Frequency-selective filtering applied separately to each path before mixing.
    for (const AcousticPath& path:paths) {
        double lateral=std::clamp(dot(normalized(path.arrival_from),ear_right),-1.0,1.0);
        double pan_l=std::sqrt((1.0-lateral)*0.5);
        double pan_r=std::sqrt((1.0+lateral)*0.5);
        // Max interaural time difference ~0.51 ms, simple geometric surrogate.
        double itd=0.175*lateral/kSoundSpeed;
        double alpha=std::exp(-2.0*pi*path.lowpass_hz/sample_rate);
        for (int ch=0;ch<2;++ch) {
            auto& output=ch?right:left;
            double gain=path.amplitude*(ch?pan_r:pan_l);
            double shift=path.delay_seconds + (ch?-itd*0.5:itd*0.5);
            double filter=0;
            for (std::size_t i=0;i<samples;++i) {
                double t=static_cast<double>(i)/sample_rate-shift;
                double phase=std::fmod(t,0.4);
                double v=0;
                if (t>=0 && phase>=0 && phase<0.10) {
                    double envelope=std::sin(pi*phase/0.10);
                    envelope*=envelope;
                    v=envelope*(std::sin(2*pi*850*phase)+0.35*std::sin(2*pi*1700*phase));
                }
                filter=(1.0-alpha)*v+alpha*filter;
                output[i]+=gain*filter;
            }
        }
    }
    // Apply identical gain to every test recording. Per-file peak normalization
    // would incorrectly make the occluded example sound as loud as the clear one.
    const double scale=0.22;
    std::ofstream f(filename,std::ios::binary);
    if(!f) throw std::runtime_error("Cannot create WAV: "+filename);
    f.write("RIFF",4);write32(f,36+static_cast<std::uint32_t>(samples*4));
    f.write("WAVEfmt ",8);write32(f,16);write16(f,1);write16(f,2);
    write32(f,sample_rate);write32(f,sample_rate*4);write16(f,4);write16(f,16);
    f.write("data",4);write32(f,static_cast<std::uint32_t>(samples*4));
    for (std::size_t i=0;i<samples;++i) {
        auto quant=[&](double v){return static_cast<std::int16_t>(std::lround(std::clamp(v*scale,-1.0,1.0)*32767));};
        write16(f,static_cast<std::uint16_t>(quant(left[i])));
        write16(f,static_cast<std::uint16_t>(quant(right[i])));
    }
    if (!f) throw std::runtime_error("WAV write failed");
}
} // namespace alicea3d
