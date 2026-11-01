/* A3D v0.7.4f -- independent x86 Miles provider probe.
 * Runs in a disposable, isolated directory outside the game. No game EXE,
 * VorpalFix, COM registration, registry writes, injection or process patching.
 * --enumerate is read-mostly; --open may initialize the sound driver, so
 * it MUST be run as an independently time-limited child by the PS harness.
 * The resulting trace is about Miles provider availability, NOT proof that
 * Alice itself selected a particular provider or that game playback works.
 */
#define IMPORT __declspec(dllimport)
#define STDCALL __attribute__((stdcall))
typedef unsigned long DWORD;
typedef unsigned short WORD;
typedef long HRESULT;
typedef void *HANDLE;
typedef void *HMODULE;
typedef __UINTPTR_TYPE__ ULONG_PTR;
#define INVALID_HANDLE_VALUE ((HANDLE)-1)
#define STD_OUTPUT_HANDLE ((DWORD)-11)
#define GENERIC_WRITE 0x40000000UL
#define CREATE_ALWAYS 2UL
#define FILE_SHARE_READ 1UL
#define FILE_ATTRIBUTE_NORMAL 0x80UL
#define CLSCTX_INPROC_SERVER 1UL
typedef struct { DWORD cbSize,dwFlags;const char *lpSource;WORD wProcessorArchitecture,wLangId;const char *lpAssemblyDirectory,*lpResourceName,*lpApplicationName;HMODULE hModule;} ACTCTXA;
IMPORT HANDLE STDCALL GetStdHandle(DWORD);
IMPORT int STDCALL WriteFile(HANDLE,const void*,DWORD,DWORD*,void*);
IMPORT HANDLE STDCALL CreateFileA(const char*,DWORD,DWORD,void*,DWORD,DWORD,HANDLE);
IMPORT int STDCALL CloseHandle(HANDLE);
IMPORT void STDCALL ExitProcess(DWORD);
IMPORT HMODULE STDCALL LoadLibraryA(const char*);
IMPORT HMODULE STDCALL GetModuleHandleA(const char*);
IMPORT void * STDCALL GetProcAddress(HMODULE,const char*);
IMPORT DWORD STDCALL GetLastError(void);
IMPORT DWORD STDCALL GetModuleFileNameA(HMODULE,char*,DWORD);
IMPORT const char* STDCALL GetCommandLineA(void);
IMPORT HANDLE STDCALL CreateActCtxA(const ACTCTXA*);
IMPORT int STDCALL ActivateActCtx(HANDLE,ULONG_PTR*);
IMPORT int STDCALL DeactivateActCtx(DWORD,ULONG_PTR);
IMPORT void STDCALL ReleaseActCtx(HANDLE);
static HANDLE stdout_h, log_h;
static DWORD length(const char*s){DWORD n=0;while(s&&s[n]&&n<8191)n++;return n;}
static void say(const char*s){DWORD w,n=length(s);if(stdout_h&&stdout_h!=INVALID_HANDLE_VALUE)WriteFile(stdout_h,s,n,&w,0);if(log_h&&log_h!=INVALID_HANDLE_VALUE)WriteFile(log_h,s,n,&w,0);}
static void hex(DWORD n){char b[11]="0x00000000";for(int i=9;i>=2;--i){unsigned v=n&15;b[i]=(char)(v<10?'0'+v:'A'+v-10);n>>=4;}say(b);}
static void linehex(const char*name,DWORD n){say(name);hex(n);say("\r\n");}
static int equals(const char*a,const char*b){if(!a||!b)return 0;while(*a&&*b){if(*a++!=*b++)return 0;}return !*a&&!*b;}
static int has(const char*s,const char*piece){if(!s||!piece)return 0;for(DWORD i=0;s[i];i++){DWORD j=0;while(piece[j]&&s[i+j]&&piece[j]==s[i+j])j++;if(!piece[j])return 1;}return 0;}
static void image(const char *name){HMODULE h=GetModuleHandleA(name);if(!h){say("A3D_DLL_NOT_LOADED\r\n");return;}char path[768];DWORD n=GetModuleFileNameA(h,path,sizeof(path));if(n&&n<sizeof(path)){path[n]=0;say("A3D_DLL_PATH ");say(path);say("\r\n");}}
typedef int (STDCALL *Startup)(void);
typedef int (STDCALL *Enum)(void**,void**,char**);
typedef int (STDCALL *Open)(void*);
typedef void* (STDCALL *Listener)(void*);
typedef void (STDCALL *Close)(void*);
typedef void (STDCALL *Shutdown)(void);
typedef void (STDCALL *SetRedist)(const char*);
typedef const char* (STDCALL *LastError)(void);
void STDCALL mainCRTStartup(void){
 int rc=0;
 stdout_h=GetStdHandle(STD_OUTPUT_HANDLE);
 log_h=CreateFileA("a3d-provider-autoprobe.log",GENERIC_WRITE,FILE_SHARE_READ,0,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
 say("A3D v0.8.3 isolated unknown-alias probe\r\n");
 const char*cmd=GetCommandLineA();int open_mode=has(cmd,"--open");
 say(open_mode?"MODE=OPEN (MAY INITIALIZE SOUND DEVICE)\r\n":"MODE=ENUMERATE\r\n");
 HMODULE miles=LoadLibraryA("SndDrivers\\mss32.dll");
 if(!miles){linehex("MILES_LOAD_FAILED_WIN32 ",GetLastError());rc=2;goto done;}
 say("MILES_LOAD_OK\r\n");
 Startup startup=(Startup)GetProcAddress(miles,"_AIL_startup@0");
 Enum enumerate=(Enum)GetProcAddress(miles,"_AIL_enumerate_3D_providers@12");
 Open openfn=(Open)GetProcAddress(miles,"_AIL_open_3D_provider@4");
 Listener listener=(Listener)GetProcAddress(miles,"_AIL_open_3D_listener@4");
 Close closefn=(Close)GetProcAddress(miles,"_AIL_close_3D_provider@4");
 Shutdown shutdown=(Shutdown)GetProcAddress(miles,"_AIL_shutdown@0");
 SetRedist set_redist=(SetRedist)GetProcAddress(miles,"_AIL_set_redist_directory@4");
 LastError last=(LastError)GetProcAddress(miles,"_AIL_last_error@0");
 if(!startup||!enumerate||!openfn||!listener||!closefn||!shutdown||!last){say("MILES_REQUIRED_EXPORTS_MISSING\r\n");rc=3;goto done;}
 /* Activation context is held over the provider enumeration/open sequence.
    This is not dependent on the external per-user COM registration. */
 HANDLE act=0;ULONG_PTR cookie=0;int active=0;
 ACTCTXA a={0};a.cbSize=sizeof(a);a.lpSource="SndDrivers\\a3d-miles-local.manifest";
 act=CreateActCtxA(&a);
 if(act && act!=INVALID_HANDLE_VALUE){active=ActivateActCtx(act,&cookie);}
 say(active?"ACTCTX_ACTIVE\r\n":"ACTCTX_FAILED_OR_INACTIVE\r\n");
 int sr=startup();linehex("AIL_STARTUP_RESULT ",(DWORD)sr);
 if(set_redist){set_redist("SndDrivers");say("MILES_REDIST_DIRECTORY SndDrivers\r\n");}
 else say("MILES_REDIST_FUNCTION_UNAVAILABLE\r\n");
 void*next=0;
 int count=0,alias_seen=0;void*selected=0;
 for(int i=0;i<64;i++){
  void*provider=0;char*name=0;
  int ok=enumerate(&next,&provider,&name);
  if(!ok){say("AIL_ENUM_END\r\n");break;}
  count++;
  linehex("PROVIDER_HANDLE ",(DWORD)(ULONG_PTR)provider);
  say("PROVIDER_NAME ");say(name?name:"(null)");say("\r\n");
  if(name&&equals(name,"unknown")){alias_seen++;selected=provider;}
  else if(name&&equals(name,"Aureal A3D 2.0 (TM)")){if(!selected)selected=provider;}
 }
 linehex("ENUM_COUNT ",(DWORD)count);
 linehex("UNKNOWN_ALIAS_COUNT ",(DWORD)alias_seen);
 if(!selected){say("A3D2_PROVIDER_NOT_ENUMERATED\r\n");rc=4;goto shutdown_miles;}
 linehex("A3D2_PROVIDER_HANDLE ",(DWORD)(ULONG_PTR)selected);
 if(open_mode){
  say("OPEN_A3D2_ATTEMPT (INDEPENDENT PROBE, NOT GAME)\r\n");
  int opened=openfn(selected);linehex("OPEN_A3D2_RESULT ",(DWORD)opened);
  if(opened!=0){say("OPEN_A3D2_ERROR ");say(last());say("\r\n");rc=5;}
  else {
   void*handle=listener(selected);linehex("LISTENER_HANDLE ",(DWORD)(ULONG_PTR)handle);
   image("a3dapi.dll");
   if(!handle)rc=6;
   closefn(selected);
  }
 }
 shutdown_miles:
 shutdown();
 if(active)DeactivateActCtx(0,cookie);
 if(act&&act!=INVALID_HANDLE_VALUE)ReleaseActCtx(act);
 done:
 linehex("RESULT_CODE ",(DWORD)rc);
 if(log_h&&log_h!=INVALID_HANDLE_VALUE)CloseHandle(log_h);
 ExitProcess(rc);
}
