/* Offline regression: a 24-tap measured HRIR must contain the actual impulse,
 * not just its near-zero leading acoustic delay. Runs on native Linux, no Wine.
 */
#include <stdio.h>
#include <stdlib.h>
#include "stream_core.h"
static A3DMix mixer;
static A3DMixVoice voice;
static unsigned char src_pcm[1024];
static unsigned char rendered[A3DMIX_BLOCK*4];
static long long output_energy(void){
 long long e=0;
 for(unsigned i=0;i<A3DMIX_BLOCK*2;i++){
  int value=(int)rendered[2*i]|((int)rendered[2*i+1]<<8);
  if(value>32767)value-=65536;
  e+=(long long)value*value;
 }
 return e;
}
int main(void){
 a3dmix_init(&mixer);a3dmix_voice_init(&voice);
 mixer.hrtf_taps=24u;mixer.master_boost=1.0f;mixer.reverb_wet=0.0f;
 voice.pcm=src_pcm;voice.bytes=sizeof(src_pcm);voice.rate=48000u;
 voice.channels=1u;voice.bits=16u;voice.looping=0u;voice.active=1u;
 voice.gain=1.0f;voice.pitch=1.0f;voice.pos[2]=-1.0f;
 src_pcm[0]=0xff;src_pcm[1]=0x7f;
 if(!a3dmix_add(&mixer,&voice))return 2;
 a3dmix_render(&mixer,rendered,A3DMIX_BLOCK);
 long long energy=output_energy();
 printf("Fast24 impulse output sum-of-squares: %lld\n",energy);
 if(energy<1000000LL){fprintf(stderr,"FAIL: 24-tap output is effectively silent\n");return 1;}
 printf("PASS: 24-tap mode produces audible-scale direct signal with reverb disabled\n");
 return 0;
}
