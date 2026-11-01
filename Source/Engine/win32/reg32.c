/* v0.5.0 SOURCE COMMENTARY — Opt-in 32-bit COM registration helper
 * Contains optional COM registration tooling for a user-controlled Wine prefix.
 * Portable installer intentionally favors game-local registration-free COM and does not
 * modify the registry.
 */
/* 32-bit Wine COM registration diagnostic for the isolated A3D research prefix.
 * Registers the test CLSID under the 32-bit MACHINE Classes branch, then
 * verifies its visibility under the merged HKCR view used by COM.
 * Do NOT run this against an unrelated Windows installation or Wine prefix.
 */
typedef unsigned long DWORD;
typedef unsigned long ULONG;
typedef long LONG;
typedef void* HANDLE;
typedef void* HKEY;
#define WINAPI __attribute__((stdcall))
#define IMPORT __declspec(dllimport)
#define HKEY_CLASSES_ROOT ((HKEY)0x80000000ul)
#define HKEY_LOCAL_MACHINE ((HKEY)0x80000002ul)
#define KEY_READ 0x20019ul
#define KEY_ALL_ACCESS 0xf003ful
#define REG_SZ 1ul
#define REG_OPTION_NON_VOLATILE 0ul
#define INVALID_FILE_ATTRIBUTES 0xfffffffful
IMPORT HANDLE WINAPI GetStdHandle(DWORD);
IMPORT int WINAPI WriteFile(HANDLE,const void*,DWORD,DWORD*,void*);
IMPORT void WINAPI ExitProcess(DWORD);
IMPORT DWORD WINAPI GetFileAttributesA(const char*);
IMPORT LONG WINAPI RegOpenKeyExA(HKEY,const char*,DWORD,DWORD,HKEY*);
IMPORT LONG WINAPI RegCreateKeyExA(HKEY,const char*,DWORD,char*,DWORD,DWORD,void*,HKEY*,DWORD*);
IMPORT LONG WINAPI RegQueryValueExA(HKEY,const char*,DWORD*,DWORD*,unsigned char*,DWORD*);
IMPORT LONG WINAPI RegSetValueExA(HKEY,const char*,DWORD,DWORD,const unsigned char*,DWORD);
IMPORT LONG WINAPI RegCloseKey(HKEY);
static const char *server="C:\\A3D2Lab\\a3dapi.dll";
static const char *cls="CLSID\\{92FA2C24-253C-11D2-90FB-006008A1F441}\\InprocServer32";
static const char *machine="Software\\Classes\\CLSID\\{92FA2C24-253C-11D2-90FB-006008A1F441}\\InprocServer32";
static DWORD slen(const char*s){DWORD n=0;while(s[n])n++;return n;}
static void say(const char*s){DWORD n=0;HANDLE h=GetStdHandle((DWORD)-11);if(h && h!=(HANDLE)-1)WriteFile(h,s,slen(s),&n,0);}
static void hex(const char*label,DWORD val){char s[12]="0x00000000\n";const char*x="0123456789ABCDEF";for(int i=0;i<8;i++)s[2+i]=x[(val>>(28-i*4))&15];say(label);say(s);}
static int eq(const char*a,const char*b){while(*a&&*b){if(*a!=*b)return 0;a++;b++;}return *a==*b;}
static LONG probe(void){
 HKEY h=0;DWORD kind=0,size=0;char path[512]; path[0]=0;
 LONG e=RegOpenKeyExA(HKEY_CLASSES_ROOT,cls,0,KEY_READ,&h);
 hex("HKCR open status => ",(DWORD)e);
 if(e)return e;
 size=sizeof(path);
 e=RegQueryValueExA(h,0,0,&kind,(unsigned char*)path,&size);
 hex("HKCR default query => ",(DWORD)e);
 if(!e && size<=sizeof(path)){path[sizeof(path)-1]=0;say("HKCR server path => ");say(path);say("\n");}
 RegCloseKey(h);
 if(e)return e;
 if(kind!=REG_SZ || !eq(path,server)){say("HKCR path mismatch or wrong type\n");return 13;}
 return 0;
}
static LONG reg(HKEY root,const char*path){
 HKEY h=0;DWORD disp=0;LONG e=RegCreateKeyExA(root,path,0,0,REG_OPTION_NON_VOLATILE,KEY_ALL_ACCESS,0,&h,&disp);
 hex("Create registration key => ",(DWORD)e);
 if(e)return e;
 e=RegSetValueExA(h,0,0,REG_SZ,(const unsigned char*)server,slen(server)+1);
 hex("Set InprocServer32 default => ",(DWORD)e);
 if(!e){e=RegSetValueExA(h,"ThreadingModel",0,REG_SZ,(const unsigned char*)"Apartment",10);
 hex("Set ThreadingModel => ",(DWORD)e);}
 RegCloseKey(h);
 return e;
}
static DWORD run(void){
 if(GetFileAttributesA(server)==INVALID_FILE_ATTRIBUTES){say("DLL missing at C:\\A3D2Lab\\a3dapi.dll\n");return 4;}
 say("Before 32-bit registration:\n");
 if(!probe()){say("32-bit HKCR registration already correct\n");return 0;}
 say("Registering under HKLM\\Software\\Classes (32-bit process)\n");
 LONG e=reg(HKEY_LOCAL_MACHINE,machine);
 if(e){say("HKLM registry write failed\n");return 5;}
 say("After HKLM registration:\n");
 if(!probe()){say("PASS: 32-bit HKCR class visible\n");return 0;}
 say("Trying direct HKCR 32-bit registration fallback\n");
 e=reg(HKEY_CLASSES_ROOT,cls);
 if(e)return 6;
 if(probe())return 7;
 say("PASS: 32-bit HKCR class visible after fallback\n");return 0;
}
void WINAPI start(void){ExitProcess(run());}
