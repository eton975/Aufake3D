/* v0.5.0 SOURCE COMMENTARY — Geometry trace conversion
 * Exports/inspects geometry traces for offline visualization; diagnostic only.
 */
#include "alice_a3d/acoustics.hpp"
#include <fstream>
#include <iostream>
#include <sstream>
#include <vector>
#include <string>
#include <cstdlib>
using namespace alicea3d;
int main(int argc, char**argv){
 if(argc!=8){std::cerr<<"Usage: alice_obj_trace geometry.obj sx sy sz lx ly lz\n";return 2;}
 std::ifstream in(argv[1]);if(!in){std::cerr<<"Cannot read OBJ\n";return 2;}
 Vec3 src{std::atof(argv[2]),std::atof(argv[3]),std::atof(argv[4])};
 Vec3 lst{std::atof(argv[5]),std::atof(argv[6]),std::atof(argv[7])};
 std::vector<Vec3> vertices;Scene scene;std::size_t count=0;
 std::string line;
 while(std::getline(in,line)){
  std::istringstream ss(line);std::string tok;ss>>tok;
  if(tok=="v"){
   Vec3 v; if(ss>>v.x>>v.y>>v.z)vertices.push_back(v);
  }else if(tok=="f"){
   unsigned a,b,c;if(!(ss>>a>>b>>c))continue;
   if(a<1||b<1||c<1||a>vertices.size()||b>vertices.size()||c>vertices.size()){
    std::cerr<<"Invalid face index\n";return 2;
   }
   scene.add({vertices[a-1],vertices[b-1],vertices[c-1],0.25,"uncalibrated"});count++;
  }
 }
 std::cout<<"Imported acoustic triangles="<<count<<" (materials/scale uncalibrated)\n";
 auto paths=scene.trace(src,lst);
 for(const auto&p:paths){
   std::cout<<path_kind_name(p.kind)<<" metres="<<p.metres<<" delay_s="<<p.delay_seconds
            <<" amplitude="<<p.amplitude<<" blockers="<<p.blockers<<"\n";
 }
 return 0;
}
