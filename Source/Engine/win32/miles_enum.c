/* v0.5.0 SOURCE COMMENTARY — Miles Sound System provider enumeration probe
 * Calls user-installed Miles interfaces to list driver names and capabilities. Vendor
 * Miles modules are not bundled with this source release.
 */
/* Diagnostic enumerator for the *user's own* Miles Sound System 6.x DLLs.
   Does not redistribute or patch any Miles game components.
   Built as PE32/i386 without a C runtime. Briefly opens the default audio driver, but does not play sounds.

   Run with working directory set to Alice's SndDrivers folder.
 */
typedef unsigned long U32;
typedef int S32;
typedef void *HMODULE;
typedef void *HANDLE;
#define WINAPI __attribute__((stdcall))
#define IMPORT __declspec(dllimport)
IMPORT HMODULE WINAPI LoadLibraryA(const char *);
IMPORT void* WINAPI GetProcAddress(HMODULE,const char*);
IMPORT int WINAPI FreeLibrary(HMODULE);
IMPORT U32 WINAPI GetCurrentDirectoryA(U32,char*);
IMPORT U32 WINAPI GetFileAttributesA(const char*);
IMPORT HANDLE WINAPI GetStdHandle(U32);
IMPORT int WINAPI WriteFile(HANDLE,const void*,U32,U32*,void*);
IMPORT void WINAPI ExitProcess(U32);

static void say(const char*s){U32 n=0,w=0;HANDLE h=GetStdHandle((U32)-11);if(!h||h==(void*)-1)return;while(s[n]&&n<65535)n++;WriteFile(h,s,n,&w,0);}
static void hex(U32 v){char b[11]="0x00000000";const char*h="0123456789ABCDEF";int i;for(i=0;i<8;i++)b[2+i]=h[(v>>(28-i*4))&15];say(b);}
static void dec(U32 v){char b[16];int i=15;b[i]=0;do{b[--i]='0'+v%10;v/=10;}while(v&&i);say(b+i);}
static int has(const char*s){return GetFileAttributesA(s)!=0xffffffffUL;}
typedef int (WINAPI *PStartup)(void);
typedef void (WINAPI *PShutdown)(void);
typedef int (WINAPI *PEnum)(void**,void**,char**);
typedef char* (WINAPI *PLastError)(void);
typedef char* (WINAPI *PRedist)(const char*);
typedef void* (WINAPI *POpenDigital)(U32,S32,S32,U32);
typedef void (WINAPI *PCloseDigital)(void*);
static void list_providers(PEnum enumer,PLastError last,const char *phase){
 void *cursor=0,*provider=0;char*name=0;U32 i,count=0,a3d=0;
 say("=== ");say(phase);say(" ===\n");
 for(i=0;i<128;i++){
  name=0;provider=0;
  if(!enumer(&cursor,&provider,&name))break;
  say("PROVIDER[");dec(i);say("] HANDLE=");hex((U32)provider);say(" NAME=");
  if(name){say(name);if((name[0]=='A'||name[0]=='a')&&(name[1]=='u'||name[1]=='U'))a3d++;}else say("(null)");
  say("\n");count++;
 }
 say("PROVIDER_COUNT=");dec(count);say("\n");
 say("AUREAL_PREFIX_COUNT=");dec(a3d);say("\n");
 if(i>=128)say("WARNING: provider enumeration safety cap reached\n");
 if(last){char*err=last();say("AIL_LAST_ERROR=");say(err?err:"(null)");say("\n");}
}


static U32 go(void){
 static char cwd[2048],path[2200];U32 n=GetCurrentDirectoryA(sizeof(cwd),cwd);
 if(!n||n>=sizeof(cwd)){say("ERROR get working directory\n");return 3;}
 say("Miles 3D provider enumeration diagnostic v0.1.9\nWORKING_DIR=");say(cwd);say("\n");
 say("MSS32_FILE=");say(has("mss32.dll")?"present\n":"absent\n");
 say("A3D2_PLUGIN_FILE=");say(has("mssa3d2.m3d")?"present\n":"absent\n");
 say("A3D1_PLUGIN_FILE=");say(has("mssa3d.m3d")?"present\n":"absent\n");
 if(!has("mss32.dll")){say("ERROR: run from the SndDrivers folder\n");return 4;}
 U32 i;for(i=0;i<n;i++)path[i]=cwd[i];
 if(n&&path[n-1]!='\\'&&path[n-1]!='/')path[n++]='\\';
 {const char suffix[]="mss32.dll";for(i=0;suffix[i];i++)path[n+i]=suffix[i];path[n+i]=0;}
 HMODULE dll=LoadLibraryA(path);
 if(!dll){say("ERROR: LoadLibraryA(mss32.dll) failed\n");return 5;}
 PStartup startup=(PStartup)GetProcAddress(dll,"_AIL_startup@0");
 PShutdown shutdown=(PShutdown)GetProcAddress(dll,"_AIL_shutdown@0");
 PEnum enumer=(PEnum)GetProcAddress(dll,"_AIL_enumerate_3D_providers@12");
 PLastError last=(PLastError)GetProcAddress(dll,"_AIL_last_error@0");
 PRedist redist=(PRedist)GetProcAddress(dll,"_AIL_set_redist_directory@4");
 say("EXPORTS startup=");say(startup?"yes":"no");say(" enumerate=");say(enumer?"yes":"no");say(" redist=");say(redist?"yes":"no");say("\n");
 if(!startup||!shutdown||!enumer){say("ERROR: required Miles export missing\n");FreeLibrary(dll);return 6;}
 if(redist){redist(cwd);say("REDIST_DIR_SET=yes\n");}
 {int rc=startup();say("AIL_STARTUP_RESULT=");dec((U32)rc);say("\n");}
 list_providers(enumer,last,"BEFORE_DIGITAL_DRIVER");
 POpenDigital open_dig=(POpenDigital)GetProcAddress(dll,"_AIL_open_digital_driver@16");
 PCloseDigital close_dig=(PCloseDigital)GetProcAddress(dll,"_AIL_close_digital_driver@4");
 if(open_dig&&close_dig){
   void *digital=open_dig(44100,16,2,0);
   say("DIGITAL_DRIVER_OPEN=");say(digital?"success":"failed");say("\n");
   if(!digital && last){char*err=last();say("DIGITAL_DRIVER_ERROR=");say(err?err:"(null)");say("\n");}
   list_providers(enumer,last,"AFTER_DIGITAL_DRIVER_ATTEMPT");
   if(digital)close_dig(digital);
 }else say("DIGITAL_DRIVER_EXPORTS_MISSING=1\n");
 shutdown();FreeLibrary(dll);
 say("DIAGNOSTIC_COMPLETE=1\n");
 return 0;
}
void WINAPI start(void){ExitProcess(go());}
