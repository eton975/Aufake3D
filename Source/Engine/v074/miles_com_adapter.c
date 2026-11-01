/* A3D v0.7.4 EXPERIMENTAL, x86, app-local Miles 3D provider activation adapter.
 *
 * NOT a replacement Miles engine: a generated PE .def forwards the original
 * mss32.dll export table to an untouched, renamed copy, a3d_mss_real.dll.
 * Only provider enumeration/open are intercepted to gather bounded evidence and
 * place an app-local activation context around AIL_open_3D_provider.
 *
 * The vendor's *own* DLL is supplied by its owner, never bundled by us.
 * No process injection, executable patching or registry writes. This may not
 * intercept calls made *internally* inside the original Miles DLL; this is an
 * experimental activation aid, not universal MSS compatibility.
 */
typedef unsigned long DWORD;
typedef unsigned long ULONG;
typedef unsigned short WORD;
typedef unsigned long long QWORD;
typedef void *HANDLE;
typedef void *HMODULE;
typedef unsigned long ULONG_PTR;
#define STDCALL __attribute__((stdcall))
#define IMPORT __declspec(dllimport)
#define INVALID_HANDLE_VALUE ((HANDLE)-1)
#define OPEN_ALWAYS 4UL
#define FILE_APPEND_DATA 0x00000004UL
#define FILE_SHARE_READ 1UL
#define FILE_ATTRIBUTE_NORMAL 0x00000080UL
#define FILE_END 2UL
#define ACTCTX_FLAG_ASSEMBLY_DIRECTORY_VALID 0x00000004UL
/* Win32 ACTCTXA, 32 bytes on x86. */
typedef struct { DWORD cbSize,dwFlags;const char *lpSource;WORD wProcessorArchitecture,wLangId;
 const char *lpAssemblyDirectory,*lpResourceName,*lpApplicationName;HMODULE hModule;} ACTCTXA;
IMPORT HMODULE STDCALL LoadLibraryA(const char*);
IMPORT void * STDCALL GetProcAddress(HMODULE,const char*);
IMPORT DWORD STDCALL GetModuleFileNameA(HMODULE,char*,DWORD);
IMPORT HMODULE STDCALL GetModuleHandleA(const char*);
IMPORT DWORD STDCALL GetEnvironmentVariableA(const char*,char*,DWORD);
IMPORT HANDLE STDCALL CreateFileA(const char*,DWORD,DWORD,void*,DWORD,DWORD,HANDLE);
IMPORT DWORD STDCALL SetFilePointer(HANDLE,long,long*,DWORD);
IMPORT int STDCALL WriteFile(HANDLE,const void*,DWORD,DWORD*,void*);
IMPORT int STDCALL CloseHandle(HANDLE);
IMPORT HANDLE STDCALL CreateActCtxA(const ACTCTXA*);
IMPORT int STDCALL ActivateActCtx(HANDLE,ULONG_PTR*);
IMPORT int STDCALL DeactivateActCtx(DWORD,ULONG_PTR);
IMPORT void STDCALL ReleaseActCtx(HANDLE);
IMPORT DWORD STDCALL GetLastError(void);
static char folder[2048],real_path[2300],manifest_path[2300],log_path[2300];
static HMODULE original;
static unsigned int init_state;
static unsigned int s_len(const char*s){unsigned int n=0;while(s&&s[n]&&n<3000)n++;return n;}
static void s_copy(char*out,const char*in){unsigned int i=0;for(;in[i]&&i<2200;i++)out[i]=in[i];out[i]=0;}
static int s_equal(const char*a,const char*b){unsigned int i=0;for(;a[i]&&b[i]&&i<1024;i++)if(a[i]!=b[i])return 0;return a[i]==b[i];}
static void path_suffix(char*out,const char*filename){s_copy(out,folder);unsigned int n=s_len(out),i=0;while(filename[i]&&n+i<2200){out[n+i]=filename[i];i++;}out[n+i]=0;}
static int setup(void){
 if(init_state)return original!=0;
 init_state=1;
 HMODULE self=GetModuleHandleA("mss32.dll");
 DWORD n=GetModuleFileNameA(self,folder,1900);
 if(!n||n>=1900)return 0;
 while(n && folder[n-1]!='\\' && folder[n-1]!='/')n--;
 folder[n]=0;
 path_suffix(real_path,"a3d_mss_real.dll");
 path_suffix(manifest_path,"a3d-miles-local.manifest");
 path_suffix(log_path,"a3d-v074-miles.log");
 original=LoadLibraryA(real_path);
 return original!=0;
}
static void report(const char*label,const char*value){
 char enabled[4];DWORD c=GetEnvironmentVariableA("A3D_MILES_TRACE",enabled,sizeof(enabled));
 if(c!=1||enabled[0]!='1')return;
 if(!setup())return;
 HANDLE h=CreateFileA(log_path,FILE_APPEND_DATA,FILE_SHARE_READ,0,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
 if(h==INVALID_HANDLE_VALUE)return;
 /* File opened for append, bounded at 64 KiB (no unbounded tracing). */
 DWORD end=SetFilePointer(h,0,0,FILE_END);
 if(end!=0xffffffffUL && end<65000UL){DWORD wrote;
  WriteFile(h,label,s_len(label),&wrote,0);
  if(value)WriteFile(h,value,s_len(value),&wrote,0);
  WriteFile(h,"\r\n",2,&wrote,0);
 }
 CloseHandle(h);
}
static void dec(char *out,unsigned int n){char b[20];unsigned int j=0,i=0;do{b[j++]=(char)('0'+n%10);n/=10;}while(n&&j<19);while(j)out[i++]=b[--j];out[i]=0;}
/* The real Miles library exports these as stdcall functions in most 5/6.x builds.
 * The export generation tool verifies names/ordinals before allowing a build. */
typedef int (STDCALL *PEnum)(void**,void**,char**);
typedef int (STDCALL *POpen)(void*);
int STDCALL a3d_intercept_enumerate(void**next,void**provider,char**name){
 if(!setup()){report("MILES_REAL_LIBRARY_MISSING",0);return 0;}
 PEnum f=(PEnum)GetProcAddress(original,"_AIL_enumerate_3D_providers@12");
 if(!f)f=(PEnum)GetProcAddress(original,"AIL_enumerate_3D_providers");
 if(!f){report("MILES_ENUM_EXPORT_MISSING",0);return 0;}
 int result=f(next,provider,name);
 if(result){report("PROVIDER_ENUM ",name&&*name?*name:"(unnamed)");}
 else report("PROVIDER_ENUM_END",0);
 return result;
}
int STDCALL a3d_intercept_open(void*provider){
 if(!setup()){report("MILES_REAL_LIBRARY_MISSING",0);return -1;}
 POpen f=(POpen)GetProcAddress(original,"_AIL_open_3D_provider@4");
 if(!f)f=(POpen)GetProcAddress(original,"AIL_open_3D_provider");
 if(!f){report("MILES_OPEN_EXPORT_MISSING",0);return -1;}
 report("PROVIDER_OPEN_BEGIN",0);
 /* Windows documented activation-context API: COM activation on THIS thread
  * searches the active context, then HKCU/HKLM as fallback. We deactivate
  * reliably on ALL paths before returning to caller. */
 ACTCTXA a;unsigned char *p=(unsigned char*)&a;
 for(unsigned int i=0;i<sizeof(a);i++)p[i]=0;
 a.cbSize=sizeof(a);a.lpSource=manifest_path;
 HANDLE ctx=CreateActCtxA(&a);ULONG_PTR cookie=0;
 int active=(ctx!=INVALID_HANDLE_VALUE && ctx!=0 && ActivateActCtx(ctx,&cookie));
 if(active)report("A3D_LOCAL_ACTCTX_ACTIVE",0);
 else {char buf[20];dec(buf,GetLastError());report("A3D_LOCAL_ACTCTX_FAILED_WIN32 ",buf);}
 int ret=f(provider);
 {char buf[20];dec(buf,(unsigned int)ret);report("PROVIDER_OPEN_RESULT ",buf);}
 if(active)DeactivateActCtx(0,cookie);
 if(ctx!=INVALID_HANDLE_VALUE&&ctx)ReleaseActCtx(ctx);
 return ret;
}
