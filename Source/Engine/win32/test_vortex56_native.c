/* Hardware-reference format/DSP integration tests; no game or sound device. */
#include <stdio.h>
#include <stdlib.h>
#include "stream_core.h"
static A3DMix m;
static A3DMixVoice v;
static unsigned char data[4096];
static unsigned char out[1024];
static int fail(const char *p){fprintf(stderr,"FAIL %s\n",p);return 1;}
static int closef(float a,float b,float tol){return aufake_v2_abs(a-b)<=tol;}
static unsigned long long signal_energy(void){
 unsigned long long e=0;
 for(unsigned i=0;i<512u;i++){
  int n=out[i*2] | ((int)out[i*2+1]<<8);
  if(n>32767)n-=65536;
  e+=(unsigned long long)(n*n);
 }
 return e;
}
static void prepare(unsigned mode){
 a3dmix_init(&m);a3dmix_voice_init(&v);
 m.hrtf_mode=mode;m.master_boost=1.0f;m.reverb_wet=0.0f;m.hrtf_taps=56u;
 v.pcm=data;v.bytes=sizeof(data);v.rate=48000u;v.channels=1u;v.bits=16u;
 v.active=1u;v.looping=1u;v.pos[2]=-1.0f;
 a3dmix_add(&m,&v);
}
int main(void){
 float c[2][56],d[2];
 aufake_v2_lookup(0.0f,0.0f,c,d);
 if(!closef(c[0][0],(float)aufake_v2_coeff[3*24][0][0],0.0001f))return fail("front tap0");
 if(!closef(d[0],0.0f,0.00001f)||!closef(d[1],0.0f,0.00001f))return fail("front zero ITD");
 aufake_v2_lookup(180.0f,0.0f,c,d);
 if(!closef(d[0],0.0f,0.00001f)||!closef(d[1],0.0f,0.00001f))return fail("corrected rear ITD");
 if(!closef(c[0][0],5945.0f,0.0001f)||!closef(c[1][0],5792.0f,0.0001f))return fail("corrected rear coeff");
 aufake_v2_lookup(90.0f,0.0f,c,d);
 if(d[0]<30.0f||d[1]!=0.0f)return fail("right azimuth must delay left ear");
 aufake_v2_lookup(270.0f,0.0f,c,d);
 if(d[1]<30.0f||d[0]!=0.0f)return fail("left azimuth must delay right ear");
 aufake_v2_lookup(355.0f,0.0f,c,d);
 if(!closef(c[0][0],((float)aufake_v2_coeff[3*24+23][0][0]*5.0f+(float)aufake_v2_coeff[3*24][0][0]*10.0f)/15.0f,1.0f))return fail("azimuth wrap");
 for(unsigned i=0;i<sizeof(data);i++)data[i]=0;
 data[0]=0xff;data[1]=0x7f;
 prepare(1u);a3dmix_render(&m,out,256u);
 if(signal_energy()<50000u)return fail("fast56 impulse silent");
 float fast=v.v2_coeff[0][0];
 prepare(2u);a3dmix_render(&m,out,256u);
 if(signal_energy()<50000u)return fail("reference56 impulse silent");
 if(v.v2_coeff[0][0]!=fast)return fail("static position modes differ");
 /* After direction change, reference glides rather than jumps immediately. */
 float before=v.v2_coeff[0][0];v.pos[0]=2.0f;
 a3dmix_render(&m,out,256u);
 float target=v.v2_target[0][0];
 if(closef(target,before,1.0f))return fail("movement did not change target");
 if(!(aufake_v2_abs(v.v2_coeff[0][0]-before)<aufake_v2_abs(target-before)))return fail("tracking jumped too far");
 printf("PASS: corrected HRTF 56 taps, channel ITD, wrap, impulse render, reference tracking\n");
 return 0;
}
