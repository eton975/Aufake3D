/* Aufake3D v0.8.8: deterministic measured-HRTF stereo calibration.
 * Compiles against the SAME shared HRTF/coordinate helper headers as the
 * existing emulator tests. It is NOT a replacement for game-loopback capture
 * or proof of player-specific A3D spatial fidelity.
 * MIT KEMAR coefficients are generic/nonindividual and not Aureal HRTF.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include "offline_sources/measured_hrtf.h"
#define SR 48000u
#define NF 48000u
static int s16(const unsigned char*p){unsigned x=(unsigned)p[0]|((unsigned)p[1]<<8);return x>=32768?(int)x-65536:(int)x;}
static void le16(FILE*f,uint16_t x){fputc(x&255,f);fputc((x>>8)&255,f);}
static void le32(FILE*f,uint32_t x){le16(f,(uint16_t)x);le16(f,(uint16_t)(x>>16));}
static int wav(const char*path,const unsigned char*pcm,unsigned frames){
 FILE*f=fopen(path,"wb");if(!f)return 0;uint32_t bytes=frames*4;
 fwrite("RIFF",1,4,f);le32(f,36+bytes);fwrite("WAVEfmt ",1,8,f);
 le32(f,16);le16(f,1);le16(f,2);le32(f,SR);le32(f,SR*4);le16(f,4);le16(f,16);
 fwrite("data",1,4,f);le32(f,bytes);int ok=fwrite(pcm,1,bytes,f)==bytes;fclose(f);return ok;
}
static void clean_stimulus(unsigned char*b){
 uint32_t rng=0xABCD1234u;
 for(unsigned i=0;i<NF;i++){
  rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;
  float n=(float)((int)(rng&65535u)-32768)/32768.0f;
  /* Correlated source across directions, low enough to avoid limiter. */
  float x=(0.18f*n+0.15f*sinf(2.0f*3.14159265358979323846f*440.0f*i/SR));
  float ramp=(i<960?i/960.0f:(i>NF-960?(NF-i)/960.0f:1.0f));
  short s=(short)(x*ramp*32767.0f);
  b[2*i]=(unsigned char)(s&255);b[2*i+1]=(unsigned char)(((unsigned short)s)>>8);
 }
}
static int clip_count(const unsigned char*b){int count=0;for(unsigned i=0;i<NF*2;i++){int v=s16(b+i*2);if(v>=32760||v<=-32760)count++;}return count;}
static void energies(const unsigned char*b,double*left,double*right){
 double l=0,r=0;for(unsigned i=0;i<NF;i++){
  double x=s16(b+4*i),y=s16(b+4*i+2);l+=x*x;r+=y*y;
 }*left=l/NF;*right=r/NF;
}
int main(int argc,char**argv){
 int want_wav=argc>=2;
 unsigned char *mono=(unsigned char*)malloc(NF*2u),*out=(unsigned char*)malloc(NF*4u);
 if(!mono||!out){fputs("allocation failure\n",stderr);return 3;}
 clean_stimulus(mono);
 const float origin[3]={0,0,0},fwd[3]={0,0,-1},up[3]={0,1,0};
 const struct {const char*name;float xyz[3];} poses[]={
  {"left",{-5,0,-5}},{"right",{5,0,-5}},{"front",{0,0,-6}},
  {"behind",{0,0,6}},{"far_left",{-20,0,-20}}
 };
 double L[5],R[5];int indices[5],fail=0;
 for(unsigned p=0;p<5;p++){
  memset(out,0,NF*4);
  A3DMeasuredPick pick=a3d_measured_pick(poses[p].xyz,origin,fwd,up,A3D_RIGHT_HANDED_CS,1.0f,SR);
  if(pick.taps==0||!a3d_measured_render(out,mono,NF,1,16,&pick)){fprintf(stderr,"HRTF render failure %s\n",poses[p].name);return 4;}
  indices[p]=pick.direction;energies(out,&L[p],&R[p]);
  if(clip_count(out))fail++;
  if(want_wav){char fn[400];int n=snprintf(fn,sizeof fn,"%s/%s.wav",argv[1],poses[p].name);if(n<=0||(unsigned)n>=sizeof fn||!wav(fn,out,NF)){fprintf(stderr,"Cannot save %s\n",poses[p].name);return 5;}}
 }
 /* Not universal perceptual thresholds: just structural/mathematical invariants. */
 double lr=10.0*log10((L[0]+1)/(R[0]+1));
 double rr=10.0*log10((R[1]+1)/(L[1]+1));
 double f=0.5*(L[2]+R[2]),b=0.5*(L[3]+R[3]);
 double near=0.5*(L[0]+R[0]),far=0.5*(L[4]+R[4]);
 if(!(lr>1.0&&rr>1.0&&L[0]>R[0]&&R[1]>L[1]))fail++;
 if(!(near>far*1.1))fail++;
 if(indices[2]==indices[3] || f<=1 || b<=1)fail++;
 printf("{\"schema\":\"aufake3d-v088-hrtf-offline\",\"source\":\"shared KEMAR HRTF code, not live Alice output\",\"sample_rate\":48000,\"left_ear_advantage_db\":%.5f,\"right_ear_advantage_db\":%.5f,\"near_to_far_energy_ratio\":%.5f,\"front_hrir_index\":%d,\"behind_hrir_index\":%d,\"clipped\":%s,\"failures\":%d}\n",lr,rr,near/(far+1e-5),indices[2],indices[3],fail?"true":"false",fail);
 free(mono);free(out);return fail?1:0;
}
