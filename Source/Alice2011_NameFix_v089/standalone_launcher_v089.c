/* Aufake3D v0.8.9 standalone, native PE32 self-extracting diagnostic launcher.
   No CRT, no external modules except Windows Kernel32 and built-in PowerShell.
   Payload is the original audit-friendly ZIP appended to this EXE.
   Writes only to a sibling Aufake3D_v089_Extracted folder.
   Builds with clang-cl/LLD and an import lib generated from kernel32.def. */
#define STDCALL __attribute__((stdcall))
#define IMPORT __declspec(dllimport)
typedef unsigned long DWORD;
typedef unsigned short WORD;
typedef unsigned char BYTE;
typedef unsigned short wchar_t;
typedef int BOOL;
typedef void* HANDLE;
typedef void* HMODULE;
typedef const wchar_t* LPCWSTR;
typedef wchar_t* LPWSTR;
typedef const void* LPCVOID;
typedef void* LPVOID;
#define INVALID_HANDLE_VALUE ((HANDLE)-1)
#define GENERIC_READ 0x80000000UL
#define GENERIC_WRITE 0x40000000UL
#define FILE_SHARE_READ 1
#define CREATE_ALWAYS 2
#define OPEN_EXISTING 3
#define FILE_ATTRIBUTE_NORMAL 128
#define FILE_BEGIN 0
#define INFINITE 0xFFFFFFFFUL
#define STD_OUTPUT_HANDLE ((DWORD)-11)
#define STD_INPUT_HANDLE ((DWORD)-10)
typedef struct {DWORD cb;LPWSTR lpReserved,lpDesktop,lpTitle;DWORD dwX,dwY,dwXSize,dwYSize,dwXCountChars,dwYCountChars,dwFillAttribute,dwFlags;WORD wShowWindow,cbReserved2;BYTE*lpReserved2;HANDLE hStdInput,hStdOutput,hStdError;} STARTUPINFOW;
typedef struct {HANDLE hProcess,hThread;DWORD dwProcessId,dwThreadId;} PROCESS_INFORMATION;
IMPORT DWORD STDCALL GetModuleFileNameW(HMODULE,LPWSTR,DWORD);
IMPORT HANDLE STDCALL CreateFileW(LPCWSTR,DWORD,DWORD,LPVOID,DWORD,DWORD,HANDLE);
IMPORT DWORD STDCALL GetFileSize(HANDLE,DWORD*);
IMPORT DWORD STDCALL SetFilePointer(HANDLE,long,long*,DWORD);
IMPORT BOOL STDCALL ReadFile(HANDLE,LPVOID,DWORD,DWORD*,LPVOID);
IMPORT BOOL STDCALL WriteFile(HANDLE,LPCVOID,DWORD,DWORD*,LPVOID);
IMPORT BOOL STDCALL CloseHandle(HANDLE);
IMPORT BOOL STDCALL CreateDirectoryW(LPCWSTR,LPVOID);
IMPORT BOOL STDCALL SetEnvironmentVariableW(LPCWSTR,LPCWSTR);
IMPORT BOOL STDCALL CreateProcessW(LPCWSTR,LPWSTR,LPVOID,LPVOID,BOOL,DWORD,LPVOID,LPCWSTR,STARTUPINFOW*,PROCESS_INFORMATION*);
IMPORT DWORD STDCALL WaitForSingleObject(HANDLE,DWORD);
IMPORT BOOL STDCALL GetExitCodeProcess(HANDLE,DWORD*);
IMPORT HANDLE STDCALL GetStdHandle(DWORD);
IMPORT BOOL STDCALL WriteConsoleW(HANDLE,LPCVOID,DWORD,DWORD*,LPVOID);
IMPORT BOOL STDCALL ReadConsoleW(HANDLE,LPVOID,DWORD,DWORD*,LPVOID);
IMPORT void STDCALL ExitProcess(DWORD);
static wchar_t me[4096],dir[4096],zip[4096],cmd[8192];
static BYTE block[65536];
static const BYTE tag[16]={'A','U','F','A','K','E','3','D','0','8','9','Z','I','P','!','!'};
static DWORD wc(const wchar_t*s){DWORD n=0;while(s[n]&&n<8000)n++;return n;}
static int append(wchar_t*d,DWORD cap,const wchar_t*s){DWORD n=wc(d),i=0;while(s[i]){if(n+1>=cap)return 0;d[n++]=s[i++];}d[n]=0;return 1;}
static void put(const wchar_t*s){DWORD n=0;WriteConsoleW(GetStdHandle(STD_OUTPUT_HANDLE),s,wc(s),&n,0);}
static void pause_end(void){wchar_t tmp[16];DWORD n=0;put(L"\nPress Enter to close this window...\n");ReadConsoleW(GetStdHandle(STD_INPUT_HANDLE),tmp,15,&n,0);}
static void zero(void *ptr,DWORD n){BYTE*p=(BYTE*)ptr;while(n--)*p++=0;}
static int launch(wchar_t *command,DWORD *exitcode){
 STARTUPINFOW si;PROCESS_INFORMATION pi;
 zero(&si,sizeof(si));zero(&pi,sizeof(pi));si.cb=sizeof(si);
 if(!CreateProcessW(0,command,0,0,0,0,0,0,&si,&pi))return 0;
 WaitForSingleObject(pi.hProcess,INFINITE);
 if(!GetExitCodeProcess(pi.hProcess,exitcode))*exitcode=999;
 CloseHandle(pi.hThread);CloseHandle(pi.hProcess);return 1;
}
static int extract(void){
 HANDLE in=INVALID_HANDLE_VALUE,out=INVALID_HANDLE_VALUE;DWORD len,got=0,sz,done=0,wrote=0;
 BYTE foot[20];
 in=CreateFileW(me,GENERIC_READ,FILE_SHARE_READ,0,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,0);
 if(in==INVALID_HANDLE_VALUE)return 0;
 sz=GetFileSize(in,0);
 if(sz==0xFFFFFFFFUL||sz<20)goto fail;
 if(SetFilePointer(in,(long)(sz-20),0,FILE_BEGIN)==0xFFFFFFFFUL)goto fail;
 if(!ReadFile(in,foot,20,&got,0)||got!=20)goto fail;
 for(unsigned i=0;i<16;i++)if(foot[i]!=tag[i])goto fail;
 len=(DWORD)foot[16]|((DWORD)foot[17]<<8)|((DWORD)foot[18]<<16)|((DWORD)foot[19]<<24);
 if(len<8192||len>30000000UL||len>sz-20)goto fail;
 if(SetFilePointer(in,(long)(sz-20-len),0,FILE_BEGIN)==0xFFFFFFFFUL)goto fail;
 out=CreateFileW(zip,GENERIC_WRITE,0,0,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
 if(out==INVALID_HANDLE_VALUE)goto fail;
 while(done<len){DWORD chunk=(len-done<65536?len-done:65536);
  if(!ReadFile(in,block,chunk,&got,0)||got!=chunk)goto fail;
  if(!WriteFile(out,block,chunk,&wrote,0)||wrote!=chunk)goto fail;
  done+=chunk;
 }
 CloseHandle(out);CloseHandle(in);return 1;
 fail:
 if(out!=INVALID_HANDLE_VALUE)CloseHandle(out);
 if(in!=INVALID_HANDLE_VALUE)CloseHandle(in);
 return 0;
}
void STDCALL mainCRTStartup(void){
 DWORD rc=0,n=GetModuleFileNameW(0,me,4096);
 put(L"Aufake3D v0.8.9 - dedicated Alice A3D2 provider naming diagnostic\n");
 put(L"Preserves your original Alice executable and Miles DLL.\n");
 put(L"A3D gain 5.0: reduce speaker/headphone volume first.\n\n");
 if(n==0||n>=4000){put(L"Cannot locate executable.\n");pause_end();ExitProcess(2);}
 for(DWORD i=0;i<n;i++)dir[i]=me[i];dir[n]=0;
 while(n>0&&dir[n-1]!=L'\\'&&dir[n-1]!=L'/')n--;
 dir[n]=0;
 if(!append(dir,4096,L"Aufake3D_v089_Extracted")){put(L"Path too long.\n");pause_end();ExitProcess(2);}
 if(!CreateDirectoryW(dir,0)){
  // Existing extraction directory is allowed; only our named files will be overwritten.
 }
 for(DWORD i=0;i<wc(dir);i++)zip[i]=dir[i];zip[wc(dir)]=0;
 if(!append(zip,4096,L"\\Aufake3D_v089_Payload.zip")){put(L"Path too long.\n");pause_end();ExitProcess(2);}
 if(!extract()){put(L"Embedded ZIP extraction failed.\n");pause_end();ExitProcess(3);}
 SetEnvironmentVariableW(L"AUFAKE_ZIP",zip);
 SetEnvironmentVariableW(L"AUFAKE_ROOT",dir);
 put(L"Extracting the bundled test package...\n");
 const wchar_t *expand=L"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"try { Expand-Archive -LiteralPath $env:AUFAKE_ZIP -DestinationPath $env:AUFAKE_ROOT -Force -ErrorAction Stop; exit 0 } catch { Write-Host $_; exit 1 }\"";
 for(DWORD i=0;i<=wc(expand);i++)cmd[i]=expand[i];
 if(!launch(cmd,&rc)||rc){put(L"PowerShell failed to unpack the package.\n");pause_end();ExitProcess(4);}
 put(L"Running targeted A3D2 provider naming control and corrected display test...\n");
 put(L"Two Alice naming-control sessions will launch. Close each to advance.\n");
 // PowerShell script path can contain spaces: pass through environment to avoid quoting errors.
 const wchar_t *run=L"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"& (Join-Path $env:AUFAKE_ROOT 'RUN_AUFAKE3D_V089_AUTOTEST.ps1'); exit $LASTEXITCODE\"";
 for(DWORD i=0;i<=wc(run);i++)cmd[i]=run[i];
 if(!launch(cmd,&rc)){put(L"Could not launch Windows PowerShell.\n");rc=5;}
 put(L"\nDiagnostic files saved in:\n");put(dir);put(L"\\results\n");
 put(L"Upload the newest Aufake3D-v089-*.zip result.\n");
 pause_end();ExitProcess(rc);
}
