/* v0.5.0 SOURCE COMMENTARY — Regression test / harness
 * Exercises the release implementation or checks its ABI/packaging contract. Do not
 * treat fixture success as proof of native Wine or retail-game compatibility.
 */
/* Host-native tests share exact DSP header with Windows DLL. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "../win32/binaural_approx.h"
static int16_t sample(const unsigned char *data,unsigned n,unsigned ch){
 unsigned i=4*n+2*ch;
 uint16_t raw=(uint16_t)((unsigned)data[i]|((unsigned)data[i+1]<<8));
 return (int16_t)raw;
}
static int iabs(int x){return x<0?-x:x;}
static int peak_at(const unsigned char *data,unsigned n,unsigned ch){
 int ix=0,max=0;
 for(unsigned i=0;i<n;i++){
  int a=iabs((int)sample(data,i,ch));if(a>max){max=a;ix=(int)i;}
 }
 return ix;
}
static unsigned energy_diff(const unsigned char *data,unsigned n,unsigned ch){
 unsigned long long val=0;
 for(unsigned i=1;i<n;i++)val+=(unsigned)iabs((int)sample(data,i,ch)-(int)sample(data,i-1,ch));
 return (unsigned)val;
}
int main(void){
 const float lis[3]={0,0,0},fwd[3]={0,0,-1},up[3]={0,1,0};
 const float right[3]={6,0,-2},left[3]={-6,0,-2};
 const float front[3]={0,0,-6},back[3]={0,0,6},top[3]={0,6,-1};
 unsigned char impulse[512]={0},out[1024]={0};
 /* Little-endian signed16 mono impulse at sample 6 */
 impulse[6*2]=0x10;impulse[6*2+1]=0x27;
 A3DBinaural r=a3d_binaural_config(right,lis,fwd,up,A3D_RIGHT_HANDED_CS,1,22050);
 assert(r.pan>0.5f&&r.delay_l>0&&r.delay_r==0&&r.lg<r.rg);
 assert(a3d_binaural_render(out,impulse,256,1,16,&r));
 assert(peak_at(out,256,0)>peak_at(out,256,1));
 A3DBinaural l=a3d_binaural_config(left,lis,fwd,up,A3D_RIGHT_HANDED_CS,1,22050);
 assert(l.delay_r>0&&l.delay_l==0&&l.lg>l.rg);
 assert(a3d_binaural_render(out,impulse,256,1,16,&l));
 assert(peak_at(out,256,1)>peak_at(out,256,0));
 A3DBinaural fr=a3d_binaural_config(front,lis,fwd,up,A3D_RIGHT_HANDED_CS,1,22050);
 A3DBinaural ba=a3d_binaural_config(back,lis,fwd,up,A3D_RIGHT_HANDED_CS,1,22050);
 A3DBinaural hi=a3d_binaural_config(top,lis,fwd,up,A3D_RIGHT_HANDED_CS,1,22050);
 assert(fr.rear==0&&ba.rear>0.6f&&hi.elevation>0.4f);
 assert(fr.delay_l==0&&fr.delay_r==0);
 for(unsigned i=0;i<256;i++){
  /* Alternating high-frequency sample sequence */
  int16_t v=(i%2==0)?9000:-9000;
  impulse[2*i]=(unsigned char)v;impulse[2*i+1]=(unsigned char)((uint16_t)v>>8);
 }
 unsigned char front_output[1024],back_output[1024],high_output[1024];
 assert(a3d_binaural_render(front_output,impulse,256,1,16,&fr));
 assert(a3d_binaural_render(back_output,impulse,256,1,16,&ba));
 assert(a3d_binaural_render(high_output,impulse,256,1,16,&hi));
 assert(energy_diff(back_output,256,0)<energy_diff(front_output,256,0));
 assert(energy_diff(high_output,256,0)!=energy_diff(front_output,256,0));
 assert(a3d_binaural_render(out,impulse,256,1,12,&r)==0);
 /* LH frame with listener facing +Z, left/right still stable. */
 const float lfwd[3]={0,0,1};
 A3DBinaural lh=a3d_binaural_config(right,lis,lfwd,up,A3D_LEFT_HANDED_CS,1,22050);
 assert(lh.pan>0.5f && lh.delay_l>0);
 puts("PASS: binaural ITD, correct channel order, rear filtering, elevation cue, invalid PCM, left-handed coordinates");
 return 0;
}
