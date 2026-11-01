/* A3D v0.7.4f -- provider-name alias (NO 2D handle substitution).
 * Zero external process edits, zero registry installation. The underlying
 * PCM/WaveOut/HRTF renderer and original Miles library remain unchanged.
 *
 * WARNING: This is an experiment, not an assurance of correct audio.  A game
 * which has explicitly chosen Miles 2D may still follow different engine
 * code paths.  Log results distinguish a successful Miles provider-open
 * from actual renderer loading and audible A3D2 playback.
 *
 * A3D_MILES_ALIAS_UNKNOWN=1 plus A3D_MILES_MODE=activate enables an unknown-name
 * alias ONLY when the true A3D2 provider is enumerated. No provider-handle
 * redirection occurs. Other modes retain provider identity unchanged.
 *
 * Original v0.7.4d -- provider identity + independent COM diagnostic.
 * Game ABI: only four Miles entrypoints are wrapped. 327 other exports remain
 * exact pass-through v0.7.4b lazy tail-call stubs.
 *
 * A3D_MILES_MODE=pass: forwarding only (no activation or added COM calls).
 * A3D_MILES_MODE=trace: non-invasive provider/return-value instrumentation.
 * A3D_MILES_MODE=activate: registration-free context during provider calls,
 * and an OPTIONAL independent diagnostic COM activation probe performed AFTER
 * original Miles open has returned.  A probe success is NOT game A3D success.
 *
 * A3D_MILES_COM_PROBE=1 enables one diagnostic COM probe when the first
 * provider-open completes. It never changes the original provider result.
 * Native Windows 32-bit, freestanding, no registry writes, remote memory APIs,
 * DLL entry point, or modification of game executable/mixer.
 */
#define STDCALL __attribute__((stdcall))
#ifdef A3D_TEST_NATIVE
#define IMPORT
#else
#define IMPORT __declspec(dllimport)
#endif
typedef unsigned int DWORD;
typedef unsigned short WORD;
typedef int BOOL;
typedef long HRESULT;
typedef void *HMODULE;
typedef void *HANDLE;
typedef __UINTPTR_TYPE__ ULONG_PTR;
#define INVALID_HANDLE_VALUE ((HANDLE)(-1))
#define GENERIC_WRITE 0x40000000UL
#define FILE_SHARE_READ 1UL
#define OPEN_ALWAYS 4UL
#define FILE_ATTRIBUTE_NORMAL 0x80UL
#define FILE_END 2UL
#define GET_FROM_ADDRESS 4UL
#define GET_UNCHANGED_REF 2UL
#define CLSCTX_INPROC_SERVER 1UL
#define ACTIVATION_CONTEXT_SECTION_COM_SERVER_REDIRECTION 4UL
#define ENUM_ORDINAL 76
#define OPEN_ORDINAL 116
#define STARTUP_ORDINAL 279
#define LISTENER_ORDINAL 114
#define LAST_ERROR_ORDINAL 99
#define CLOSE_ORDINAL 52
#define OBJECT_ORDINAL 115
#define PROVIDER_ATTRIBUTE_ORDINAL 4
#define SPEAKER_GET_ORDINAL 18
#define SPEAKER_SET_ORDINAL 221
#define ROOM_GET_ORDINAL 5
#define ROOM_SET_ORDINAL 207
#define PROVIDER_PREF_SET_ORDINAL 206
/* Same ACTCTXA x86 layout as the previously tested v0.7.4c. */
typedef struct {DWORD cbSize,dwFlags;const char *lpSource;WORD wProcessorArchitecture,wLangId;
 const char *lpAssemblyDirectory,*lpResourceName,*lpApplicationName;HMODULE hModule;} ACTCTXA;
typedef struct {DWORD a;WORD b,c;unsigned char d[8];} GUID;
/* ACTCTX_SECTION_KEYED_DATA x86: 44-byte prefix + 20-byte assembly metadata. */
typedef struct {void *lpInformation,*lpSectionBase;DWORD ulSectionLength;
 void *lpSectionGlobalDataBase;DWORD ulSectionGlobalDataLength;} ASM_META;
typedef struct {DWORD cbSize,ulDataFormatVersion;void *lpData;DWORD ulLength;
 void *lpSectionGlobalData;DWORD ulSectionGlobalDataLength;void *lpSectionBase;
 DWORD ulSectionTotalLength;HANDLE hActCtx;DWORD ulAssemblyRosterIndex,ulFlags;
 ASM_META AssemblyMetadata;} ACTCTX_SECTION_KEYED_DATA;
typedef struct IUnknown {struct IUnknownVTable *lpVtbl;} IUnknown;
typedef struct IUnknownVTable {HRESULT (STDCALL *QueryInterface)(IUnknown*,const GUID*,void**);
 DWORD (STDCALL *AddRef)(IUnknown*);DWORD (STDCALL *Release)(IUnknown*);} IUnknownVTable;
IMPORT BOOL STDCALL GetModuleHandleExA(DWORD,const char*,HMODULE*);
IMPORT HMODULE STDCALL GetModuleHandleA(const char*);
IMPORT DWORD STDCALL GetModuleFileNameA(HMODULE,char*,DWORD);
IMPORT DWORD STDCALL GetEnvironmentVariableA(const char*,char*,DWORD);
IMPORT HANDLE STDCALL CreateFileA(const char*,DWORD,DWORD,void*,DWORD,DWORD,HANDLE);
IMPORT DWORD STDCALL SetFilePointer(HANDLE,long,long*,DWORD);
IMPORT BOOL STDCALL WriteFile(HANDLE,const void*,DWORD,DWORD*,void*);
IMPORT BOOL STDCALL CloseHandle(HANDLE);
IMPORT HANDLE STDCALL CreateActCtxA(const ACTCTXA*);
IMPORT BOOL STDCALL ActivateActCtx(HANDLE,ULONG_PTR*);
IMPORT BOOL STDCALL DeactivateActCtx(DWORD,ULONG_PTR);
IMPORT void STDCALL ReleaseActCtx(HANDLE);
IMPORT DWORD STDCALL GetLastError(void);
IMPORT BOOL STDCALL FindActCtxSectionGuid(DWORD,const GUID*,DWORD,const GUID*,ACTCTX_SECTION_KEYED_DATA*);
IMPORT HRESULT STDCALL CoInitialize(void*);
IMPORT void STDCALL CoUninitialize(void);
IMPORT HRESULT STDCALL CoCreateInstance(const GUID*,IUnknown*,DWORD,const GUID*,void**);
extern void* __cdecl a3d_resolve(DWORD);
static const GUID CLSID_A3D = {0x92FA2C24,0x253C,0x11D2,{0x90,0xFB,0x00,0x60,0x08,0xA1,0xF4,0x41}};
static const GUID IID_IUNKNOWN = {0,0,0,{0xC0,0,0,0,0,0,0,0x46}};
static DWORD slen(const char*s){DWORD n=0;while(s && s[n] && n<4000)n++;return n;}
static void scopy(char*d,const char*s){while((*d++=*s++)!=0) {}}
static BOOL makepath(char*dest,const char*filename){
 HMODULE self=0;
 if(!GetModuleHandleExA(GET_FROM_ADDRESS|GET_UNCHANGED_REF,(const char*)&makepath,&self))return 0;
 DWORD n=GetModuleFileNameA(self,dest,700);
 if(!n||n>=700)return 0;
 while(n && dest[n-1]!='\\' && dest[n-1]!='/')n--;
 dest[n]=0;scopy(dest+n,filename);return 1;
}
static BOOL env_one(const char*s){char value[8];return GetEnvironmentVariableA(s,value,sizeof(value))==1 && value[0]=='1';}
static int mode(void){
 char s[24];DWORD n=GetEnvironmentVariableA("A3D_MILES_MODE",s,sizeof(s));
 if(n==4 && s[0]=='p' && s[1]=='a' && s[2]=='s' && s[3]=='s')return 0;
 if(n==8 && s[0]=='a' && s[1]=='c' && s[2]=='t' && s[3]=='i' && s[4]=='v' && s[5]=='a' && s[6]=='t' && s[7]=='e')return 2;
 return 1;
}
static void trace(const char*message){
 if(!env_one("A3D_MILES_TRACE"))return;
 char path[768];if(!makepath(path,"a3d-v074f-miles.log"))return;
 HANDLE h=CreateFileA(path,GENERIC_WRITE,FILE_SHARE_READ,0,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
 if(!h || h==INVALID_HANDLE_VALUE)return;
 DWORD pos=SetFilePointer(h,0,0,FILE_END),n=slen(message),written=0;
 if(pos!=0xffffffffUL && pos+n+2<=65536UL){
  WriteFile(h,message,n,&written,0);WriteFile(h,"\r\n",2,&written,0);
 }
 CloseHandle(h);
}
static int same(const char*a,const char*b){
 if(!a||!b)return 0;
 for(unsigned i=0;i<120;i++){
  if(a[i]!=b[i])return 0;
  if(!a[i])return 1;
 }
 return 0;
}
/* Game-side provider handles are opaque and are learned from the LIVE enum,
 * not hardcoded ordinals 4/8.  Compare-and-swap publication permits concurrent
 * Miles startup/enum paths without allocating or touching game memory. */
static void *volatile detected_a3d2;
static void *volatile detected_2d;
static char a3d2_alias[] = "unknown";
static void *translate(void*p){return p;} /* keep the game-selected provider exactly */
static void result(const char*label,DWORD value){
 char buf[180];DWORD n=slen(label),j=0;
 if(n>140)return;
 while(j<n){buf[j]=label[j];j++;}
 buf[j++]=' ';buf[j++]='0';buf[j++]='x';
 for(int i=7;i>=0;i--){int d=(value>>(i*4))&15;buf[j++]=(char)(d<10?'0'+d:'A'+d-10);}
 buf[j]=0;trace(buf);
}
static void string_value(const char*tag,const char*value){
 /* Names come from the original Miles library, not an arbitrary DLL export.
  * Bound strings strictly, remove control characters, do not change pointers. */
 char buf[240];DWORD n=slen(tag),j=0;
 if(n>65)return;
 while(j<n){buf[j]=tag[j];j++;}
 buf[j++]=' ';
 if(!value){scopy(buf+j,"(null)");trace(buf);return;}
 for(unsigned i=0;i<130 && value[i];i++){
  unsigned char c=(unsigned char)value[i];
  buf[j++]=(c>=32 && c<127)?(char)c:'?';
 }
 buf[j]=0;trace(buf);
}
static void module_status(const char*tag){
 HMODULE m=GetModuleHandleA("a3dapi.dll");
 if(!m){trace(tag);return;}
 char path[800];DWORD n=GetModuleFileNameA(m,path,sizeof(path));
 result("A3DAPI_MODULE_HANDLE",(DWORD)(ULONG_PTR)m);
 if(n>0 && n<sizeof(path))string_value("A3DAPI_MODULE_PATH",path);
}
typedef struct {HANDLE ctx;ULONG_PTR cookie;BOOL active;} LOCAL_CTX;
static LOCAL_CTX enter_context(void){
 LOCAL_CTX state={0,0,0};
 if(mode()!=2)return state;
 char path[768];if(!makepath(path,"a3d-miles-local.manifest")){trace("ACTCTX_PATH_FAILED");return state;}
 ACTCTXA a={0};a.cbSize=sizeof(a);a.lpSource=path;
 state.ctx=CreateActCtxA(&a);
 if(state.ctx==INVALID_HANDLE_VALUE || !state.ctx){
  result("ACTCTX_CREATE_FAILED_WIN32",GetLastError());state.ctx=0;return state;
 }
 state.active=ActivateActCtx(state.ctx,&state.cookie);
 if(state.active)trace("ACTCTX_ACTIVE");
 else result("ACTCTX_ACTIVATE_FAILED_WIN32",GetLastError());
 return state;
}
static void leave_context(LOCAL_CTX *ctx){
 if(ctx->active && !DeactivateActCtx(0,ctx->cookie))trace("ACTCTX_DEACTIVATE_FAILED");
 if(ctx->ctx)ReleaseActCtx(ctx->ctx);
}
static void com_probe(void){
 /* Explicitly independent from the game's provider. The preload/no-preload
  * trace comes BEFORE this method, to avoid contaminating activation evidence.
  * This probe may load a3dapi.dll even when the game never requested it. */
 trace("COM_PROBE_INDEPENDENT_BEGIN_NOT_GAME_INITIALISATION");
 ACTCTX_SECTION_KEYED_DATA section={0};section.cbSize=sizeof(section);
 if(FindActCtxSectionGuid(0,0,ACTIVATION_CONTEXT_SECTION_COM_SERVER_REDIRECTION,&CLSID_A3D,&section))
   trace("COM_PROBE_ACTCTX_CLSID_REDIRECTION_FOUND");
 else result("COM_PROBE_ACTCTX_CLSID_REDIRECTION_MISSING_WIN32",GetLastError());
 HRESULT init=CoInitialize(0);
 result("COM_PROBE_COINIT_HR",(DWORD)init);
 IUnknown *unknown=0;
 HRESULT hr=CoCreateInstance(&CLSID_A3D,0,CLSCTX_INPROC_SERVER,&IID_IUNKNOWN,(void**)&unknown);
 result("COM_PROBE_COCREATE_HR",(DWORD)hr);
 if(hr>=0 && unknown){unknown->lpVtbl->Release(unknown);trace("COM_PROBE_OBJECT_RELEASED");}
 if(init>=0)CoUninitialize();
 module_status("COM_PROBE_A3DAPI_NOT_LOADED");
 trace("COM_PROBE_INDEPENDENT_END");
}
typedef int (STDCALL *PEnum)(void**,void**,char**);
typedef int (STDCALL *POpen)(void*);
typedef int (STDCALL *PStartup)(void);
typedef void* (STDCALL *PListener)(void*);
typedef const char* (STDCALL *PLastError)(void);
int STDCALL a3d_hook_enumerate(void**next,void**provider,char**name){
 PEnum f=(PEnum)a3d_resolve(ENUM_ORDINAL);
 if(mode()==0)return f(next,provider,name);
 trace("AIL_ENUM_BEGIN");LOCAL_CTX c=enter_context();
 int r=f(next,provider,name);
 result("AIL_ENUM_RETURN",(DWORD)r);
 if(r && provider && name){
  result("AIL_ENUM_PROVIDER_HANDLE",(DWORD)(ULONG_PTR)*provider);
  string_value("AIL_ENUM_PROVIDER_NAME",*name);
  if(*provider && *name){
   if(same(*name,"Aureal A3D 2.0 (TM)")){
     __atomic_store_n(&detected_a3d2,*provider,__ATOMIC_RELEASE);
     result("A3D2_ENUM_SELECTED_CANDIDATE",(DWORD)(ULONG_PTR)*provider);
     /* Opt-in UNKNOWN alias for experimental selector fallback. This is the NAME the game looks up, not a
      * provider-handle swap.  The original provider identity and its handle
      * remain intact, and alias storage lives for the process lifetime. */
     if(c.active && mode()==2 && env_one("A3D_MILES_ALIAS_UNKNOWN")){
       *name=a3d2_alias;
       trace("A3D2_ALIAS_ADVERTISED unknown");
     }
   }else if(same(*name,"Miles Fast 2D Positional Audio")){
     __atomic_store_n(&detected_2d,*provider,__ATOMIC_RELEASE);
   }
  }
 }
 leave_context(&c);return r;
}
typedef void (STDCALL *PClose)(void*);
int STDCALL a3d_hook_open(void*provider){
 POpen f=(POpen)a3d_resolve(OPEN_ORDINAL);
 if(mode()==0)return f(provider);
 result("AIL_OPEN_BEGIN_PROVIDER",(DWORD)(ULONG_PTR)provider);
 LOCAL_CTX c=enter_context();
 module_status("AIL_OPEN_PRE_A3DAPI_NOT_LOADED");
 int r=f(provider); /* never silently redirect 2D provider */
 result("AIL_OPEN_RETURN",(DWORD)r);
 module_status("AIL_OPEN_POST_A3DAPI_NOT_LOADED");
 if(r!=0){
  PLastError err=(PLastError)a3d_resolve(LAST_ERROR_ORDINAL);
  string_value("AIL_OPEN_MILES_LAST_ERROR",err());
 }
 static volatile int probed=0;
 if(c.active && env_one("A3D_MILES_COM_PROBE") &&
    __sync_bool_compare_and_swap(&probed,0,1))com_probe();
 leave_context(&c);return r;
}
int STDCALL a3d_hook_startup(void){
 PStartup f=(PStartup)a3d_resolve(STARTUP_ORDINAL);
 if(mode()==0)return f();
 trace("AIL_STARTUP_BEGIN");LOCAL_CTX c=enter_context();
 int r=f();result("AIL_STARTUP_RETURN",(DWORD)r);
 leave_context(&c);return r;
}
void* STDCALL a3d_hook_listener(void*provider){
 PListener f=(PListener)a3d_resolve(LISTENER_ORDINAL);
 if(mode()==0)return f(provider);
 result("AIL_OPEN_LISTENER_PROVIDER_REQUESTED",(DWORD)(ULONG_PTR)provider);
 LOCAL_CTX c=enter_context();
 void *effective=translate(provider);
 result("AIL_OPEN_LISTENER_PROVIDER_EFFECTIVE",(DWORD)(ULONG_PTR)effective);
 void *r=f(effective);
 result("AIL_OPEN_LISTENER_RETURN",(DWORD)(ULONG_PTR)r);
 module_status("AIL_LISTENER_POST_A3DAPI_NOT_LOADED");
 leave_context(&c);return r;
}
void STDCALL a3d_hook_close(void*provider){
 PClose f=(PClose)a3d_resolve(CLOSE_ORDINAL);
 void*actual=translate(provider);
 if(mode()!=0)result("AIL_CLOSE_EFFECTIVE_PROVIDER",(DWORD)(ULONG_PTR)actual);
 f(actual);

}
typedef void* (STDCALL *PObject)(void*);
void* STDCALL a3d_hook_object(void*provider){
 PObject f=(PObject)a3d_resolve(OBJECT_ORDINAL);
 LOCAL_CTX c=enter_context();void*r=f(translate(provider));leave_context(&c);return r;
}
typedef int (STDCALL *PProviderGet)(void*);
typedef int (STDCALL *PProviderSet)(void*,int);
typedef int (STDCALL *PProviderSet3)(void*,int,int);
int STDCALL a3d_hook_get_speaker(void*provider){
 return ((PProviderGet)a3d_resolve(SPEAKER_GET_ORDINAL))(translate(provider));
}
int STDCALL a3d_hook_set_speaker(void*provider,int value){
 return ((PProviderSet)a3d_resolve(SPEAKER_SET_ORDINAL))(translate(provider),value);
}
int STDCALL a3d_hook_get_room(void*provider){
 return ((PProviderGet)a3d_resolve(ROOM_GET_ORDINAL))(translate(provider));
}
int STDCALL a3d_hook_set_room(void*provider,int value){
 return ((PProviderSet)a3d_resolve(ROOM_SET_ORDINAL))(translate(provider),value);
}
int STDCALL a3d_hook_set_preference(void*provider,int key,int value){
 return ((PProviderSet3)a3d_resolve(PROVIDER_PREF_SET_ORDINAL))(translate(provider),key,value);
}
int STDCALL a3d_hook_provider_attribute(void*provider,int key,int value){
 return ((PProviderSet3)a3d_resolve(PROVIDER_ATTRIBUTE_ORDINAL))(translate(provider),key,value);
}
