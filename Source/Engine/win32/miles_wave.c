/* v0.5.0 SOURCE COMMENTARY — Miles PCM/sample capture diagnostic
 * Creates or probes sample buffers via Miles and observes source callbacks. Is intended
 * to separate audio-source delivery from higher-level A3D activation.
 */
/* Cross-game Miles 6 A3D 2.0 WAV-data / optional playback diagnostic.
 * Uses only the user's installed Miles DLLs; never writes game files or
 * accesses Aureal hardware. Explicit `play-*` modes play a synthetic tone.
 * The existing position/wave/wave16 modes remain SILENT.
 */
typedef unsigned long U32;
int _fltused=0;
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
IMPORT void WINAPI Sleep(U32);

typedef int (WINAPI *PStartup)(void);
typedef void (WINAPI *PShutdown)(void);
typedef int (WINAPI *PEnumerate)(void**,void**,char**);
typedef char* (WINAPI *PLastError)(void);
typedef char* (WINAPI *PRedist)(const char*);
typedef int (WINAPI *POpen3D)(void*);
typedef void (WINAPI *PClose3D)(void*);
typedef void* (WINAPI *PAlloc3DSample)(void*);
typedef void (WINAPI *PRelease3DSample)(void*);
typedef int (WINAPI *PSet3DSampleFile)(void*,const void*);
typedef void (WINAPI *PSet3DPosition)(void*,float,float,float);
typedef void (WINAPI *PStart3DSample)(void*);
/* In-memory unsigned 8-bit and 16-bit mono RIFF/WAVE silence fixtures.
 * Playback is only initiated by explicit `play-*` modes below. */
static unsigned char synthetic_wave[44+2048];
static unsigned char synthetic_wave16[44+4096];
static void little16(unsigned char*p,unsigned int v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);}
static void little32(unsigned char*p,U32 v){little16(p,(unsigned int)v);little16(p+2,(unsigned int)(v>>16));}
static void synthetic_init(void){
 const char*riff="RIFF",*wave="WAVE",*fmt="fmt ",*data="data";
 unsigned int i;
 for(i=0;i<4;i++){synthetic_wave[i]=riff[i];synthetic_wave[8+i]=wave[i];synthetic_wave[12+i]=fmt[i];synthetic_wave[36+i]=data[i];}
 little32(synthetic_wave+4,36+2048);
 little32(synthetic_wave+16,16);
 little16(synthetic_wave+20,1); /* PCM */
 little16(synthetic_wave+22,1); /* mono */
 little32(synthetic_wave+24,22050);
 little32(synthetic_wave+28,22050); /* bytes/s */
 little16(synthetic_wave+32,1); /* block align */
 little16(synthetic_wave+34,8); /* bits */
 little32(synthetic_wave+40,2048);
 for(i=44;i<sizeof(synthetic_wave);i++)synthetic_wave[i]=128;
}


static void synthetic16_init(void){
 const char*riff="RIFF",*wave="WAVE",*fmt="fmt ",*data="data";
 unsigned int i;
 for(i=0;i<4;i++){synthetic_wave16[i]=riff[i];synthetic_wave16[8+i]=wave[i];synthetic_wave16[12+i]=fmt[i];synthetic_wave16[36+i]=data[i];}
 little32(synthetic_wave16+4,36+4096);
 little32(synthetic_wave16+16,16);
 little16(synthetic_wave16+20,1);
 little16(synthetic_wave16+22,1);
 little32(synthetic_wave16+24,22050);
 little32(synthetic_wave16+28,44100);
 little16(synthetic_wave16+32,2);
 little16(synthetic_wave16+34,16);
 little32(synthetic_wave16+40,4096);
 for(i=44;i<sizeof(synthetic_wave16);i++)synthetic_wave16[i]=0;
}

/* 400ms broadband noise burst for measured HRTF perception tests.
 * Tones do not provide sufficient spectral content for robust front/back/up cues.
 * Deterministic pseudo-random noise, 20ms fade at each edge, ~-17dBFS peak.
 */
#define TONE_SAMPLES 8820UL
static unsigned char synthetic_tone16[44+TONE_SAMPLES*2];
static void synthetic_tone_init(void){
 unsigned int i;U32 rng=0x31a2b55bUL;int prev=0;
 for(i=0;i<44;i++)synthetic_tone16[i]=synthetic_wave16[i];
 little32(synthetic_tone16+4,36+TONE_SAMPLES*2);
 little32(synthetic_tone16+40,TONE_SAMPLES*2);
 for(i=0;i<TONE_SAMPLES;i++){
  rng=(rng*1664525UL+1013904223UL)&0xffffffffUL;
  int raw=((int)((rng>>16)&0x7fffUL)-16384)/2;
  int x=(raw*3+prev)/4; prev=raw;
  if(i<441u)x=x*(int)i/441;
  if(i>TONE_SAMPLES-441u)x=x*(int)(TONE_SAMPLES-i)/441;
  little16(synthetic_tone16+44+2*i,(unsigned short)x);
 }
}

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
 print("Miles A3D2 PCM/positional playback probe v0.2.6\nTARGET=");print(want);print("\n");
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
      if(sample){
       char testmode[20]={0};
       GetEnvironmentVariableA("A3D_MILES_WAVE_MODE",testmode,sizeof(testmode));
       PSet3DPosition setposition=(PSet3DPosition)GetProcAddress(lib,"_AIL_set_3D_position@16");
       PSet3DSampleFile setfile=(PSet3DSampleFile)GetProcAddress(lib,"_AIL_set_3D_sample_file@8");
       PStart3DSample start_sample=(PStart3DSample)GetProcAddress(lib,"_AIL_start_3D_sample@4");
       print("MODE=");print(testmode);print("\nEXPORT_SET_POSITION=");print(setposition?"yes":"no");
       print("\nEXPORT_SET_FILE=");print(setfile?"yes":"no");print("\n");
       if(eq(testmode,"position") && setposition){
        print("POSITION_CALL_BEGIN=1\n");
        setposition(sample,1.0f,2.0f,3.0f);
        print("POSITION_CALL_RETURNED=1\n");
       }
       if((eq(testmode,"wave") || eq(testmode,"wave16") || eq(testmode,"play-left") || eq(testmode,"play-center") || eq(testmode,"play-right") || eq(testmode,"play-front") || eq(testmode,"play-back") || eq(testmode,"play-up")) && setfile){
        const void *wave_data=0;
        int isplay=eq(testmode,"play-left")||eq(testmode,"play-center")||eq(testmode,"play-right")||eq(testmode,"play-front")||eq(testmode,"play-back")||eq(testmode,"play-up");
        if(isplay){
         synthetic16_init();synthetic_tone_init();wave_data=synthetic_tone16;
         print("WAVE_BUFFER=RIFF/PCM mono 16bit 22050Hz 8820 samples faded broadband noise\n");
        }else if(eq(testmode,"wave16")){
         synthetic16_init();wave_data=synthetic_wave16;
         print("WAVE_BUFFER=RIFF/PCM mono 16bit 22050Hz 2048 samples silence\n");
        }else{
         synthetic_init();wave_data=synthetic_wave;
         print("WAVE_BUFFER=RIFF/PCM mono 8bit 22050Hz 2048 samples silence\n");
        }
        print("SET_WAVE_FILE_CALL_BEGIN=1\n");
        int file_result=setfile(sample,wave_data);
        print("SET_WAVE_FILE_RETURNED=1\nSET_WAVE_FILE_RESULT=");decimal((U32)file_result);print("\n");
        if(last){char*e=last();print("AIL_LAST_ERROR_AFTER_WAVE=");print(e?e:"(null)");print("\n");}
        if(isplay){
         if(file_result!=1){print("PLAY_SKIPPED=wave rejected\n");}
         else if(!start_sample||!setposition){print("PLAY_SKIPPED=missing Miles start or position export\n");}
         else{
          float x=eq(testmode,"play-left")?-5.0f:(eq(testmode,"play-right")?5.0f:0.0f);
          print("PLAYBACK_POSITION=");print(testmode);print("\n");
          /* Default RH listener looks along -Z; front and back are along Z.
           * Left/center/right test keeps previous v0.2.7 coordinates. */
          float y=eq(testmode,"play-up")?6.0f:0.0f;
          float z=eq(testmode,"play-front")?-6.0f:(eq(testmode,"play-back")?6.0f:(eq(testmode,"play-up")?-2.0f:2.0f));
          setposition(sample,x,y,z);
          print("AIL_START_3D_SAMPLE_BEGIN=1\n");
          start_sample(sample);
          print("AIL_START_3D_SAMPLE_RETURNED=1\n");
          if(last){char*e=last();print("AIL_LAST_ERROR_AFTER_START=");print(e?e:"(null)");print("\n");}
          /* 400 ms broadband burst + generous finish time before handle release. */
          Sleep(800);
          print("PLAYBACK_WAIT_COMPLETE=1\n");
         }
        }else if(setposition){
         print("POSITION_AFTER_WAVE_BEGIN=1\n");
         setposition(sample,4.0f,5.0f,6.0f);
         print("POSITION_AFTER_WAVE_RETURNED=1\n");
        }
       }
       print("SAMPLE_RELEASE_BEGIN=1\n");release(sample);print("SAMPLE_RELEASE_RETURNED=1\n");
      }
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
