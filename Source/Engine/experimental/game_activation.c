/* v0.7.0-alpha shared activation launcher for Half-Life and Unreal.
 * Compile twice with GAME_EXE set to the adjacent original executable.
 * An explicit Half-Life option can skip a checked obsolete splash routine in RAM.
 * No game files are patched. The inherited activation bootstrap
 * redirects only the newly created child's startup to activate its local COM
 * manifest. This is infrastructure, not a claim that either game's ABI works.
 * ANSI path support matches the existing launch bridges; Unicode is future work.
 */
#include "native_host.h"
DLLIMPORT HANDLE STDCALL CreateFileA(LPCSTR,DWORD,DWORD,LPVOID,DWORD,DWORD,HANDLE);
DLLIMPORT BOOL STDCALL ReadFile(HANDLE,LPVOID,DWORD,DWORD*,LPVOID);
DLLIMPORT DWORD STDCALL SetFilePointer(HANDLE,long,long*,DWORD);
#include "launcher_diagnostics.h"
#include "../native_activation.inc"
#include "halflife_splash_compat.h"
#ifndef GAME_EXE
#error GAME_EXE must name the target adjacent executable
#endif
static char folder[2048],exe[2048],cmd[8192];
static int same_path(const char *a,const char *b){
 for(;*a&&*b;a++,b++){
  unsigned x=(unsigned char)*a,y=(unsigned char)*b;
  if(x>='A'&&x<='Z')x+=32;if(y>='A'&&y<='Z')y+=32;
  if(x!=y)return 0;
 }
 return !*a&&!*b;
}
#include "generic_target.h"

/* Inspect PE headers before creating a process: x64/NE and malformed files are
 * not valid targets for the x86 CONTEXT/bootstrap layout. This is format checking,
 * not game-edition detection. Unknown PE32 builds are still experimental. */
static int pe32_file(const char *name){
 BYTE dos[64]={0},header[26];DWORD got=0;
 HANDLE file=CreateFileA(name,0x80000000u,1u,0,3u,0x80u,0);
 if(file==(HANDLE)-1)return 0;
 int ok=ReadFile(file,dos,sizeof(dos),&got,0)&&got==sizeof(dos)&&dos[0]=='M'&&dos[1]=='Z';
 DWORD offset=(DWORD)dos[60]|((DWORD)dos[61]<<8)|((DWORD)dos[62]<<16)|((DWORD)dos[63]<<24);
 if(ok && offset>=64u && offset<=0x4000000u && SetFilePointer(file,(long)offset,0,0)==offset){
  ok=ReadFile(file,header,sizeof(header),&got,0)&&got==sizeof(header)&&
     header[0]=='P'&&header[1]=='E'&&!header[2]&&!header[3]&&
     header[4]==0x4c&&header[5]==1&&header[24]==0x0b&&header[25]==1;
 }else ok=0;
 CloseHandle(file);return ok;
}
/* Require an adjacent manifest; the child bootstrap validates its contents via
 * CreateActCtxA. Missing/invalid activation must never silently fall back to
 * an unrelated globally registered A3D server. */
static int manifest_exists(const char *name){
 static char manifest[2080];DWORD n=0;
 while(name[n]){manifest[n]=name[n];n++;}
 const char *suffix=".manifest";while(*suffix)manifest[n++]=*suffix++;manifest[n]=0;
 HANDLE file=CreateFileA(manifest,0x80000000u,1u,0,3u,0x80u,0);
 if(file==(HANDLE)-1)return 0;CloseHandle(file);return 1;
}
void mainCRTStartup(void){
 const char *args=a3d_own_args(GetCommandLineA());const char *target=GAME_EXE;
#ifdef A3D_GENERIC
 target=a3d_generic_target(&args);
 if(!target){out(GetStdHandle(STD_ERROR_HANDLE),"Usage: a3d-launch.exe --game adjacent.exe -- [game arguments]\r\n");ExitProcess(2);}
#endif
 HANDLE err=GetStdHandle(STD_ERROR_HANDLE);DWORD n=GetModuleFileNameA(0,folder,sizeof(folder));
 if(!n||n>=sizeof(folder)-1){out(err,"Cannot resolve launcher directory.\r\n");ExitProcess(2);}
 DWORD cut=0;for(DWORD i=0;i<n;i++)if(folder[i]=='\\'||folder[i]=='/')cut=i+1;
 if(!cut||cut+slen(target)+1u>sizeof(exe)){out(err,"Game path is too long.\r\n");ExitProcess(2);}
 static char launcher[2048];for(DWORD i=0;i<=n;i++)launcher[i]=folder[i];
 folder[cut]=0;launch_log_open(folder);launch_event(err,"A3D launcher: preflight\r\n");
 for(DWORD i=0;i<cut;i++)exe[i]=folder[i];
 while(*target)exe[cut++]=*target++;exe[cut]=0;
 if(same_path(exe,launcher)){launch_event(err,"Refusing recursive launch of this launcher as the game.\r\n");launch_close();ExitProcess(2);}
 if(!pe32_file(exe)){launch_event(err,"Missing or invalid adjacent PE32 game executable.\r\n");launch_close();ExitProcess(2);}
 if(!manifest_exists(exe)){launch_event(err,"Missing adjacent game executable manifest.\r\n");launch_close();ExitProcess(2);}
 DWORD at=0;cmd[at++]='"';for(DWORD i=0;exe[i];i++)cmd[at++]=exe[i];cmd[at++]='"';
 if(*args)cmd[at++]=' ';
 while(*args){if(at+1>=sizeof(cmd)){launch_event(err,"Game arguments too long; refusing truncation.\r\n");launch_close();ExitProcess(2);}cmd[at++]=*args++;}
 cmd[at]=0;
 PROCESS_INFORMATION proc={0};STARTUPINFOA start={0};start.cb=sizeof(start);
 if(!CreateProcessA(exe,cmd,0,0,FALSE,CREATE_SUSPENDED,0,folder,&start,&proc)){
  DWORD error=GetLastError();launch_code(err,"CreateProcess failed; Win32 error",error);launch_close();ExitProcess(3);
 }
 launch_event(err,"Child created suspended.\r\n");
 if(!halflife_splash_compat(&proc,err)){
  TerminateProcess(proc.hProcess,4);CloseHandle(proc.hThread);CloseHandle(proc.hProcess);launch_close();ExitProcess(4);
 }
 if(!activate_child(&proc,exe,err)){
  DWORD error=GetLastError();launch_code(err,"Activation bootstrap installation failed; Win32 error",error);
  TerminateProcess(proc.hProcess,4);CloseHandle(proc.hThread);CloseHandle(proc.hProcess);launch_close();ExitProcess(4);
 }
 launch_event(err,"Activation bootstrap installed; execution not yet confirmed.\r\n");
 if(ResumeThread(proc.hThread)==0xffffffffu){
  DWORD error=GetLastError();launch_code(err,"ResumeThread failed; Win32 error",error);
  TerminateProcess(proc.hProcess,5);CloseHandle(proc.hThread);CloseHandle(proc.hProcess);launch_close();ExitProcess(5);
 }
 launch_event(err,"Child resumed.\r\n");
 DWORD code=6;
 if(WaitForSingleObject(proc.hProcess,WAIT_INFINITE)!=0){
  DWORD error=GetLastError();launch_code(err,"WaitForSingleObject failed; Win32 error",error);
  CloseHandle(proc.hThread);CloseHandle(proc.hProcess);launch_close();ExitProcess(6);
 }
 if(!GetExitCodeProcess(proc.hProcess,&code))launch_code(err,"GetExitCodeProcess failed; Win32 error",GetLastError());
 launch_code(err,"Child exit code (not an A3D compatibility result)",code);
 CloseHandle(proc.hThread);CloseHandle(proc.hProcess);launch_close();ExitProcess(code);
}
