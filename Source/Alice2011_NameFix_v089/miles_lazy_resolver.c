/* A3D v0.7.4b: import-free Miles ABI thunks with lazy original-DLL resolution.
 * This is pass-through ONLY: no A3D selection, COM, audio modification, registry,
 * external process access, or executable patching. The original game DLL remains
 * alongside this module under a3d_mss_real.dll and is never modified.
 *
 * The x86 trampolines preserve all arguments and the caller's original stack.
 * The resolver returns the ORIGINAL function address, then they tail-jump to it.
 * Forwarding is by checked ordinal from the exact original export inventory.
 *
 * The resolver NEVER runs in DllMain (this DLL has no DllMain).  Windows DLL
 * loader-lock constraints still apply to the host; the first import is lazily
 * loaded during a normal application function call, not during our load.
 */
#define STDCALL __attribute__((stdcall))
#define IMPORT __declspec(dllimport)
typedef unsigned long DWORD;
typedef int BOOL;
typedef void *HMODULE;
typedef void *FARPROC;
typedef void *HANDLE;
typedef struct {void *Ptr;} A3D_INIT_ONCE;
#define FROM_ADDRESS 0x00000004UL
#define UNCHANGED_REFCOUNT 0x00000002UL
#define FILE_APPEND_DATA 0x00000004UL
#define FILE_SHARE_READ 0x00000001UL
#define OPEN_ALWAYS 4UL
#define FILE_ATTRIBUTE_NORMAL 0x00000080UL
#define INVALID_HANDLE_VALUE ((HANDLE)(-1))
IMPORT BOOL STDCALL GetModuleHandleExA(DWORD,const char *,HMODULE *);
IMPORT DWORD STDCALL GetModuleFileNameA(HMODULE,char *,DWORD);
IMPORT HMODULE STDCALL LoadLibraryA(const char *);
IMPORT FARPROC STDCALL GetProcAddress(HMODULE,const char *);
IMPORT DWORD STDCALL GetLastError(void);
IMPORT BOOL STDCALL InitOnceExecuteOnce(A3D_INIT_ONCE*,BOOL (STDCALL*)(A3D_INIT_ONCE*,void*,void**),void*,void**);
IMPORT DWORD STDCALL GetEnvironmentVariableA(const char*,char*,DWORD);
IMPORT HANDLE STDCALL CreateFileA(const char*,DWORD,DWORD,void*,DWORD,DWORD,HANDLE);
IMPORT BOOL STDCALL WriteFile(HANDLE,const void*,DWORD,DWORD*,void*);
IMPORT BOOL STDCALL CloseHandle(HANDLE);
IMPORT void STDCALL ExitProcess(DWORD);

static A3D_INIT_ONCE once = {0};
static HMODULE original;
/* The build replaces COUNT with the original export count + 1. */
#ifndef A3D_MILES_SLOT_COUNT
#error A3D_MILES_SLOT_COUNT must be provided by the tailored builder
#endif
void *volatile target[A3D_MILES_SLOT_COUNT];
static char original_path[4096];
static char log_path[4096];
static DWORD nlen(const char*s){DWORD i=0;while(s&&s[i] && i<4095)i++;return i;}
static void cpy(char*d,const char*s){while((*d++=*s++)!=0) {}}
static void diag(const char *msg){
 char v[4]; if(GetEnvironmentVariableA("A3D_MILES_TRACE",v,sizeof(v))!=1 || v[0]!='1')return;
 HANDLE h=CreateFileA(log_path,FILE_APPEND_DATA,FILE_SHARE_READ,0,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
 if(h==(HANDLE)(-1))return;
 /* FILE_APPEND_DATA preserves each line; only initialization/failure logs are written. */
 DWORD n=nlen(msg),w=0;WriteFile(h,msg,n,&w,0); CloseHandle(h);
}
static BOOL STDCALL initialize(A3D_INIT_ONCE*once_arg,void*arg,void**context){
 (void)once_arg; (void)arg; (void)context;
 HMODULE self=0;
 if(!GetModuleHandleExA(FROM_ADDRESS|UNCHANGED_REFCOUNT,(const char*)&initialize,&self))return 0;
 DWORD n=GetModuleFileNameA(self,original_path,sizeof(original_path));
 if(!n||n>=sizeof(original_path)-32)return 0;
 while(n>0 && original_path[n-1]!='\\' && original_path[n-1]!='/')n--;
 original_path[n]=0;
 cpy(original_path+n,"a3d_mss_real.dll");
 cpy(log_path,original_path);
 cpy(log_path+n,"a3d-v074b-loader.log");
 diag("v074b: attempting app-local Miles load\r\n");
 original=LoadLibraryA(original_path);
 if(!original){diag("v074b: original Miles DLL failed loading\r\n");return 0;}
 diag("v074b: app-local Miles DLL loaded\r\n");
 return 1;
}
/* index IS the exact export ordinal; validated by the tailored build. */
void * __cdecl a3d_resolve(DWORD index){
 if(index==0 || index>=A3D_MILES_SLOT_COUNT)ExitProcess(126);
 if(!InitOnceExecuteOnce(&once,initialize,0,0) || !original){
   /* Do not jump to NULL and generate another obscure access violation. */
   ExitProcess(126);
 }
 void*p=(void*)GetProcAddress(original,(const char*)(unsigned long)index);
 if(!p){diag("v074b: original Miles export missing\r\n");ExitProcess(127);}
 /* Clang emits a native x86 LOCK CMPXCHG; no possibly missing Kernel32
  * pointer-interlocked export is imported by the DLL loader. */
 void*expected=0;
 if(__atomic_compare_exchange_n(&target[index],&expected,p,0,__ATOMIC_SEQ_CST,__ATOMIC_SEQ_CST))return p;
 return expected;
}
/* A pointer-table access shim in assembly jumps directly after first call. */
