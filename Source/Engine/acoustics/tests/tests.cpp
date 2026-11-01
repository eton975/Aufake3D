/* v0.5.0 SOURCE COMMENTARY — Regression test / harness
 * Exercises the release implementation or checks its ABI/packaging contract. Do not
 * treat fixture success as proof of native Wine or retail-game compatibility.
 */
#include "alice_a3d/acoustics.hpp"
#include "alice_a3d/bsp.hpp"
#include <cassert>
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>
using namespace alicea3d;
static bool near(double a,double b,double error=1e-5){return std::abs(a-b)<=error;}
static void expect(bool valid,const char* message) {
    if (!valid) throw std::runtime_error(message);
}
int main(){
    try {
        Scene empty;
        auto clear=empty.trace({3,0,0},{0,0,0});
        expect(clear.size()==1,"Empty scene: should have direct path only");
        expect(clear[0].kind==PathKind::Direct,"Empty scene must not obstruct direct path");
        expect(near(clear[0].delay_seconds,3.0/kSoundSpeed),"Wrong propagation time");
        Scene divider;
        divider.add({{1,-2,-2},{1,2,-2},{1,0,2},0.2,"stone"});
        auto occluded=divider.trace({2,0,0},{0,0,0});
        expect(occluded[0].kind==PathKind::Occluded,"Wall should obstruct direct ray");
        expect(occluded[0].blockers==1,"Expected one wall obstruction");
        expect(occluded[0].amplitude<clear[0].amplitude,"Wall must attenuate sound");
        expect(occluded[0].lowpass_hz<clear[0].lowpass_hz,"Wall must lowpass sound");
        Scene floor;
        floor.add({{-3,-3,0},{3,-3,0},{0,3,0},0.2,"floor"});
        auto paths=floor.trace({1,0,1},{0,0,1});
        expect(paths.size()==2,"Expected direct and first-order floor reflection");
        expect(paths[1].kind==PathKind::FirstReflection,"Second path must be reflection");
        expect(near(paths[1].bounce_point.x,0.5),"Wrong image-source bounce x");
        expect(near(paths[1].bounce_point.z,0),"Wrong image-source bounce z");
        expect(near(paths[1].metres,std::sqrt(5.0)),"Wrong specular path length");
        Scene behind_floor;
        behind_floor.add({{-3,-3,0},{3,-3,0},{0,3,0},0.2,"floor"});
        auto no_reflection=behind_floor.trace({1,0,-1},{0,0,1});
        expect(no_reflection.size()==1,"Opposite-side source should have no specular reflection");
        expect(no_reflection[0].kind==PathKind::Occluded,"Floor should block opposite-side source");
        render_diagnostic_wav("test_output.wav",paths);
        std::ifstream wav("test_output.wav",std::ios::binary|std::ios::ate);
        expect(wav && wav.tellg()==static_cast<std::streamoff>(44+48000*2*4),"WAV size invalid");
        wav.seekg(0);
        char riff[4];wav.read(riff,4);
        expect(std::string(riff,4)=="RIFF","WAV RIFF header invalid");
        std::cout<<"PASS: direct sound, occlusion, first-order image reflections, delays, and WAV generation\n";
    } catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}
}
