/* v0.5.0 SOURCE COMMENTARY — Geometry object and A3D scene submission
 * Tracks triangles, materials and scene updates for experimental occlusion and
 * reflection processing. COM callbacks are distinct from the physics/ray-tracing
 * implementation; the game must actually submit geometry for this path to affect audio.
 */
/* A3D 2.0 geometry submission and bounded first-order acoustic processing. */
#ifndef E_INVALIDARG
#define E_INVALIDARG ((HRESULT)0x80070057L)
#endif
#include "acoustic_scene.h"
static A3DScene a3d_scene;
static int a3d_scene_ready=0;
/* Lazy scene storage initialization. COM geometry submission is a contract
 * boundary: Begin/Vertex/End and transform-stack calls update the scene, but
 * a scene with zero submitted triangles cannot yield real occlusion. Material
 * serialization and several geometry features deliberately return E_NOTIMPL. */
static void ensure_scene(void){if(!a3d_scene_ready){a3d_scene_init(&a3d_scene);a3d_scene_ready=1;}}

typedef struct Geom Geom;
struct Geom {void **vt; volatile long ref; DWORD primitive;};
static HRESULT WINAPI gqi(Geom*,const GUID*,void**);
static ULONG WINAPI gadd(Geom*g){return (ULONG)InterlockedIncrement(&g->ref);}
static ULONG WINAPI grel(Geom*g){long n=InterlockedDecrement(&g->ref);if(n<1){g->ref=1;return 1;}return (ULONG)n;}
static const GUID iid_geom=G(0xc398e561,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static void hexval(char*p,DWORD v){const char h[]="0123456789abcdef";for(int i=0;i<8;i++)p[i]=h[(v>>(28-4*i))&15];}
static void log3(const char*prefix,float a,float b,float c){
 union {float f;DWORD v;} x,y,z;
 x.f=a;y.f=b;z.f=c;
 char str[96];int i=0;
 while(prefix[i]&&i<48){str[i]=prefix[i];i++;}
 str[i++]=' ';hexval(str+i,x.v);i+=8;str[i++]=' ';
 hexval(str+i,y.v);i+=8;str[i++]=' ';
 hexval(str+i,z.v);i+=8;str[i]=0;
 logline(str);
}
static unsigned g_vertex_log_count=0;
static void gvertex(float a,float b,float c){ensure_scene();a3d_scene_vertex(&a3d_scene,a,b,c);if(g_vertex_log_count++<12)log3("IA3dGeom.Vertex3f",a,b,c);}

static HRESULT WINAPI g_Enable(Geom*g,DWORD flags){(void)g;ensure_scene();if(flags&~(A3D_SCENE_OCCLUSIONS|A3D_SCENE_REFLECTIONS))return E_INVALIDARG;a3d_scene.global_flags|=flags;return S_OK;}
static HRESULT WINAPI g_Disable(Geom*g,DWORD flags){(void)g;ensure_scene();if(flags&~(A3D_SCENE_OCCLUSIONS|A3D_SCENE_REFLECTIONS))return E_INVALIDARG;a3d_scene.global_flags&=~flags;return S_OK;}
static BOOL WINAPI g_IsEnabled(Geom*g,DWORD flags){(void)g;ensure_scene();return (a3d_scene.global_flags&flags)==flags;}
static HRESULT WINAPI g_SetOcclusionMode(Geom*g,DWORD x){(void)g;(void)x;return E_NOTIMPL;}
static HRESULT WINAPI g_GetOcclusionMode(Geom*g,DWORD*p){(void)g;if(p)*p=0;return E_NOTIMPL;}
static HRESULT WINAPI g_SetReflectionMode(Geom*g,DWORD x){(void)g;(void)x;return E_NOTIMPL;}
static HRESULT WINAPI g_GetReflectionMode(Geom*g,DWORD*p){(void)g;if(p)*p=0;return E_NOTIMPL;}
static float g_ref_gain=1.0f,g_ref_delay=1.0f;
static HRESULT WINAPI g_SetReflectionGainScale(Geom*g,float x){(void)g;if(x<0.0f||x>4.0f)return E_INVALIDARG;g_ref_gain=x;return S_OK;}
static HRESULT WINAPI g_GetReflectionGainScale(Geom*g,float*x){(void)g;if(!x)return E_POINTER;*x=g_ref_gain;return S_OK;}
static HRESULT WINAPI g_SetReflectionDelayScale(Geom*g,float x){(void)g;if(x<0.0f||x>4.0f)return E_INVALIDARG;g_ref_delay=x;return S_OK;}
static HRESULT WINAPI g_GetReflectionDelayScale(Geom*g,float*x){(void)g;if(!x)return E_POINTER;*x=g_ref_delay;return S_OK;}
static ULONG WINAPI g_PushMatrix(Geom*g){(void)g;ensure_scene();if(a3d_scene.stack_level+1>=A3D_SCENE_MAX_STACK)return 0;
 for(int i=0;i<16;i++)a3d_scene.matrix[a3d_scene.stack_level+1][i]=a3d_scene.matrix[a3d_scene.stack_level][i];return ++a3d_scene.stack_level+1;}
static ULONG WINAPI g_PopMatrix(Geom*g){(void)g;ensure_scene();if(!a3d_scene.stack_level)return 0;return a3d_scene.stack_level--;}
static HRESULT WINAPI g_LoadIdentity(Geom*g){(void)g;ensure_scene();a3d_identity(a3d_scene.matrix[a3d_scene.stack_level]);return S_OK;}
static HRESULT WINAPI g_LoadMatrix(Geom*g,const float*m){(void)g;if(!m)return E_POINTER;ensure_scene();for(int i=0;i<16;i++)a3d_scene.matrix[a3d_scene.stack_level][i]=m[i];return S_OK;}
static HRESULT WINAPI g_GetMatrix(Geom*g,float*m){(void)g;if(!m)return E_POINTER;ensure_scene();for(int i=0;i<16;i++)m[i]=a3d_scene.matrix[a3d_scene.stack_level][i];return S_OK;}
static HRESULT WINAPI g_MultMatrix(Geom*g,const float*m){(void)g;if(!m)return E_POINTER;ensure_scene();a3d_matmul(a3d_scene.matrix[a3d_scene.stack_level],m);return S_OK;}
static HRESULT WINAPI g_Translate3f(Geom*g,float x,float y,float z){(void)g;ensure_scene();float m[16];a3d_identity(m);m[12]=x;m[13]=y;m[14]=z;a3d_matmul(a3d_scene.matrix[a3d_scene.stack_level],m);return S_OK;}
static HRESULT WINAPI g_Translate3fv(Geom*g,const float*x){return x?g_Translate3f(g,x[0],x[1],x[2]):E_POINTER;}
/* Range-reduced sine/cosine used only for scene transform, without CRT linkage. */
static float g_sin(float x){const float tau=6.28318530718f;int turns=(int)(x/tau);x-=turns*tau;
 if(x>3.14159265f)x-=tau;if(x< -3.14159265f)x+=tau;
 if(x>1.57079632679f)x=3.14159265359f-x;
 if(x< -1.57079632679f)x=-3.14159265359f-x;
 float xx=x*x;return x*(1.0f+xx*(-0.1666666667f+xx*(0.0083333333f+xx*(-0.0001984127f+xx*0.0000027557f))));}
static HRESULT WINAPI g_Rotate3f(Geom*g,float degrees,float x,float y,float z){(void)g;ensure_scene();
 float n=a3d_sqrt(x*x+y*y+z*z);if(n<1.e-6f)return E_INVALIDARG;x/=n;y/=n;z/=n;
 float rad=degrees*0.01745329251994f,si=g_sin(rad),co=g_sin(rad+1.57079632679f),ic=1.0f-co;
 float m[16];a3d_identity(m);
 m[0]=co+x*x*ic;m[4]=x*y*ic-z*si;m[8]=x*z*ic+y*si;
 m[1]=y*x*ic+z*si;m[5]=co+y*y*ic;m[9]=y*z*ic-x*si;
 m[2]=z*x*ic-y*si;m[6]=z*y*ic+x*si;m[10]=co+z*z*ic;
 a3d_matmul(a3d_scene.matrix[a3d_scene.stack_level],m);return S_OK;}
static HRESULT WINAPI g_Rotate3fv(Geom*g,float degrees,const float*x){return x?g_Rotate3f(g,degrees,x[0],x[1],x[2]):E_POINTER;}
static HRESULT WINAPI g_Scale3f(Geom*g,float x,float y,float z){(void)g;ensure_scene();float m[16];a3d_identity(m);m[0]=x;m[5]=y;m[10]=z;a3d_matmul(a3d_scene.matrix[a3d_scene.stack_level],m);return S_OK;}
static HRESULT WINAPI g_Scale3fv(Geom*g,const float*x){return x?g_Scale3f(g,x[0],x[1],x[2]):E_POINTER;}
/* The incoming primitive and current transform determine how vertices
 * become bounded scene geometry. The order in which the game submits
 * triangles matters; this is not an offline mesh import API. */
static HRESULT WINAPI g_Begin(Geom*g, DWORD x0){ensure_scene();a3d_scene_begin(&a3d_scene,x0);g->primitive=x0;static unsigned begin_log_count=0;
 if(begin_log_count++<12){char m[]="IA3dGeom.Begin 00000000";hexval(m+15,x0);logline(m);}return S_OK;}
static HRESULT WINAPI g_End(Geom*g){(void)g;ensure_scene();a3d_scene.primitive=0;a3d_scene.vcount=0;return S_OK;}
static HRESULT WINAPI g_Vertex3f(Geom*g, float a, float b, float c){(void)g;gvertex(a,b,c);return S_OK;}
static HRESULT WINAPI g_Vertex3fv(Geom*g, float *v){(void)g;if(!v)return E_POINTER;gvertex(v[0],v[1],v[2]);return S_OK;}
static HRESULT WINAPI g_Normal3f(Geom*g, DWORD x0, DWORD x1, DWORD x2){(void)g;(void)x0;(void)x1;(void)x2;/* Plane normal is derived from polygon vertices. */return S_OK;}
static HRESULT WINAPI g_Normal3fv(Geom*g, DWORD x0){(void)g;return x0?S_OK:E_POINTER;}
static HRESULT WINAPI g_Tag(Geom*g, DWORD x0){(void)g;ensure_scene();a3d_scene.tag=x0;return S_OK;}
static HRESULT WINAPI g_SetOpeningFactorf(Geom*g, DWORD x0){(void)g;(void)x0;return E_NOTIMPL;}
static HRESULT WINAPI g_SetOpeningFactorfv(Geom*g, DWORD x0){(void)g;(void)x0;return E_NOTIMPL;}
/* Materials are COM objects with independent lifetimes. Their acoustic coefficients
 * are stored for future geometry processing; no DSP is connected yet.
 * These method signatures follow the A3D 2.x ABI documented in the public SDK.
 */
typedef struct Material Material;
typedef struct MaterialVtbl {
 HRESULT (WINAPI *QueryInterface)(Material*,const GUID*,void**);
 ULONG (WINAPI *AddRef)(Material*);
 ULONG (WINAPI *Release)(Material*);
 HRESULT (WINAPI *Load)(Material*,const char*);
 HRESULT (WINAPI *Save)(Material*,const char*);
 HRESULT (WINAPI *Unserialize)(Material*,const void*,DWORD);
 HRESULT (WINAPI *Serialize)(Material*,void**,DWORD*);
 HRESULT (WINAPI *Duplicate)(Material*,Material**);
 HRESULT (WINAPI *SetNameID)(Material*,const char*);
 HRESULT (WINAPI *GetNameID)(Material*,char*,int);
 HRESULT (WINAPI *SelectPreset)(Material*,DWORD);
 HRESULT (WINAPI *GetClosestPreset)(Material*,DWORD*);
 HRESULT (WINAPI *SetReflectance)(Material*,float,float);
 HRESULT (WINAPI *GetReflectance)(Material*,float*,float*);
 HRESULT (WINAPI *SetTransmittance)(Material*,float,float);
 HRESULT (WINAPI *GetTransmittance)(Material*,float*,float*);
} MaterialVtbl;
struct Material {const MaterialVtbl *vt; volatile long ref; DWORD magic;
 float reflectance[2],transmittance[2]; char name[64];};
static const GUID iid_material=G(0xc398e565,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const DWORD material_magic=0x334d5441UL; /* 'ATM3' */
static const MaterialVtbl material_vt;
static Material *active_material=0;
IMPORT HANDLE WINAPI GetProcessHeap(void);
IMPORT void* WINAPI HeapAlloc(HANDLE,DWORD,DWORD);
IMPORT BOOL WINAPI HeapFree(HANDLE,DWORD,void*);
static ULONG WINAPI madd(Material*m){return (ULONG)InterlockedIncrement(&m->ref);}
static ULONG WINAPI mrel(Material*m){
 long n=InterlockedDecrement(&m->ref);
 if(n==0){m->magic=0;HeapFree(GetProcessHeap(),0,m);}
 return (ULONG)n;
}
/* Support IUnknown and log any requested material-specific IID until confirmed
 * against the SDK; do not manufacture support for unknown interfaces. */
static HRESULT WINAPI mqi(Material*m,const GUID*i,void**o){
 if(!o)return E_POINTER;*o=0;logguid("IA3dMaterial.QueryInterface",i);
 if(eqguid(i,&iid_unk)||eqguid(i,&iid_material)){*o=m;madd(m);return S_OK;}
 return E_NOINTERFACE;
}
static HRESULT WINAPI mduplicate(Material*m,Material**o){(void)m;if(o)*o=0;return E_NOTIMPL;}
static HRESULT WINAPI mload(Material*m,const char*p){(void)m;(void)p;return E_NOTIMPL;}
static HRESULT WINAPI msave(Material*m,const char*p){(void)m;(void)p;return E_NOTIMPL;}
static HRESULT WINAPI msetname(Material*m,const char*s){
 if(!s)return E_POINTER;
 int i=0;while(i<63 && s[i]){m->name[i]=s[i];i++;}m->name[i]=0;
 logline("IA3dMaterial.SetNameID");return S_OK;
}
static HRESULT WINAPI mgetname(Material*m,char*s,int capacity){
 if(!s)return E_POINTER;
 if(capacity<=0)return E_FAIL;
 int i=0;while(i<capacity-1 && m->name[i]){s[i]=m->name[i];i++;}s[i]=0;
 return m->name[i]?E_FAIL:S_OK;
}
static int valid_coeff(float a,float b){return a>=0.0f && a<=1.0f && b>=0.0f && b<=1.0f;}
static HRESULT WINAPI msetreflect(Material*m,float a,float b){
 if(!valid_coeff(a,b))return E_FAIL;
 m->reflectance[0]=a;m->reflectance[1]=b;
 log3("IA3dMaterial.SetReflectance",a,b,0.0f);return S_OK;
}
static HRESULT WINAPI mgetreflect(Material*m,float*a,float*b){
 if(!a||!b)return E_POINTER;*a=m->reflectance[0];*b=m->reflectance[1];return S_OK;
}
static HRESULT WINAPI msettrans(Material*m,float a,float b){
 if(!valid_coeff(a,b))return E_FAIL;
 m->transmittance[0]=a;m->transmittance[1]=b;
 log3("IA3dMaterial.SetTransmittance",a,b,0.0f);return S_OK;
}
static HRESULT WINAPI mgettrans(Material*m,float*a,float*b){
 if(!a||!b)return E_POINTER;*a=m->transmittance[0];*b=m->transmittance[1];return S_OK;
}
static HRESULT WINAPI mselect(Material*m,DWORD id){(void)m;(void)id;return E_NOTIMPL;}
static HRESULT WINAPI mclosest(Material*m,DWORD*id){(void)m;if(id)*id=0;return E_NOTIMPL;}
static HRESULT WINAPI mserialize(Material*m,void**p,DWORD*n){(void)m;if(p)*p=0;if(n)*n=0;return E_NOTIMPL;}
static HRESULT WINAPI munserialize(Material*m,const void*p,DWORD n){(void)m;(void)p;(void)n;return E_NOTIMPL;}
/* Slots 8, 12, 14 verified against mssa3d2.m3d code at RVA 0x2db3
 * (SetNameID) and RVA 0x20a6/0x20b9 (reflectance/transmittance). */
static const MaterialVtbl material_vt={mqi,madd,mrel,mload,msave,munserialize,
 mserialize,mduplicate,msetname,mgetname,mselect,mclosest,
 msetreflect,mgetreflect,msettrans,mgettrans};
static HRESULT WINAPI g_NewMaterial(Geom*g,void**out){
 (void)g;if(!out)return E_POINTER;*out=0;
 Material*m=(Material*)HeapAlloc(GetProcessHeap(),8,sizeof(Material));
 if(!m){logline("IA3dGeom.NewMaterial OOM");return E_FAIL;}
 m->vt=&material_vt;m->ref=1;m->magic=material_magic;
 m->reflectance[0]=1.0f;m->reflectance[1]=1.0f;
 m->transmittance[0]=0.0f;m->transmittance[1]=0.0f;
 *out=m;logline("IA3dGeom.NewMaterial => S_OK (diagnostic material object)");return S_OK;
}
static HRESULT WINAPI g_BindMaterial(Geom*g,void*ptr){
 (void)g;Material*m=(Material*)ptr;
 if(m && m->magic!=material_magic)return E_FAIL;
 if(m)madd(m);
 if(active_material)mrel(active_material);
 active_material=m;
 ensure_scene();if(m){a3d_scene.reflect[0]=m->reflectance[0];a3d_scene.reflect[1]=m->reflectance[1];a3d_scene.trans[0]=m->transmittance[0];a3d_scene.trans[1]=m->transmittance[1];}
 if(trace_detail())logline("IA3dGeom.BindMaterial => S_OK");return S_OK;
}
#include "geometry_lists.inc"
static HRESULT WINAPI g_BindListener(Geom*g){(void)g;return E_NOTIMPL;}
static HRESULT WINAPI g_BindSource(Geom*g, DWORD x0){(void)g;(void)x0;return E_NOTIMPL;}
static HRESULT WINAPI g_NewEnvironment(Geom*g, DWORD x0){(void)g;if(x0)*(void**)(unsigned long)x0=0;logline("IA3dGeom.NewEnvironment not implemented");return E_NOTIMPL;}
static HRESULT WINAPI g_BindEnvironment(Geom*g, DWORD x0){(void)g;(void)x0;return E_NOTIMPL;}
static HRESULT WINAPI g_SetRenderMode(Geom*g,DWORD mode){(void)g;ensure_scene();if(mode&~(A3D_SCENE_REFLECTIONS|A3D_SCENE_OCCLUSIONS))return E_INVALIDARG;a3d_scene.mode=mode;return S_OK;}
static HRESULT WINAPI g_GetRenderMode(Geom*g,DWORD*out){(void)g;if(!out)return E_POINTER;ensure_scene();*out=a3d_scene.mode;return S_OK;}
static HRESULT WINAPI g_SetPolygonBloatFactor(Geom*g, DWORD x0){(void)g;(void)x0;return E_NOTIMPL;}
static HRESULT WINAPI g_GetPolygonBloatFactor(Geom*g, DWORD x0){(void)g;(void)x0;if(x0)*(DWORD*)(unsigned long)x0=0;return E_NOTIMPL;}
static HRESULT WINAPI g_SetReflectionUpdateInterval(Geom*g, DWORD x0){(void)g;(void)x0;return E_NOTIMPL;}
static HRESULT WINAPI g_GetReflectionUpdateInterval(Geom*g, DWORD x0){(void)g;(void)x0;if(x0)*(DWORD*)(unsigned long)x0=0;return E_NOTIMPL;}
static HRESULT WINAPI g_SetOcclusionUpdateInterval(Geom*g, DWORD x0){(void)g;(void)x0;return E_NOTIMPL;}
static HRESULT WINAPI g_GetOcclusionUpdateInterval(Geom*g, DWORD x0){(void)g;(void)x0;if(x0)*(DWORD*)(unsigned long)x0=0;return E_NOTIMPL;}
static void* geom_vt[]={ (void*)gqi,(void*)gadd,(void*)grel,
 (void*)g_Enable,
 (void*)g_Disable,
 (void*)g_IsEnabled,
 (void*)g_SetOcclusionMode,
 (void*)g_GetOcclusionMode,
 (void*)g_SetReflectionMode,
 (void*)g_GetReflectionMode,
 (void*)g_SetReflectionGainScale,
 (void*)g_GetReflectionGainScale,
 (void*)g_SetReflectionDelayScale,
 (void*)g_GetReflectionDelayScale,
 (void*)g_PushMatrix,
 (void*)g_PopMatrix,
 (void*)g_LoadIdentity,
 (void*)g_LoadMatrix,
 (void*)g_GetMatrix,
 (void*)g_MultMatrix,
 (void*)g_Translate3f,
 (void*)g_Translate3fv,
 (void*)g_Rotate3f,
 (void*)g_Rotate3fv,
 (void*)g_Scale3f,
 (void*)g_Scale3fv,
 (void*)g_Begin,
 (void*)g_End,
 (void*)g_Vertex3f,
 (void*)g_Vertex3fv,
 (void*)g_Normal3f,
 (void*)g_Normal3fv,
 (void*)g_Tag,
 (void*)g_SetOpeningFactorf,
 (void*)g_SetOpeningFactorfv,
 (void*)g_NewMaterial,
 (void*)g_BindMaterial,
 (void*)g_NewList,
 (void*)g_BindListener,
 (void*)g_BindSource,
 (void*)g_NewEnvironment,
 (void*)g_BindEnvironment,
 (void*)g_SetRenderMode,
 (void*)g_GetRenderMode,
 (void*)g_SetPolygonBloatFactor,
 (void*)g_GetPolygonBloatFactor,
 (void*)g_SetReflectionUpdateInterval,
 (void*)g_GetReflectionUpdateInterval,
 (void*)g_SetOcclusionUpdateInterval,
 (void*)g_GetOcclusionUpdateInterval,
};
static Geom geom={geom_vt,1,0};
static HRESULT WINAPI gqi(Geom*g,const GUID*i,void**o){
 if(!o)return E_POINTER;*o=0;logguid("IA3dGeom.QueryInterface",i);
 if(eqguid(i,&iid_unk)||eqguid(i,&iid_geom)){*o=g;gadd(g);return S_OK;}
 return E_NOINTERFACE;
}
