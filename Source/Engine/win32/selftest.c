/* v0.5.0 SOURCE COMMENTARY — ABI/export self-test
 * Checks expected DLL entry points in a Win32 loader environment. It is a smoke test of
 * ABI visibility, not an acoustic validation.
 */
/* Standalone Win32 ABI test: no Alice installation or hardware needed. */
int _fltused=0;
typedef unsigned long DWORD;
typedef long HRESULT;
typedef unsigned long ULONG;
typedef unsigned short WORD;
typedef void* HANDLE;
#define WINAPI __attribute__((stdcall))
#define IMPORT __declspec(dllimport)
IMPORT HANDLE WINAPI LoadLibraryA(const char*);
IMPORT void* WINAPI GetProcAddress(HANDLE,const char*);
IMPORT int WINAPI FreeLibrary(HANDLE);
IMPORT void WINAPI ExitProcess(DWORD);
typedef struct {DWORD d1;WORD d2,d3;unsigned char d4[8];} GUID;
#define G(a,b,c,d,e,f,g,h,i,j,k) {a,b,c,{d,e,f,g,h,i,j,k}}
static const GUID cls=G(0x92fa2c24,0x253c,0x11d2,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID ifactory=G(1,0,0,0xc0,0,0,0,0,0,0,0x46);
static const GUID geomid=G(0xc398e561,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID listenerid=G(0xc398e563,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID ia3d3=G(0xc398e560,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID ia3d4=G(0xe4c40280,0xccba,0x11d2,0x9d,0xcf,0,0x50,0x04,0x11,0x58,0x2f);
struct Factory;
typedef struct {HRESULT(WINAPI*qi)(struct Factory*,const GUID*,void**);
 ULONG(WINAPI*add)(struct Factory*); ULONG(WINAPI*rel)(struct Factory*);
 HRESULT(WINAPI*create)(struct Factory*,void*,const GUID*,void**);
 HRESULT(WINAPI*lock)(struct Factory*,int);} FactoryV;
typedef struct Factory {const FactoryV*vt;} Factory;
typedef struct {const void**vt;} Root;
typedef HRESULT(WINAPI*GetClass)(const GUID*,const GUID*,void**);
typedef HRESULT(WINAPI*Init)(Root*,GUID*,DWORD,DWORD);
typedef HRESULT(WINAPI*SetMode)(Root*,DWORD,DWORD,DWORD);
typedef HRESULT(WINAPI*GetMode)(Root*,DWORD*,DWORD*,DWORD*);
typedef HRESULT(WINAPI*NewSource)(Root*,DWORD,void**);
typedef struct {void **vt;} Src;
typedef HRESULT(WINAPI*SetSourcePos)(Src*,float,float,float);
typedef HRESULT(WINAPI*GetSourcePos)(Src*,float*,float*,float*);
typedef HRESULT(WINAPI*PlaySource)(Src*,int);
typedef ULONG(WINAPI*ReleaseSource)(Src*);
typedef ULONG(WINAPI*Release)(Root*);
typedef HRESULT(WINAPI*QI)(Root*,const GUID*,void**);
typedef HRESULT(WINAPI*Begin)(Root*,DWORD);
typedef HRESULT(WINAPI*End)(Root*);
typedef HRESULT(WINAPI*Vertex)(Root*,float,float,float);
typedef HRESULT(WINAPI*SetPosition)(Root*,float,float,float);
typedef HRESULT(WINAPI*NewMaterial)(Root*,Root**);
typedef HRESULT(WINAPI*NewList)(Root*,Root**);
typedef HRESULT(WINAPI*ListCall)(Root*);
typedef HRESULT(WINAPI*BindMaterial)(Root*,Root*);
typedef HRESULT(WINAPI*MatSet)(Root*,float,float);
typedef HRESULT(WINAPI*MatGet)(Root*,float*,float*);
typedef HRESULT(WINAPI*SetScalar)(Root*,float);
typedef HRESULT(WINAPI*GetScalar)(Root*,float*);
typedef HRESULT(WINAPI*GetPosition)(Root*,float*,float*,float*);
static DWORD probe(void){
 HANDLE h=LoadLibraryA("a3dapi.dll"); if(!h)return 10;
 GetClass get=(GetClass)GetProcAddress(h,"DllGetClassObject");if(!get)return 11;
 Factory*f=0;if(get(&cls,&ifactory,(void**)&f)||!f)return 12;
 Root*r=0;if(f->vt->create(f,0,&ia3d3,(void**)&r)||!r)return 13;
 if(((Init)r->vt[15])(r,0,0x42,0))return 14;
 if(((SetMode)r->vt[3])(r,1,2,3))return 15;
 DWORD a=0,b=0,c=0;
 if(((GetMode)r->vt[4])(r,&a,&b,&c)||a!=1||b!=2||c!=3)return 16;
 void*src=(void*)1;
 if(((NewSource)r->vt[17])(r,0,&src)!=0||!src)return 17;
 {Src*s=(Src*)src;float x=0,y=0,z=0;
  if(((SetSourcePos)s->vt[20])(s,3.0f,4.0f,5.0f)!=0)return 31;
  if(((GetSourcePos)s->vt[21])(s,&x,&y,&z)!=0||x!=3.0f||y!=4.0f||z!=5.0f)return 32;
  /* Empty source must fail rather than report phantom playback. */
  if(((PlaySource)s->vt[13])(s,0)!=(HRESULT)0x80004005L)return 33;
  ((ReleaseSource)s->vt[2])(s);
 }
 Root*geom=0;
 if(((QI)r->vt[0])(r,&geomid,(void**)&geom)||!geom)return 18;
 if(((Begin)geom->vt[26])(geom,3))return 19;
 if(((Vertex)geom->vt[28])(geom,0.0f,0.0f,0.0f))return 20;
 if(((Vertex)geom->vt[28])(geom,1.0f,0.0f,0.0f))return 21;
 if(((Vertex)geom->vt[28])(geom,0.0f,1.0f,0.0f))return 22;
 if(((End)geom->vt[27])(geom))return 23;
 ((Release)geom->vt[2])(geom);
 Root*lis=0;
 if(((QI)r->vt[0])(r,&listenerid,(void**)&lis)||!lis)return 24;
 if(((SetPosition)lis->vt[3])(lis,1.0f,2.0f,3.0f))return 25;
 float px=0,py=0,pz=0;
 if(((GetPosition)lis->vt[4])(lis,&px,&py,&pz)||px!=1.0f||py!=2.0f||pz!=3.0f)return 26;
 ((Release)lis->vt[2])(lis);
 ((Release)r->vt[2])(r);
 /* Miles mssa3d2.m3d explicitly requests IID_IA3d4, not IA3d3. */
 Root*r4=0;
 if(f->vt->create(f,0,&ia3d4,(void**)&r4)||!r4)return 27;
 float units=0.0f;
 if(((SetScalar)r4->vt[32])(r4,2.5f))return 28;
 if(((GetScalar)r4->vt[33])(r4,&units)||units!=2.5f)return 29;
 Root*gg=0;
 if(((QI)r4->vt[0])(r4,&geomid,(void**)&gg)||!gg)return 30;
 Root*mat=0;
 if(((NewMaterial)gg->vt[35])(gg,&mat)||!mat)return 31;
 float mr=0,mt=0;
 if(((MatSet)mat->vt[12])(mat,0.75f,0.25f))return 32;
 if(((MatGet)mat->vt[13])(mat,&mr,&mt)||mr!=0.75f||mt!=0.25f)return 33;
 if(((MatSet)mat->vt[14])(mat,0.1f,0.5f))return 34;
 if(((MatGet)mat->vt[15])(mat,&mr,&mt)||mr!=0.1f||mt!=0.5f)return 35;
 if(((BindMaterial)gg->vt[36])(gg,mat))return 36;
 ((Release)mat->vt[2])(mat);
 ((BindMaterial)gg->vt[36])(gg,0);
 Root*list=0;
 if(((NewList)gg->vt[37])(gg,&list)||!list)return 37;
 if(((ListCall)list->vt[3])(list))return 38;
 if(((Begin)gg->vt[26])(gg,3))return 39;
 if(((Vertex)gg->vt[28])(gg,0.0f,0.0f,0.0f))return 40;
 if(((Vertex)gg->vt[28])(gg,0.0f,1.0f,0.0f))return 41;
 if(((Vertex)gg->vt[28])(gg,0.0f,0.0f,1.0f))return 42;
 if(((End)gg->vt[27])(gg))return 43;
 if(((ListCall)list->vt[4])(list)!=1)return 44;
 if(((ListCall)list->vt[5])(list)!=1)return 45;
 ((Release)list->vt[2])(list);
 ((Release)gg->vt[2])(gg);
 ((Release)r4->vt[2])(r4);
 f->vt->rel(f);
 FreeLibrary(h);
 return 0;
}
void WINAPI start(void){ExitProcess(probe());}
