/* Aufake3D independent Descent 3 A3D2 contract smoke probe.
 * Does NOT execute Descent 3 or reproduce its missing SUPPORT_AUREAL glue.
 * Exercises the documented A3D2 COM calls underlying its historical sources.
 * Load a game-local a3dapi.dll without COM registration or machine changes.
 * Optional --audio explicitly enables a brief, moderate-volume synthesized tone.
 * Windows x86 / freestanding clang, no CRT, no third-party/game binaries.
 */
int _fltused=0;
typedef unsigned long DWORD;
typedef unsigned short WORD;
typedef long HRESULT;
typedef unsigned long ULONG;
typedef void *HMODULE;
typedef void *HANDLE;
#define WINAPI __attribute__((stdcall))
#define IMPORT __declspec(dllimport)
IMPORT HMODULE WINAPI LoadLibraryA(const char *);
IMPORT void *WINAPI GetProcAddress(HMODULE,const char *);
IMPORT int WINAPI FreeLibrary(HMODULE);
IMPORT void WINAPI ExitProcess(DWORD);
IMPORT void *WINAPI GetStdHandle(DWORD);
IMPORT int WINAPI WriteFile(void*,const void*,DWORD,DWORD*,void*);
IMPORT void WINAPI Sleep(DWORD);
IMPORT char *WINAPI GetCommandLineA(void);

typedef struct { DWORD d1; WORD d2,d3; unsigned char d4[8]; } GUID;
#define G(a,b,c,d,e,f,g,h,i,j,k) {a,b,c,{d,e,f,g,h,i,j,k}}
static const GUID cls=G(0x92fa2c24,0x253c,0x11d2,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID iid_factory=G(0x00000001,0,0,0xc0,0,0,0,0,0,0,0x46);
static const GUID iid_root=G(0xe4c40280,0xccba,0x11d2,0x9d,0xcf,0x00,0x50,0x04,0x11,0x58,0x2f);
static const GUID iid_geom=G(0xc398e561,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static const GUID iid_listener=G(0xc398e563,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);

typedef struct Obj { void **vt; } Obj;
typedef HRESULT (WINAPI *DllGetClassObjectFn)(const GUID*,const GUID*,void**);
typedef HRESULT (WINAPI *CreateFn)(Obj*,void*,const GUID*,void**);
typedef HRESULT (WINAPI *QueryFn)(Obj*,const GUID*,void**);
typedef ULONG (WINAPI *ReleaseFn)(Obj*);
typedef HRESULT (WINAPI *NoArgFn)(Obj*);
typedef HRESULT (WINAPI *U32Fn)(Obj*,DWORD);
typedef HRESULT (WINAPI *OutFn)(Obj*,void**);
typedef HRESULT (WINAPI *NewSourceFn)(Obj*,DWORD,Obj**);
typedef HRESULT (WINAPI *GetCoeffFn)(Obj*,float*,float*);
typedef HRESULT (WINAPI *InitFn)(Obj*,GUID*,DWORD,DWORD);
typedef HRESULT (WINAPI *Vec3Fn)(Obj*,float,float,float);
typedef HRESULT (WINAPI *Vec6Fn)(Obj*,float,float,float,float,float,float);
typedef HRESULT (WINAPI *CoeffFn)(Obj*,float,float);
typedef HRESULT (WINAPI *BindFn)(Obj*,Obj*);
typedef HRESULT (WINAPI *FormatFn)(Obj*,const void*);
typedef HRESULT (WINAPI *AllocateFn)(Obj*,int);
typedef HRESULT (WINAPI *LockFn)(Obj*,DWORD,DWORD,void**,DWORD*,void**,DWORD*,DWORD);
typedef HRESULT (WINAPI *UnlockFn)(Obj*,void*,DWORD,void*,DWORD);
typedef HRESULT (WINAPI *PlayFn)(Obj*,int);
typedef HRESULT (WINAPI *DistanceFn)(Obj*,float,float,DWORD);
#define CALL(o,n,T) ((T)((o)->vt[n]))
static DWORD count(const char*s){DWORD n=0;while(s[n])n++;return n;}
static void say(const char*s){DWORD n=0;void*h=GetStdHandle((DWORD)-11);if(h)WriteFile(h,s,count(s),&n,0);}
static void sayhr(const char*s,HRESULT h){const char*x="0123456789ABCDEF";char b[]=" 0x00000000\r\n";
 for(int j=0;j<8;j++)b[j+3]=x[((DWORD)h>>(28-4*j))&15];say(s);say(b);}
static int ok(const char*name,HRESULT hr){sayhr(name,hr);return hr>=0;}
static int flag_audio(void){const char*p=GetCommandLineA();const char*needle="--audio";
 while(*p){int k=0;while(needle[k]&&p[k]==needle[k])k++;if(!needle[k]&&(p[k]==0||p[k]==' '||p[k]=='\t'||p[k]=='\"'))return 1;p++;}
 return 0;
}

typedef struct {WORD tag,channels;DWORD rate,avg;WORD align,bits,extra;} WaveFmt;
static int source_test(Obj*root,int audio){
 Obj*src=0;
 HRESULT r=CALL(root,17,NewSourceFn)(root,0,&src);
 if(!ok("NewSource",r)||!src)return 30;
 int rc=0;
 /* Original Descent 3 Aureal mixer creates both 8-bit/16-bit static and
  * streaming buffers at 22050 Hz. This fixture exercises 16-bit mono. */
 WaveFmt fmt={1,1,22050,44100,2,16,0};
 r=CALL(src,7,FormatFn)(src,&fmt);
 if(!ok("Source.SetWaveFormat",r)){rc=31;goto done;}
 const DWORD samples=5512u,bytes=samples*2u;
 r=CALL(src,5,AllocateFn)(src,(int)bytes);
 if(!ok("Source.AllocateWaveData",r)){rc=32;goto done;}
 void*pa=0,*pb=0;DWORD na=0,nb=0;
 r=CALL(src,11,LockFn)(src,0,bytes,&pa,&na,&pb,&nb,0);
 if(!ok("Source.Lock",r)||!pa||na!=bytes||pb||nb){rc=33;goto done;}
 unsigned char*b=(unsigned char*)pa;
 for(DWORD i=0;i<samples;i++){
  /* 440 Hz gentle triangle: no math library / no prerecorded samples. */
  DWORD phase=(i*440u)%22050u;
  long amp=(long)(phase<11025u?phase:22050u-phase);
  int v=(int)((amp*7000L)/11025L)-3500;
  b[2*i]=(unsigned char)v;
  b[2*i+1]=(unsigned char)((unsigned short)v>>8);
 }
 r=CALL(src,12,UnlockFn)(src,pa,na,pb,nb);
 if(!ok("Source.Unlock",r)){rc=34;goto done;}
 r=CALL(src,20,Vec3Fn)(src,3.0f,0.0f,2.0f);
 if(!ok("Source.SetPosition3f",r)){rc=35;goto done;}
 r=CALL(src,32,Vec3Fn)(src,0.0f,0.0f,0.0f);
 if(!ok("Source.SetVelocity3f",r)){rc=36;goto done;}
 r=CALL(src,38,DistanceFn)(src,1.0f,100.0f,0);
 if(!ok("Source.SetMinMaxDistance",r)){rc=37;goto done;}
 if(audio){
  say("Audio opt-in: short low-level tone from +X position\r\n");
  r=CALL(src,13,PlayFn)(src,0);
  if(!ok("Source.Play",r)){rc=38;goto done;}
  Sleep(350);
  r=CALL(src,14,NoArgFn)(src);
  if(!ok("Source.Stop",r)){rc=39;goto done;}
 }else say("Source playback skipped (use --audio to enable)\r\n");
 done:
 CALL(src,2,ReleaseFn)(src);
 return rc;
}
static int submit_quad(Obj*geom,Obj*mat,DWORD tag,float z){
 HRESULT r=CALL(geom,36,BindFn)(geom,mat);
 if(!ok("Geom.BindMaterial",r))return 50;
 r=CALL(geom,32,U32Fn)(geom,tag);
 if(!ok("Geom.Tag",r))return 51;
 r=CALL(geom,26,U32Fn)(geom,4); /* A3D_QUADS */
 if(!ok("Geom.Begin(A3D_QUADS)",r))return 52;
 const float xyz[4][3]={{-2.0f,-2.0f,0.0f},{2.0f,-2.0f,0.0f},{2.0f,2.0f,0.0f},{-2.0f,2.0f,0.0f}};
 for(unsigned i=0;i<4;i++){
  r=CALL(geom,28,Vec3Fn)(geom,xyz[i][0],xyz[i][1],z);
  if(!ok("Geom.Vertex3f",r))return 53;
 }
 r=CALL(geom,27,NoArgFn)(geom);
 if(!ok("Geom.End",r))return 54;
 return 0;
}
static int material_test(Obj*geom,const char*name,float tg,float th,float rg,float rh,Obj**out){
 *out=0;
 HRESULT r=CALL(geom,35,OutFn)(geom,(void**)out);
 if(!ok(name,r)||!*out)return 60;
 r=CALL(*out,14,CoeffFn)(*out,tg,th);
 if(!ok("Material.SetTransmittance",r))return 61;
 r=CALL(*out,12,CoeffFn)(*out,rg,rh);
 if(!ok("Material.SetReflectance",r))return 62;
 float a=0,b=0;
 r=CALL(*out,15,GetCoeffFn)(*out,&a,&b);
 if(!ok("Material.GetTransmittance",r)||a!=tg||b!=th)return 63;
 r=CALL(*out,13,GetCoeffFn)(*out,&a,&b);
 if(!ok("Material.GetReflectance",r)||a!=rg||b!=rh)return 64;
 return 0;
}
static int geometry_test(Obj*root){
 Obj*geom=0,*list=0,*mat[3]={0,0,0};int rc=0;
 HRESULT r=CALL(root,0,QueryFn)(root,&iid_geom,(void**)&geom);
 if(!ok("QueryInterface(IA3dGeom)",r)||!geom)return 70;
 r=CALL(geom,3,U32Fn)(geom,0x42u); /* occlusion and first reflections */
 if(!ok("Geom.Enable(occlusion|reflection)",r)){rc=71;goto done;}
 const struct {const char *name;float tg,th,rg,rh;} preset[3]={
  {"Material.CreateRock",0.2f,0.5f,0.9f,0.8f},
  {"Material.CreateWater",1.0f,0.3f,0.8f,0.7f},
  {"Material.CreateMetal",0.1f,0.1f,0.95f,0.85f}};
 for(unsigned i=0;i<3;i++){
  rc=material_test(geom,preset[i].name,preset[i].tg,preset[i].th,preset[i].rg,preset[i].rh,&mat[i]);
  if(rc)goto done;
 }
 r=CALL(geom,37,OutFn)(geom,(void**)&list);
 if(!ok("Geom.NewList",r)||!list){rc=72;goto done;}
 r=CALL(list,3,NoArgFn)(list);
 if(!ok("List.Begin",r)){rc=73;goto done;}
 /* Historical Descent3 batches static triangles and quads into cached
  * polygon groups. Preserve polygon counting rather than HRESULT==S_OK. */
 for(unsigned i=0;i<3;i++){
  rc=submit_quad(geom,mat[i],0xD300u+i,(float)i);
  if(rc)goto done;
 }
 r=CALL(list,4,NoArgFn)(list);
 if(!ok("List.End",r)||r!=3){rc=74;goto done;}
 r=CALL(list,5,NoArgFn)(list);
 if(!ok("List.Call",r)||r!=3){rc=75;goto done;}
 r=CALL(root,13,NoArgFn)(root);
 if(!ok("Root.Flush",r)){rc=76;goto done;}
 say("3 geometry polygons committed; 3 historical material presets verified\r\n");
 done:
 if(list)CALL(list,2,ReleaseFn)(list);
 for(unsigned i=0;i<3;i++)if(mat[i])CALL(mat[i],2,ReleaseFn)(mat[i]);
 if(geom)CALL(geom,2,ReleaseFn)(geom);
 return rc;
}
static DWORD run(void){
 say("Aufake3D Descent 3 source-contract probe; NOT the retail game\r\n");
 HMODULE h=LoadLibraryA("a3dapi.dll");
 if(!h){say("FAIL: cannot load local a3dapi.dll\r\n");return 10;}
 DllGetClassObjectFn get=(DllGetClassObjectFn)GetProcAddress(h,"DllGetClassObject");
 if(!get){say("FAIL: missing DllGetClassObject\r\n");FreeLibrary(h);return 11;}
 Obj*fac=0,*root=0,*lis=0;int rc=0;
 HRESULT r=get(&cls,&iid_factory,(void**)&fac);
 if(!ok("DllGetClassObject",r)||!fac){rc=12;goto done;}
 r=CALL(fac,3,CreateFn)(fac,0,&iid_root,(void**)&root);
 if(!ok("Factory.CreateInstance(IA3d4)",r)||!root){rc=13;goto done;}
 r=CALL(root,15,InitFn)(root,0,0x42u,0);
 if(!ok("Root.Init",r)){rc=14;goto done;}
 r=CALL(root,0,QueryFn)(root,&iid_listener,(void**)&lis);
 if(!ok("QueryInterface(IA3dListener)",r)||!lis){rc=15;goto done;}
 r=CALL(lis,3,Vec3Fn)(lis,0.0f,0.0f,0.0f);
 if(!ok("Listener.SetPosition3f",r)){rc=16;goto done;}
 r=CALL(lis,11,Vec6Fn)(lis,0.0f,0.0f,-1.0f,0.0f,1.0f,0.0f);
 if(!ok("Listener.SetOrientation6f",r)){rc=17;goto done;}
 rc=geometry_test(root);
 if(rc)goto done;
 rc=source_test(root,flag_audio());
 if(rc)goto done;
 say("PASS: Descent 3 A3D2 synthetic API contract\r\n");
 done:
 if(lis)CALL(lis,2,ReleaseFn)(lis);
 if(root){CALL(root,40,NoArgFn)(root);CALL(root,2,ReleaseFn)(root);}
 if(fac)CALL(fac,2,ReleaseFn)(fac);
 FreeLibrary(h);
 if(rc)say("FAIL: a synthetic contract step failed\r\n");
 return (DWORD)rc;
}
void WINAPI start(void){ExitProcess(run());}
