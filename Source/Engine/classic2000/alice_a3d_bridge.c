/* Alice A3D 1.x / 2.0 runtime selector bridge, experimental, x86-only.
 * Does NOT write or change alice.exe on disk. Changes six bytes in the
 * suspended CHILD PROCESS MEMORY, after strict signature checks.
 * Source input: original Alice 2000 2,209,835-byte build selector disassembly.
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
static DWORD gen_stub(BYTE *b,DWORD base){
  DWORD n=0,jumps[5],rel_to_end_1,rel_to_end_2,fb;
  const BYTE name[]="Aureal A3D 2.0 (TM)"; /* 20 bytes incl NUL */
  DWORD i;
  /* Test one byte at a time: no four-byte read past short cvar strings. */
  put8(b,&n,0x8a);put8(b,&n,0x03); /* mov al, [ebx] */
  put8(b,&n,0x0c);put8(b,&n,0x20); /* or al, 0x20 */
  put8(b,&n,0x3c);put8(b,&n,0x61); /* cmp al, 'a' */
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[0]=n;put32(b,&n,0);
  put8(b,&n,0x80);put8(b,&n,0x7b);put8(b,&n,0x01);put8(b,&n,0x33); /* [ebx+1]=='3' */
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[1]=n;put32(b,&n,0);
  put8(b,&n,0x8a);put8(b,&n,0x43);put8(b,&n,0x02); /* mov al,[ebx+2] */
  put8(b,&n,0x0c);put8(b,&n,0x20); /* lowercase */
  put8(b,&n,0x3c);put8(b,&n,0x64); /* 'd' */
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[2]=n;put32(b,&n,0);
  put8(b,&n,0x80);put8(b,&n,0x7b);put8(b,&n,0x03);put8(b,&n,0x32); /* '2' */
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[3]=n;put32(b,&n,0);
  put8(b,&n,0x80);put8(b,&n,0x7b);put8(b,&n,0x04);put8(b,&n,0x00); /* NUL */
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[4]=n;put32(b,&n,0);
  /* Copy "Aureal A3D 2.0 (TM)" into the 32-byte provider-name
   * local buffer at [esp+0x20] (no stack change). */
  for(i=0;i<20;i+=4){
    put8(b,&n,0xc7);put8(b,&n,0x44);put8(b,&n,0x24);
    put8(b,&n,(BYTE)(0x20+i));
    put8(b,&n,name[i]);put8(b,&n,name[i+1]);put8(b,&n,name[i+2]);put8(b,&n,name[i+3]);
  }
  /* The stock A3D Interactive provider uses classification 5. */
  put8(b,&n,0xbe);put32(b,&n,5);
  put8(b,&n,0xe9);rel_to_end_1=n;put32(b,&n,0);
  fb=n;
  for(i=0;i<5;i++)rel32(b,jumps[i],base,base+fb);
  /* Fallback for ANY other unrecognised setting: retain original "unknown". */
  {const BYTE old[] = {0x8b,0x0d,0x70,0xa4,0x51,0x00,
                       0x8b,0x15,0x74,0xa4,0x51,0x00,
                       0x89,0x4c,0x24,0x20,
                       0x89,0x54,0x24,0x24};
   for(i=0;i<sizeof(old);i++)put8(b,&n,old[i]);}
  put8(b,&n,0xe9);rel_to_end_2=n;put32(b,&n,0);
  rel32(b,rel_to_end_1,base,0x0046f27au);
  rel32(b,rel_to_end_2,base,0x0046f27au);
  return n;
}

static int patch_child(HANDLE p,HANDLE err){
  BYTE sig[20],branch=0,name[23],stub[256],jump[6];
  DWORD n,old_protect=0,junk_protect=0,stubsize,remote;
  SIZE_T done=0;
  LPVOID mem;
  const BYTE expected[]={0x8b,0x0d,0x70,0xa4,0x51,0x00,
    0x8b,0x15,0x74,0xa4,0x51,0x00,0x89,0x4c,0x24,0x20,0x89,0x54,0x24,0x24};
  const BYTE expected_name[]="Aureal A3D Interactive";
  /* Accept only the supported selector and its known one-byte inverted variant. */
  if(!ReadProcessMemory(p,(LPCSTR)0x0046f1f5u,&branch,1,&done)||done!=1||(branch!=0x75&&branch!=0x74)){
    out(err,"Refusing: not the expected original Alice selector branch.\r\n");return 0;}
  if(!ReadProcessMemory(p,(LPCSTR)0x0046f266u,sig,sizeof(sig),&done)||done!=sizeof(sig)||!eq(sig,expected,sizeof(sig))){
    out(err,"Refusing: original selector instructions do not match.\r\n");return 0;}
  if(!ReadProcessMemory(p,(LPCSTR)0x00520098u,name,sizeof(name),&done)||done!=sizeof(name)||!eq(name,expected_name,sizeof(name))){
    out(err,"Refusing: original A3D1 provider name mismatch.\r\n");return 0;}
  /* Support the installed inverted selector without changing alice.exe on disk.
   * All original instruction/name signatures above still must match. */
  if(branch==0x74){BYTE repaired=0x75;
    if(!VirtualProtectEx(p,(LPVOID)0x0046f1f5u,1,PAGE_EXECUTE_READWRITE,&old_protect))return 0;
    n=WriteProcessMemory(p,(LPVOID)0x0046f1f5u,(LPCSTR)&repaired,1,&done);
    VirtualProtectEx(p,(LPVOID)0x0046f1f5u,1,old_protect,&junk_protect);
    if(!n||done!=1)return 0;
    FlushInstructionCache(p,(LPCSTR)0x0046f1f5u,1);
    out(err,"Corrected inverted A3D selector in child RAM only.\r\n");
  }
  mem=VirtualAllocEx(p,0,4096,MEM_RESERVE|MEM_COMMIT,PAGE_EXECUTE_READWRITE);
  if(!mem){out(err,"Could not allocate child-process bridge memory.\r\n");return 0;}
  remote=(DWORD)mem;
  stubsize=gen_stub(stub,remote);
  if(!WriteProcessMemory(p,mem,(LPCSTR)stub,stubsize,&done)||done!=stubsize){
    out(err,"Could not install child-process selector bridge.\r\n");return 0;}
  /* 5-byte JMP rel32 plus NOP replaces six original bytes. */
  jump[0]=0xe9;u32(jump+1,remote-(0x0046f266u+5));jump[5]=0x90;
  if(!VirtualProtectEx(p,(LPVOID)0x0046f266u,6,PAGE_EXECUTE_READWRITE,&old_protect)){
    out(err,"Could not enable temporary write protection for selector.\r\n");return 0;}
  done=0;
  n=WriteProcessMemory(p,(LPVOID)0x0046f266u,(LPCSTR)jump,6,&done);
  VirtualProtectEx(p,(LPVOID)0x0046f266u,6,old_protect,&junk_protect);
  if(!n||done!=6){out(err,"Could not write selector jump.\r\n");return 0;}
  FlushInstructionCache(p,(LPCSTR)mem,stubsize);
  FlushInstructionCache(p,(LPCSTR)0x0046f266u,6);
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
  if(!slash){out(err,"Place alice-a3d-bridge.exe beside alice.exe.\r\n");ExitProcess(2);}
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
  out(info,"Alice A3D selector bridge installed in child memory; executable file unchanged.\r\n");
  out(info,"a3d => stock A3D Interactive; a3d2 => Aureal A3D 2.0 (TM).\r\n");
  if(ResumeThread(proc.hThread)==0xffffffffu){
    TerminateProcess(proc.hProcess,5);CloseHandle(proc.hThread);CloseHandle(proc.hProcess);ExitProcess(5);}
  WaitForSingleObject(proc.hProcess,WAIT_INFINITE);
  GetExitCodeProcess(proc.hProcess,&exit_code);
  CloseHandle(proc.hThread);CloseHandle(proc.hProcess);
  ExitProcess((UINT)exit_code);
}
