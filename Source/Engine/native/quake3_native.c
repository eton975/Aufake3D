/* Quake III Arena 1.17 A3D runtime selector bridge, experimental, x86-only.
 * Does NOT write or change quake3.exe on disk. Changes six bytes in the
 * suspended CHILD PROCESS MEMORY, after strict signature checks.
 * Source input: checked Quake III 1.17 selector instruction signatures below.
 * No DLL overwrite, no injection into other processes; this launcher starts
 * only the adjacent quake3.exe and declines unknown or patched versions.
 */
#define STDCALL __stdcall
#define DLLIMPORT __declspec(dllimport)
typedef void *HANDLE;
typedef void *LPVOID;
typedef unsigned long DWORD;
typedef unsigned int UINT;
typedef int BOOL;
typedef unsigned long SIZE_T;
typedef const char *LPCSTR;
typedef char *LPSTR;
typedef unsigned char BYTE;
#define FALSE 0
#define CREATE_SUSPENDED 0x00000004u
#define MEM_COMMIT 0x00001000u
#define MEM_RESERVE 0x00002000u
#define PAGE_EXECUTE_READWRITE 0x40u
#define WAIT_INFINITE 0xffffffffu
#define STD_OUTPUT_HANDLE ((DWORD)-11)
#define STD_ERROR_HANDLE ((DWORD)-12)

typedef struct {
  DWORD cb; LPSTR lpReserved; LPSTR lpDesktop; LPSTR lpTitle;
  DWORD dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars;
  DWORD dwFillAttribute, dwFlags;
  unsigned short wShowWindow, cbReserved2;
  BYTE *lpReserved2;
  HANDLE hStdInput, hStdOutput, hStdError;
} STARTUPINFOA;
typedef struct {
  HANDLE hProcess; HANDLE hThread; DWORD dwProcessId; DWORD dwThreadId;
} PROCESS_INFORMATION;

DLLIMPORT DWORD STDCALL GetModuleFileNameA(HANDLE, LPSTR, DWORD);
DLLIMPORT LPSTR STDCALL GetCommandLineA(void);
DLLIMPORT BOOL STDCALL CreateProcessA(LPCSTR, LPSTR, LPVOID, LPVOID, BOOL, DWORD,
                                      LPVOID, LPCSTR, STARTUPINFOA *, PROCESS_INFORMATION *);
DLLIMPORT BOOL STDCALL ReadProcessMemory(HANDLE, LPCSTR, LPVOID, SIZE_T, SIZE_T *);
DLLIMPORT BOOL STDCALL WriteProcessMemory(HANDLE, LPVOID, LPCSTR, SIZE_T, SIZE_T *);
DLLIMPORT LPVOID STDCALL VirtualAllocEx(HANDLE, LPVOID, SIZE_T, DWORD, DWORD);
DLLIMPORT BOOL STDCALL VirtualProtectEx(HANDLE, LPVOID, SIZE_T, DWORD, DWORD *);
DLLIMPORT BOOL STDCALL FlushInstructionCache(HANDLE, LPCSTR, SIZE_T);
DLLIMPORT DWORD STDCALL ResumeThread(HANDLE);
DLLIMPORT DWORD STDCALL WaitForSingleObject(HANDLE, DWORD);
DLLIMPORT BOOL STDCALL GetExitCodeProcess(HANDLE, DWORD *);
DLLIMPORT BOOL STDCALL TerminateProcess(HANDLE, UINT);
DLLIMPORT BOOL STDCALL CloseHandle(HANDLE);
DLLIMPORT HANDLE STDCALL GetStdHandle(DWORD);
DLLIMPORT BOOL STDCALL WriteFile(HANDLE, LPCSTR, DWORD, DWORD *, LPVOID);
DLLIMPORT void STDCALL ExitProcess(UINT);

static DWORD slen(const char *s) { DWORD n=0; while(s[n])n++;return n; }
static void out(HANDLE h,const char *s) { DWORD n=0;WriteFile(h,s,slen(s),&n,0); }
static int eq(const BYTE *p,const BYTE *q,DWORD n){DWORD i;for(i=0;i<n;i++)if(p[i]!=q[i])return 0;return 1;}
static void u32(BYTE *p,DWORD n){p[0]=(BYTE)n;p[1]=(BYTE)(n>>8);p[2]=(BYTE)(n>>16);p[3]=(BYTE)(n>>24);}
static int patch_child(HANDLE p,HANDLE err){BYTE sig[16];SIZE_T done=0;
 const BYTE expected0[]={0x51,0x56,0x8b,0x74,0x24,0x10,0x85,0xf6,0xc7,0x44,0x24,0x4,0x0,0x0,0x0,0x0};
 if(!ReadProcessMemory(p,(LPCSTR)0x402f90u,sig,16,&done)||done!=16||!eq(sig,expected0,16)){out(err,"Unsupported Quake III executable signature.\r\n");return 0;}
 const BYTE expected1[]={0x24,0x2c,0xfa,0x92,0x3c,0x25,0xd2,0x11,0x90,0xfb,0x0,0x60,0x8,0xa1,0xf4,0x41};
 if(!ReadProcessMemory(p,(LPCSTR)0x4af300u,sig,16,&done)||done!=16||!eq(sig,expected1,16)){out(err,"Unsupported Quake III executable signature.\r\n");return 0;}
 const BYTE expected2[]={0x80,0x2,0xc4,0xe4,0xba,0xcc,0xd2,0x11,0x9d,0xcf,0x0,0x50,0x4,0x11,0x58,0x2f};
 if(!ReadProcessMemory(p,(LPCSTR)0x4af340u,sig,16,&done)||done!=16||!eq(sig,expected2,16)){out(err,"Unsupported Quake III executable signature.\r\n");return 0;}
return 1;}
#include "../native_activation.inc"
static char path[2048];
static char cmd[2300];
static char game_exe[2048];
void mainCRTStartup(void){
  char *slash=0,*i;DWORD k,exit_code=1;
  PROCESS_INFORMATION proc={0};STARTUPINFOA start={0};
  HANDLE err=GetStdHandle(STD_ERROR_HANDLE),info=GetStdHandle(STD_OUTPUT_HANDLE);
  k=GetModuleFileNameA(0,path,sizeof(path));
  if(!k||k>=sizeof(path)-16){out(err,"Could not determine launcher directory.\r\n");ExitProcess(2);}
  for(i=path;*i;i++)if(*i=='\\'||*i=='/')slash=i;
  if(!slash){out(err,"Place quake3-a3d-native.exe beside quake3.exe.\r\n");ExitProcess(2);}
  slash[1]=0;
  {const char *exe="quake3.exe";char *p=slash+1;while(*exe)*p++=*exe++;*p=0;}
  {DWORD z=0;while(path[z]){game_exe[z]=path[z];z++;}game_exe[z]=0;}
  cmd[0]='"';k=1;
  for(i=path;*i&&k<sizeof(cmd)-3;i++)cmd[k++]=*i;
  cmd[k++]='"';cmd[k]=0;
  /* Forward optional command-line game arguments after launcher name. */
  {const char *args=GetCommandLineA();
   if(*args=='"'){args++;while(*args&&*args!='"')args++;if(*args)args++;}
   else while(*args&&*args!=' '&&*args!='\t')args++;
   while(*args==' '||*args=='\t')args++;
   if(*args){cmd[k++]=' ';while(*args&&k<sizeof(cmd)-1)cmd[k++]=*args++;cmd[k]=0;}}
  start.cb=sizeof(start);
  /* Use the game directory as CWD to preserve resource/config resolution. */
  *(slash+1)=0; /* path becomes directory after cmd is constructed */
  if(!CreateProcessA(0,cmd,0,0,FALSE,CREATE_SUSPENDED,0,path,&start,&proc)){
    out(err,"Failed to launch adjacent quake3.exe.\r\n");ExitProcess(3);}
  if(!patch_child(proc.hProcess,err) || !activate_child(&proc,game_exe,err)){
    TerminateProcess(proc.hProcess,4);CloseHandle(proc.hThread);CloseHandle(proc.hProcess);
    ExitProcess(4);
  }
  out(info,"Quake III native A3D activation installed in child memory; executable file unchanged.\r\n");
  out(info,"Use the Quake III s_enable_a3d command to enable A3D.\r\n");
  if(ResumeThread(proc.hThread)==0xffffffffu){
    TerminateProcess(proc.hProcess,5);CloseHandle(proc.hThread);CloseHandle(proc.hProcess);ExitProcess(5);}
  WaitForSingleObject(proc.hProcess,WAIT_INFINITE);
  GetExitCodeProcess(proc.hProcess,&exit_code);
  CloseHandle(proc.hThread);CloseHandle(proc.hProcess);
  ExitProcess((UINT)exit_code);
}
