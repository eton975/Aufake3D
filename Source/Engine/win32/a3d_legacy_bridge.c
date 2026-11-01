/* v0.5.0 SOURCE COMMENTARY — Legacy A3D 1.x Win32 frontend
 * Exports historical A3dCreate spellings and legacy COM entry points. The creation
 * function delegates to DirectSoundCreate; it does not perform Aureal HRTF or
 * Wavetracing processing. COM class-factory requests are forwarded to a3dapi.dll. The
 * diagnostic file writer is opt-in. Return codes distinguish missing dependency,
 * invalid output pointer, and unsupported registration.
 */
/*
 * A3D legacy entry-point bridge for older A3D/Quake III executables.
 *
 * WARNING: A3dCreate does not give us Aureal Wavetracing or its HRTF engine.
 * This compatibility shim uses Microsoft's DirectSoundCreate to keep an older
 * DirectSound-based sound path accessible on modern Windows and Wine.
 *
 * Separately, applications that ask for the A3D 2.x CLSID are forwarded to
 * the independently written a3dapi.dll. That is the geometry-aware backend.
 *
 * The implementation has no third-party code and does not bundle vendor DLLs.
 * Functions are Windows 32-bit stdcall. A3dCreate is exported under the exact
 * historical decorated name _A3dCreate@12, not as an invented C export.
 */
typedef unsigned long DWORD;
typedef long HRESULT;
typedef void *HMODULE;
typedef const char *LPCSTR;
typedef void *HANDLE;
#define WINAPI __attribute__((stdcall))
#define EXPORT __declspec(dllexport)
#define IMPORT __declspec(dllimport)
#define E_FAIL ((HRESULT)0x80004005L)
#define CLASS_E_CLASSNOTAVAILABLE ((HRESULT)0x80040111L)
#define E_POINTER ((HRESULT)0x80004003L)
#define E_NOTIMPL ((HRESULT)0x80004001L)
IMPORT HMODULE WINAPI LoadLibraryA(LPCSTR);
IMPORT void *WINAPI GetProcAddress(HMODULE,LPCSTR);
IMPORT unsigned long WINAPI GetEnvironmentVariableA(LPCSTR,char*,unsigned long);
IMPORT HANDLE WINAPI CreateFileA(LPCSTR,unsigned long,unsigned long,void*,unsigned long,unsigned long,HANDLE);
IMPORT int WINAPI WriteFile(HANDLE,const void*,unsigned long,unsigned long*,void*);
IMPORT int WINAPI CloseHandle(HANDLE);
/* Separate legacy-bridge diagnostics: opt-in and tightly bounded.
 * This bridge is not used for the Alice2000 render callback; keep all
 * logging off when the environment explicitly leaves A3D_LOG unset. */
static unsigned long bridge_trace_bytes=0;
static void trace(const char *s) {
 char flag[8]={0};
 unsigned long fn=GetEnvironmentVariableA("A3D_LOG",flag,sizeof(flag));
 if(fn!=1||flag[0]!='1')return;
 char path[512];
 unsigned long n=GetEnvironmentVariableA("A3D_PROBE_LOG",path,sizeof(path));
 if(n==0||n>=sizeof(path))return;
 unsigned long len=0,out=0;while(s[len])len++;
 if(len+2UL>32768UL-bridge_trace_bytes)return;
 HANDLE h=CreateFileA(path,4UL,3UL,0,4UL,128UL,0);
 if(h==(HANDLE)-1)return;
 WriteFile(h,s,len,&out,0);WriteFile(h,"\r\n",2,&out,0);CloseHandle(h);
 bridge_trace_bytes+=len+2UL;
}

typedef HRESULT (WINAPI *A3DFactory)(const void *, const void *, void **);
typedef HRESULT (WINAPI *DSCreate)(const void *, void **, void *);
typedef HRESULT (WINAPI *Unloader)(void);
static HMODULE backend;
static HMODULE dsound;
/*
 * DirectSoundCreate's documented ABI is (LPCGUID, LPDIRECTSOUND *, IUnknown *).
 * The same 12-byte stack convention is used by the legacy Aureal A3dCreate
 * export. The returned DirectSound object is NOT an emulated AU8830 interface.
 */
/* REVIEW NOTE — legacy_a3d_create: Legacy entrypoint: *not* real A3D1 HRTF; returns a DirectSound-created object to satisfy basic loader expectations. */
HRESULT WINAPI legacy_a3d_create(const void *guid, void **result, void *outer) {
    if (!result) return E_POINTER;
    *result=0;
    trace("A3D1.A3dCreate entered (DirectSound fallback path)");
    if (!dsound) dsound=LoadLibraryA("dsound.dll");
    if (!dsound) return E_FAIL;
    DSCreate create=(DSCreate)GetProcAddress(dsound,"DirectSoundCreate");
    HRESULT hr=create ? create(guid,result,outer) : E_FAIL;
    trace(hr>=0 ? "A3D1.A3dCreate DirectSound PASS" : "A3D1.A3dCreate DirectSound FAIL");
    return hr;
}
static void *backend_export(LPCSTR name) {
    if (!backend) backend=LoadLibraryA("a3dapi.dll");
    return backend ? GetProcAddress(backend,name) : 0;
}
/* REVIEW NOTE — DllGetClassObject: Legacy COM forwarding: class-factory requests are passed to a3dapi.dll; this is not universal A3D3 support. */
HRESULT WINAPI DllGetClassObject(const void *clsid,const void *iid,void **out) {
    if (!out) return E_POINTER;
    *out=0;
    trace("A3D1.DllGetClassObject forwarding to A3D2 backend");
    A3DFactory fn=(A3DFactory)backend_export("DllGetClassObject");
    return fn ? fn(clsid,iid,out) : CLASS_E_CLASSNOTAVAILABLE;
}
HRESULT WINAPI DllCanUnloadNow(void) {
    Unloader fn=(Unloader)backend_export("DllCanUnloadNow");
    return fn ? fn() : E_FAIL;
}
HRESULT WINAPI DllRegisterServer(void) {return E_NOTIMPL;}
HRESULT WINAPI DllUnregisterServer(void) {return E_NOTIMPL;}
