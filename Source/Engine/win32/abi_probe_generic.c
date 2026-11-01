/* Generic A3D interface SURVEY utility (Win32/i386).
 *
 * Tests publicly visible ABI entry points only; it does not call game functions,
 * allocate sound voices, or modify a game's process or files. The returned IID
 * information is NOT proof of usable 1.x or 3.x spatial rendering: e.g. the
 * current IA3d1/IA3d2 COM prefixes are aliases on the A3D 2.x class, while
 * the legacy DirectSound3D interception and A3D3 extensions are unsupported.
 *
 * Build freestanding with Clang/lld-link and use a local reg-free COM manifest.
 * Errors: 10 COM init failed; 11 A3D2 CoCreateInstance failed; 12 missing
 * IUnknown or invalid COM object. Unsupported interface probes are informational.
 */
typedef unsigned long DWORD;
typedef unsigned long ULONG;
typedef long HRESULT;
typedef unsigned short WORD;
typedef void* HANDLE;
typedef void* HMODULE;
typedef const char* LPCSTR;
#define STDCALL __attribute__((stdcall))
#define DLLIMPORT __declspec(dllimport)
DLLIMPORT HRESULT STDCALL CoInitialize(void*);
DLLIMPORT void STDCALL CoUninitialize(void);
DLLIMPORT HRESULT STDCALL CoCreateInstance(const void*,void*,DWORD,const void*,void**);
DLLIMPORT HMODULE STDCALL LoadLibraryA(LPCSTR);
DLLIMPORT void* STDCALL GetProcAddress(HMODULE,LPCSTR);
DLLIMPORT void STDCALL ExitProcess(DWORD);
DLLIMPORT HANDLE STDCALL GetStdHandle(DWORD);
DLLIMPORT int STDCALL WriteFile(HANDLE,const void*,DWORD,DWORD*,void*);
typedef struct {DWORD a;WORD b,c;unsigned char d[8];} GUID;
#define G(a,b,c,d,e,f,g,h,i,j,k) {a,b,c,{d,e,f,g,h,i,j,k}}
static const GUID cls_api=G(0x92fa2c24,0x253c,0x11d2,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID iid_unknown=G(0,0,0,0xc0,0,0,0,0,0,0,0x46);
static const GUID iid_a3d1=G(0xd8f1eee1,0xf634,0x11cf,0x87,0,0,0xa0,0x24,0x5d,0x91,0x8b);
static const GUID iid_a3d2=G(0xfb80d1e0,0x98d3,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID iid_a3d3=G(0xc398e560,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID iid_a3d4=G(0xe4c40280,0xccba,0x11d2,0x9d,0xcf,0,0x50,0x04,0x11,0x58,0x2f);
static const GUID iid_a3d5=G(0x9ae07221,0x8ac4,0x11d3,0xb6,0xaa,0,0x60,0x08,0x79,0xf3,0xee);
static const GUID iid_source2=G(0x3d54c5c1,0x2a5c,0x11d3,0xa8,0x7f,0,0x60,0x08,0x79,0xf3,0xee);
static const GUID iid_geom2=G(0x4730c6c2,0xb797,0x11d3,0xa3,0x3d,0,0x10,0x4b,0x67,0xd1,0x0e);
typedef struct Obj Obj;
typedef struct {HRESULT(STDCALL *QueryInterface)(Obj*,const GUID*,void**);ULONG(STDCALL *AddRef)(Obj*);ULONG(STDCALL *Release)(Obj*);} VTable;
struct Obj {const VTable* vt;};
static void emit(const char*msg){DWORD n=0,w=0;while(msg[n])n++;WriteFile(GetStdHandle((DWORD)-11),msg,n,&w,0);}
static void hexhr(HRESULT h){const char*dig="0123456789abcdef";char b[13]="0x00000000\r\n";unsigned v=(unsigned)h;for(int i=0;i<8;i++)b[i+2]=dig[(v>>(28-4*i))&15];emit(b);}
static void probe(Obj*o,const char*name,const GUID*g){
 void* p=0;HRESULT r=o->vt->QueryInterface(o,g,&p);
 emit(name);emit(r>=0&&p?"YES ":"NO ");hexhr(r);
 if(p)((Obj*)p)->vt->Release((Obj*)p);
}
static DWORD survey(void){
 emit("A3D generic ABI survey; no game audio or gameplay tested\r\n");
 HMODULE dll=LoadLibraryA("a3d.dll");
 if(!dll)emit("legacy a3d.dll: not loadable\r\n");
 else {
  emit("legacy _A3dCreate@12 export: ");
  emit(GetProcAddress(dll,"_A3dCreate@12")||GetProcAddress(dll,"A3dCreate")?"PRESENT (DirectSound fallback, not A3D1 HRTF)\r\n":"MISSING\r\n");
 }
 HRESULT r=CoInitialize(0);emit("CoInitialize: ");hexhr(r);
 if(r<0)return 10;
 Obj* p=0;r=CoCreateInstance(&cls_api,0,1,&iid_a3d4,(void**)&p);
 emit("A3D API CLSID / IA3d4 activation: ");hexhr(r);
 if(r<0||!p){CoUninitialize();return 11;}
 void*unk=0;r=p->vt->QueryInterface(p,&iid_unknown,&unk);
 emit("IUnknown identity available: ");hexhr(r);
 if(r<0||!unk){p->vt->Release(p);CoUninitialize();return 12;}
 ((Obj*)unk)->vt->Release((Obj*)unk);
 probe(p,"IA3d (COM prefix only): ",&iid_a3d1);
 probe(p,"IA3d2 (COM prefix only): ",&iid_a3d2);
 probe(p,"IA3d3: ",&iid_a3d3);
 probe(p,"IA3d4: ",&iid_a3d4);
 probe(p,"IA3d5 (A3D3): ",&iid_a3d5);
 probe(p,"IA3dSource2 (A3D3): ",&iid_source2);
 probe(p,"IA3dGeom2 (A3D3): ",&iid_geom2);
 p->vt->Release(p);CoUninitialize();
 emit("Survey complete. Interface claims are not game compatibility proof.\r\n");return 0;
}
void STDCALL start(void){ExitProcess(survey());}
