/* A3D v0.7.3-dev: explicit, reversible *per-user* A3D2 COM registration.
 *
 * This utility is intentionally compiled as a plain 32-bit Windows EXE.
 * It never modifies a game process, injects DLLs, patches game files, or
 * writes machine-wide registry keys. Install/Uninstall are explicit actions.
 * The 32-bit process uses the 32-bit redirected registry view automatically.
 *
 * Security design: no automatic replacement of preexisting per-user or
 * machine-wide COM registrations, and on removal only owner-marked values
 * identifying this very DLL path are deleted. This is deliberately stricter
 * than regsvr32's traditional overwrite behavior.
 *
 * Registry activation cannot bypass an application's explicit COM manifest
 * that maps this CLSID elsewhere, nor can it implement missing A3D 1/3 APIs.
 */
typedef unsigned long DWORD;
typedef long LONG;
typedef void *HANDLE;
typedef void *HKEY;
#define WINAPI __attribute__((stdcall))
#define IMPORT __declspec(dllimport)
#define HKCU ((HKEY)0x80000001UL)
#define HKCR ((HKEY)0x80000000UL)
#define KEY_QUERY_VALUE 0x0001UL
#define KEY_READ 0x20019UL
#define KEY_WRITE 0x20006UL
#define KEY_WOW64_32KEY 0x0200UL
#define REG_SZ 1UL
#define ERROR_SUCCESS 0UL
#define ERROR_FILE_NOT_FOUND 2UL
#define ERROR_PATH_NOT_FOUND 3UL
#define INVALID_FILE_ATTRIBUTES 0xffffffffUL
#define STD_OUTPUT_HANDLE ((DWORD)-11)
#define STD_ERROR_HANDLE ((DWORD)-12)
IMPORT DWORD WINAPI GetModuleFileNameA(void*,char*,DWORD);
IMPORT char* WINAPI GetCommandLineA(void);
IMPORT DWORD WINAPI GetFileAttributesA(const char*);
IMPORT HANDLE WINAPI GetStdHandle(DWORD);
IMPORT int WINAPI WriteFile(HANDLE,const void*,DWORD,DWORD*,void*);
IMPORT void WINAPI ExitProcess(DWORD);
IMPORT LONG WINAPI RegOpenKeyExA(HKEY,const char*,DWORD,DWORD,HKEY*);
IMPORT LONG WINAPI RegCreateKeyExA(HKEY,const char*,DWORD,char*,DWORD,DWORD,void*,HKEY*,DWORD*);
IMPORT LONG WINAPI RegQueryValueExA(HKEY,const char*,DWORD*,DWORD*,unsigned char*,DWORD*);
IMPORT LONG WINAPI RegSetValueExA(HKEY,const char*,DWORD,DWORD,const unsigned char*,DWORD);
IMPORT LONG WINAPI RegDeleteValueA(HKEY,const char*);
IMPORT LONG WINAPI RegEnumValueA(HKEY,DWORD,char*,DWORD*,DWORD*,DWORD*,unsigned char*,DWORD*);
IMPORT LONG WINAPI RegDeleteKeyA(HKEY,const char*);
IMPORT LONG WINAPI RegCloseKey(HKEY);
static const char *cls="Software\\Classes\\CLSID\\{92FA2C24-253C-11D2-90FB-006008A1F441}";
static const char *cr="CLSID\\{92FA2C24-253C-11D2-90FB-006008A1F441}\\InprocServer32";
static const char *sub="Software\\Classes\\CLSID\\{92FA2C24-253C-11D2-90FB-006008A1F441}\\InprocServer32";
static const char *marker="A3DUserRegistrationOwner";
static char server[2048];
static DWORD length(const char *s){DWORD n=0;while(s[n])n++;return n;}
static void logline(const char *s){DWORD n=0;WriteFile(GetStdHandle(STD_OUTPUT_HANDLE),s,length(s),&n,0);}
static int same(const char*a,const char*b){
 if(!a||!b)return 0;
 while(*a && *b){unsigned char x=(unsigned char)*a++,y=(unsigned char)*b++;
  if(x>='A'&&x<='Z')x+=32;if(y>='A'&&y<='Z')y+=32;if(x!=y)return 0;
 }return *a==*b;
}
static int path(void){
 DWORD n=GetModuleFileNameA(0,server,sizeof(server));
 if(!n||n>=sizeof(server)-16)return 0;
 while(n>0&&server[n-1]!='\\'&&server[n-1]!='/')n--;
 if(n==0)return 0;
 const char *dll="a3dapi.dll";
 for(DWORD i=0;dll[i];i++)server[n+i]=dll[i];
 server[n+length(dll)]=0;
 return GetFileAttributesA(server)!=INVALID_FILE_ATTRIBUTES;
}
static int read_string(HKEY h,const char*name,char *out,DWORD max){
 DWORD type=0,size=max;out[0]=0;
 if(RegQueryValueExA(h,name,0,&type,(unsigned char*)out,&size)!=0||type!=REG_SZ||!size||size>=max)return 0;
 out[size-1]=0;
 return 1;
}
static int owned(HKEY h){char v[2048],p[2048];
 return read_string(h,marker,v,sizeof(v))&&same(v,server)&&read_string(h,0,p,sizeof(p))&&same(p,server);
}
static DWORD install(void){
 HKEY reg=0;LONG status;
 if(!path()){logline("Cannot find a3dapi.dll beside a3d-com-user.exe.\r\n");return 2;}
 /* Refuse when any per-user CLSID key is already present, unless it is ours.
  * Also refuse a machine registration visible through HKCR, rather than
  * unexpectedly shadowing someone's original drivers. */
 status=RegOpenKeyExA(HKCU,cls,0,KEY_READ|KEY_WOW64_32KEY,&reg);
 if(status==0){
  RegCloseKey(reg);reg=0;
  if(RegOpenKeyExA(HKCU,sub,0,KEY_READ|KEY_WOW64_32KEY,&reg)==0){
   int ok=owned(reg);RegCloseKey(reg);
   if(ok){logline("This DLL is already registered for the current user.\r\n");return 0;}
  }
  logline("REFUSED: a per-user A3D CLSID key exists. No values changed.\r\n");return 3;
 }
 if(status!=ERROR_FILE_NOT_FOUND&&status!=ERROR_PATH_NOT_FOUND){logline("Cannot safely inspect user COM registration.\r\n");return 4;}
 if(RegOpenKeyExA(HKCR,cr,0,KEY_READ|KEY_WOW64_32KEY,&reg)==0){
  RegCloseKey(reg);logline("REFUSED: a COM registration already exists (possibly machine-wide).\r\n");return 5;
 }
 DWORD created=0;
 status=RegCreateKeyExA(HKCU,sub,0,0,0,KEY_WRITE|KEY_WOW64_32KEY,0,&reg,&created);
 if(status){logline("Unable to create per-user COM registration.\r\n");return 6;}
 status=RegSetValueExA(reg,0,0,REG_SZ,(const unsigned char*)server,length(server)+1);
 if(!status)status=RegSetValueExA(reg,"ThreadingModel",0,REG_SZ,(const unsigned char*)"Both",5);
 if(!status)status=RegSetValueExA(reg,marker,0,REG_SZ,(const unsigned char*)server,length(server)+1);
 RegCloseKey(reg);
 if(status){logline("Registry write failed; inspect registration before retrying.\r\n");return 7;}
 logline("Registered A3D2 COM for current user (32-bit view).\r\n");
 logline("Do not move this installation without removing its registration first.\r\n");return 0;
}
static DWORD remove_registration(void){
 if(!path()){logline("Cannot locate companion DLL; uninstall from its original folder.\r\n");return 2;}
 HKEY h=0;
 LONG status=RegOpenKeyExA(HKCU,sub,0,KEY_READ|KEY_WRITE|KEY_WOW64_32KEY,&h);
 if(status){logline("No matching per-user A3D registration found.\r\n");return 3;}
 if(!owned(h)){RegCloseKey(h);logline("REFUSED: registration does not belong to this DLL.\r\n");return 4;}
 char model[32];
 if(!read_string(h,"ThreadingModel",model,sizeof(model))||!same(model,"Both")){
  RegCloseKey(h);logline("REFUSED: threading model changed; not removing.\r\n");return 4;
 }
 /* Never delete unrelated named values in a registry key we once created. */
 for(DWORD idx=0;idx<64;idx++){
   char name[256]; DWORD nch=sizeof(name),type=0;
   LONG e=RegEnumValueA(h,idx,name,&nch,0,&type,0,0);
   if(e==259UL)break; /* ERROR_NO_MORE_ITEMS */
   if(e || idx==63 || nch>=sizeof(name)){
    RegCloseKey(h);logline("REFUSED: cannot safely inventory registry values.\r\n");return 4;
   }
   name[nch]=0;
   if(!same(name,marker)&&!same(name,"ThreadingModel")&&!same(name,"")){
    RegCloseKey(h);logline("REFUSED: unknown registry values present; not removing.\r\n");return 4;
   }
 }
 /* Unknown values were checked above; RegDeleteKeyA refuses subkeys. */
 status=RegDeleteValueA(h,marker);
 if(!status)status=RegDeleteValueA(h,"ThreadingModel");
 if(!status)status=RegDeleteValueA(h,0);
 RegCloseKey(h);
 if(status){logline("Unable to remove owned registration values.\r\n");return 5;}
 status=RegDeleteKeyA(HKCU,sub);
 if(status){logline("Removed our values; key may have other entries (left intact).\r\n");return 6;}
 status=RegDeleteKeyA(HKCU,cls);
 if(status)logline("Unregistered DLL; retained nonempty/shared CLSID parent.\r\n");
 else logline("Unregistered DLL and removed empty CLSID parent.\r\n");
 return 0;
}
static DWORD status_check(void){HKEY h=0;if(!path()){logline("Companion DLL missing.\r\n");return 2;}
 if(RegOpenKeyExA(HKCU,sub,0,KEY_READ|KEY_WOW64_32KEY,&h)!=0){logline("Not registered under current user.\r\n");return 1;}
 int ok=owned(h);RegCloseKey(h);
 logline(ok?"This DLL has an active per-user registration.\r\n":"Different or unowned per-user registration exists.\r\n");return ok?0:3;
}
static int argument(const char*want){const char *p=GetCommandLineA();
 if(*p=='"'){p++;while(*p&&*p!='"')p++;if(*p)p++;}
 else{while(*p&&*p!=' '&&*p!='\t')p++;}
 while(*p==' '||*p=='\t')p++;
 if(!*p)return 0;
 while(*want&&*p==*want){p++;want++;}
 return !*want&&(!*p||*p==' '||*p=='\t');
}
void WINAPI start(void){DWORD code;
 if(argument("--install"))code=install();
 else if(argument("--remove"))code=remove_registration();
 else if(argument("--status"))code=status_check();
 else {logline("Usage: a3d-com-user.exe --install | --status | --remove\r\n");code=1;}
 ExitProcess(code);
}
