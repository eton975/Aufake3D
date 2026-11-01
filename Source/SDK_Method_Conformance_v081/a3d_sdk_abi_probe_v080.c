/* Generated from Aureal original SDK 1.2/2.0/3.0 GUID declarations. No vendor code. */
#define IMPORT __declspec(dllimport)
#define STDCALL __attribute__((stdcall))
typedef unsigned int DWORD; typedef unsigned int ULONG; typedef long HRESULT; typedef void* HMODULE; typedef void* HANDLE;
typedef struct { unsigned int a;unsigned short b,c;unsigned char d[8];} GUID;
typedef struct {void **vt;} OBJ;
typedef HRESULT (STDCALL *DllGetClassObjectT)(const GUID*,const GUID*,void**);
typedef HRESULT (STDCALL *QueryT)(OBJ*,const GUID*,void**);
typedef ULONG (STDCALL *ReleaseT)(OBJ*);
typedef HRESULT (STDCALL *CreateT)(OBJ*,void*,const GUID*,void**);
IMPORT HMODULE STDCALL LoadLibraryA(const char*); IMPORT void* STDCALL GetProcAddress(HMODULE,const char*);
IMPORT DWORD STDCALL GetLastError(void);IMPORT HANDLE STDCALL GetStdHandle(DWORD);
IMPORT int STDCALL WriteFile(HANDLE,const void*,DWORD,DWORD*,void*);IMPORT void STDCALL ExitProcess(DWORD);
IMPORT HANDLE STDCALL CreateFileA(const char*,DWORD,DWORD,void*,DWORD,DWORD,HANDLE);IMPORT int STDCALL CloseHandle(HANDLE);
#define NOGUID {0,0,0,{0,0,0,0,0,0,0,0}}
static const GUID IID_CF={0x00000001,0x0000,0x0000,{0xC0,0,0,0,0,0,0,0x46}};
static const GUID IID_UNK={0x00000000,0x0000,0x0000,{0xC0,0,0,0,0,0,0,0x46}};
typedef struct {const char *name;GUID id;} NAMED;
static const NAMED IID_LIST[]={
 {"IID_IA3d",{0xD8F1EEE1,0xF634,0x11CF,{0x87,0x00,0x00,0xa0,0x24,0x5d,0x91,0x8b}}},
 {"IID_IA3d2",{0xFB80D1E0,0x98D3,0x11D1,{0x90,0xfb,0x00,0x60,0x08,0xa1,0xf4,0x41}}},
 {"IID_IA3d3",{0xC398E560,0xD90B,0x11D1,{0x90,0xfb,0x00,0x60,0x08,0xa1,0xf4,0x41}}},
 {"IID_IA3d4",{0xE4C40280,0xCCBA,0x11D2,{0x9d,0xcf,0x00,0x50,0x04,0x11,0x58,0x2f}}},
 {"IID_IA3d5",{0x9AE07221,0x8AC4,0x11D3,{0xb6,0xaa,0x00,0x60,0x08,0x79,0xf3,0xee}}},
 {"IID_IA3dGeom",{0xC398E561,0xD90B,0x11D1,{0x90,0xfb,0x00,0x60,0x08,0xa1,0xf4,0x41}}},
 {"IID_IA3dGeom2",{0x4730C6C2,0xB797,0x11D3,{0xa3,0x3d,0x00,0x10,0x4b,0x67,0xd1,0x0e}}},
 {"IID_IA3dList",{0xC398E564,0xD90B,0x11D1,{0x90,0xfb,0x00,0x60,0x08,0xa1,0xf4,0x41}}},
 {"IID_IA3dListener",{0xC398E563,0xD90B,0x11D1,{0x90,0xfb,0x00,0x60,0x08,0xa1,0xf4,0x41}}},
 {"IID_IA3dMaterial",{0xC398E565,0xD90B,0x11D1,{0x90,0xfb,0x00,0x60,0x08,0xa1,0xf4,0x41}}},
 {"IID_IA3dPropertySet",{0x2A1A0A60,0xF190,0x11D2,{0x9d,0xcf,0x00,0x50,0x04,0x11,0x58,0x2f}}},
 {"IID_IA3dReflection",{0x1996D3C3,0x6C43,0x11D3,{0xa3,0x3d,0x00,0x50,0x04,0x88,0x18,0x1d}}},
 {"IID_IA3dReverb",{0xC38D8C01,0x44D6,0x11D3,{0xa8,0x7f,0x00,0x60,0x08,0x79,0xf3,0xee}}},
 {"IID_IA3dSource",{0xC398E562,0xD90B,0x11D1,{0x90,0xfb,0x00,0x60,0x08,0xa1,0xf4,0x41}}},
 {"IID_IA3dSource2",{0x3D54C5C1,0x2A5C,0x11D3,{0xa8,0x7f,0x00,0x60,0x08,0x79,0xf3,0xee}}},
};
static HANDLE hlog,hout;
static DWORD slen(const char*s){DWORD i=0;while(s&&s[i]&&i<10240)i++;return i;}
static void say(const char*s){DWORD n=slen(s),w=0;if(hout&&hout!=(HANDLE)-1)WriteFile(hout,s,n,&w,0);if(hlog&&hlog!=(HANDLE)-1)WriteFile(hlog,s,n,&w,0);}
static void hx(unsigned int n){char b[11]="0x00000000";for(int i=9;i>=2;i--){int q=n&15;b[i]=(char)(q<10?48+q:55+q);n>>=4;}say(b);}
static void result(const char*s,HRESULT hr){say(s);say(" ");hx((unsigned)hr);say("\r\n");}
static int check(const char*path,const GUID*cls){
 say("DLL ");say(path);say("\r\n");
 HMODULE m=LoadLibraryA(path);if(!m){say("LOAD_FAILED ");hx(GetLastError());say("\r\n");return 1;}
 DllGetClassObjectT get=(DllGetClassObjectT)GetProcAddress(m,"DllGetClassObject");
 if(!get){say("DLL_CLASS_FACTORY_EXPORT_MISSING\r\n");return 1;}
 OBJ *factory=0;HRESULT hr=get(cls,&IID_CF,(void**)&factory);result("DllGetClassObject",hr);
 if(hr<0||!factory)return 1;
 OBJ *obj=0;CreateT create=(CreateT)factory->vt[3];
 hr=create(factory,0,&IID_UNK,(void**)&obj);result("IClassFactory_CreateInstance_IUnknown",hr);
 if(hr>=0&&obj){for(unsigned i=0;i<sizeof(IID_LIST)/sizeof(IID_LIST[0]);i++){
 OBJ*q=0;QueryT qi=(QueryT)obj->vt[0];hr=qi(obj,&IID_LIST[i].id,(void**)&q);say("SDK_QI ");say(IID_LIST[i].name);say(" ");hx((unsigned)hr);
 say(hr>=0&&q?" PRESENT\r\n":" ABSENT_OR_FAILED\r\n");
 if(q){ReleaseT rel=(ReleaseT)q->vt[2];rel(q);}}ReleaseT rel=(ReleaseT)obj->vt[2];rel(obj);}
 ReleaseT rel=(ReleaseT)factory->vt[2];rel(factory);
 return hr<0?0:0;
}
void STDCALL mainCRTStartup(void){hout=GetStdHandle((DWORD)-11);hlog=CreateFileA("a3d-sdk-abi-v080.log",0x40000000,1,0,2,0x80,0);
 say("A3D_SDK_V080_ABI_DISCOVERY_REGISTRY_FREE_DIRECT_FACTORY\r\n");
 say("CONFORMANCE_LIMIT: QI only; does NOT call methods, initialise sound, or prove playback.\r\n");
 static const GUID cls1={0xD8F1EEE0,0xF634,0x11CF,{0x87,0x00,0x00,0xa0,0x24,0x5d,0x91,0x8b}};
 static const GUID cls2={0x92FA2C24,0x253C,0x11D2,{0x90,0xfb,0x00,0x60,0x08,0xa1,0xf4,0x41}};
 int a=check("bin\\a3d.dll",&cls1);int b=check("bin\\a3dapi.dll",&cls2);
 say(a||b?"RESULT: PARTIAL_OR_FAILED\r\n":"RESULT: FACTORY_PROBES_COMPLETED\r\n");
 if(hlog&&hlog!=(HANDLE)-1)CloseHandle(hlog);ExitProcess((a||b)?1:0);}
