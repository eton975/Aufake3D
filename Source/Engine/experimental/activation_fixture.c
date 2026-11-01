/* Synthetic console child used to test the alpha launchers. No game code.
 * The parent must preserve quoted args, environment and this exit status while
 * activating the adjacent manifest before CoCreateInstance reaches the server.
 */
#define start fixture_original_start
#include "../win32/com_test.c"
#undef start
IMPORT char* WINAPI GetCommandLineA(void);
IMPORT DWORD WINAPI GetEnvironmentVariableA(const char*,char*,DWORD);
static int contains(const char *text,const char *needle){
 for(;*text;text++){unsigned i=0;while(needle[i]&&text[i]==needle[i])i++;if(!needle[i])return 1;}return 0;
}
/* Exercise an independently written subset of the Galaxy startup contract
 * observed in the inspected Unreal Gold build: IA3d4, Init flags 0xc2, the
 * left-handed coordinate system, geometry and listener discovery. No source
 * playback, DirectSound interoperation or game code is exercised here. */
static DWORD galaxy_contract(void){
 Obj *root=0,*listener=0,*geometry=0;
 static const GUID listener_id=G(0xc398e563,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
 typedef HRESULT(WINAPI *InitRoot)(Obj*,const GUID*,DWORD,DWORD);
 typedef HRESULT(WINAPI *SetCoords)(Obj*,DWORD);
 if(CoInitialize(0)<0)return 92;
 if(CoCreateInstance(&cls,0,1,&ia3d4,(void**)&root)<0||!root)return 93;
 const void **slots=*(const void ***)root;
 if(((InitRoot)slots[15])(root,0,0xc2u,0))return 94;
 if(((SetCoords)slots[23])(root,1u))return 95;
 if(root->vt->qi(root,&listener_id,(void**)&listener)<0||!listener)return 96;
 if(root->vt->qi(root,&geom,(void**)&geometry)<0||!geometry)return 97;
 listener->vt->release(listener);geometry->vt->release(geometry);root->vt->release(root);
 CoUninitialize();say("GALAXY SUBSET PASS: IA3d4, Init 0xc2, left-handed coordinates, geometry/listener\n");return 0;
}
#include "client_contracts.inc"
void WINAPI start(void){
 char token[32]={0};GetEnvironmentVariableA("A3D_ALPHA_FIXTURE_TOKEN",token,sizeof(token));
 if(!contains(token,"inherited value"))ExitProcess(90);
 if(!contains(GetCommandLineA(),"+alpha_probe \"two words\""))ExitProcess(91);
 DWORD result=test();if(result)ExitProcess(result);
 result=galaxy_contract();if(result)ExitProcess(result);
 result=broad_contract();if(result)ExitProcess(result);
 say("ALPHA FIXTURE PASS: quoted args, environment, child COM activation, exit forwarding\n");
 ExitProcess(37);
}
