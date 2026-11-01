/* Independent client-side ABI checks, not game code or an A3D SDK header.
 * Test the Half-Life-style IA3d3 Init/PCM sequence, legacy control prefixes,
 * bounded capability writes, and deliberate refusal of unimplemented IA3d5.
 * No Play call is made: this does not test an output device or gameplay. */
static DWORD broad_contract(void){
 static const GUID old1=G(0xd8f1eee1,0xf634,0x11cf,0x87,0,0,0xa0,0x24,0x5d,0x91,0x8b);
 static const GUID old2=G(0xfb80d1e0,0x98d3,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
 static const GUID newer=G(0x9ae07221,0x8ac4,0x11d3,0xb6,0xaa,0,0x60,0x08,0x79,0xf3,0xee);
 typedef HRESULT(WINAPI *InitCall)(Obj*,const GUID*,DWORD,DWORD);
 typedef HRESULT(WINAPI *CapsCall)(Obj*,DWORD*);
 typedef HRESULT(WINAPI *SetModeCall)(Obj*,DWORD,DWORD,DWORD);
 typedef HRESULT(WINAPI *GetModeCall)(Obj*,DWORD*,DWORD*,DWORD*);
 typedef HRESULT(WINAPI *NewCall)(Obj*,DWORD,Obj**);
 typedef HRESULT(WINAPI *FormatCall)(Obj*,const void*);
 typedef HRESULT(WINAPI *AllocCall)(Obj*,int);
 typedef DWORD(WINAPI *SizeCall)(Obj*);
 typedef HRESULT(WINAPI *LockCall)(Obj*,DWORD,DWORD,void**,DWORD*,void**,DWORD*,DWORD);
 typedef HRESULT(WINAPI *UnlockCall)(Obj*,void*,DWORD,void*,DWORD);
 Obj *root=0,*view=0,*identity=0,*source=0;
 if(CoInitialize(0)<0)return 100;
 if(CoCreateInstance(&cls,0,1,&ia3d3,(void**)&root)<0||!root)return 101;
 const void **v=*(const void ***)root;
 if(((InitCall)v[15])(root,0,0x7fu,0))return 102;
 for(unsigned i=0;i<2;i++){
  if(root->vt->qi(root,i?&old2:&old1,(void**)&view)<0||!view)return 103;
  const void **cv=*(const void ***)view;
  if(((SetModeCall)cv[3])(view,1,1,1))return 104;
  DWORD a=0,b=0,c=0;if(((GetModeCall)cv[4])(view,&a,&b,&c)||a!=1||b!=1||c!=1)return 105;
  if(view->vt->qi(view,&iidunk,(void**)&identity)<0||identity!=root)return 106;
  identity->vt->release(identity);view->vt->release(view);
 }
 DWORD shortcaps[6]={20,0,0,0,0,0xa55aa55au};
 if(((CapsCall)v[10])(root,shortcaps)||shortcaps[1]!=20||shortcaps[5]!=0xa55aa55au)return 107;
 char limit_text[12]={0};DWORD expected_limit=128;
 if(GetEnvironmentVariableA("A3D_ALPHA_EXPECTED_VOICES",limit_text,sizeof(limit_text))){
  expected_limit=0;for(unsigned i=0;limit_text[i]>='0'&&limit_text[i]<='9';i++)expected_limit=expected_limit*10+(DWORD)(limit_text[i]-'0');
 }
 DWORD caps[11]={40,0,0,0,0,0,0,0,0,0,0xa55aa55au};
 if(((CapsCall)v[10])(root,caps)||caps[5]!=2||caps[6]!=8000||caps[7]!=192000||caps[8]!=expected_limit||caps[9]!=expected_limit||caps[10]!=0xa55aa55au)return 108;
 DWORD hardware[10]={36,1,1,1,1,1,1,1,1,0xa55aa55au};
 if(((CapsCall)v[11])(root,hardware)||hardware[9]!=0xa55aa55au)return 109;
 for(unsigned i=1;i<9;i++)if(hardware[i])return 110;
 view=(Obj*)1;
 if(root->vt->qi(root,&newer,(void**)&view)!=(HRESULT)0x80004002u||view)return 111;
 if(((NewCall)v[17])(root,4,&source)||!source)return 112;
 const void **sv=*(const void ***)source;
 /* Packed 16-byte PCM format prefix: PCM, stereo, 22050 Hz, 16 bit. */
 WORD format[8]={1,2,22050,0,22664,1,4,16};
 if(((FormatCall)sv[7])(source,format)||((AllocCall)sv[5])(source,65536))return 113;
 if(((SizeCall)sv[9])(source)!=65536)return 114;
 void *data=0;DWORD bytes=0;
 if(((LockCall)sv[11])(source,0,65536,&data,&bytes,0,0,2)||!data||bytes!=65536)return 115;
 if(((UnlockCall)sv[12])(source,data,bytes,0,0))return 116;
 source->vt->release(source);root->vt->release(root);CoUninitialize();
 say("BROAD CONTRACT PASS: Half-Life Init/PCM, IA3d control prefixes, bounded caps, IA3d5 refusal\n");return 0;
}
