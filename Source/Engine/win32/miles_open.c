/* v0.5.0 SOURCE COMMENTARY — Miles provider opening diagnostic
 * Tests opening named Miles providers without claiming full game compatibility. Use
 * return codes and the captured logs to distinguish provider discovery, COM loading,
 * and actual sound rendering.
 */
/* Cross-game Miles Sound System 5/6 3D provider-open probe.
 * Loads only the user's installed Miles DLLs, never writes game files,
 * plays samples, or accesses Aureal hardware. Built as freestanding PE32.
 * Each 3D provider is opened in its own process to isolate crashes/failures.
 */
typedef unsigned long U32;
typedef void *HMODULE;
typedef void *HANDLE;
#define WINAPI __attribute__((stdcall))
#define IMPORT __declspec(dllimport)
IMPORT HMODULE WINAPI LoadLibraryA(const char*);
IMPORT void* WINAPI GetProcAddress(HMODULE,const char*);
IMPORT int WINAPI FreeLibrary(HMODULE);
IMPORT U32 WINAPI GetCurrentDirectoryA(U32,char*);
IMPORT U32 WINAPI GetFileAttributesA(const char*);
IMPORT U32 WINAPI GetEnvironmentVariableA(const char*,char*,U32);
IMPORT HANDLE WINAPI GetStdHandle(U32);
IMPORT int WINAPI WriteFile(HANDLE,const void*,U32,U32*,void*);
IMPORT void WINAPI ExitProcess(U32);

typedef int (WINAPI *PStartup)(void);
typedef void (WINAPI *PShutdown)(void);
typedef int (WINAPI *PEnumerate)(void**,void**,char**);
typedef char* (WINAPI *PLastError)(void);
typedef char* (WINAPI *PRedist)(const char*);
typedef int (WINAPI *POpen3D)(void*);
typedef void (WINAPI *PClose3D)(void*);
typedef void* (WINAPI *PAlloc3DSample)(void*);
typedef void (WINAPI *PRelease3DSample)(void*);

static U32 size(const char*s){U32 n=0;if(s)while(s[n]&&n<32768)n++;return n;}
static void print(const char*s){U32 w=0;HANDLE h=GetStdHandle((U32)-11);if(h&&(U32)h!=0xffffffffUL)WriteFile(h,s,size(s),&w,0);}
static void decimal(U32 v){char b[16];int i=15;b[i]=0;do{b[--i]=(char)('0'+(v%10));v/=10;}while(v&&i);print(b+i);}
static void hexadecimal(U32 v){char b[]="0x00000000",h[]="0123456789ABCDEF";int i;for(i=0;i<8;i++)b[2+i]=h[(v>>(28-i*4))&15];print(b);}
static int eq(const char*a,const char*b){if(!a||!b)return 0;while(*a&&*b){if(*a++!=*b++)return 0;}return *a==*b;}
static int contains(const char*a,const char*b){U32 i=0,j;while(a&&a[i]){for(j=0;b[j]&&a[i+j]==b[j];j++){ /* substring scan */ } if(!b[j])return 1;i++;}return 0;}
static char *requested_name(const char*code){
 if(eq(code,"a3d2"))return "Aureal A3D 2.0 (TM)";
 if(eq(code,"a3d1"))return "Aureal A3D Interactive (TM)";
 if(eq(code,"fast2d"))return "Miles Fast 2D Positional Audio";
 return 0;
}
static U32 run(void){
 static char cwd[2048],path[2112],provider_code[48];
 U32 n=GetCurrentDirectoryA(sizeof(cwd),cwd),i;
 U32 c=GetEnvironmentVariableA("A3D_MILES_PROVIDER",provider_code,sizeof(provider_code));
 if(!c||c>=sizeof(provider_code)){print("ERROR: A3D_MILES_PROVIDER must be a3d2, a3d1, or fast2d\n");return 2;}
 char*want=requested_name(provider_code);
 if(!want){print("ERROR: unknown provider code\n");return 2;}
 print("Miles direct provider open v0.2.0\nTARGET=");print(want);print("\n");
 if(!n||n>=sizeof(cwd)-20){print("ERROR: working directory too long\n");return 3;}
 print("WORKING_DIR=");print(cwd);print("\n");
 if(GetFileAttributesA("mss32.dll")==0xffffffffUL){print("ERROR: mss32.dll not in current directory\n");return 4;}
 for(i=0;i<n;i++)path[i]=cwd[i];
 if(n&&path[n-1]!='\\'&&path[n-1]!='/')path[n++]='\\';
 {const char f[]="mss32.dll";for(i=0;f[i];i++)path[n+i]=f[i];path[n+i]=0;}
 HMODULE lib=LoadLibraryA(path);
 if(!lib){print("ERROR: LoadLibraryA mss32.dll\n");return 5;}
 PStartup startup=(PStartup)GetProcAddress(lib,"_AIL_startup@0");
 PShutdown shutdown=(PShutdown)GetProcAddress(lib,"_AIL_shutdown@0");
 PEnumerate enumerate=(PEnumerate)GetProcAddress(lib,"_AIL_enumerate_3D_providers@12");
 PLastError last=(PLastError)GetProcAddress(lib,"_AIL_last_error@0");
 PRedist redist=(PRedist)GetProcAddress(lib,"_AIL_set_redist_directory@4");
 POpen3D open3d=(POpen3D)GetProcAddress(lib,"_AIL_open_3D_provider@4");
 PClose3D close3d=(PClose3D)GetProcAddress(lib,"_AIL_close_3D_provider@4");
 print("EXPORTS startup=");print(startup?"yes":"no");
 print(" enumerate=");print(enumerate?"yes":"no");
 print(" open3d=");print(open3d?"yes":"no");
 print(" close3d=");print(close3d?"yes":"no");print("\n");
 if(!startup||!shutdown||!enumerate||!open3d||!close3d){print("ERROR: missing required exports\n");FreeLibrary(lib);return 6;}
 if(redist){redist(cwd);print("REDIST_DIR_SET=yes\n");}
 {int rc=startup();print("AIL_STARTUP_RESULT=");decimal((U32)rc);print("\n");}
 void *cursor=0,*handle=0,*selected=0;char *name=0;U32 count=0;
 for(i=0;i<128;i++){
   handle=0;name=0;
   if(!enumerate(&cursor,&handle,&name))break;
   count++;
   if(name&&contains(name,"Aureal")){
     print("ENUM_AUREAL=");print(name);print(" handle=");hexadecimal((U32)handle);print("\n");
   }
   if(name&&eq(name,want)){selected=handle;print("MATCH_HANDLE=");hexadecimal((U32)selected);print("\n");}
 }
 print("ENUMERATED_COUNT=");decimal(count);print("\n");
 if(!selected){print("MATCHED_PROVIDER=no\n");shutdown();FreeLibrary(lib);return 10;}
 print("MATCHED_PROVIDER=yes\nOPEN_CALL_BEGIN=1\n");
 /* NOTE: the provider may invoke the A3D driver API or fail to activate without hardware.
    Keep this as a separate child process; external timeout protects against deadlocks. */
 int result=open3d(selected);
 print("OPEN_CALL_RETURNED=1\nOPEN_RESULT=");decimal((U32)result);
 print("\nOPEN_RESULT_HEX=");hexadecimal((U32)result);print("\n");
 if(last){char*e=last();print("AIL_LAST_ERROR_AFTER_OPEN=");print(e?e:"(null)");print("\n");}
 if(result==0){
   print("OPEN_STATUS=success\n");
   {
    char sample_option[8];
    if(GetEnvironmentVariableA("A3D_MILES_SAMPLE_TEST",sample_option,sizeof(sample_option))>0 && sample_option[0]=='1'){
     PAlloc3DSample alloc=(PAlloc3DSample)GetProcAddress(lib,"_AIL_allocate_3D_sample_handle@4");
     PRelease3DSample release=(PRelease3DSample)GetProcAddress(lib,"_AIL_release_3D_sample_handle@4");
     print("SAMPLE_EXPORT_ALLOC=");print(alloc?"yes":"no");print("\nSAMPLE_EXPORT_RELEASE=");print(release?"yes":"no");print("\n");
     if(alloc&&release){
      print("SAMPLE_ALLOC_BEGIN=1\n");
      void*sample=alloc(selected);
      print("SAMPLE_ALLOC_RETURNED=1\nSAMPLE_ALLOC_NONNULL=");print(sample?"yes":"no");print("\n");
      if(last){char*e=last();print("AIL_LAST_ERROR_AFTER_ALLOC=");print(e?e:"(null)");print("\n");}
      if(sample){print("SAMPLE_RELEASE_BEGIN=1\n");release(sample);print("SAMPLE_RELEASE_RETURNED=1\n");}
     }
    }
   }
   print("CLOSE_CALL_BEGIN=1\n");
   close3d(selected);print("CLOSE_CALL_RETURNED=1\n");
 }else print("OPEN_STATUS=failed\n");
 shutdown();FreeLibrary(lib);
 print("PROBE_COMPLETE=1\n");
 return result==0?0:20;
}
void WINAPI start(void){ExitProcess(run());}
