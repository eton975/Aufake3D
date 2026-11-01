/* v0.5.0 SOURCE COMMENTARY — BSP file parser and triangle extraction
 * Reads game geometry from known BSP layouts with bounds checking. Never trust lump
 * offsets/counts from arbitrary game data; geometry is converted to a form the acoustic
 * routines can query.
 */
#include "alice_a3d/bsp.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace alicea3d {
namespace {
using Bytes=std::vector<std::uint8_t>;
struct Lump { std::size_t offset=0, length=0; };
std::uint32_t u32(const Bytes& b, std::size_t at) {
    if(at>b.size() || b.size()-at<4) throw std::runtime_error("Truncated BSP integer");
    return (std::uint32_t)b[at] | ((std::uint32_t)b[at+1]<<8) |
           ((std::uint32_t)b[at+2]<<16) | ((std::uint32_t)b[at+3]<<24);
}
std::int32_t i32(const Bytes& b,std::size_t at) { return static_cast<std::int32_t>(u32(b,at)); }
float f32(const Bytes& b,std::size_t at) {
    std::uint32_t raw=u32(b,at);float value;
    std::memcpy(&value,&raw,4);return value;
}
Vec3 position(const Bytes& b,std::size_t at,double scale) {
    return {f32(b,at)*scale,f32(b,at+4)*scale,f32(b,at+8)*scale};
}
std::string shader_name(const Bytes& b,std::size_t at) {
    std::size_t len=0;while (len<64 && b[at+len]!=0) ++len;
    return std::string(reinterpret_cast<const char*>(b.data()+at),len);
}
double nominal_absorption(std::string shader) {
    // Illustrative broadband values only. Game texture names are not calibrated
    // acoustic absorption measurements; material assignment must be validated.
    std::transform(shader.begin(),shader.end(),shader.begin(),[](char c){
        return (c>='A'&&c<='Z') ? char(c-'A'+'a') : c;
    });
    if(shader.find("metal")!=std::string::npos) return 0.08;
    if(shader.find("stone")!=std::string::npos || shader.find("brick")!=std::string::npos) return 0.11;
    if(shader.find("wood")!=std::string::npos) return 0.17;
    if(shader.find("cloth")!=std::string::npos || shader.find("carpet")!=std::string::npos) return 0.65;
    return 0.25;
}
Vec3 quadratic(Vec3 a,Vec3 b,Vec3 c,double t) {
    return a*((1-t)*(1-t))+b*(2*t*(1-t))+c*(t*t);
}
Vec3 patch_point(const std::array<std::array<Vec3,3>,3>& cp,double u,double v) {
    Vec3 r0=quadratic(cp[0][0],cp[0][1],cp[0][2],u);
    Vec3 r1=quadratic(cp[1][0],cp[1][1],cp[1][2],u);
    Vec3 r2=quadratic(cp[2][0],cp[2][1],cp[2][2],u);
    return quadratic(r0,r1,r2,v);
}
} // namespace
BspReport load_ibsp46(const std::string& filename,Scene& scene,double scale,int subdivisions) {
    if(!(scale>0.0) || !std::isfinite(scale) || subdivisions<1 || subdivisions>32)
        throw std::invalid_argument("Invalid BSP scale or subdivisions");
    std::ifstream f(filename,std::ios::binary|std::ios::ate);
    if(!f) throw std::runtime_error("Cannot read BSP: "+filename);
    std::streamoff length=f.tellg();
    if(length<144 || length>1024LL*1024*1024) throw std::runtime_error("BSP size invalid");
    Bytes buf(static_cast<std::size_t>(length));
    f.seekg(0);f.read(reinterpret_cast<char*>(buf.data()),length);
    if(!f) throw std::runtime_error("Truncated BSP file");
    if(std::memcmp(buf.data(),"IBSP",4)!=0) throw std::runtime_error("Not an IBSP file");
    int version=i32(buf,4);
    if(version!=46) throw std::runtime_error("Unsupported BSP version "+std::to_string(version)+" (requires Quake III IBSP 46)");
    std::array<Lump,17> lumps;
    for(int i=0;i<17;++i) {
        auto off=i32(buf,8+i*8),len=i32(buf,12+i*8);
        if(off<0 || len<0 || static_cast<std::size_t>(off)>buf.size() ||
           static_cast<std::size_t>(len)>buf.size()-static_cast<std::size_t>(off))
            throw std::runtime_error("Invalid BSP lump bounds");
        lumps[i]={static_cast<std::size_t>(off),static_cast<std::size_t>(len)};
    }
    constexpr std::size_t kShaderSize=72,kVertexSize=44,kFaceSize=104;
    if(lumps[1].length%kShaderSize || lumps[10].length%kVertexSize ||
       lumps[11].length%4 || lumps[13].length%kFaceSize)
        throw std::runtime_error("Malformed standard IBSP 46 lump sizes");
    const std::size_t shaderCount=lumps[1].length/kShaderSize;
    const std::size_t vertexCount=lumps[10].length/kVertexSize;
    const std::size_t meshCount=lumps[11].length/4;
    const std::size_t faceCount=lumps[13].length/kFaceSize;
    if(faceCount>2'000'000 || vertexCount>5'000'000)
        throw std::runtime_error("BSP geometry limits exceeded");
    std::vector<std::string> shaderNames;
    for(std::size_t i=0;i<shaderCount;++i)
        shaderNames.push_back(shader_name(buf,lumps[1].offset+i*kShaderSize));
    std::vector<Vec3> vertices;
    vertices.reserve(vertexCount);
    for(std::size_t i=0;i<vertexCount;++i)
        vertices.push_back(position(buf,lumps[10].offset+i*kVertexSize,scale));
    BspReport report;
    report.version=version;report.format="IBSP";report.faces=faceCount;report.textures=shaderCount;
    report.units_to_metres=scale;
    for(std::size_t i=0;i<faceCount;++i) {
        const std::size_t off=lumps[13].offset+i*kFaceSize;
        const int shader=i32(buf,off), type=i32(buf,off+8);
        const int firstVertex=i32(buf,off+12),nVertices=i32(buf,off+16);
        const int firstMesh=i32(buf,off+20),nMeshes=i32(buf,off+24);
        if(shader<0 || static_cast<std::size_t>(shader)>=shaderCount || firstVertex<0 || nVertices<0 ||
           static_cast<std::size_t>(firstVertex)>vertexCount ||
           static_cast<std::size_t>(nVertices)>vertexCount-static_cast<std::size_t>(firstVertex)) {
            ++report.skipped_faces;continue;
        }
        const auto& name=shaderNames[shader];
        const double absorption=nominal_absorption(name);
        auto add_face=[&](int a,int b,int c) {
            if(a<0 || b<0 || c<0 || a>=nVertices || b>=nVertices || c>=nVertices) return;
            std::size_t before=scene.surfaces().size();
            scene.add({vertices[firstVertex+a],vertices[firstVertex+b],vertices[firstVertex+c],absorption,name});
            report.triangles+=scene.surfaces().size()-before;
        };
        if(type==1 || type==3) {
            if(nMeshes>=3 && firstMesh>=0 &&
               static_cast<std::size_t>(firstMesh)<=meshCount &&
               static_cast<std::size_t>(nMeshes)<=meshCount-static_cast<std::size_t>(firstMesh)) {
                for(int j=0;j+2<nMeshes;j+=3) {
                    auto index=[&](int k){return i32(buf,lumps[11].offset+4*(static_cast<std::size_t>(firstMesh)+j+k));};
                    add_face(index(0),index(1),index(2));
                }
            } else if(type==1) {
                for(int j=1;j+1<nVertices;++j) add_face(0,j,j+1);
            } else ++report.skipped_faces;
        } else if(type==2) {
            ++report.patches;
            int w=i32(buf,off+96),h=i32(buf,off+100);
            if(w<3 || h<3 || w>129 || h>129 || !(w&1) || !(h&1) || w*h>nVertices) {
                ++report.skipped_faces;continue;
            }
            for(int py=0;py+2<h;py+=2) for(int px=0;px+2<w;px+=2) {
                std::array<std::array<Vec3,3>,3> cp;
                for(int y=0;y<3;++y) for(int x=0;x<3;++x)
                    cp[y][x]=vertices[firstVertex+(py+y)*w+px+x];
                const int n=subdivisions;
                for(int y=0;y<n;++y) for(int x=0;x<n;++x) {
                    double x0=double(x)/n,x1=double(x+1)/n;
                    double y0=double(y)/n,y1=double(y+1)/n;
                    Vec3 a=patch_point(cp,x0,y0),b=patch_point(cp,x1,y0);
                    Vec3 c=patch_point(cp,x1,y1),d=patch_point(cp,x0,y1);
                    std::size_t before=scene.surfaces().size();
                    scene.add({a,b,c,absorption,name});scene.add({a,c,d,absorption,name});
                    report.triangles+=scene.surfaces().size()-before;
                }
            }
        } else ++report.skipped_faces;
    }
    return report;
}

BspReport load_fakk42(const std::string& filename,Scene& scene,double scale,int subdivisions) {
    if(!(scale>0.0) || !std::isfinite(scale) || subdivisions<1 || subdivisions>32)
        throw std::invalid_argument("Invalid FAKK scale/subdivisions");
    std::ifstream f(filename,std::ios::binary|std::ios::ate);
    if(!f) throw std::runtime_error("Cannot read FAKK map: "+filename);
    auto length=f.tellg();
    if(length<172 || length>1024LL*1024*1024) throw std::runtime_error("FAKK map size invalid");
    Bytes buf(static_cast<std::size_t>(length));
    f.seekg(0);f.read(reinterpret_cast<char*>(buf.data()),length);
    if(!f) throw std::runtime_error("Truncated FAKK map");
    if(std::memcmp(buf.data(),"FAKK",4)!=0) throw std::runtime_error("Not a FAKK map");
    int version=i32(buf,4);
    if(version!=42) throw std::runtime_error("Unsupported FAKK map version "+std::to_string(version)+" (Alice requires 42)");
    // FAKK has a checksum at offset 8 before its 20 lump descriptors.
    std::array<Lump,20> lumps;
    for(int i=0;i<20;++i){
        auto off=i32(buf,12+i*8),len=i32(buf,16+i*8);
        if(off<0 || len<0 || static_cast<std::size_t>(off)>buf.size() ||
           static_cast<std::size_t>(len)>buf.size()-static_cast<std::size_t>(off))
            throw std::runtime_error("Invalid FAKK lump bounds");
        lumps[i]={static_cast<std::size_t>(off),static_cast<std::size_t>(len)};
    }
    // FAKK lump order differs from Quake III: shader=0, surface=3,
    // draw-vertices=4, draw-indices=5. See layout notes in README.
    constexpr int sh=0,fa=3,ve=4,me=5;
    constexpr std::size_t shaderSize=76,faceSize=108,vertexSize=44;
    if(lumps[sh].length%shaderSize || lumps[fa].length%faceSize ||
       lumps[ve].length%vertexSize || lumps[me].length%4)
        throw std::runtime_error("Malformed FAKK 42 shader/surface/vertex/index lumps");
    const auto numShaders=lumps[sh].length/shaderSize;
    const auto numFaces=lumps[fa].length/faceSize;
    const auto numVerts=lumps[ve].length/vertexSize;
    const auto numMeshes=lumps[me].length/4;
    if(numFaces>2'000'000 || numVerts>5'000'000)
        throw std::runtime_error("FAKK geometry limits exceeded");
    std::vector<std::string> names;
    for(std::size_t i=0;i<numShaders;++i)
        names.push_back(shader_name(buf,lumps[sh].offset+shaderSize*i));
    std::vector<Vec3> verts;
    verts.reserve(numVerts);
    for(std::size_t i=0;i<numVerts;++i)
        verts.push_back(position(buf,lumps[ve].offset+vertexSize*i,scale));
    BspReport report;
    report.version=version;report.format="FAKK";report.faces=numFaces;
    report.textures=numShaders;report.units_to_metres=scale;
    for(std::size_t i=0;i<numFaces;++i){
        const auto off=lumps[fa].offset+faceSize*i;
        int shader=i32(buf,off),type=i32(buf,off+8);
        int firstVert=i32(buf,off+12),countVert=i32(buf,off+16);
        int firstIndex=i32(buf,off+20),countIndex=i32(buf,off+24);
        if(shader<0 || static_cast<std::size_t>(shader)>=numShaders ||
           firstVert<0 || countVert<0 || static_cast<std::size_t>(firstVert)>numVerts ||
           static_cast<std::size_t>(countVert)>numVerts-static_cast<std::size_t>(firstVert)){
            ++report.skipped_faces;continue;
        }
        const auto& name=names[shader];
        double absorption=nominal_absorption(name);
        auto add_face=[&](int a,int b,int c){
            if(a<0||b<0||c<0||a>=countVert||b>=countVert||c>=countVert) return;
            auto before=scene.surfaces().size();
            scene.add({verts[firstVert+a],verts[firstVert+b],verts[firstVert+c],absorption,name});
            report.triangles+=scene.surfaces().size()-before;
        };
        if(type==1 || type==3){
            if(firstIndex>=0 && countIndex>=3 &&
                static_cast<std::size_t>(firstIndex)<=numMeshes &&
                static_cast<std::size_t>(countIndex)<=numMeshes-static_cast<std::size_t>(firstIndex)){
                for(int j=0;j+2<countIndex;j+=3){
                    auto idx=[&](int n){return i32(buf,lumps[me].offset+4*(static_cast<std::size_t>(firstIndex)+j+n));};
                    add_face(idx(0),idx(1),idx(2));
                }
            } else if(type==1) {
                for(int j=1;j+1<countVert;++j) add_face(0,j,j+1);
            } else ++report.skipped_faces;
        } else if(type==2){
            ++report.patches;
            int w=i32(buf,off+96),h=i32(buf,off+100);
            if(w<3||h<3||w>129||h>129||!(w&1)||!(h&1)||w*h>countVert){
                ++report.skipped_faces;continue;
            }
            for(int py=0;py+2<h;py+=2) for(int px=0;px+2<w;px+=2){
                std::array<std::array<Vec3,3>,3> cp;
                for(int y=0;y<3;++y) for(int x=0;x<3;++x)
                    cp[y][x]=verts[firstVert+(py+y)*w+px+x];
                for(int y=0;y<subdivisions;++y) for(int x=0;x<subdivisions;++x){
                    double u0=double(x)/subdivisions,u1=double(x+1)/subdivisions;
                    double v0=double(y)/subdivisions,v1=double(y+1)/subdivisions;
                    Vec3 a=patch_point(cp,u0,v0),b=patch_point(cp,u1,v0);
                    Vec3 c=patch_point(cp,u1,v1),d=patch_point(cp,u0,v1);
                    auto before=scene.surfaces().size();
                    scene.add({a,b,c,absorption,name});scene.add({a,c,d,absorption,name});
                    report.triangles+=scene.surfaces().size()-before;
                }
            }
        } else ++report.skipped_faces;
    }
    return report;
}
BspReport load_bsp(const std::string& filename,Scene& scene,double scale,int subdivisions){
    std::ifstream f(filename,std::ios::binary);
    if(!f) throw std::runtime_error("Cannot open BSP: "+filename);
    char magic[4];f.read(magic,4);
    if(!f) throw std::runtime_error("Truncated BSP header");
    if(std::memcmp(magic,"FAKK",4)==0) return load_fakk42(filename,scene,scale,subdivisions);
    if(std::memcmp(magic,"IBSP",4)==0) return load_ibsp46(filename,scene,scale,subdivisions);
    throw std::runtime_error("Unsupported map format (expected Alice FAKK 42 or Quake III IBSP 46)");
}
} // namespace alicea3d
