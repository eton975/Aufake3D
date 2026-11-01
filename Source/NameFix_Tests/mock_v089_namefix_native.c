/* Native A3D v0.7.4e harness: real hook C, mocked Miles/Win32 only.
 * Build under ASAN+UBSAN; never runs the proprietary game or A3D DSP. */
#define A3D_TEST_NATIVE 1
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Keep the test doubles separate from real Windows API exports.  A native
 * Windows C runtime imports kernel32 functions such as GetLastError and
 * WriteFile; defining those names here causes LNK2005 duplicate symbols.
 * Renaming applies to the included provider source AND the mocks below, but
 * not to the CRT headers (included above).  Production source is unchanged.
 */
#define GetModuleHandleExA      a3d_mock_GetModuleHandleExA
#define GetModuleHandleA        a3d_mock_GetModuleHandleA
#define GetModuleFileNameA      a3d_mock_GetModuleFileNameA
#define GetEnvironmentVariableA a3d_mock_GetEnvironmentVariableA
#define GetCommandLineA        a3d_mock_GetCommandLineA
#define CreateFileA            a3d_mock_CreateFileA
#define SetFilePointer         a3d_mock_SetFilePointer
#define WriteFile              a3d_mock_WriteFile
#define CloseHandle            a3d_mock_CloseHandle
#define CreateActCtxA          a3d_mock_CreateActCtxA
#define ActivateActCtx         a3d_mock_ActivateActCtx
#define DeactivateActCtx       a3d_mock_DeactivateActCtx
#define ReleaseActCtx          a3d_mock_ReleaseActCtx
#define GetLastError           a3d_mock_GetLastError
#define FindActCtxSectionGuid  a3d_mock_FindActCtxSectionGuid
#define CoInitialize          a3d_mock_CoInitialize
#define CoUninitialize        a3d_mock_CoUninitialize
#define CoCreateInstance      a3d_mock_CoCreateInstance

#include "../Alice2011_NameFix_v089/miles_selection_v089.c"

static const char *cli="alice.exe +set s_milesdriver a3d2";
static int display_flag=0;
static int require_cli=1;
static const char *setting="pass";
static int prefer=0,trace_enabled=1,ctx_failed=0,fail_a3d=0,fail_listener=0;
static int calls4,calls8,closes4,closes8,listener4,listener8,objects4,objects8;
static int speaker4,speaker8,attr4,attr8,pref4,pref8;
static int act_created,act_on,act_off,act_release,co_created;
static unsigned enumeration_index=0;
static char output[90000];static size_t output_size=0;
static int STDCALL fake_enum(void **next,void **p,char **name){
 (void)next;
 if((enumeration_index++ & 1)==0){*p=(void*)(ULONG_PTR)4;*name="Aureal A3D 2.0 (TM)";}
 else {*p=(void*)(ULONG_PTR)8;*name="Miles Fast 2D Positional Audio";}
 return 1;
}
static int STDCALL fake_open(void*p){
 if((ULONG_PTR)p==4){calls4++;return fail_a3d?2:0;}
 if((ULONG_PTR)p==8){calls8++;return 0;}
 abort();
}
static void STDCALL fake_close(void*p){
 if((ULONG_PTR)p==4)closes4++;
 else if((ULONG_PTR)p==8)closes8++;
 else abort();
}
static void* STDCALL fake_listener(void*p){
 if((ULONG_PTR)p==4){listener4++;return fail_listener?0:(void*)(ULONG_PTR)0x4444;}
 if((ULONG_PTR)p==8){listener8++;return (void*)(ULONG_PTR)0x8888;}
 abort();
}
static void* STDCALL fake_object(void*p){
 if((ULONG_PTR)p==4)objects4++;
 else if((ULONG_PTR)p==8)objects8++;
 else abort();return (void*)(ULONG_PTR)0x1234;
}
static int STDCALL fake_get_speaker(void*p){
 if((ULONG_PTR)p==4)speaker4++;
 else if((ULONG_PTR)p==8)speaker8++;
 else abort();return 2;
}
static int STDCALL fake_set_speaker(void*p,int a){
 if(a!=7)abort();return fake_get_speaker(p);
}
static int STDCALL fake_get_room(void*p){return fake_get_speaker(p);}
static int STDCALL fake_set_room(void*p,int a){return fake_set_speaker(p,a);}
static int STDCALL fake_set_pref(void*p,int k,int v){
 if(k!=5||v!=6)abort();
 if((ULONG_PTR)p==4)pref4++;
 else if((ULONG_PTR)p==8)pref8++;
 else abort();return 1;
}
static int STDCALL fake_attr(void*p,int k,int v){
 if(k!=5||v!=6)abort();
 if((ULONG_PTR)p==4)attr4++;
 else if((ULONG_PTR)p==8)attr8++;
 else abort();return 1;
}
static int STDCALL fake_start(void){return 1;}
static const char* STDCALL fake_error(void){return "A3D2 failed to initialise";}
void* a3d_resolve(DWORD ord){switch(ord){
 case ENUM_ORDINAL:return fake_enum;case OPEN_ORDINAL:return fake_open;
 case CLOSE_ORDINAL:return fake_close;case STARTUP_ORDINAL:return fake_start;
 case LISTENER_ORDINAL:return fake_listener;case OBJECT_ORDINAL:return fake_object;
 case LAST_ERROR_ORDINAL:return fake_error;
 case SPEAKER_GET_ORDINAL:return fake_get_speaker;
 case SPEAKER_SET_ORDINAL:return fake_set_speaker;
 case ROOM_GET_ORDINAL:return fake_get_room;
 case ROOM_SET_ORDINAL:return fake_set_room;
 case PROVIDER_PREF_SET_ORDINAL:return fake_set_pref;
 case PROVIDER_ATTRIBUTE_ORDINAL:return fake_attr;
 default:abort();
}}
BOOL GetModuleHandleExA(DWORD flags,const char*addr,HMODULE*result){(void)flags;(void)addr;*result=(void*)0x1234;return 1;}
HMODULE GetModuleHandleA(const char*name){(void)name;return 0;}
DWORD GetModuleFileNameA(HMODULE m,char*dest,DWORD max){(void)m;const char*s="C:\\Example\\SndDrivers\\mss32.dll";DWORD n=(DWORD)strlen(s);if(max<=n)abort();memcpy(dest,s,n+1);return n;}
DWORD GetEnvironmentVariableA(const char*name,char*dest,DWORD max){
 const char*v=!strcmp(name,"A3D_MILES_MODE")?setting:!strcmp(name,"A3D_MILES_TRACE")?(trace_enabled?"1":"0"):
 !strcmp(name,"A3D_MILES_ALIAS_UNKNOWN")?(prefer?"1":"0"):
 !strcmp(name,"A3D_MILES_DISPLAY_CANONICAL")?(display_flag?"1":"0"):
 !strcmp(name,"A3D_MILES_REQUIRE_CLI_A3D2")?(require_cli?"1":"0"):"0";
 DWORD n=(DWORD)strlen(v);if(max<=n)abort();memcpy(dest,v,n+1);return n;
}
const char* GetCommandLineA(void){return cli;}
HANDLE CreateFileA(const char*a,DWORD b,DWORD c,void*d,DWORD e,DWORD f,HANDLE g){(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;(void)g;return (void*)0x4455;}
DWORD SetFilePointer(HANDLE a,long b,long*c,DWORD d){(void)a;(void)b;(void)c;(void)d;return (DWORD)output_size;}
BOOL WriteFile(HANDLE a,const void*b,DWORD n,DWORD*w,void*d){(void)a;(void)d;if(output_size+n>=sizeof(output))abort();memcpy(output+output_size,b,n);output_size+=n;output[output_size]=0;*w=n;return 1;}
BOOL CloseHandle(HANDLE h){(void)h;return 1;}
HANDLE CreateActCtxA(const ACTCTXA*a){act_created++;if(a->cbSize!=sizeof(*a))abort();return ctx_failed?INVALID_HANDLE_VALUE:(void*)0x3333;}
BOOL ActivateActCtx(HANDLE h,ULONG_PTR*c){if(h!=(void*)0x3333)abort();act_on++;*c=0x123;return 1;}
BOOL DeactivateActCtx(DWORD flags,ULONG_PTR cookie){(void)flags;if(cookie!=0x123)abort();act_off++;return 1;}
void ReleaseActCtx(HANDLE h){(void)h;act_release++;}
DWORD GetLastError(void){return 5;}
BOOL FindActCtxSectionGuid(DWORD f,const GUID*a,DWORD sec,const GUID*b,ACTCTX_SECTION_KEYED_DATA*p){(void)f;(void)a;(void)sec;(void)b;(void)p;return 1;}
HRESULT CoInitialize(void*a){(void)a;return 0;}
void CoUninitialize(void){}
HRESULT CoCreateInstance(const GUID*c,IUnknown*o,DWORD ctx,const GUID*i,void**out){(void)c;(void)o;(void)ctx;(void)i;(void)out;co_created++;return -1;}
static void check(int cond,const char*s){if(!cond){fprintf(stderr,"FAIL %s\n%s\n",s,output);abort();}}
static void enum_both(void){void*n=0,*p=0;char*s=0;check(a3d_hook_enumerate(&n,&p,&s)==1,"enum A3D");check(a3d_hook_enumerate(&n,&p,&s)==1,"enum 2D");}
static void clear_runtime(void){calls4=calls8=closes4=closes8=listener4=listener8=objects4=objects8=0; speaker4=speaker8=attr4=attr8=pref4=pref8=0;fail_a3d=fail_listener=ctx_failed=0;}
int main(void){
 void *next=0,*prov=0;char *name=0;
 setting="pass";prefer=1;
 check(a3d_hook_enumerate(&next,&prov,&name)==1,"pass enum");
 check(!strcmp(name,"Aureal A3D 2.0 (TM)"),"pass must preserve true identity");
 check(a3d_hook_open((void*)8)==0 && calls8==1 && calls4==0,"pass original 2D");
 check(act_created==0,"pass no actctx");
 setting="trace";
 check(a3d_hook_enumerate(&next,&prov,&name)==1,"trace enum");
 check(!strcmp(name,"Miles Fast 2D Positional Audio"),"trace keeps other names");
 setting="activate";prefer=1;
 enumeration_index=0;
 check(a3d_hook_enumerate(&next,&prov,&name)==1,"alias enum");
 check((ULONG_PTR)prov==4 && !strcmp(name,"unknown"),"alias only original A3D2 handle");
 check(strstr(output,"A3D2_ALIAS_ADVERTISED")!=0,"logs alias, not fake playback");
 check(a3d_hook_enumerate(&next,&prov,&name)==1,"2D enum");
 check((ULONG_PTR)prov==8 && !strcmp(name,"Miles Fast 2D Positional Audio"),"2D identity unchanged");
 calls4=calls8=0;
 check(a3d_hook_open((void*)8)==0 && calls8==1 && calls4==0,"DO NOT FORCE A3D2 BEHIND 2D");
 check(a3d_hook_listener((void*)8)==(void*)0x8888 && listener8==1,"2D listener unchanged");
 check(a3d_hook_open((void*)4)==0 && calls4==1,"game-selected A3D2 opens");
 check(a3d_hook_listener((void*)4)==(void*)0x4444 && listener4==1,"game-selected A3D listener");
 a3d_hook_close((void*)4);check(closes4==1,"correct close");
 cli="alice.exe +set s_milesdriver a3d";prefer=1;enumeration_index=0;
 check(a3d_hook_enumerate(&next,&prov,&name)==1 && !strcmp(name,"Aureal A3D 2.0 (TM)"),"non-a3d2 CLI must not alias");
 cli="alice.exe +set s_milesdriver a3d21";enumeration_index=0;
 check(a3d_hook_enumerate(&next,&prov,&name)==1 && !strcmp(name,"Aureal A3D 2.0 (TM)"),"invalid a3d2 token must not alias");
 cli="alice.exe +set s_milesdriver A3D2";enumeration_index=0;
 check(a3d_hook_enumerate(&next,&prov,&name)==1 && !strcmp(name,"unknown"),"A3D2 case insensitive opt-in");
 cli="alice.exe +set s_milesdriver a3d2";
 prefer=0;enumeration_index=0;
 check(a3d_hook_enumerate(&next,&prov,&name)==1 && !strcmp(name,"Aureal A3D 2.0 (TM)"),"no alias unless opt-in");
 prefer=1;ctx_failed=1;enumeration_index=0;
 check(a3d_hook_enumerate(&next,&prov,&name)==1 && !strcmp(name,"Aureal A3D 2.0 (TM)"),"no alias without actctx");
 check(act_created>0 && act_on==act_off && act_release==act_on,"activation cleanup counts");
 check(co_created==0,"no unrequested COM probe");

 /* v089 specifically: game captures *name pointer on enum, prints it AFTER
  * open. Verify pointer identity, buffer lifetime and conditional mutation. */
 ctx_failed=0;setting="activate";prefer=1;require_cli=1;display_flag=1;
 cli="alice.exe +set s_milesdriver a3d2";enumeration_index=0;
 check(a3d_hook_enumerate(&next,&prov,&name)==1 && !strcmp(name,"unknown"),"v089 lookup must still see unknown");
 char *stable_name_pointer=name;
 check((ULONG_PTR)prov==4,"v089 canonical handle remains 4");
 check(a3d_hook_open(prov)==0,"v089 real A3D2 opens");
 check(name==stable_name_pointer,"v089 pointer unchanged after open");
 check(!strcmp(name,"Aureal A3D 2.0 (TM)"),"v089 display becomes canonical after open");
 check(strstr(output,"A3D2_DISPLAY_NAME_UPGRADED Aureal A3D 2.0 (TM)")!=0,"v089 audited upgrade trace");
 display_flag=0;enumeration_index=0;
 check(a3d_hook_enumerate(&next,&prov,&name)==1 && !strcmp(name,"unknown"),"legacy lookup text");
 check(a3d_hook_open(prov)==0 && !strcmp(name,"unknown"),"v089 opt-out leaves unknown");
 display_flag=1;enumeration_index=0;fail_a3d=1;
 check(a3d_hook_enumerate(&next,&prov,&name)==1 && !strcmp(name,"unknown"),"failure path lookup");
 check(a3d_hook_open(prov)==2 && !strcmp(name,"unknown"),"failed provider open does not upgrade");
 fail_a3d=0;display_flag=1;enumeration_index=0;
 check(a3d_hook_enumerate(&next,&prov,&name)==1 && !strcmp(name,"unknown"),"2D isolation begin");
 check(a3d_hook_open((void*)8)==0 && !strcmp(name,"unknown"),"2D open never upgrades A3D2 alias");
 cli="alice.exe +set s_milesdriver software";enumeration_index=0;
 check(a3d_hook_enumerate(&next,&prov,&name)==1 && !strcmp(name,"Aureal A3D 2.0 (TM)"),"software CLI must never alias");
 check(a3d_hook_open(prov)==0 && !strcmp(name,"Aureal A3D 2.0 (TM)"),"no upgrade when no alias");
 check(act_created>0 && act_on==act_off && act_release==act_on,"context count balanced");
 puts("PASS v089 real-C native test: lookup unknown then canonical display, handle intact, failure/2D/CLI/opt-out safe");return 0;
}
