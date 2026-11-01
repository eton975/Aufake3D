"""Boundary tests for shared caps, explicit compatibility, and launcher failures."""
from pathlib import Path
import os, shutil, subprocess, tempfile, unittest
import test_alpha as alpha
R=Path(__file__).resolve().parents[1]

class PortableBoundaryTests(unittest.TestCase):
    def test_caps_and_signature_boundaries(self):
        compiler=shutil.which('clang') or shutil.which('cc')
        if not compiler:self.skipTest('Host C compiler required')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'bounds.c';exe=root/('bounds.exe' if os.name=='nt' else 'bounds')
            source.write_text(r'''
#include <string.h>
#include "win32/capability_contract.h"
#include "experimental/halflife_splash_signature.h"
int main(void){
 unsigned char b[100],pe[84]={0},code[128]={0},names[]="Software\\Aureal\\A3D\0SplashScreen";
 unsigned char head[]={0x55,0x8b,0xec,0x83,0xec,0x10,0x53,0x56,0x57,0x89,0x4d,0xf0};
 unsigned char tail[]={0xb8,1,0,0,0,0xe9,0,0,0,0,0x5f,0x5e,0x5b,0xc9,0xc3};
 if(a3dcap_fill(0,0,24)!=1)return 1;
 for(unsigned h=0;h<2;h++)for(unsigned size=0;size<=80;size++){
  memset(b,0xa5,sizeof(b));a3dcap_write32(b+1,size);
  unsigned result=a3dcap_fill(b+1,h,24),minimum=h?16:20,known=h?36:40;
  if(result!=(size<minimum?2u:0u)||b[0]!=0xa5||a3dcap_read32(b+1)!=size)return 2;
  unsigned end=size<minimum?4:(size<known?size/4*4:known);
  for(unsigned i=end+1;i<sizeof(b);i++)if(b[i]!=0xa5)return 3;
  if(!h&&size>=40&&(a3dcap_read32(b+33)!=24||a3dcap_read32(b+37)!=24))return 4;
 }
 pe[0]='P';pe[1]='E';pe[4]=0x4c;pe[5]=1;pe[24]=0x0b;pe[25]=1;
 a3dcap_write32(pe+8,0x3749e58a);a3dcap_write32(pe+40,0x7e5c0);a3dcap_write32(pe+80,0x12c000);
 memcpy(code,head,sizeof(head));memcpy(code+113,tail,sizeof(tail));
 code[43]=0xff;code[44]=0x15;code[49]=0x85;code[50]=0xc0;code[51]=0x0f;code[52]=0x84;
 if(!hl_splash_signature(pe,code,names))return 5;
 unsigned indices[]={0,4,8,24,40,80};
 for(unsigned i=0;i<6;i++){pe[indices[i]]^=1;if(hl_splash_signature(pe,code,names))return 6;pe[indices[i]]^=1;}
 for(unsigned i=0;i<sizeof(head);i++){code[i]^=1;if(hl_splash_signature(pe,code,names))return 7;code[i]^=1;}
 for(unsigned i=113;i<128;i++){code[i]^=1;if(hl_splash_signature(pe,code,names))return 8;code[i]^=1;}
 for(unsigned i=0;i<sizeof(names);i++){names[i]^=1;if(hl_splash_signature(pe,code,names))return 9;names[i]^=1;}
 return 0;
}
''')
            subprocess.run([compiler,'-O2','-Wall','-Wextra','-Werror','-I',str(R),str(source),'-o',str(exe)],check=True)
            subprocess.run([str(exe)],check=True,timeout=20)

@unittest.skipUnless(os.name=='nt','Windows launch contracts')
class ProgressActivationTests(alpha.ActivationTests):
    def test_known_layout_child_memory_workaround(self):
        # Entirely synthetic PE: only the recognizer's landmarks are present.
        # Entry calls the stub and exits 37 only after the RAM replacement works.
        # This exercises the actual Windows read/protect/write/flush path.
        import struct
        folder,game=self.setup_profile('HalfLife-Retail')
        assembly=folder/'layout.s';obj=folder/'layout.obj'
        assembly.write_text('''.intel_syntax noprefix
.text
.org 0x661d4
_splash:
.byte 0x55,0x8b,0xec,0x83,0xec,0x10,0x53,0x56,0x57,0x89,0x4d,0xf0
.org 0x661d4+43
.byte 0xff,0x15,0,0,0,0,0x85,0xc0,0x0f,0x84
.org 0x661d4+113
.byte 0xb8,1,0,0,0,0xe9,0,0,0,0,0x5f,0x5e,0x5b,0xc9,0xc3
.org 0x7d5c0
.globl _start
_start:
call _splash
cmp eax,1
jne failed
push 37
call dword ptr ["__imp__ExitProcess@4"]
failed:
push 99
call dword ptr ["__imp__ExitProcess@4"]
.org 0xc4844
.asciz "Software\\\\Aureal\\\\A3D"
.asciz "SplashScreen"
''')
        subprocess.run([shutil.which('clang'),'-target','i686-pc-windows-msvc','-c',str(assembly),'-o',str(obj)],check=True)
        link=[shutil.which('lld-link')] if shutil.which('lld-link') else [shutil.which('ld.lld'),'-flavor','link']
        subprocess.run(link+['/machine:x86','/subsystem:console','/entry:start','/nodefaultlib','/safeseh:no','/timestamp:927589770','/out:'+str(game),str(obj),str(R/'experimental/build/kernel32.lib'),'/alternatename:__imp__ExitProcess@4=__imp__ExitProcess'],check=True)
        data=bytearray(game.read_bytes());pe=struct.unpack_from('<I',data,60)[0]
        # A larger reserved image is valid; no extra code or proprietary bytes.
        struct.pack_into('<I',data,pe+80,0x12c000)
        self.assertEqual(struct.unpack_from('<I',data,pe+40)[0],0x7e5c0)
        game.write_bytes(data);before=game.read_bytes()
        env=os.environ.copy();env.update(A3D_HALFLIFE_SPLASH_FIX='1',A3D_LAUNCH_LOG='1')
        result=subprocess.run([str(folder/'halflife-a3d-alpha.exe')],env=env,capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,37,result.stdout+result.stderr)
        self.assertIn('splash setup skipped in child RAM',result.stderr)
        self.assertEqual(game.read_bytes(),before)
    def test_configured_voice_limit_and_optional_log(self):
        folder,_=self.setup_profile('HalfLife-Retail')
        env=os.environ.copy();env.update(A3D_ALPHA_FIXTURE_TOKEN='inherited value',A3D_VOICE_LIMIT='24',A3D_ALPHA_EXPECTED_VOICES='24',A3D_LOG='0',A3D_LAUNCH_LOG='0')
        command=[str(folder/'halflife-a3d-alpha.exe'),'+alpha_probe','two words']
        first=subprocess.run(command,env=env,capture_output=True,text=True,timeout=25)
        self.assertEqual(first.returncode,37,first.stdout+first.stderr)
        log=folder/'a3d-launcher.log';self.assertFalse(log.exists())
        env['A3D_LAUNCH_LOG']='1'
        second=subprocess.run(command,env=env,capture_output=True,text=True,timeout=25)
        self.assertEqual(second.returncode,37,second.stdout+second.stderr)
        text=log.read_text();self.assertIn('Child resumed',text);self.assertIn('0x00000025',text)
        self.assertNotIn('two words',text);self.assertLess(log.stat().st_size,65537)
    def test_requested_workaround_rejects_unknown_game(self):
        folder,game=self.setup_profile('HalfLife-Retail');before=game.read_bytes()
        env=os.environ.copy();env.update(A3D_HALFLIFE_SPLASH_FIX='1',A3D_LAUNCH_LOG='1')
        result=subprocess.run([str(folder/'halflife-a3d-alpha.exe')],env=env,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,4,result.stdout+result.stderr)
        self.assertIn('unknown signature',result.stderr);self.assertEqual(game.read_bytes(),before)
    def test_generic_self_target_rejected(self):
        folder=self.root/'recursive';folder.mkdir()
        shutil.copy2(R/'experimental/build/a3d-launch.exe',folder/'a3d-launch.exe')
        result=subprocess.run([str(folder/'a3d-launch.exe'),'--game','a3d-launch.exe','--'],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,2);self.assertIn('recursive',result.stderr)
    def test_preflight_failure_log(self):
        folder,_=self.setup_profile('HalfLife-Retail');(folder/'hl.exe.manifest').unlink()
        env=os.environ.copy();env.update(A3D_LAUNCH_LOG='1')
        result=subprocess.run([str(folder/'halflife-a3d-alpha.exe')],env=env,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,2)
        self.assertIn('Missing adjacent',(folder/'a3d-launcher.log').read_text())
