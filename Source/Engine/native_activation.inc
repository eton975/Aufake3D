/* v0.6.12 activation boundary: keep registration local to the launched child.
 * Activation manifests resolve the adjacent A3D COM server without global
 * registration. Selector edits are signature-checked in suspended child RAM;
 * unknown executable layouts fail closed. Original game files stay on disk.
 */
void *memset(void *ptr,int value,unsigned long size){unsigned char *p=(unsigned char*)ptr;for(unsigned long i=0;i<size;i++)p[i]=(unsigned char)value;return ptr;}
/* Native Windows: explicitly activate the adjacent manifest in the child's main
 * thread after loader startup, before the game entry point. No registry changes. */
DLLIMPORT BOOL STDCALL GetThreadContext(HANDLE,LPVOID);
DLLIMPORT BOOL STDCALL SetThreadContext(HANDLE,LPCSTR);
DLLIMPORT HANDLE STDCALL CreateActCtxA(LPVOID);
DLLIMPORT BOOL STDCALL ActivateActCtx(HANDLE,LPVOID);
static int activate_child(PROCESS_INFORMATION *p,const char *exe,HANDLE err){
 static DWORD ctx[179];DWORD n=0,remote,entry,k=0; SIZE_T done=0;
 static BYTE block[4096]; char *manifest=(char*)block+512; char *dir=(char*)block+2048;
 BYTE *code=block+64; LPVOID mem;
 while(exe[k]&&k<1400){manifest[k]=exe[k];dir[k]=exe[k];k++;}
 if(exe[k]||k>1400){out(err,"Manifest path too long.\r\n");return 0;}
 {const char *suffix=".manifest";DWORD j=0;while(suffix[j]){manifest[k+j]=suffix[j];j++;}}
 {DWORD j=k;while(j&&dir[j-1]!='\\'&&dir[j-1]!='/')j--;dir[j]=0;}
 ctx[0]=0x10003u;
 if(!GetThreadContext(p->hThread,ctx)){out(err,"GetThreadContext failed.\r\n");return 0;}
 entry=ctx[44];
 mem=VirtualAllocEx(p->hProcess,0,sizeof(block),MEM_RESERVE|MEM_COMMIT,PAGE_EXECUTE_READWRITE);
 if(!mem)return 0;remote=(DWORD)mem;
 u32(block,32);u32(block+4,4);u32(block+8,remote+512);u32(block+16,remote+2048);
 /* pushfd; pushad; CreateActCtxA(&act); ActivateActCtx(act,&cookie). */
 code[n++]=0x9c;code[n++]=0x60;code[n++]=0x68;u32(code+n,remote);n+=4;
 code[n++]=0xb8;u32(code+n,(DWORD)CreateActCtxA);n+=4;code[n++]=0xff;code[n++]=0xd0;
 code[n++]=0x83;code[n++]=0xf8;code[n++]=0xff;code[n++]=0x74;DWORD fail1=n++;
 code[n++]=0x68;u32(code+n,remote+32);n+=4;code[n++]=0x50;
 code[n++]=0xb8;u32(code+n,(DWORD)ActivateActCtx);n+=4;code[n++]=0xff;code[n++]=0xd0;
 code[n++]=0x85;code[n++]=0xc0;code[n++]=0x74;DWORD fail2=n++;
 code[n++]=0x61;code[n++]=0x9d;code[n++]=0x68;u32(code+n,entry);n+=4;code[n++]=0xc3;
 DWORD failure=n;code[fail1]=(BYTE)(failure-fail1-1);code[fail2]=(BYTE)(failure-fail2-1);
 code[n++]=0x68;u32(code+n,0xa3d00001u);n+=4;code[n++]=0xb8;u32(code+n,(DWORD)ExitProcess);n+=4;code[n++]=0xff;code[n++]=0xd0;
 if(!WriteProcessMemory(p->hProcess,mem,(LPCSTR)block,sizeof(block),&done)||done!=sizeof(block))return 0;
 FlushInstructionCache(p->hProcess,(LPCSTR)mem,sizeof(block));
 ctx[44]=remote+64;
 if(!SetThreadContext(p->hThread,(LPCSTR)ctx))return 0;
 out(err,"Native child manifest bootstrap installed; no registry or game-file changes.\r\n");return 1;
}
