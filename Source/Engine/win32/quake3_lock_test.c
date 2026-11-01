/* Quake III Arena 1.17 A3D output-buffer ABI regression test.
 * This test uses the real compiled a3dapi.dll, through its COM class factory,
 * to recreate the exact single-region Lock signature used in quake3.exe.
 * Run under Wine/Windows, with the DLL beside this probe.
 */
typedef unsigned long DWORD;
typedef long HRESULT;
typedef unsigned long ULONG;
typedef unsigned short WORD;
typedef void *HANDLE;
#define WINAPI __attribute__((stdcall))
#define IMPORT __declspec(dllimport)
#define E_POINTER ((HRESULT)0x80004003L)
IMPORT HANDLE WINAPI LoadLibraryA(const char*);
IMPORT void* WINAPI GetProcAddress(HANDLE,const char*);
IMPORT HANDLE WINAPI GetStdHandle(DWORD);
IMPORT int WINAPI WriteFile(HANDLE,const void*,DWORD,DWORD*,void*);
IMPORT void WINAPI ExitProcess(DWORD);
typedef struct { DWORD d1;WORD d2,d3;unsigned char d4[8]; } GUID;
#define G(a,b,c,d,e,f,g,h,i,j,k) {a,b,c,{d,e,f,g,h,i,j,k}}
static const GUID cls=G(0x92fa2c24,0x253c,0x11d2,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID factory_guid=G(1,0,0,0xc0,0,0,0,0,0,0,0x46);
static const GUID ia3d4=G(0xe4c40280,0xccba,0x11d2,0x9d,0xcf,0,0x50,0x04,0x11,0x58,0x2f);
typedef struct Factory Factory;
typedef struct { void*qi;void*add;ULONG(WINAPI*rel)(Factory*);HRESULT(WINAPI*create)(Factory*,void*,const GUID*,void**); } FactoryV;
struct Factory { const FactoryV*vt; };
typedef struct {void **vt;} Obj;
typedef struct {WORD tag,channels;DWORD rate,avg_bytes;WORD block_align,bits,extra;} WaveFmt;
typedef HRESULT(WINAPI*GetClass)(const GUID*,const GUID*,void**);
typedef HRESULT(WINAPI*NewSource)(Obj*,DWORD,void**);
typedef HRESULT(WINAPI*Format)(Obj*,const void*);
typedef HRESULT(WINAPI*Allocate)(Obj*,int);
typedef HRESULT(WINAPI*Lock)(Obj*,DWORD,DWORD,void**,DWORD*,void**,DWORD*,DWORD);
typedef HRESULT(WINAPI*Unlock)(Obj*,void*,DWORD,void*,DWORD);
typedef ULONG(WINAPI*Release)(Obj*);
static void say(const char*s){DWORD n=0,w=0;while(s[n])n++;WriteFile(GetStdHandle((DWORD)-11),s,n,&w,0);}
static DWORD run(void){
 HANDLE lib=LoadLibraryA("a3dapi.dll");if(!lib)return 10;
 GetClass get=(GetClass)GetProcAddress(lib,"DllGetClassObject");if(!get)return 11;
 Factory*f=0;if(get(&cls,&factory_guid,(void**)&f)||!f)return 12;
 Obj*r=0;if(f->vt->create(f,0,&ia3d4,(void**)&r)||!r)return 13;
 Obj*s=0;if(((NewSource)r->vt[17])(r,3,(void**)&s)||!s)return 14;
 WaveFmt w={1,2,22050,88200,4,16,0};
 if(((Format)s->vt[7])(s,&w))return 15;
 if(((Allocate)s->vt[5])(s,88200))return 16;
 void*a=0;DWORD an=0;
 /* Exact Quake III lock: second-region output parameters are NULL. */
 if(((Lock)s->vt[11])(s,0,88200,&a,&an,0,0,0))return 17;
 if(!a||an!=88200)return 18;
 ((unsigned char*)a)[0]=0;((unsigned char*)a)[1]=0;
 if(((Unlock)s->vt[12])(s,a,an,0,0))return 19;
 /* A ring-wrapping lock still requires both second-region outputs. */
 a=0;an=0;
 if(((Lock)s->vt[11])(s,88196,8,&a,&an,0,0,0)!=E_POINTER)return 20;
 if(a||an)return 21;
 void*b=0;DWORD bn=0;
 if(((Lock)s->vt[11])(s,88196,8,&a,&an,&b,&bn,0))return 22;
 if(!a||!b||an!=4||bn!=4)return 23;
 if(((Unlock)s->vt[12])(s,a,an,b,bn))return 24;
 ((Release)s->vt[2])(s);((Release)r->vt[2])(r);f->vt->rel(f);
 return 0;
}
void WINAPI start(void){DWORD code=run();if(code)say("FAIL: Quake III IA3dSource.Lock regression\r\n");else say("PASS: Quake III single-region and wrap Lock/Unlock ABI\r\n");ExitProcess(code);}
