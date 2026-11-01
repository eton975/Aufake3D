/* Optional, bounded per-run launcher diagnostics. Normal launches keep this
 * off. Never dump the game command line, environment, credentials or raw data.
 * The log is overwritten at the start of an explicitly enabled run. */
DLLIMPORT DWORD STDCALL GetEnvironmentVariableA(LPCSTR,LPSTR,DWORD);
DLLIMPORT DWORD STDCALL GetLastError(void);
static HANDLE launch_log=(HANDLE)-1;
static DWORD launch_log_bytes=0;
static void launch_log_open(const char *directory){
 char flag[8]={0};DWORD n=GetEnvironmentVariableA("A3D_LAUNCH_LOG",flag,sizeof(flag));
 if(!n)n=GetEnvironmentVariableA("A3D_LOG",flag,sizeof(flag));
 if(n!=1||flag[0]!='1')return;
 static char path[2300];n=GetEnvironmentVariableA("A3D_LAUNCH_LOG_PATH",path,sizeof(path));
 if(n>=sizeof(path))return;
 if(!n){
  DWORD i=0;while(directory[i]&&i+32<sizeof(path)){path[i]=directory[i];i++;}
  if(directory[i])return;const char *name="a3d-launcher.log";
  while(*name)path[i++]=*name++;path[i]=0;
 }
 launch_log=CreateFileA(path,0x40000000u,3,0,2,128,0);
}
static void launch_event(HANDLE err,const char *text){
 out(err,text);
 if(launch_log==(HANDLE)-1)return;
 DWORD n=slen(text),done=0;
 if(n>65536u-launch_log_bytes)return;
 WriteFile(launch_log,text,n,&done,0);launch_log_bytes+=n;
}
static void launch_code(HANDLE err,const char *stage,DWORD code){
 char text[112];DWORD n=0;const char *hex="0123456789abcdef";
 while(*stage&&n<90)text[n++]=*stage++;
 text[n++]=' ';text[n++]='0';text[n++]='x';
 for(DWORD i=0;i<8;i++)text[n++]=hex[(code>>(28-i*4))&15u];
 text[n++]='\r';text[n++]='\n';text[n]=0;launch_event(err,text);
}
static void launch_close(void){if(launch_log!=(HANDLE)-1){CloseHandle(launch_log);launch_log=(HANDLE)-1;}}
