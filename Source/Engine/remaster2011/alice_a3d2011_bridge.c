/* Alice 2011 remaster + VorpalFix 4.2.1 A3D 2.0 selector bridge, experimental, x86-only.
 * Does NOT write or change alice.exe on disk. Changes six bytes in the
 * suspended CHILD PROCESS MEMORY, after strict signature checks.
 * Source input: SHA256-pinned Alice 2011 32-bit remaster selector disassembly.
 * No DLL overwrite, no injection into other processes; this launcher starts
 * only the adjacent alice.exe and declines unknown or patched versions.
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
static void put8(BYTE *buf,DWORD *at,BYTE b){buf[(*at)++]=b;}
static void put32(BYTE *buf,DWORD *at,DWORD v){u32(buf+*at,v);*at+=4;}
static void rel32(BYTE *buf,DWORD pos,DWORD instr_addr,DWORD dest){u32(buf+pos,dest-(instr_addr+pos+4));}
/* 2011 remaster, SHA256 08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50
 * Verified on the exact uploaded PE32 image. The selector at 0x467492 begins
 * by PUSHing the address of "A3D" and calling its case-insensitive comparator.
 * We hijack ONLY that one PUSH while the child is suspended. Other values are
 * deliberately passed back to the untouched original selector at 0x467497.
 * A3D2 selects the Miles provider "Aureal A3D 2.0 (TM)" (20 bytes incl NUL),
 * sets classification ESI=5 (same type as original A3D provider), and resumes
 * at the normal Miles enumerate/open sequence at 0x467546.
 * The user-owned alice.exe bytes on disk are never touched.
 */
#define REMASTER_PATCH_ADDRESS 0x00467492u
#define REMASTER_FALLBACK_ADDRESS 0x00467497u
#define REMASTER_SUCCESS_ADDRESS 0x00467546u

static DWORD gen_stub(BYTE *b,DWORD base){
  DWORD n=0,jumps[5],go_success,go_fallback,fb,i;
  const BYTE name[]="Aureal A3D 2.0 (TM)";
  /* EBP is the untouched first argument to the remaster selector. Do not
   * alter EBP or EBX; the original function depends on both registers. */
  put8(b,&n,0x8a);put8(b,&n,0x45);put8(b,&n,0x00); /* mov al,[ebp] */
  put8(b,&n,0x0c);put8(b,&n,0x20); /* OR 'A' to lowercase 'a' */
  put8(b,&n,0x3c);put8(b,&n,0x61);
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[0]=n;put32(b,&n,0);
  put8(b,&n,0x80);put8(b,&n,0x7d);put8(b,&n,0x01);put8(b,&n,0x33); /* '3' */
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[1]=n;put32(b,&n,0);
  put8(b,&n,0x8a);put8(b,&n,0x45);put8(b,&n,0x02); /* [ebp+2] */
  put8(b,&n,0x0c);put8(b,&n,0x20);
  put8(b,&n,0x3c);put8(b,&n,0x64); /* 'd' */
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[2]=n;put32(b,&n,0);
  put8(b,&n,0x80);put8(b,&n,0x7d);put8(b,&n,0x03);put8(b,&n,0x32); /* '2' */
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[3]=n;put32(b,&n,0);
  put8(b,&n,0x80);put8(b,&n,0x7d);put8(b,&n,0x04);put8(b,&n,0x00); /* NUL */
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[4]=n;put32(b,&n,0);
  /* The already allocated local provider buffer is [ESP+0x20], 32 bytes.
   * The selected name is 19 ASCII characters plus zero terminator. */
  for(i=0;i<sizeof(name);i+=4){
    put8(b,&n,0xc7);put8(b,&n,0x44);put8(b,&n,0x24);
    put8(b,&n,(BYTE)(0x20+i));
    put8(b,&n,name[i]);put8(b,&n,name[i+1]);put8(b,&n,name[i+2]);put8(b,&n,name[i+3]);
  }
  put8(b,&n,0xbe);put32(b,&n,5); /* mov esi,5: Miles A3D class */
  put8(b,&n,0xe9);go_success=n;put32(b,&n,0);
  fb=n;
  for(i=0;i<5;i++)rel32(b,jumps[i],base,base+fb);
  /* Replay the displaced original instruction for all other selectors,
   * including a3d, eax, eax2, dolby, miles, software, unknown. */
  put8(b,&n,0x68);put32(b,&n,0x005274e4u); /* push "A3D" */
  put8(b,&n,0xe9);go_fallback=n;put32(b,&n,0);
  rel32(b,go_success,base,REMASTER_SUCCESS_ADDRESS);
  rel32(b,go_fallback,base,REMASTER_FALLBACK_ADDRESS);
  return n;
}

static int patch_child(HANDLE p,HANDLE err){
  BYTE sig[5],label[23],a3dstr[4],verify[5],stub[256],jump[5];
  DWORD old_protect=0,junk_protect=0,stubsize,remote;
  SIZE_T done=0; LPVOID mem;
  const BYTE expected[]={0x68,0xe4,0x74,0x52,0x00};
  const BYTE expected_label[]="Aureal A3D Interactive";
  const BYTE expected_a3d[]={ 'A','3','D',0 };
  if(!ReadProcessMemory(p,(LPCSTR)REMASTER_PATCH_ADDRESS,sig,5,&done)||done!=5||!eq(sig,expected,5)){
    out(err,"Refusing: remaster 2011 selector instruction is not the expected original.\r\n");return 0;}
  if(!ReadProcessMemory(p,(LPCSTR)0x005274ccu,label,23,&done)||done!=23||!eq(label,expected_label,23)){
    out(err,"Refusing: 2011 remaster A3D provider label mismatch.\r\n");return 0;}
  if(!ReadProcessMemory(p,(LPCSTR)0x005274e4u,a3dstr,4,&done)||done!=4||!eq(a3dstr,expected_a3d,4)){
    out(err,"Refusing: 2011 remaster A3D selector string mismatch.\r\n");return 0;}
  /* Check the untouched next instruction too. This rejects unrelated
   * executable revisions even if they happen to have the same PUSH bytes. */
  {const BYTE next[]={0x55,0xe8,0x73,0xe3,0xfb,0xff}; BYTE got[6];
   if(!ReadProcessMemory(p,(LPCSTR)REMASTER_FALLBACK_ADDRESS,got,6,&done)||done!=6||!eq(got,next,6)){
    out(err,"Refusing: unexpected 2011 remaster control-flow signature.\r\n");return 0;}}
  mem=VirtualAllocEx(p,0,4096,MEM_RESERVE|MEM_COMMIT,PAGE_EXECUTE_READWRITE);
  if(!mem){out(err,"Failed to allocate bridge memory.\r\n");return 0;}
  remote=(DWORD)mem;stubsize=gen_stub(stub,remote);
  if(stubsize>sizeof(stub)||!WriteProcessMemory(p,mem,(LPCSTR)stub,stubsize,&done)||done!=stubsize){
    out(err,"Failed to write RAM-only remaster selector stub.\r\n");return 0;}
  jump[0]=0xe9;u32(jump+1,remote-(REMASTER_PATCH_ADDRESS+5u));
  if(!VirtualProtectEx(p,(LPVOID)REMASTER_PATCH_ADDRESS,5,PAGE_EXECUTE_READWRITE,&old_protect)){
    out(err,"Failed to adjust suspended child's selector page protection.\r\n");return 0;}
  done=0;
  {BOOL ok=WriteProcessMemory(p,(LPVOID)REMASTER_PATCH_ADDRESS,(LPCSTR)jump,5,&done);
   VirtualProtectEx(p,(LPVOID)REMASTER_PATCH_ADDRESS,5,old_protect,&junk_protect);
   if(!ok||done!=5){out(err,"Failed to patch child-process memory.\r\n");return 0;}}
  done=0;
  if(!ReadProcessMemory(p,(LPCSTR)REMASTER_PATCH_ADDRESS,verify,5,&done)||done!=5||!eq(jump,verify,5)){
    out(err,"Failed to verify the selector patch in child process.\r\n");return 0;}
  FlushInstructionCache(p,(LPCSTR)mem,stubsize);
  FlushInstructionCache(p,(LPCSTR)REMASTER_PATCH_ADDRESS,5);
  return 1;
}

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
  if(!slash){out(err,"Place alice-a3d2011-bridge.exe beside alice.exe.\r\n");ExitProcess(2);}
  slash[1]=0;
  {const char *exe="alice.exe";char *p=slash+1;while(*exe)*p++=*exe++;*p=0;}
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
    out(err,"Failed to launch adjacent alice.exe.\r\n");ExitProcess(3);}
  if(!patch_child(proc.hProcess,err) || !activate_child(&proc,game_exe,err)){
    TerminateProcess(proc.hProcess,4);CloseHandle(proc.hThread);CloseHandle(proc.hProcess);
    ExitProcess(4);
  }
  out(info,"Alice 2011 A3D2 selector bridge installed in child memory; EXE file unchanged.\r\n");
  out(info,"a3d => stock A3D Interactive; a3d2 => Aureal A3D 2.0 (TM).\r\n");
  if(ResumeThread(proc.hThread)==0xffffffffu){
    TerminateProcess(proc.hProcess,5);CloseHandle(proc.hThread);CloseHandle(proc.hProcess);ExitProcess(5);}
  WaitForSingleObject(proc.hProcess,WAIT_INFINITE);
  GetExitCodeProcess(proc.hProcess,&exit_code);
  CloseHandle(proc.hThread);CloseHandle(proc.hProcess);
  ExitProcess((UINT)exit_code);
}
