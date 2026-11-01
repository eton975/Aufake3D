"""Exercise the actual v0.6.6 logging gate and writer with mocked Win32 I/O.
This validates the release's opt-in policy and hard byte cap, but does not
replace gameplay or Windows-on-device testing.
"""
import pathlib, shutil, subprocess, tempfile, unittest
API=(pathlib.Path(__file__).resolve().parents[1]/'win32/a3dapi.c')

def extract(s, token):
    p=s.index(token)
    opening=s.index('{',p)
    depth=0
    for i in range(opening,len(s)):
        if s[i]=='{': depth+=1
        elif s[i]=='}':
            depth-=1
            if not depth: return s[p:i+1]
    raise RuntimeError(token)

class LoggingSafety(unittest.TestCase):
    def test_log_disabled_by_default_and_hard_cap(self):
        if not shutil.which('cc'): self.skipTest('native C compiler missing')
        code=API.read_text()
        self.assertIn('#define A3D_LOG_LIMIT_BYTES (1024u*1024u)',code)
        gate=extract(code,'static int a3d_log_enabled(void)')
        write=extract(code,'static void logline(const char *s)')
        native=r'''#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef uint32_t DWORD;
typedef int BOOL;
typedef void *HANDLE;
#define INVALID_HANDLE_VALUE ((HANDLE)(-1))
#define A3D_LOG_LIMIT_BYTES (1024u*1024u)
#define GENERIC_WRITE 0x40000000UL
#define CREATE_ALWAYS 2UL
#define FILE_APPEND_DATA 4UL
#define FILE_SHARE_READ 1UL
#define FILE_SHARE_WRITE 2UL
#define OPEN_ALWAYS 4UL
#define FILE_ATTRIBUTE_NORMAL 128UL
static int a3d_log_gate=-1,a3d_log_created=0;
static volatile long a3d_log_bytes=0;
static size_t mock_bytes=0;
static unsigned mock_opens=0,mock_truncates=0;
static int mock_enabled=0;
static DWORD cstrlen(const char *s){return (DWORD)strlen(s);}
static DWORD GetEnvironmentVariableA(const char *key,char *out,DWORD size){
 const char *s="";
 if(strcmp(key,"A3D_LOG")==0)s=mock_enabled?"1":"0";
 if(strcmp(key,"A3D_PROBE_LOG")==0)s="alice-a3d-test.log";
 DWORD n=(DWORD)strlen(s);
 if(n>=size)return n+1;
 memcpy(out,s,n+1);return n;
}
static long InterlockedCompareExchange(volatile long *loc,long next,long expect){
 long old=*loc; if(old==expect)*loc=next;return old;
}
static HANDLE CreateFileA(const char *p,DWORD access,DWORD share,void *security,
 DWORD mode,DWORD attrs,HANDLE tpl){
 (void)p;(void)access;(void)share;(void)security;(void)attrs;(void)tpl;
 mock_opens++;
 if(mode==CREATE_ALWAYS){mock_truncates++;mock_bytes=0;}
 return (HANDLE)1;
}
static BOOL WriteFile(HANDLE h,const void *data,DWORD size,DWORD *written,void *overlapped){
 (void)h;(void)data;(void)overlapped;
 mock_bytes+=size;*written=size;return 1;
}
static BOOL CloseHandle(HANDLE h){(void)h;return 1;}
'''+gate+'\n'+write+r'''
int main(void){
 for(int i=0;i<2000;i++)logline("no output by default");
 assert(mock_opens==0 && mock_bytes==0);
 mock_enabled=1;a3d_log_gate=-1;
 for(int i=0;i<80000;i++)logline("Bounded diagnostics during a prolonged real-time audio session");
 assert(mock_truncates==1);
 assert(mock_bytes>500000 && mock_bytes<=A3D_LOG_LIMIT_BYTES);
 unsigned before=mock_opens;
 for(int i=0;i<1000;i++)logline("No more file writes after reaching the byte budget");
 assert(mock_opens==before);
 puts("PASS: no default logging; hard 1MiB lifetime cap");
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as d:
            f=pathlib.Path(d)/'log.c'; o=pathlib.Path(d)/'logtest'
            f.write_text(native)
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(f),'-o',str(o)],check=True,capture_output=True,text=True)
            out=subprocess.check_output([str(o)],text=True)
            self.assertIn('PASS',out)
    def test_profiles_never_log_without_explicit_enable(self):
        r=API.read_text()
        self.assertIn('if(!a3d_log_enabled()||!s)return;',r)
        w=(API.parent.parent/'deploy-v066/Alice2000/RUN_A3D_WINDOWS.cmd').read_text()
        self.assertIn('A3D_LOG=0',w)
        for name in ('6x256','3x512','8x256','4x256'):
            c=(API.parent.parent/f'deploy-v066/Alice2000/RUN_A3D_{name}_WINDOWS.cmd').read_text()
            self.assertIn('A3D_LOG=1',c)
            self.assertIn('A3D_WAVEOUT_ADAPTIVE=0',c)

if __name__=='__main__':unittest.main()
