/* v0.7.4b: independent no-game loader, export and SAFE function-call preflight.
 * Must run from isolated A3D-Probe folder, NOT next to VorpalFix winmm.dll.
 * No Miles provider is opened, no real game launched, no COM registration.
 */
#define STDCALL __attribute__((stdcall))
#define IMPORT __declspec(dllimport)
typedef unsigned long DWORD;
typedef void *HANDLE;
typedef void *HMODULE;
#define GENERIC_WRITE 0x40000000UL
#define FILE_SHARE_READ 1UL
#define CREATE_ALWAYS 2UL
#define FILE_ATTRIBUTE_NORMAL 0x80UL
#define INVALID_HANDLE_VALUE ((HANDLE)(-1))
IMPORT HMODULE STDCALL LoadLibraryA(const char*);
IMPORT HMODULE STDCALL GetModuleHandleA(const char*);
IMPORT void* STDCALL GetProcAddress(HMODULE,const char*);
IMPORT DWORD STDCALL GetLastError(void);
IMPORT DWORD STDCALL GetModuleFileNameA(HMODULE,char*,DWORD);
IMPORT const char* STDCALL GetCommandLineA(void);
IMPORT HANDLE STDCALL CreateFileA(const char*,DWORD,DWORD,void*,DWORD,DWORD,HANDLE);
IMPORT int STDCALL WriteFile(HANDLE,const void*,DWORD,DWORD*,void*);
IMPORT int STDCALL CloseHandle(HANDLE);
IMPORT HANDLE STDCALL GetStdHandle(DWORD);
IMPORT void STDCALL ExitProcess(DWORD);
static const char *names[]={
#include "miles_original_exports.inc"
};
static const unsigned short ordinals[]={
#include "miles_original_ordinals.inc"
};
static HANDLE file_log,out;
static DWORD slen(const char*s){DWORD n=0;while(s&&s[n]&&n<4096)n++;return n;}
static void put(const char*s){DWORD wrote=0,n=slen(s);
 if(file_log&&file_log!=INVALID_HANDLE_VALUE)WriteFile(file_log,s,n,&wrote,0);
 if(out&&out!=INVALID_HANDLE_VALUE)WriteFile(out,s,n,&wrote,0);
}
static void number(DWORD v){char b[16],o[16];DWORD i=0,j=0;
 do{b[i++]=(char)('0'+v%10);v/=10;}while(v&&i<15);
 while(i)o[j++]=b[--i];o[j]=0;put(o);
}
static void result(const char*s,DWORD n){put(s);number(n);put("\r\n");}
static void show_image(HMODULE h){char p[1024];DWORD n=GetModuleFileNameA(h,p,sizeof(p));
 if(n && n<sizeof(p)){p[n]=0;put(p);put("\r\n");}
}
void STDCALL mainCRTStartup(void){
 int fail=0;DWORD err=0;
 file_log=CreateFileA("a3d-v074b-preflight.log",GENERIC_WRITE,FILE_SHARE_READ,0,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
 out=GetStdHandle((DWORD)-11);
 put("A3D v0.7.4b preflight: isolated DLL loader; NO GAME LAUNCHED\r\n");
 HMODULE original_before=GetModuleHandleA("a3d_mss_real.dll");
 if(original_before){put("FAIL: original Miles library was already loaded before proxy\r\n");fail=2;goto done;}
 HMODULE proxy=LoadLibraryA("SndDrivers\\mss32.dll");
 if(!proxy){result("FAIL: proxy LoadLibrary error ",GetLastError());fail=3;goto done;}
 put("Proxy: ");show_image(proxy);
 if(GetModuleHandleA("a3d_mss_real.dll")){
   put("FAIL: original Miles library loaded eagerly during proxy LoadLibrary\r\n");fail=4;goto done;
 }
 put("PASS: no eager dependency loading\r\n");
 DWORD failures=0;
 for(DWORD i=0;i<sizeof(ordinals)/sizeof(ordinals[0]);i++){
   void*p=GetProcAddress(proxy,names[i]);
   if(!p){put("FAIL name: ");put(names[i]);put("\r\n");failures++;}
   void*q=GetProcAddress(proxy,(const char*)(unsigned long)ordinals[i]);
   if(!q){put("FAIL ordinal: ");number(ordinals[i]);put("\r\n");failures++;}
   if(p&&q&&p!=q){put("FAIL differing addresses: ");put(names[i]);put("\r\n");failures++;}
 }
 result("Number of exports: ",sizeof(ordinals)/sizeof(ordinals[0]));
 result("Export lookup failures: ",failures);
 if(failures){fail=5;goto done;}
 if(GetModuleHandleA("a3d_mss_real.dll")){
  put("FAIL: symbol lookup improperly eager-loaded original library\r\n");fail=6;goto done;
 }
 /* A harmless original Miles hardware capability query to exercise a real thunk. */
 typedef int (STDCALL *cpu_query)(void);
 cpu_query fn=(cpu_query)GetProcAddress(proxy,"_AIL_MMX_available@0");
 if(!fn){put("FAIL: safe Miles function unavailable\r\n");fail=7;goto done;}
 put("Invoking _AIL_MMX_available@0 via proxy (no game audio)...\r\n");
 int got=fn();
 HMODULE original=GetModuleHandleA("a3d_mss_real.dll");
 if(!original){put("FAIL: original library did not load on first call\r\n");fail=8;goto done;}
 put("Original loaded app-locally: ");show_image(original);
 cpu_query direct=(cpu_query)GetProcAddress(original,"_AIL_MMX_available@0");
 if(!direct){put("FAIL: original query function not found\r\n");fail=9;goto done;}
 int expected=direct();
 if(got!=expected){put("FAIL: proxy CPU query result different from direct call\r\n");fail=10;goto done;}
 if(fn()!=direct()){put("FAIL: repeated cached call differs from direct\r\n");fail=11;goto done;}
 put("PASS: actual forwarded function call, cached call, and direct call agree\r\n");
 put("RESULT: PASS (loader, 331 exports, actual pass-through; GAME STILL UNTESTED)\r\n");
 done:
 if(fail){result("RESULT: FAIL code ",(DWORD)fail);}
 if(file_log&&file_log!=INVALID_HANDLE_VALUE)CloseHandle(file_log);
 ExitProcess(fail);
}
