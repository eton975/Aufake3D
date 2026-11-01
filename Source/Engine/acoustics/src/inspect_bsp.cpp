/* v0.5.0 SOURCE COMMENTARY — BSP inspection utility
 * Prints detected map structure and parser results for offline inspection of level
 * geometry.
 */
#include "alice_a3d/bsp.hpp"
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <stdexcept>
using namespace alicea3d;
int main(int argc,char** argv) {
    if(argc<2) { std::cerr<<"Usage: alice_bsp_inspect <extracted_level.bsp> [units_to_metres] [x y z source_x source_y source_z]\n";return 2; }
    try {
        double scale=argc>2?std::stod(argv[2]):0.0254;
        Scene scene;
        auto report=load_bsp(argv[1],scene,scale);
        std::cout<<"BSP format="<<report.format<<" version="<<report.version<<" faces="<<report.faces
                 <<" patches="<<report.patches<<" triangles="<<report.triangles
                 <<" skipped="<<report.skipped_faces<<" shaders="<<report.textures
                 <<" metres_per_unit="<<report.units_to_metres<<'\n';
        if(argc==9) {
            Vec3 listener{std::stod(argv[3]),std::stod(argv[4]),std::stod(argv[5])};
            Vec3 source{std::stod(argv[6]),std::stod(argv[7]),std::stod(argv[8])};
            auto paths=scene.trace(source*scale,listener*scale,4);
            for(const auto& p:paths)
                std::cout<<path_kind_name(p.kind)<<" length="<<std::fixed<<std::setprecision(3)
                         <<p.metres<<"m delay="<<p.delay_seconds*1000<<"ms gain="<<p.amplitude
                         <<" blockers="<<p.blockers<<" reflector="<<p.reflector<<'\n';
        }
    } catch(const std::exception& e) {
        std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;
    }
}
