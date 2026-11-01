/* v0.5.0 SOURCE COMMENTARY — Legacy A3dCreate loader diagnostic
 * Calls the exported legacy function through the loaded DLL and exercises returned
 * DirectSound. It does not establish genuine hardware Aureal A3D 1.x audio processing.
 */
/* Minimal independent A3D 1.x legacy entrypoint diagnostic.
 * Calls our a3d.dll _A3dCreate@12 and releases the returned DirectSound
 * object. Makes NO claim that DirectSound pass-through is HRTF/Wavetracing.
 * No CRT or bundled vendor DLLs. Win32/x86 only.
 */
typedef unsigned long DWORD;
typedef long HRESULT;
typedef void *HMODULE;
typedef const char *LPCSTR;
typedef unsigned long ULONG;
typedef void *HANDLE;
#define WINAPI __attribute__((stdcall))
#define IMPORT __declspec(dllimport)
IMPORT HMODULE WINAPI LoadLibraryA(LPCSTR);
IMPORT void *WINAPI GetProcAddress(HMODULE,LPCSTR);
IMPORT HANDLE WINAPI GetStdHandle(DWORD);
IMPORT int WINAPI WriteFile(HANDLE,const void*,DWORD,DWORD*,void*);
IMPORT void WINAPI ExitProcess(DWORD);
static void say(const char *s) { DWORD n=0,w=0;while(s[n])n++;WriteFile(GetStdHandle((DWORD)-11),s,n,&w,0); }
typedef HRESULT (WINAPI *Create)(const void*,void**,void*);
typedef struct DS { void **vt; } DS;
typedef ULONG (WINAPI *Release)(DS*);
void WINAPI start(void) {
  HMODULE lib=LoadLibraryA("a3d.dll");
  if (!lib) { say("ERROR: a3d.dll not loaded\r\n");ExitProcess(2); }
  Create fn=(Create)GetProcAddress(lib,"_A3dCreate@12");
  if(!fn) fn=(Create)GetProcAddress(lib,"A3dCreate");
  if(!fn){say("ERROR: legacy A3dCreate export not found\r\n");ExitProcess(3);}
  void *result=0;HRESULT hr=fn(0,&result,0);
  if(hr<0 || !result){say("ERROR: A3dCreate/DirectSound initialisation failed\r\n");ExitProcess(4);}
  say("PASS: legacy A3dCreate returned a DirectSound object (not HRTF proof)\r\n");
  DS *ds=(DS*)result;
  if(ds->vt && ds->vt[2]) {Release release=(Release)ds->vt[2];release(ds);}
  ExitProcess(0);
}
