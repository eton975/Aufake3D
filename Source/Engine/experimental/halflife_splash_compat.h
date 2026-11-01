/* Explicit opt-in workaround for an obsolete HKLM Aureal SplashScreen write.
 * Only the newly created suspended child's RAM changes; no registry settings,
 * disk executable, licence checks or unrelated routines are modified.
 * Unknown editions fail closed when this option is requested. */
#include "halflife_splash_signature.h"
static int hl_read(HANDLE process,DWORD address,void *buffer,DWORD size){
 SIZE_T got=0;return ReadProcessMemory(process,(LPCSTR)address,buffer,size,&got)&&got==size;
}
static int halflife_splash_compat(PROCESS_INFORMATION *p,HANDLE err){
 char option[8];DWORD ctx[179]={0},base=0,offset=0,old=0,unused=0;SIZE_T done=0;
 BYTE dos[64],pe[84],code[128],names[33];
 const BYTE replacement[]={0xb8,1,0,0,0,0xc3};
 if(GetEnvironmentVariableA("A3D_HALFLIFE_SPLASH_FIX",option,sizeof(option))!=1||option[0]!='1')return 1;
 ctx[0]=0x10003u;
 if(!GetThreadContext(p->hThread,ctx)||!hl_read(p->hProcess,ctx[41]+8,&base,4)||
    !hl_read(p->hProcess,base,dos,sizeof(dos))||dos[0]!='M'||dos[1]!='Z')goto rejected;
 offset=(DWORD)dos[60]|((DWORD)dos[61]<<8)|((DWORD)dos[62]<<16)|((DWORD)dos[63]<<24);
 if(offset<64||offset>4096||!hl_read(p->hProcess,base+offset,pe,sizeof(pe))||
    !hl_read(p->hProcess,base+0x671d4u,code,sizeof(code))||
    !hl_read(p->hProcess,base+0xc5844u,names,sizeof(names))||!hl_splash_signature(pe,code,names))goto rejected;
 if(!VirtualProtectEx(p->hProcess,(LPVOID)(base+0x671d4u),6,PAGE_EXECUTE_READWRITE,&old))goto rejected;
 BOOL wrote=WriteProcessMemory(p->hProcess,(LPVOID)(base+0x671d4u),(LPCSTR)replacement,6,&done)&&done==6;
 BOOL restored=VirtualProtectEx(p->hProcess,(LPVOID)(base+0x671d4u),6,old,&unused);
 if(!wrote||!restored||!FlushInstructionCache(p->hProcess,(LPCSTR)(base+0x671d4u),6))goto rejected;
 launch_event(err,"Half-Life 1.0.1.1: optional Aureal splash setup skipped in child RAM.\r\n");return 1;
 rejected:launch_event(err,"Requested Half-Life splash workaround rejected: unknown signature or memory operation failed.\r\n");return 0;
}
