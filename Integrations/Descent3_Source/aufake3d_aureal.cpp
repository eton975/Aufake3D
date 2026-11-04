/* SPDX-License-Identifier: MIT
 * Experimental replacement for the missing Descent 3 A3D_* helper layer.
 * For source-built Descent 3 only. NOT part of original retail game or a
 * drop-in retail executable compatibility claim. No vendor DLLs or SDK code.
 * Link into GPL Descent 3 builds only under their applicable licence terms.
 *
 * Windows x86 only: loads the local a3dapi.dll by its genuine COM class
 * factory and calls real IA3d4, IA3dSource, IA3dListener, IA3dGeom methods.
 * No registry, patching, process injection or fake sound providers.
 */
#ifdef AUFAKE3D_ADAPTER_STANDALONE
/* Only for syntax/ABI compilation in the project CI (without Descent 3). */
typedef unsigned long DWORD;
typedef unsigned short WORD;
typedef void *HANDLE;
typedef void *HWND;
typedef void *HMODULE;
typedef unsigned int uint;
typedef unsigned short ushort;
struct vector {float x,y,z;};
struct matrix {vector rvec,uvec,fvec;};
extern "C" __declspec(dllimport) HMODULE __stdcall LoadLibraryA(const char *);
extern "C" __declspec(dllimport) void *__stdcall GetProcAddress(HMODULE,const char *);
extern "C" __declspec(dllimport) int __stdcall FreeLibrary(HMODULE);
#else
#include "auddev.h"
#ifndef SUPPORT_AUREAL
#error "The Descent 3 source build must enable SUPPORT_AUREAL"
#endif
#endif

typedef long A3dResult;
typedef unsigned long A3dRefcount;
typedef struct {DWORD d1;WORD d2,d3;unsigned char d4[8];} A3dGuid;
#define AG(a,b,c,d,e,f,g,h,i,j,k) {a,b,c,{d,e,f,g,h,i,j,k}}
static const A3dGuid CLS_A3dApi=AG(0x92fa2c24,0x253c,0x11d2,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const A3dGuid IID_Factory=AG(1,0,0,0xc0,0,0,0,0,0,0,0x46);
static const A3dGuid IID_A3d4=AG(0xe4c40280,0xccba,0x11d2,0x9d,0xcf,0,0x50,0x04,0x11,0x58,0x2f);
static const A3dGuid IID_Geometry=AG(0xc398e561,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const A3dGuid IID_Listener=AG(0xc398e563,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
struct A3dObj {void **vt;};
typedef A3dResult (__stdcall *A3dFactoryFn)(const A3dGuid*,const A3dGuid*,void**);
typedef A3dResult (__stdcall *A3dCreateFn)(A3dObj*,void*,const A3dGuid*,void**);
typedef A3dResult (__stdcall *A3dQueryFn)(A3dObj*,const A3dGuid*,void**);
typedef A3dRefcount (__stdcall *A3dReleaseFn)(A3dObj*);
typedef A3dResult (__stdcall *A3dNoargFn)(A3dObj*);
typedef A3dResult (__stdcall *A3dUintFn)(A3dObj*,DWORD);
typedef A3dResult (__stdcall *A3dUintOutFn)(A3dObj*,DWORD*);
typedef A3dResult (__stdcall *A3dInitFn)(A3dObj*,A3dGuid*,DWORD,DWORD);
typedef A3dResult (__stdcall *A3dNewSourceFn)(A3dObj*,DWORD,A3dObj**);
typedef A3dResult (__stdcall *A3dDupSourceFn)(A3dObj*,A3dObj*,A3dObj**);
typedef A3dResult (__stdcall *A3dOutFn)(A3dObj*,void**);
typedef A3dResult (__stdcall *A3dFloatFn)(A3dObj*,float);
typedef A3dResult (__stdcall *A3dGetFloatFn)(A3dObj*,float*);
typedef A3dResult (__stdcall *A3dFloat2Fn)(A3dObj*,float,float);
typedef A3dResult (__stdcall *A3dVec3Fn)(A3dObj*,float,float,float);
typedef A3dResult (__stdcall *A3dVec3OutFn)(A3dObj*,float*,float*,float*);
typedef A3dResult (__stdcall *A3dVec6Fn)(A3dObj*,float,float,float,float,float,float);
typedef A3dResult (__stdcall *A3dVec6OutFn)(A3dObj*,float*,float*,float*,float*,float*,float*);
typedef A3dResult (__stdcall *A3dDistanceFn)(A3dObj*,float,float,DWORD);
typedef A3dResult (__stdcall *A3dWaveFmtFn)(A3dObj*,const void*);
typedef A3dResult (__stdcall *A3dSizeFn)(A3dObj*,int);
typedef A3dResult (__stdcall *A3dLockFn)(A3dObj*,DWORD,DWORD,void**,DWORD*,void**,DWORD*,DWORD);
typedef A3dResult (__stdcall *A3dUnlockFn)(A3dObj*,void*,DWORD,void*,DWORD);
typedef A3dResult (__stdcall *A3dPanFn)(A3dObj*,DWORD,float*);
typedef A3dResult (__stdcall *A3dWaveEventFn)(A3dObj*,DWORD,HANDLE);
typedef A3dResult (__stdcall *A3dBindFn)(A3dObj*,A3dObj*);
#define ACALL(o,index,type) ((type)((o)->vt[index]))
static A3dObj *d3root=0,*d3geom=0,*d3lis=0;
static HMODULE d3module=0;
#define D3_LIST_COUNT 512
static A3dObj *d3lists[D3_LIST_COUNT];
static A3dObj *d3temp=0;
static A3dObj* obj(void*p){return (A3dObj*)p;}
static int passed(A3dResult r){return r>=0;}
static void release(A3dObj*&p){if(p){ACALL(p,2,A3dReleaseFn)(p);p=0;}}

bool A3D_Init(HWND hwnd){
 if(d3root)return true;
 d3module=LoadLibraryA("a3dapi.dll");if(!d3module)return false;
 A3dFactoryFn get=(A3dFactoryFn)GetProcAddress(d3module,"DllGetClassObject");
 if(!get){FreeLibrary(d3module);d3module=0;return false;}
 A3dObj *fac=0;
 if(!passed(get(&CLS_A3dApi,&IID_Factory,(void**)&fac))||!fac){FreeLibrary(d3module);d3module=0;return false;}
 A3dResult r=ACALL(fac,3,A3dCreateFn)(fac,0,&IID_A3d4,(void**)&d3root);
 release(fac);
 if(!passed(r)||!d3root){FreeLibrary(d3module);d3module=0;return false;}
 /* 0x42 requests known A3D 2.0 geometry features, not a fake provider. */
 r=ACALL(d3root,15,A3dInitFn)(d3root,0,0x42,0);
 if(!passed(r)){release(d3root);FreeLibrary(d3module);d3module=0;return false;}
 (void)hwnd; /* no stolen HWND, registry or DirectSound device */
 return true;
}
void A3D_DestroyGeometryInterface();
void A3D_Destroy(){
 A3D_DestroyGeometryInterface();release(d3lis);
 if(d3root){ACALL(d3root,40,A3dNoargFn)(d3root);release(d3root);}
 if(d3module){FreeLibrary(d3module);d3module=0;}
}
void A3D_SetUnitsPerMeter(float value){if(d3root)ACALL(d3root,32,A3dFloatFn)(d3root,value);}
void A3D_SetRolloffFactor(float value){if(d3root)ACALL(d3root,36,A3dFloatFn)(d3root,value);}
void A3D_SetDopplerFactor(float value){if(d3root)ACALL(d3root,34,A3dFloatFn)(d3root,value);}
bool A3D_CreateListener(){
 if(d3lis)return true;if(!d3root)return false;
 return passed(ACALL(d3root,0,A3dQueryFn)(d3root,&IID_Listener,(void**)&d3lis))&&d3lis;
}
void A3D_SetListenerVelocity(float x,float y,float z){if(d3lis)ACALL(d3lis,15,A3dVec3Fn)(d3lis,x,y,z);}
void A3D_SetListenerPosition(float x,float y,float z){if(d3lis)ACALL(d3lis,3,A3dVec3Fn)(d3lis,x,y,z);}
void A3D_SetListenerOrient(vector*f,vector*u){
 if(d3lis&&f&&u)ACALL(d3lis,11,A3dVec6Fn)(d3lis,f->x,f->y,f->z,u->x,u->y,u->z);
}

struct D3WaveFormat {WORD tag,channels;DWORD rate,avg;WORD align,bits,extra;};
void *A3D_CreateSSource(int size,int bps,bool stereo,bool streaming,ushort freq,bool is3d){
 if(!d3root||size<=0||(bps!=8&&bps!=16)||!freq)return 0;
 A3dObj*s=0;
 if(!passed(ACALL(d3root,17,A3dNewSourceFn)(d3root,0,&s))||!s)return 0;
 D3WaveFormat w={1,(WORD)(stereo?2:1),freq,0,0,(WORD)bps,0};
 w.align=(WORD)(w.channels*(bps/8));w.avg=freq*w.align;
 if(!passed(ACALL(s,7,A3dWaveFmtFn)(s,&w))||
    !passed(ACALL(s,5,A3dSizeFn)(s,size))){release(s);return 0;}
 /* Head-relative coordinates for menu/stereo sources. */
 if(!is3d)ACALL(s,61,A3dUintFn)(s,1u);
 (void)streaming; /* both types use bounded mutable PCM rings */
 return s;
}
void *A3D_DuplicateSource(void*source){
 if(!d3root||!source)return 0;A3dObj*out=0;
 if(!passed(ACALL(d3root,18,A3dDupSourceFn)(d3root,obj(source),&out)))return 0;
 return out;
}
void A3D_FreeSSource(void*p){A3dObj*s=obj(p);release(s);}
bool A3D_LoadSample(void*p,void*data,int size){
 if(!p||!data||size<=0)return false;
 void*a=0,*b=0;DWORD na=0,nb=0;
 A3dObj*s=obj(p);
 if(!passed(ACALL(s,11,A3dLockFn)(s,0,(DWORD)size,&a,&na,&b,&nb,0)))return false;
 unsigned char*in=(unsigned char*)data;
 if(a)for(DWORD i=0;i<na;i++)((unsigned char*)a)[i]=in[i];
 if(b)for(DWORD i=0;i<nb;i++)((unsigned char*)b)[i]=in[na+i];
 return passed(ACALL(s,12,A3dUnlockFn)(s,a,na,b,nb));
}
void A3D_Play(void*p,bool looping){if(p)ACALL(obj(p),13,A3dUintFn)(obj(p),looping?1:0);}
void A3D_Stop(void*p){if(p)ACALL(obj(p),14,A3dNoargFn)(obj(p));}
void A3D_GetCurrentPosition(void*p,uint*at){
 if(at)*at=0;
 if(p&&at)ACALL(obj(p),19,A3dUintOutFn)(obj(p),(DWORD*)at);
}
void A3D_SetCurrentPosition(void*p,uint at){if(p)ACALL(obj(p),18,A3dUintFn)(obj(p),(DWORD)at);}
void A3D_SetSourcePriority(void*p,float f){if(p)ACALL(obj(p),50,A3dFloatFn)(obj(p),f);}
void A3D_SetSourcePan(void*p,float left,float right){
 if(p){float vals[2]={left,right};ACALL(obj(p),57,A3dPanFn)(obj(p),2,vals);}
}
void A3D_GetSourcePan(void*p,float*left,float*right){
 if(left)*left=1.0f;if(right)*right=1.0f;
 if(!p||!left||!right)return;
 float vals[2]={1.0f,1.0f};
 if(passed(ACALL(obj(p),58,A3dPanFn)(obj(p),2,vals))){*left=vals[0];*right=vals[1];}
}
void A3D_SetSourceVolume(void*p,float value){if(p)ACALL(obj(p),40,A3dFloatFn)(obj(p),value);}
float A3D_GetSourceVolume(void*p){float f=0.0f;
 if(p)ACALL(obj(p),41,A3dGetFloatFn)(obj(p),&f);return f;}
void A3D_SetSourceCone(void*p,float a,float b,float c){if(p)ACALL(obj(p),36,A3dVec3Fn)(obj(p),a,b,c);}
void A3D_SetSourceVelocity(void*p,float a,float b,float c){if(p)ACALL(obj(p),32,A3dVec3Fn)(obj(p),a,b,c);}
void A3D_GetSourceVelocity(void*p,vector*v){if(p&&v)ACALL(obj(p),33,A3dVec3OutFn)(obj(p),&v->x,&v->y,&v->z);}
void A3D_SetSourcePosition(void*p,float a,float b,float c){if(p)ACALL(obj(p),20,A3dVec3Fn)(obj(p),a,b,c);}
void A3D_GetSourcePosition(void*p,vector*v){if(p&&v)ACALL(obj(p),21,A3dVec3OutFn)(obj(p),&v->x,&v->y,&v->z);}
void A3D_SetSourceOrientation(void*p,const vector*f,const vector*u){
 if(p&&f&&u)ACALL(obj(p),28,A3dVec6Fn)(obj(p),f->x,f->y,f->z,u->x,u->y,u->z);
}
void A3D_GetSourceOrientation(void*p,matrix*out){
 if(!p||!out)return;
 ACALL(obj(p),29,A3dVec6OutFn)(obj(p),&out->fvec.x,&out->fvec.y,&out->fvec.z,
   &out->uvec.x,&out->uvec.y,&out->uvec.z);
 /* Right vector derived from forward x up. */
 out->rvec.x=out->fvec.y*out->uvec.z-out->fvec.z*out->uvec.y;
 out->rvec.y=out->fvec.z*out->uvec.x-out->fvec.x*out->uvec.z;
 out->rvec.z=out->fvec.x*out->uvec.y-out->fvec.y*out->uvec.x;
}
void A3D_SetMinMaxDistance(void*p,float lo,float hi,bool mute_max){
 if(p)ACALL(obj(p),38,A3dDistanceFn)(obj(p),lo,hi,mute_max?1:0);
}
bool A3D_SetSourceWaveEvent(void*p,DWORD point,HANDLE h){
 return p&&passed(ACALL(obj(p),59,A3dWaveEventFn)(obj(p),point,h));
}
bool A3D_ClearSourceWaveEvents(void*p){return p&&passed(ACALL(obj(p),60,A3dNoargFn)(obj(p)));}
int A3D_GetSourceStatus(void*p){DWORD status=0;
 if(p)ACALL(obj(p),56,A3dUintOutFn)(obj(p),&status);return (int)status;}
bool A3D_Lock(void*p,DWORD at,DWORD size,void**a,DWORD*na,void**b,DWORD*nb){
 return p&&passed(ACALL(obj(p),11,A3dLockFn)(obj(p),at,size,a,na,b,nb,0));
}
bool A3D_Unlock(void*p,void*a,DWORD na,void*b,DWORD nb){
 return p&&passed(ACALL(obj(p),12,A3dUnlockFn)(obj(p),a,na,b,nb));
}
bool A3D_SetEnvironmentalReverb(float volume,float damping,float decay){
 (void)volume;(void)damping;(void)decay;return false; /* not emulated */
}

bool A3D_CreateGeometryInterface(){
 if(d3geom)return true;if(!d3root)return false;
 if(!passed(ACALL(d3root,0,A3dQueryFn)(d3root,&IID_Geometry,(void**)&d3geom))||!d3geom)return false;
 ACALL(d3geom,3,A3dUintFn)(d3geom,0x42u);return true;
}
void A3D_DestroyGeometryInterface(){
 for(int i=0;i<D3_LIST_COUNT;i++)release(d3lists[i]);
 release(d3temp);release(d3geom);
}
static A3dObj*& list_slot(int id){return id>=0&&id<D3_LIST_COUNT?d3lists[id]:d3temp;}
void A3D_GeomListStart(int id){
 if(!d3geom)return;
 A3dObj*&v=list_slot(id);release(v);
 if(passed(ACALL(d3geom,37,A3dOutFn)(d3geom,(void**)&v))&&v)
  ACALL(v,3,A3dNoargFn)(v);
}
void A3D_GeomListEnd(int id){A3dObj*v=list_slot(id);if(v)ACALL(v,4,A3dNoargFn)(v);}
void A3D_GeomListExec(int id){A3dObj*v=list_slot(id);if(v)ACALL(v,5,A3dNoargFn)(v);}
void A3D_Clear(){if(d3root)ACALL(d3root,12,A3dNoargFn)(d3root);}
void A3D_Flush(){if(d3root)ACALL(d3root,13,A3dNoargFn)(d3root);}
void A3D_StartFrame(){} /* root A3D2 COM has no StartFrame operation */
void A3D_EndFrame(){A3D_Flush();}
void A3D_GeomAddListener(vector*pos,matrix*orient){
 if(pos)A3D_SetListenerPosition(pos->x,pos->y,pos->z);
 if(orient)A3D_SetListenerOrient(&orient->fvec,&orient->uvec);
}
void A3D_GeomAddSource(void*p,vector*pos,matrix*orient){
 if(p&&pos)A3D_SetSourcePosition(p,pos->x,pos->y,pos->z);
 if(p&&orient)A3D_SetSourceOrientation(p,&orient->fvec,&orient->uvec);
}
void A3D_GeomBindMaterial(void*p){if(d3geom)ACALL(d3geom,36,A3dBindFn)(d3geom,obj(p));}
static void add_poly(unsigned tag,vector**vs,int count){
 if(!d3geom||!vs)return;
 ACALL(d3geom,32,A3dUintFn)(d3geom,tag);
 if(!passed(ACALL(d3geom,26,A3dUintFn)(d3geom,(DWORD)count)))return;
 for(int i=0;i<count;i++)if(vs[i])ACALL(d3geom,28,A3dVec3Fn)(d3geom,vs[i]->x,vs[i]->y,vs[i]->z);
 ACALL(d3geom,27,A3dNoargFn)(d3geom);
}
void A3D_GeomAddTriangle(unsigned tag,vector**v){add_poly(tag,v,3);}
void A3D_GeomAddQuad(unsigned tag,vector**v){add_poly(tag,v,4);}
void* A3D_CreateMaterial(float tg,float th,float rg,float rh){
 if(!d3geom)return 0;A3dObj*m=0;
 if(!passed(ACALL(d3geom,35,A3dOutFn)(d3geom,(void**)&m))||!m)return 0;
 if(!passed(ACALL(m,14,A3dFloat2Fn)(m,tg,th))||
    !passed(ACALL(m,12,A3dFloat2Fn)(m,rg,rh))){release(m);return 0;}
 return m;
}
void A3D_DestroyMaterial(void*p){A3dObj*m=obj(p);release(m);}
