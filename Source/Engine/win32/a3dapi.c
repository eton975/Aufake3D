/* v0.6.12 RELEASE SOURCE MAP
 * This is the single A3D 2.x translation unit for all three game profiles.
 * Included .inc units share private types; do not compile them separately.
 * source_probe.inc implements sources, stream_winmm.inc owns the waveOut
 * worker, and stream_core.h contains portable sample rendering. Profiles
 * select behavior through environment variables rather than forked DLLs.
 * ABI rule: preserve vtable order, x86 stdcall decoration and 32-bit DWORD.
 */
/* v0.5.0 SOURCE COMMENTARY — A3D 2.x COM shim and root-object implementation
 * Defines GUIDs and IA3d3/IA3d4 vtables, validates COM QueryInterface requests, manages
 * reference counts and forwards listener, geometry and source methods to included
 * implementation units. Vtable slot order and 32-bit stdcall signatures are ABI-
 * critical. The software playback path is an approximation, not a vendor-compatible
 * copy of an AU8830 hardware driver.
 */
/* Independently written A3D 1.x/2.x COM compatibility implementation.
 * The WaveOut renderer has passed scoped Alice 2011 listening tests; this
 * is NOT a complete hardware-accurate Aureal or A3D 3.0 emulation.
 * Freestanding Clang/LLD Win32 build; no original Aureal binaries bundled.
 */
typedef unsigned long DWORD;
typedef long HRESULT;
typedef unsigned long ULONG;
typedef int BOOL;
typedef void* HANDLE;
typedef const char* LPCSTR;
typedef unsigned short WORD;
#define WINAPI __attribute__((stdcall))
#define EXPORT __declspec(dllexport)
#define IMPORT __declspec(dllimport)
#define S_OK ((HRESULT)0)
#define S_FALSE ((HRESULT)1)
#define E_FAIL ((HRESULT)0x80004005L)
#define E_NOINTERFACE ((HRESULT)0x80004002L)
#define E_POINTER ((HRESULT)0x80004003L)
#define E_NOTIMPL ((HRESULT)0x80004001L)
#define CLASS_E_CLASSNOTAVAILABLE ((HRESULT)0x80040111L)
#define CLASS_E_NOAGGREGATION ((HRESULT)0x80040110L)
#define FILE_APPEND_DATA 4UL
#define FILE_SHARE_READ 1UL
#define FILE_SHARE_WRITE 2UL
#define OPEN_ALWAYS 4UL
#define FILE_ATTRIBUTE_NORMAL 128UL
#define INVALID_HANDLE_VALUE ((HANDLE)(-1))

IMPORT HANDLE WINAPI CreateFileA(LPCSTR,DWORD,DWORD,void*,DWORD,DWORD,HANDLE);
IMPORT BOOL WINAPI WriteFile(HANDLE,const void*,DWORD,DWORD*,void*);
IMPORT BOOL WINAPI CloseHandle(HANDLE);
IMPORT DWORD WINAPI GetEnvironmentVariableA(LPCSTR,char*,DWORD);
IMPORT long WINAPI InterlockedIncrement(volatile long*);
IMPORT long WINAPI InterlockedDecrement(volatile long*);
IMPORT long WINAPI InterlockedCompareExchange(volatile long*,long,long);

typedef struct { DWORD d1; WORD d2,d3; unsigned char d4[8]; } GUID;
#define G(a,b,c,d,e,f,g,h,i,j,k) {a,b,c,{d,e,f,g,h,i,j,k}}
static const GUID iid_unk = G(0x00000000,0,0,0xc0,0,0,0,0,0,0,0x46);
static const GUID iid_factory = G(0x00000001,0,0,0xc0,0,0,0,0,0,0,0x46);
static const GUID clsid_a3dapi = G(0x92fa2c24,0x253c,0x11d2,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
/* IA3d and IA3d2 have the same documented control-method prefix as IA3d3.
 * Exposing these views of the API-class root preserves COM identity. This does
 * not implement the separate legacy CLSID/DirectSound3D rendering pipeline. */
static const GUID iid_ia3d1=G(0xd8f1eee1,0xf634,0x11cf,0x87,0,0,0xa0,0x24,0x5d,0x91,0x8b);
static const GUID iid_ia3d2=G(0xfb80d1e0,0x98d3,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID iid_ia3d3 = G(0xc398e560,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
/* IA3d4 is the actual root interface requested by Alice's Miles A3D2 provider. */
static const GUID iid_ia3d4 = G(0xe4c40280,0xccba,0x11d2,0x9d,0xcf,0x00,0x50,0x04,0x11,0x58,0x2f);
static volatile long locks=0;
int _fltused=0;
static int eqguid(const GUID*a,const GUID*b){
 if(!a||!b)return 0;
 if(a->d1!=b->d1||a->d2!=b->d2||a->d3!=b->d3)return 0;
 for(int n=0;n<8;n++)if(a->d4[n]!=b->d4[n])return 0;
 return 1;
}
static DWORD cstrlen(const char*s){DWORD n=0;if(!s)return 0;while(s[n])n++;return n;}
/* Detailed sample/position trace is opt-in: synchronous file operations on the
 * game's timing-critical callbacks caused avoidable overhead in v0.4.1. */
static int trace_detail(void){
 static int state=-1;
 if(state<0){char flag[8]={0};GetEnvironmentVariableA("A3D_TRACE_DETAIL",flag,sizeof(flag));state=(flag[0]=='1')?1:0;}
 return state;
}
/* Strict bounded decimal parser for user-supplied tuning environment values.
 * No CRT dependency; invalid values keep the normal defaults. */
/* REVIEW NOTE — a3d_tuning_env: Configuration parser: deliberately reject malformed/out-of-range values rather than silently accepting arbitrary strings. */
static float a3d_tuning_env(const char *key,float fallback,float low,float high){
 char buf[32]={0};DWORD n=GetEnvironmentVariableA(key,buf,sizeof(buf));
 if(!n||n>=sizeof(buf))return fallback;
 unsigned i=0,digits=0;float value=0.0f,denom=1.0f;int frac=0;
 for(;i<n;i++){
  unsigned char c=(unsigned char)buf[i];
  if(c=='.' && !frac){frac=1;continue;}
  if(c<'0'||c>'9')return fallback;
  if(++digits>8)return fallback;
  if(!frac)value=value*10.0f+(float)(c-'0');
  else{denom*=10.0f;value+=(float)(c-'0')/denom;}
 }
 if(!digits||value<low||value>high)return fallback;
 return value;
}
/* v0.6.6 release logging policy: no file I/O unless A3D_LOG=1.
 * When opted in, truncate the diagnostic log on the first message of each
 * process and enforce an absolute, per-process 1 MiB byte budget. This is
 * intentionally independent of event frequency: an unattended session
 * cannot write unlimited data. A3D_TRACE_DETAIL also requires A3D_LOG=1. */
#define A3D_LOG_LIMIT_BYTES (1024u*1024u)
#define GENERIC_WRITE 0x40000000UL
#define CREATE_ALWAYS 2UL
static int a3d_log_gate=-1,a3d_log_created=0;
/* Atomic byte reservations keep the cap valid even with concurrent COM calls. */
static volatile long a3d_log_bytes=0;
static int a3d_log_enabled(void){
 if(a3d_log_gate<0){
  char option[8]={0};
  DWORD n=GetEnvironmentVariableA("A3D_LOG",option,sizeof(option));
  a3d_log_gate=(n==1 && option[0]=='1')?1:0;
 }
 return a3d_log_gate;
}
/* Diagnostic logging is synchronous and deliberately opt-in, not a
 * scheduling primitive. The per-process 1 MiB reservation prevents unbounded
 * log growth; avoid adding this call to the WaveOut real-time path. */
static void logline(const char *s){
 if(!a3d_log_enabled()||!s)return;
 DWORD len=cstrlen(s);
 if(len==0||len+2u>A3D_LOG_LIMIT_BYTES)return;
 for(;;){
  long old=a3d_log_bytes;
  if(old<0||(DWORD)old>A3D_LOG_LIMIT_BYTES-(len+2u))return;
  if(InterlockedCompareExchange(&a3d_log_bytes,old+(long)(len+2u),old)==old)break;
 }
 char filename[512];
 DWORD n=GetEnvironmentVariableA("A3D_PROBE_LOG",filename,(DWORD)sizeof(filename));
 const char *path=(n>0 && n<(DWORD)sizeof(filename))?filename:"a3d2-probe.log";
 int first=!a3d_log_created;
 HANDLE h=CreateFileA(path,first?GENERIC_WRITE:FILE_APPEND_DATA,
  FILE_SHARE_READ|FILE_SHARE_WRITE,0,first?CREATE_ALWAYS:OPEN_ALWAYS,
  FILE_ATTRIBUTE_NORMAL,0);
 if(h==INVALID_HANDLE_VALUE)return;
 a3d_log_created=1;
 DWORD written=0,ending=0;
 BOOL ok=WriteFile(h,s,len,&written,0);
 if(ok&&written==len)ok=WriteFile(h,"\r\n",2,&ending,0);
 CloseHandle(h);
 /* Reservation stays charged even on write failures. The counter is
  * monotonically increasing, never overflowing or allowing a larger log. */
 (void)ok; (void)ending;
}
static void logguid(const char*tag,const GUID*g){
 const char hexdig[]="0123456789abcdef";
 unsigned char a[16];char buf[96];int p=0,i;
 const char* t=tag;while(*t&&p<50)buf[p++]=*t++;
 buf[p++]=' ';
 if(!g){buf[p++]='?';buf[p]=0;logline(buf);return;}
 a[0]=(unsigned char)(g->d1>>24);a[1]=(unsigned char)(g->d1>>16);a[2]=(unsigned char)(g->d1>>8);a[3]=(unsigned char)g->d1;
 a[4]=(unsigned char)(g->d2>>8);a[5]=(unsigned char)g->d2;
 a[6]=(unsigned char)(g->d3>>8);a[7]=(unsigned char)g->d3;
 for(i=0;i<8;i++)a[i+8]=g->d4[i];
 for(i=0;i<16;i++){
  if(i==4||i==6||i==8||i==10)buf[p++]='-';
  buf[p++]=hexdig[a[i]>>4];buf[p++]=hexdig[a[i]&15];
 }
 buf[p]=0;logline(buf);
}

/* ABI ownership map (Win32 x86, COM):
 * A3D root exposes the documented IA3d1/2/3/4 prefix and the IA3d4 tail.
 * The vtable is a serialized external binary contract: do not reorder members,
 * change WINAPI calling convention, GUIDs, or signed HRESULT widths.
 * QueryInterface success must return an AddRef'd view; unsupported versions
 * (notably IA3d5/A3D3) must never be silently advertised as implemented.
 * See Docs/COM_ABI_AND_LIFETIMES.md before modifying an interface method. */
typedef struct A3D A3D;
typedef struct {
 DWORD dwSize,dwVersion,dwFlags,dwReserved,dwReserved2;
 DWORD dwOutputChannels,dwMinSampleRate,dwMaxSampleRate,dwMax2DBuffers,dwMax3DBuffers;
} SoftwareCaps;
typedef struct {
 DWORD dwSize,dwFlags,dwReserved,dwReserved2;
 DWORD dwOutputChannels,dwMinSampleRate,dwMaxSampleRate,dwMax2DBuffers,dwMax3DBuffers;
} HardwareCaps;
typedef struct {
 HRESULT (WINAPI *QueryInterface)(A3D*,const GUID*,void**);
 ULONG (WINAPI *AddRef)(A3D*); ULONG (WINAPI *Release)(A3D*);
 HRESULT (WINAPI *SetOutputMode)(A3D*,DWORD,DWORD,DWORD);
 HRESULT (WINAPI *GetOutputMode)(A3D*,DWORD*,DWORD*,DWORD*);
 HRESULT (WINAPI *SetResourceManagerMode)(A3D*,DWORD);
 HRESULT (WINAPI *GetResourceManagerMode)(A3D*,DWORD*);
 HRESULT (WINAPI *SetHFAbsorbFactor)(A3D*,float);
 HRESULT (WINAPI *GetHFAbsorbFactor)(A3D*,float*);
 HRESULT (WINAPI *RegisterVersion)(A3D*,DWORD);
 HRESULT (WINAPI *GetSoftwareCaps)(A3D*,SoftwareCaps*);
 HRESULT (WINAPI *GetHardwareCaps)(A3D*,HardwareCaps*);
 HRESULT (WINAPI *Clear)(A3D*); HRESULT (WINAPI *Flush)(A3D*);
 HRESULT (WINAPI *Compat)(A3D*,DWORD,DWORD);
 HRESULT (WINAPI *Init)(A3D*,GUID*,DWORD,DWORD);
 HRESULT (WINAPI *IsFeatureAvailable)(A3D*,DWORD);
 HRESULT (WINAPI *NewSource)(A3D*,DWORD,void**);
 HRESULT (WINAPI *DuplicateSource)(A3D*,void*,void**);
 HRESULT (WINAPI *SetCooperativeLevel)(A3D*,void*,DWORD);
 HRESULT (WINAPI *GetCooperativeLevel)(A3D*,DWORD*);
 HRESULT (WINAPI *SetMaxReflectionDelayTime)(A3D*,float);
 HRESULT (WINAPI *GetMaxReflectionDelayTime)(A3D*,float*);
 HRESULT (WINAPI *SetCoordinateSystem)(A3D*,DWORD);
 HRESULT (WINAPI *GetCoordinateSystem)(A3D*,DWORD*);
 HRESULT (WINAPI *SetOutputGain)(A3D*,float);
 HRESULT (WINAPI *GetOutputGain)(A3D*,float*);
 HRESULT (WINAPI *SetNumFallbackSources)(A3D*,DWORD);
 HRESULT (WINAPI *GetNumFallbackSources)(A3D*,DWORD*);
 /* IA3d4 extension. This must follow IA3d3 entries in exact ABI order. */
 HRESULT (WINAPI *SetRMPriorityBias)(A3D*,float);
 HRESULT (WINAPI *GetRMPriorityBias)(A3D*,float*);
 HRESULT (WINAPI *DisableViewer)(A3D*);
 HRESULT (WINAPI *SetUnitsPerMeter)(A3D*,float);
 HRESULT (WINAPI *GetUnitsPerMeter)(A3D*,float*);
 HRESULT (WINAPI *SetDopplerScale)(A3D*,float);
 HRESULT (WINAPI *GetDopplerScale)(A3D*,float*);
 HRESULT (WINAPI *SetDistanceModelScale)(A3D*,float);
 HRESULT (WINAPI *GetDistanceModelScale)(A3D*,float*);
 HRESULT (WINAPI *SetEq)(A3D*,float);
 HRESULT (WINAPI *GetEq)(A3D*,float*);
 HRESULT (WINAPI *Shutdown)(A3D*);
 HRESULT (WINAPI *RegisterApp)(A3D*,const GUID*);
} A3DVtbl;
struct A3D {const A3DVtbl*vt; volatile long ref; DWORD mode[3],res,cooperative,coords,falls; float hfa,delay,gain; float rm_bias, units, doppler, distance, eq;};
static const A3DVtbl av;
static A3D root={&av,1,{0,0,0},0,0,0,0,0.0f,0.0f,1.0f,0.5f,1.0f,1.0f,1.0f,0.0f};
static ULONG WINAPI aadd(A3D*s){return (ULONG)InterlockedIncrement(&s->ref);}
static void mixer_shutdown(void);
static ULONG WINAPI arel(A3D*s){
 long n=InterlockedDecrement(&s->ref);
 if(n<1){s->ref=1;return 1;}
 if(n==1){
  /* v0.8.17 provider-transition probe: log is opt-in and bounded; this
   * does not change release order or the actual mixer teardown. */
  logline("A3D.Root final external Release; mixer shutdown requested");
  mixer_shutdown();
  logline("A3D.Root final external Release; shutdown returned");
 }
 return (ULONG)n;
}
static void mix_enter(void);
static void mix_leave(void);
static void mixer_update_listener(void);
static void mixer_update_global(void);
static void mixer_shutdown(void);
/* The freestanding PE32 build has no C runtime. Clang may lower large
 * aggregate copies (e.g. one-time worker voice state initialization) to
 * memcpy, so supply a private freestanding implementation. */
void *memcpy(void *out,const void *in,unsigned long n){
 unsigned char *d=(unsigned char*)out;
 const unsigned char *s=(const unsigned char*)in;
 for(unsigned long i=0;i<n;i++)d[i]=s[i];
 return out;
}
#include "geom_trace.inc"
#include "listener_trace.inc"
#include "source_probe.inc"
/* REVIEW NOTE — aqi: Root COM QueryInterface: A3D2 callers discover IA3d3/IA3d4, listener, and geometry through this dispatch. Interface IDs and ref-counting are ABI-critical. */
static HRESULT WINAPI aqi(A3D*s,const GUID*i,void**o){
 if(!o)return E_POINTER;*o=0;logguid("IA3d3.QueryInterface",i);
 if(eqguid(i,&iid_unk)||eqguid(i,&iid_ia3d1)||eqguid(i,&iid_ia3d2)||eqguid(i,&iid_ia3d3)||eqguid(i,&iid_ia3d4)){*o=s;aadd(s);return S_OK;}
 if(eqguid(i,&iid_geom)){*o=&geom;gadd(&geom);return S_OK;}
 if(eqguid(i,&iid_listener)){*o=&listener;ladd(&listener);return S_OK;}
 return E_NOINTERFACE;
}
static HRESULT WINAPI setmode(A3D*s,DWORD a,DWORD b,DWORD c){s->mode[0]=a;s->mode[1]=b;s->mode[2]=c;logline("IA3d3.SetOutputMode");return S_OK;}
static HRESULT WINAPI getmode(A3D*s,DWORD*a,DWORD*b,DWORD*c){if(!a||!b||!c)return E_POINTER;*a=s->mode[0];*b=s->mode[1];*c=s->mode[2];return S_OK;}
#define SETD(name,field) static HRESULT WINAPI name(A3D*s,DWORD x){s->field=x;return S_OK;}
#define GETD(name,field) static HRESULT WINAPI name(A3D*s,DWORD*x){if(!x)return E_POINTER;*x=s->field;return S_OK;}
#define SETF(name,field) static HRESULT WINAPI name(A3D*s,float x){s->field=x;return S_OK;}
#define GETF(name,field) static HRESULT WINAPI name(A3D*s,float*x){if(!x)return E_POINTER;*x=s->field;return S_OK;}
SETD(setres,res) GETD(getres,res)
static HRESULT WINAPI setcoords(A3D*s,DWORD v){if(v>1)return E_FAIL;s->coords=v;mixer_update_listener();logline(v?"IA3d4.SetCoordinateSystem LEFT_HANDED":"IA3d4.SetCoordinateSystem RIGHT_HANDED");return S_OK;}
GETD(getcoords,coords)
SETD(setfalls,falls) GETD(getfalls,falls) SETF(sethfa,hfa) GETF(gethfa,hfa)
SETF(setdelay,delay) GETF(getdelay,delay)
static HRESULT WINAPI setgain(A3D*s,float x){if(!(x>=0))return E_INVALIDARG;s->gain=x;mixer_update_global();return S_OK;}
GETF(getgain,gain)
static HRESULT WINAPI regver(A3D*s,DWORD v){(void)s;sr_logu("IA3d3.RegisterVersion requested",v);return S_OK;}
/* Accept the older short capability records as well as the extended SDK
 * layouts. Never write beyond the caller-declared size. Earlier versions left
 * the extension untouched, so a client could read zero/garbage buffer limits.
 * The two source maxima share one software voice pool; they are not additive.
 * No Aureal hardware capabilities are claimed. */
#include "capability_contract.h"
static HRESULT cap_result(unsigned result){return result==1u?E_POINTER:result==2u?E_FAIL:S_OK;}
static HRESULT WINAPI softcaps(A3D*s,SoftwareCaps*c){
 (void)s;logline("IA3d3.GetSoftwareCaps");if(!c)return E_POINTER;
 mix_enter();unsigned voices=mixer.voice_limit;mix_leave();
 return cap_result(a3dcap_fill(c,0,voices));
}
static HRESULT WINAPI hardcaps(A3D*s,HardwareCaps*c){
 (void)s;logline("IA3d3.GetHardwareCaps");return cap_result(a3dcap_fill(c,1,0));
}
static HRESULT WINAPI cl(A3D*s){(void)s;mix_enter();ensure_scene();a3d_scene_clear(&a3d_scene);mix_leave();return S_OK;}
static HRESULT WINAPI fl(A3D*s){(void)s;mix_enter();ensure_scene();a3d_scene_flush(&a3d_scene);DWORD count=a3d_scene.committed.count;mix_leave();static unsigned frame_log=0;if(frame_log++%120u==0u)sr_logu("A3D.Scene.Flush triangles",count);return S_OK;}
static HRESULT WINAPI compat(A3D*s,DWORD a,DWORD b){(void)s;(void)a;(void)b;logline("IA3d3.Compat");return S_OK;}
/* REVIEW NOTE — init: A3D root initialization: initializes scene state and runtime DSP options; do not equate successful Init with successful gameplay buffer routing. */
static HRESULT WINAPI init(A3D*s,GUID*g,DWORD flags,DWORD mode){(void)s;(void)g;(void)mode;mix_enter();ensure_scene();a3d_scene_init(&a3d_scene);a3d_scene.global_flags=flags&(A3D_SCENE_OCCLUSIONS|A3D_SCENE_REFLECTIONS);
 /* Late reverb enabled only if game requests A3D_LATE_REFLECTIONS (0x04),
  * unless enhanced reverb is explicitly enabled for research. */
 char enhanced[8]={0};GetEnvironmentVariableA("A3D_ENHANCED_REVERB",enhanced,8);
 mixer.reverb_wet=((flags&0x04UL)||enhanced[0]=='1')?0.14f:0.0f;
 mixer.reverb_wet=a3d_tuning_env("A3D_REVERB_WET",mixer.reverb_wet,0.0f,0.30f);
 mixer.direct_trim=a3d_tuning_env("A3D_DIRECT_TRIM",1.0f,0.25f,3.0f);
 mixer.early_reflection_trim=a3d_tuning_env("A3D_EARLY_REFLECTION_TRIM",1.0f,0.0f,2.0f);
 mixer.master_boost=a3d_tuning_env("A3D_MASTER_GAIN",5.0f,0.1f,5.0f);
 /* Preserve the environment opt-in already loaded by mix_enter; game Init
  * does not change it. Profile launchers set it only for Alice. */
 mixer.distance_strength=a3d_tuning_env("A3D_DISTANCE_STRENGTH",1.0f,0.0f,1.0f);
 /* 48 taps default; 96 is v0.4.1 quality; 24 is a diagnostic fast setting. */
 char taps[8]={0};GetEnvironmentVariableA("A3D_HRTF_TAPS",taps,sizeof(taps));
 mixer.hrtf_taps=(taps[0]=='9' && taps[1]=='6' && !taps[2])?96u:
                 (taps[0]=='2' && taps[1]=='4' && !taps[2])?24u:48u;
 /* HF9: do not turn off HRTF or alter game audio-source lifetimes.
  * Geometry can be disabled to isolate acoustic scene tracing from PCM
  * streaming, and its cache age can be tuned without a new DLL. */
 {
  char opt[12]={0};DWORD n=GetEnvironmentVariableA("A3D_GEOMETRY_TRACE",opt,sizeof(opt));
  mixer.geometry_enabled=!(n==1&&opt[0]=='0');
  char blocks[12]={0};n=GetEnvironmentVariableA("A3D_GEOMETRY_RETRACE_BLOCKS",blocks,sizeof(blocks));
  if(n&&n<sizeof(blocks)){
   unsigned v=0,valid=1;
   for(DWORD j=0;j<n;j++){
    if(blocks[j]<'0'||blocks[j]>'9'){valid=0;break;}
    v=v*10u+(unsigned)(blocks[j]-'0');
    if(v>32u){valid=0;break;}
   }
   if(valid)mixer.geometry_retrace_blocks=v;
  }
 }
 mixer.doppler_enabled=(flags&0x10UL)?1u:0u;
 mixer.distance_enabled=(flags&0x20UL)?1u:0u;
 mix_leave();sr_logu("IA3d4.Init requested_flags",flags);sr_logu("A3D.HRTF.taps",mixer.hrtf_taps);
 sr_logu("A3D.MasterGain.Init.x1000",(DWORD)(mixer.master_boost*1000.0f+0.5f));
 logline("A3D v0.7.0-alpha: shared core; new game profiles unverified");return S_OK;}
static HRESULT WINAPI feature(A3D*s,DWORD f){(void)s;sr_logu("IA3d3.IsFeatureAvailable unsupported",f);return S_FALSE;}
static HRESULT WINAPI newsrc(A3D*s,DWORD f,void**o){(void)s;return source_new(f,o);}
static HRESULT WINAPI dupsrc(A3D*s,void*src,void**o){(void)s;return source_duplicate((Source*)src,o);}
static HRESULT WINAPI setcoop(A3D*s,void*h,DWORD f){(void)h;s->cooperative=f;return S_OK;}
GETD(getcoop,cooperative)
/* These methods are ABI-correct control probes, not functioning audio processing. */
SETF(setrmbias,rm_bias) GETF(getrmbias,rm_bias)
static HRESULT WINAPI setunits(A3D*s,float x){if(!(x>0))return E_INVALIDARG;s->units=x;mixer_update_global();return S_OK;}
GETF(getunits,units)
static HRESULT WINAPI setdoppler(A3D*s,float x){if(!(x>=0))return E_INVALIDARG;s->doppler=x;mixer_update_global();return S_OK;}
GETF(getdoppler,doppler)
static HRESULT WINAPI setdistance(A3D*s,float x){if(!(x>=0))return E_INVALIDARG;s->distance=x;mixer_update_global();return S_OK;}
GETF(getdistance,distance)
SETF(seteq,eq) GETF(geteq,eq)
static HRESULT WINAPI disableviewer(A3D*s){(void)s;logline("IA3d4.DisableViewer (no viewer)");return S_OK;}
static HRESULT WINAPI shutdown(A3D*s){(void)s;mixer_shutdown();logline("IA3d4.Shutdown mixer");return S_OK;}
static HRESULT WINAPI registerapp(A3D*s,const GUID*g){(void)s;logguid("IA3d4.RegisterApp",g);return g?S_OK:E_POINTER;}
static const A3DVtbl av={aqi,aadd,arel,setmode,getmode,setres,getres,sethfa,gethfa,regver,softcaps,hardcaps,
 cl,fl,compat,init,feature,newsrc,dupsrc,setcoop,getcoop,setdelay,getdelay,setcoords,getcoords,setgain,getgain,setfalls,getfalls,
 setrmbias,getrmbias,disableviewer,setunits,getunits,setdoppler,getdoppler,setdistance,getdistance,seteq,geteq,shutdown,registerapp};

typedef struct Factory Factory;
typedef struct { HRESULT (WINAPI*QueryInterface)(Factory*,const GUID*,void**);
 ULONG (WINAPI*AddRef)(Factory*);ULONG (WINAPI*Release)(Factory*);
 HRESULT (WINAPI*CreateInstance)(Factory*,void*,const GUID*,void**);
 HRESULT (WINAPI*LockServer)(Factory*,BOOL);
} FactoryVtbl;
struct Factory{const FactoryVtbl*vt;volatile long ref;};
static const FactoryVtbl fv;
static Factory factory={&fv,1};
static ULONG WINAPI fadd(Factory*f){return (ULONG)InterlockedIncrement(&f->ref);}
static ULONG WINAPI frel(Factory*f){long n=InterlockedDecrement(&f->ref);if(n<1){f->ref=1;return 1;}return (ULONG)n;}
static HRESULT WINAPI fqi(Factory*f,const GUID*i,void**o){if(!o)return E_POINTER;*o=0;logguid("Factory.QueryInterface",i);if(eqguid(i,&iid_unk)||eqguid(i,&iid_factory)){*o=f;fadd(f);return S_OK;}return E_NOINTERFACE;}
static HRESULT WINAPI create(Factory*f,void*outer,const GUID*i,void**o){(void)f;if(!o)return E_POINTER;*o=0;logguid("Factory.CreateInstance IID",i);if(outer)return CLASS_E_NOAGGREGATION;return aqi(&root,i,o);}
static HRESULT WINAPI lock(Factory*f,BOOL on){(void)f;if(on)InterlockedIncrement(&locks);else InterlockedDecrement(&locks);return S_OK;}
static const FactoryVtbl fv={fqi,fadd,frel,create,lock};
EXPORT HRESULT WINAPI DllGetClassObject(const GUID*cls,const GUID*i,void**o){
 if(!o)return E_POINTER;*o=0;logguid("DllGetClassObject CLSID",cls);
 if(!eqguid(cls,&clsid_a3dapi))return CLASS_E_CLASSNOTAVAILABLE;
 return fqi(&factory,i,o);
}
EXPORT HRESULT WINAPI DllCanUnloadNow(void){return (mix_waveout==0 && locks==0 && root.ref<=1 && geom.ref<=1 && listener.ref<=1 && factory.ref<=1)?S_OK:S_FALSE;}
/* Registration is done by per-prefix Wine .reg, not by modifying Windows registry here. */
EXPORT HRESULT WINAPI DllRegisterServer(void){logline("DllRegisterServer; use generated .reg instead");return E_NOTIMPL;}
EXPORT HRESULT WINAPI DllUnregisterServer(void){return E_NOTIMPL;}
