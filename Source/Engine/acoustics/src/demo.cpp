/* v0.5.0 SOURCE COMMENTARY — Acoustics demo program
 * Runs a synthetic scene example separately from any game or Aureal COM object. Helps
 * diagnose geometry and path calculations without sound-card dependencies.
 */
#include "alice_a3d/acoustics.hpp"
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
using namespace alicea3d;
static void quad(Scene& scene,Vec3 a,Vec3 b,Vec3 c,Vec3 d,double absorption,const char* label) {
    scene.add({a,b,c,absorption,label});
    scene.add({a,c,d,absorption,label});
}
static void print_paths(std::ostream& out,const std::vector<AcousticPath>& paths) {
    for(const auto& p: paths) {
        out<<std::fixed<<std::setprecision(4)
           <<path_kind_name(p.kind)<<",distance_m="<<p.metres
           <<",arrival_xyz="<<p.arrival_from.x<<"/"<<p.arrival_from.y<<"/"<<p.arrival_from.z
           <<",delay_ms="<<p.delay_seconds*1000
           <<",amplitude="<<p.amplitude
           <<",lowpass_hz="<<p.lowpass_hz
           <<",reflector="<<p.reflector<<",blockers="<<p.blockers<<'\n';
    }
}
int main(int argc,char** argv) {
    try {
        const std::string prefix=argc>1?argv[1]:"alice-a3d";
        // 8m x 6m x 3m room. Reflective ceiling + floor and a middle wall.
        Scene room;
        quad(room,{-4,-3,-1.5},{4,-3,-1.5},{4,3,-1.5},{-4,3,-1.5},0.12,"stone-floor");
        quad(room,{-4,-3,1.5},{-4,3,1.5},{4,3,1.5},{4,-3,1.5},0.36,"ceiling");
        quad(room,{-4,3,-1.5},{4,3,-1.5},{4,3,1.5},{-4,3,1.5},0.18,"back-wall");
        quad(room,{-4,-3,-1.5},{-4,-3,1.5},{4,-3,1.5},{4,-3,-1.5},0.18,"front-wall");
        quad(room,{-4,-3,-1.5},{-4,3,-1.5},{-4,3,1.5},{-4,-3,1.5},0.18,"left-wall");
        quad(room,{4,-3,-1.5},{4,-3,1.5},{4,3,1.5},{4,3,-1.5},0.18,"right-wall");
        Vec3 listener{0,0,0}, source{2,1,0};
        auto clear=room.trace(source,listener);
        // A separate isolated scene for wall occlusion; avoid occluding floor paths.
        Scene wall;
        quad(wall,{1,-1,-1},{1,1,-1},{1,1,1},{1,-1,1},0.12,"stone-wall");
        auto occluded=wall.trace({2,0,0},{0,0,0});
        auto unobstructed=wall.trace({0,2,0},{0,0,0});
        render_diagnostic_wav(prefix+"_room.wav",clear);
        render_diagnostic_wav(prefix+"_wall.wav",occluded);
        render_diagnostic_wav(prefix+"_open.wav",unobstructed);
        std::ofstream results(prefix+"_paths.txt");
        if(!results) throw std::runtime_error("Failed to write path report");
        results<<"ROOM (first-order reflections):\n";print_paths(results,clear);
        results<<"\nWALL (occluded):\n";print_paths(results,occluded);
        results<<"\nOPEN (direct):\n";print_paths(results,unobstructed);
        std::cout<<"Created three stereo WAV files and path report using prefix: "<<prefix<<"\n";
        std::cout<<"Room paths: "<<clear.size()<<"; wall direct blockers: "<<occluded[0].blockers<<'\n';
    } catch(const std::exception& e) {
        std::cerr<<"ERROR: "<<e.what()<<'\n';return EXIT_FAILURE;
    }
}
