/* Native offline integrity test for adaptive source snapshots, high rate/pitch
   and Doppler, plus deterministic multi-block DSP output hash.
   Build twice against the v062 and v063 stream_core.h to compare DSP hashes. */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>
#include "stream_core.h"
#define CAP (A3DMIX_BLOCK*8u+2u)
static A3DMix original, windowed;
static A3DMixVoice full_voice, short_voice;
static A3DScene scene;
static unsigned char pcm[49159*4], snap[CAP*4];
static unsigned char a_out[1024],b_out[1024];
static float random_u(unsigned n){return (float)((n*1664525u+1013904223u)&0xffffu)/65535.0f;}
static unsigned capture_count(const A3DMix *m,const A3DMixVoice *v){
 const float origin[3]={0};
 const float *lis=v->head_relative?origin:m->listener;
 float dop=a3dmix_doppler(m,v,v->pos,lis);
 float step=(float)v->rate/(float)A3DMIX_RATE*v->pitch*dop;
 if(step<0.1f)step=0.1f;if(step>8.0f)step=8.0f;
 unsigned n=(unsigned)((float)A3DMIX_BLOCK*step)+4u;
 if(n>CAP)n=CAP;if(n<4)n=4;
 return n;
}
static int same_audio(unsigned test){
 const unsigned rates[]={8000,11025,16000,22050,32000,44100,48000,96000,192000};
 const float pitches[]={0.1f,0.5f,1.0f,1.6f,4.5f,8.0f};
 unsigned rate=rates[test%9], channels=1+(test/9)%2, bits=(test/18)%2?16:8;
 unsigned total= 1 + (test*73u)%49159;
 unsigned stride=channels*(bits/8);
 float pitch=pitches[(test/36)%6];
 unsigned looping=(test/216)%2, doppler=(test/432)%2;
 for(unsigned j=0;j<total*stride;j++)pcm[j]=(unsigned char)((j*71u+(j>>4)+test*13u)&255u);
 a3dmix_init(&original);a3dmix_init(&windowed);
 a3d_scene_init(&scene);
 original.scene=&scene;windowed.scene=&scene;
 original.doppler_enabled=windowed.doppler_enabled=doppler;
 original.listener[0]=windowed.listener[0]=1.f;
 original.listener_vel[0]=windowed.listener_vel[0]=44.f;
 a3dmix_voice_init(&full_voice);
 full_voice.pcm=pcm;full_voice.bytes=total*stride;
 full_voice.rate=rate;full_voice.pitch=pitch;full_voice.bits=bits;
 full_voice.channels=channels;full_voice.active=1;full_voice.looping=looping;
 full_voice.cursor=(double)((test*119u)%total)+0.63;
 if(full_voice.cursor>=total)full_voice.cursor=total-0.01;
 full_voice.pos[0]=9;full_voice.pos[2]=4;
 full_voice.vel[0]= test%2? -70.f:70.f;
 full_voice.min_dist=2;full_voice.max_dist=600;
 short_voice=full_voice;
 unsigned base=(unsigned)short_voice.cursor%total;
 unsigned nf=capture_count(&windowed,&short_voice);
 for(unsigned i=0;i<nf;i++){
  unsigned pos=(base+i)%total;
  memcpy(snap+i*stride,pcm+pos*stride,stride);
 }
 short_voice.pcm=snap;short_voice.pcm_window=snap;
 short_voice.pcm_window_start=base;short_voice.pcm_window_frames=nf;
 a3dmix_add(&original,&full_voice);a3dmix_add(&windowed,&short_voice);
 a3dmix_render(&original,a_out,256);
 a3dmix_render(&windowed,b_out,256);
 if(memcmp(a_out,b_out,sizeof(a_out))||full_voice.active!=short_voice.active||
    full_voice.cursor!=short_voice.cursor){
    fprintf(stderr,"Mismatch %u rate=%u pitch=%g cursor=%g count=%u frames=%u\n",test,rate,pitch,short_voice.cursor,nf,total);
    return 1;
 }
 return 0;
}
static unsigned char big_pcm[32768];
static A3DMix bench;
static A3DMixVoice voices[10];
static uint64_t sample_hash(void){
 a3dmix_init(&bench);
 for(unsigned i=0;i<sizeof(big_pcm);i++)big_pcm[i]=(unsigned char)((i*61u+i/3)&255u);
 for(unsigned v=0;v<10;v++){
  a3dmix_voice_init(&voices[v]);
  voices[v].pcm=big_pcm;voices[v].bytes=sizeof(big_pcm);
  voices[v].rate=22050+11025*(v%3);voices[v].bits=16;voices[v].channels=1;
  voices[v].looping=1;voices[v].active=1;voices[v].pitch=0.9f+0.04f*v;
  voices[v].pos[0]=v*1.5f;voices[v].pos[2]=-3.f-v*2.f;
  a3dmix_add(&bench,&voices[v]);
 }
 uint64_t h=1469598103934665603ULL;
 clock_t t0=clock();
 for(unsigned iter=0;iter<80;iter++){
  bench.listener[0]=0.125f*iter;
  a3dmix_render(&bench,a_out,256);
  for(unsigned i=0;i<sizeof(a_out);i++){h^=a_out[i];h*=1099511628211ULL;}
 }
 double dt=(double)(clock()-t0)/CLOCKS_PER_SEC;
 printf("multivoice_hash=%016llx dsp_80x10_cpu_seconds=%.6f\n",(unsigned long long)h,dt);
 return h;
}
int main(void){
 unsigned failed=0;
 for(unsigned t=0;t<864;t++)failed+=same_audio(t);
 printf("adaptive_capture_parity_cases=864 failed=%u\n",failed);
 sample_hash();
 return failed?1:0;
}
