/* v0.5.0 SOURCE COMMENTARY — Standalone small playback test
 * Generates short diagnostic playback outside of a game. Keep test level conservative;
 * successful output is not evidence of full per-game spatial accuracy.
 */
/* User-invoked, conservative-volume, standalone Aureal-API playback smoke test.
 * Exercises CoCreateInstance -> IA3d4.NewSource -> SetWaveFormat -> Allocate ->
 * Lock -> Unlock -> SetPosition -> Play -> Stop. Does not use Miles/Alice files.
 */
typedef unsigned long DWORD;
typedef long HRESULT;
typedef unsigned long ULONG;
typedef unsigned short WORD;
#define WINAPI __attribute__((stdcall))
#define IMPORT __declspec(dllimport)
IMPORT HRESULT WINAPI CoInitialize(void*);
IMPORT void WINAPI CoUninitialize(void);
IMPORT HRESULT WINAPI CoCreateInstance(const void*,void*,DWORD,const void*,void**);
IMPORT void WINAPI ExitProcess(DWORD);
IMPORT void* WINAPI GetStdHandle(DWORD);
IMPORT int WINAPI WriteFile(void*,const void*,DWORD,DWORD*,void*);
IMPORT void WINAPI Sleep(DWORD);
static DWORD slen(const char*s){DWORD n=0;while(s[n])n++;return n;}
static void say(const char*s){DWORD done=0;WriteFile(GetStdHandle((DWORD)-11),s,slen(s),&done,0);}
static void sayhr(const char*msg,HRESULT hr){const char*d="0123456789ABCDEF";char hex[]="0x00000000\n";for(int i=0;i<8;i++)hex[2+i]=d[((DWORD)hr>>(28-i*4))&15];say(msg);say(hex);}
int _fltused=0;
typedef struct{DWORD d1;WORD d2,d3;unsigned char d4[8];} GUID;
#define G(a,b,c,d,e,f,g,h,i,j,k) {a,b,c,{d,e,f,g,h,i,j,k}}
static const GUID cls=G(0x92fa2c24,0x253c,0x11d2,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID ia3d4=G(0xe4c40280,0xccba,0x11d2,0x9d,0xcf,0x00,0x50,0x04,0x11,0x58,0x2f);
typedef struct{WORD wFormatTag,nChannels;DWORD nSamplesPerSec,nAvgBytesPerSec;WORD nBlockAlign,wBitsPerSample,cbSize;} WaveFormat;
typedef struct Obj Obj;
struct Obj{void**vt;};
typedef ULONG(WINAPI*Rel)(Obj*);
typedef HRESULT(WINAPI*NewSource)(Obj*,DWORD,Obj**);
typedef HRESULT(WINAPI*SetFmt)(Obj*,const WaveFormat*);
typedef HRESULT(WINAPI*Allocate)(Obj*,int);
typedef HRESULT(WINAPI*Lock)(Obj*,DWORD,DWORD,void**,DWORD*,void**,DWORD*,DWORD);
typedef HRESULT(WINAPI*Unlock)(Obj*,void*,DWORD,void*,DWORD);
typedef HRESULT(WINAPI*SetPos)(Obj*,float,float,float);
typedef HRESULT(WINAPI*Play)(Obj*,int);
typedef HRESULT(WINAPI*Stop)(Obj*);
#define CALL(o,slot,type) ((type)((o)->vt[(slot)]))
static int fill(Obj*s){
 WaveFormat fmt={1,1,22050,44100,2,16,0};
 HRESULT hr=CALL(s,7,SetFmt)(s,&fmt);sayhr("SetWaveFormat=",hr);if(hr<0)return 20;
 /* 0.30 seconds at 22.05 kHz; deliberately moderate volume. */
 const DWORD samples=6615,bytes=samples*2;
 hr=CALL(s,5,Allocate)(s,(int)bytes);sayhr("AllocateWaveData=",hr);if(hr<0)return 21;
 void *a=0,*b=0;DWORD an=0,bn=0;
 hr=CALL(s,11,Lock)(s,0,bytes,&a,&an,&b,&bn,0);sayhr("Lock=",hr);
 if(hr<0||!a||an!=bytes||b||bn)return 22;
 unsigned char *dest=(unsigned char*)a;
 for(DWORD i=0;i<samples;i++){
  /* 440-Hz triangle without requiring libm/CRT; never full scale. */
  DWORD phase=(i*440UL)%22050UL;
  int x=(int)((phase*4UL*10000UL)/22050UL);
  if(phase<5512)x=(int)((phase*4UL*10000UL)/22050UL);
  else if(phase<11025)x=20000-(int)((phase*4UL*10000UL)/22050UL);
  else if(phase<16537)x=-(int)(((phase-11025UL)*4UL*10000UL)/22050UL);
  else x=-20000+(int)(((phase-11025UL)*4UL*10000UL)/22050UL);
  if(x>10000)x=10000;if(x< -10000)x=-10000;
  dest[2*i]=(unsigned char)x;dest[2*i+1]=(unsigned char)((unsigned short)x>>8);
 }
 hr=CALL(s,12,Unlock)(s,a,an,b,bn);sayhr("Unlock=",hr);return hr<0?23:0;
}
static DWORD run(void){
 say("A3D 2.0 prototype playback smoke test (not authentic HRTF)\n");
 HRESULT hr=CoInitialize(0);sayhr("CoInitialize=",hr);if(hr<0)return 10;
 Obj*root=0;
 hr=CoCreateInstance(&cls,0,1,&ia3d4,(void**)&root);sayhr("CoCreateInstance(IA3d4)=",hr);
 if(hr<0||!root){CoUninitialize();return 11;}
 int fail=0;
 /* Fresh sources let us test lifetime and independently located voices. */
 const float xvals[]={-5.0f,0.0f,5.0f};
 for(int n=0;n<3;n++){
  Obj*src=0;
  hr=CALL(root,17,NewSource)(root,0,&src);sayhr("NewSource=",hr);
  if(hr<0||!src){fail=12;break;}
  fail=fill(src);
  if(fail){CALL(src,2,Rel)(src);break;}
  say(n==0?"LEFT_POSITION\n":(n==1?"CENTER_POSITION\n":"RIGHT_POSITION\n"));
  hr=CALL(src,20,SetPos)(src,xvals[n],0.0f,2.0f);sayhr("SetPosition3f=",hr);
  if(hr>=0){hr=CALL(src,13,Play)(src,0);sayhr("Play=",hr);}
  if(hr<0)fail=13;
  Sleep(470);
  CALL(src,14,Stop)(src);
  CALL(src,2,Rel)(src);
  if(fail)break;
 }
 CALL(root,2,Rel)(root);
 CoUninitialize();
 say(fail?"PLAYBACK_DEMO_FAILED\n":"PLAYBACK_DEMO_QUEUED_ALL_THREE\n");
 return fail;
}
void WINAPI start(void){ExitProcess(run());}
