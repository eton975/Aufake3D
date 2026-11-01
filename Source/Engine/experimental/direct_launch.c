/* v0.7.1 generic direct-launch candidate: intentionally never injects code,
 * creates a suspended process, changes thread contexts, modifies any process's
 * memory, or touches game executable bytes. Compatible with a locally installed
 * game only if Windows/Wine honors its external COM activation manifest.
 *
 * This is a *lower-invasive experiment*, not an anti-cheat bypass, nor a
 * guarantee that COM activation succeeds. Do not use on protected multiplayer
 * servers without explicit permission. PE32/x86 only by release policy.
 */
#include "native_host.h"
#include "generic_target.h"
DLLIMPORT HANDLE STDCALL CreateFileA(LPCSTR,DWORD,DWORD,LPVOID,DWORD,DWORD,HANDLE);
DLLIMPORT BOOL STDCALL ReadFile(HANDLE,LPVOID,DWORD,DWORD*,LPVOID);
DLLIMPORT DWORD STDCALL SetFilePointer(HANDLE,long,long*,DWORD);
static char folder[2048], exe[2048], command[8192];

static int valid_pe32(const char *name) {
  BYTE dos[64]={0}, hdr[26]={0}; DWORD count=0;
  HANDLE file=CreateFileA(name,0x80000000u,1,0,3,0x80,0);
  if(file==(HANDLE)-1) return 0;
  int valid=ReadFile(file,dos,64,&count,0)&&count==64&&dos[0]=='M'&&dos[1]=='Z';
  DWORD offset=(DWORD)dos[60]|((DWORD)dos[61]<<8)|((DWORD)dos[62]<<16)|((DWORD)dos[63]<<24);
  if(valid&&offset>=64&&offset<=0x4000000u&&SetFilePointer(file,(long)offset,0,0)==offset) {
    valid=ReadFile(file,hdr,26,&count,0)&&count==26&&
      hdr[0]=='P'&&hdr[1]=='E'&&hdr[2]==0&&hdr[3]==0&&
      hdr[4]==0x4c&&hdr[5]==0x01&&hdr[24]==0x0b&&hdr[25]==0x01;
  } else valid=0;
  CloseHandle(file);return valid;
}
static int manifest_present(const char *game) {
  char path[2080];DWORD n=0;
  while(game[n]&&n<2040) {path[n]=game[n];++n;}
  if(game[n])return 0;
  const char *suffix=".manifest";
  while(*suffix)path[n++]=*suffix++;
  path[n]=0;
  HANDLE file=CreateFileA(path,0x80000000u,1,0,3,0x80,0);
  if(file==(HANDLE)-1)return 0;
  CloseHandle(file);return 1;
}
static int same_file(const char *name,const char *full) {
  /* Prevent launching ourselves even under renamed copies. */
  const char *part=full;
  for(const char *p=full;*p;p++) if(*p=='/'||*p=='\\')part=p+1;
  while(*name&&*part) {
    unsigned char a=(unsigned char)*name++,b=(unsigned char)*part++;
    if(a>='A'&&a<='Z')a+=32;
    if(b>='A'&&b<='Z')b+=32;
    if(a!=b)return 0;
  }
  return !*name&&!*part;
}
void mainCRTStartup(void) {
  HANDLE err=GetStdHandle(STD_ERROR_HANDLE);
  const char *args=a3d_own_args(GetCommandLineA());
  const char *game=a3d_generic_target(&args);
  if(!game) {out(err,"Usage: a3d-direct.exe --game name.exe -- [game arguments]\r\n");ExitProcess(2);}
  DWORD n=GetModuleFileNameA(0,folder,sizeof(folder));
  if(!n||n>=sizeof(folder)-1) {out(err,"Cannot locate launcher.\r\n");ExitProcess(2);}
  if(same_file(game,folder)) {out(err,"Refusing recursive launch.\r\n");ExitProcess(2);}
  DWORD cut=0;
  for(DWORD i=0;i<n;i++)if(folder[i]=='/'||folder[i]=='\\')cut=i+1;
  if(!cut||cut+slen(game)+1>=sizeof(exe)) {out(err,"Game filename too long.\r\n");ExitProcess(2);}
  for(DWORD i=0;i<cut;i++)exe[i]=folder[i];
  DWORD pos=cut;for(const char *p=game;*p;p++)exe[pos++]=*p;exe[pos]=0;
  folder[cut]=0;
  if(!valid_pe32(exe)) {out(err,"Missing/invalid PE32 game executable.\r\n");ExitProcess(2);}
  if(!manifest_present(exe)) {out(err,"Missing game.exe.manifest.\r\n");ExitProcess(2);}
  /* Build a quoted, bounded child command line; forward all remaining args.
   * CreateProcessA requires writable command-line memory. */
  pos=0;command[pos++]='"';
  for(const char *p=exe;*p;p++)command[pos++]=*p;
  command[pos++]='"';
  if(*args)command[pos++]=' ';
  while(*args){if(pos+1>=sizeof(command)){out(err,"Arguments too long.\r\n");ExitProcess(2);}command[pos++]=*args++;}
  command[pos]=0;
  PROCESS_INFORMATION proc={0}; STARTUPINFOA start={0};start.cb=sizeof(start);
  /* Flags=0: ordinary CreateProcess, with no suspended-start bootstrap. */
  if(!CreateProcessA(exe,command,0,0,FALSE,0,0,folder,&start,&proc)) {
    out(err,"Direct game creation failed.\r\n");ExitProcess(3);
  }
  DWORD code=6;
  if(WaitForSingleObject(proc.hProcess,WAIT_INFINITE)!=0||
     !GetExitCodeProcess(proc.hProcess,&code))code=6;
  CloseHandle(proc.hThread); CloseHandle(proc.hProcess);
  ExitProcess(code);
}
