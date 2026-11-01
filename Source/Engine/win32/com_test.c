/* v0.5.0 SOURCE COMMENTARY — A3D 2.x COM activation diagnostic
 * Attempts class activation and checks COM object availability. A PASS proves
 * loader/COM wiring, not that game sound sources are spatialised.
 */
/* Real Win32 COM activation test via CoCreateInstance.
 * Code 0 means registered CLSID resolved to an IA3d3 object.
 * Codes 10/11/12/13 distinguish CoInitialize/activation/QueryInterface/Release failures.
 */
typedef unsigned long DWORD;
typedef long HRESULT;
typedef unsigned long ULONG;
typedef unsigned short WORD;
#define WINAPI __attribute__((stdcall))
#define IMPORT __declspec(dllimport)
IMPORT HRESULT WINAPI CoInitialize(void*);
IMPORT void WINAPI CoUninitialize(void);
IMPORT HRESULT WINAPI CoCreateInstance(const void*, void*, DWORD,const void*,void**);
IMPORT void WINAPI ExitProcess(DWORD);
IMPORT void* WINAPI GetStdHandle(DWORD);
IMPORT int WINAPI WriteFile(void*,const void*,DWORD,DWORD*,void*);
static DWORD slen(const char*s){DWORD n=0;while(s[n])n++;return n;}
static void say(const char*s){DWORD n=0;void*h=GetStdHandle((DWORD)-11);if(h && h!=(void*)-1)WriteFile(h,s,slen(s),&n,0);}
static void sayhr(const char*prefix,HRESULT hr){
 char buf[12]="0x00000000\n";const char*x="0123456789ABCDEF";
 DWORD v=(DWORD)hr;for(int n=0;n<8;n++)buf[2+n]=x[(v>>(28-n*4))&15];
 say(prefix);say(buf);
}
int _fltused=0;
typedef struct {DWORD d1;WORD d2,d3;unsigned char d4[8];} GUID;
#define G(a,b,c,d,e,f,g,h,i,j,k) {a,b,c,{d,e,f,g,h,i,j,k}}
static const GUID cls=G(0x92fa2c24,0x253c,0x11d2,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID ia3d3=G(0xc398e560,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID ia3d4=G(0xe4c40280,0xccba,0x11d2,0x9d,0xcf,0x00,0x50,0x04,0x11,0x58,0x2f);
static const GUID geom=G(0xc398e561,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID iidunk=G(0,0,0,0xc0,0,0,0,0,0,0,0x46);
typedef struct Obj Obj;
typedef struct {HRESULT(WINAPI*qi)(Obj*,const GUID*,void**);ULONG(WINAPI*add)(Obj*);ULONG(WINAPI*release)(Obj*);} ObjVT;
struct Obj {const ObjVT*vt;};
static DWORD test(void){
 HRESULT r=CoInitialize(0);sayhr("CoInitialize => ",r);if(r<0)return 10;
 Obj* p=0;
 r=CoCreateInstance(&cls,0,1,&ia3d3,(void**)&p);
 sayhr("CoCreateInstance => ",r);
 if(r<0||!p){CoUninitialize();return 11;}
 Obj* unknown=0;
 r=p->vt->qi(p,&iidunk,(void**)&unknown);sayhr("QueryInterface(IUnknown) => ",r);
 if(r<0||!unknown){p->vt->release(p);CoUninitialize();return 12;}
 unknown->vt->release(unknown);
 if(!p->vt->release(p)){/* zero ref is acceptable */}
 Obj* q=0;
 r=CoCreateInstance(&cls,0,1,&ia3d4,(void**)&q);
 sayhr("CoCreateInstance(IA3d4) => ",r);
 if(r<0||!q){CoUninitialize();return 13;}
 Obj* g=0;
 r=q->vt->qi(q,&geom,(void**)&g);
 sayhr("IA3d4.QueryInterface(IA3dGeom) => ",r);
 if(r<0||!g){q->vt->release(q);CoUninitialize();return 14;}
 g->vt->release(g);q->vt->release(q);
 say("COM roundtrip PASS (IA3d3 + IA3d4 + IA3dGeom)\n");CoUninitialize();return 0;
}
void WINAPI start(void){ExitProcess(test());}
