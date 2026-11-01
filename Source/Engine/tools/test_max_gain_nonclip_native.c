/* Standalone regression for the existing A3D v0.6.1 sample-peak limiter. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "../win32/stream_core.h"
int main(void){
 A3DMix *m=calloc(1,sizeof(*m));
 A3DMixVoice *voices=calloc(16,sizeof(*voices));
 assert(m && voices);
 static unsigned char sample[1024];
 for(unsigned i=0;i<512;i++){
  short s=(short)((i%2)?-30000:30000);
  sample[2*i]=(unsigned char)((unsigned short)s&255);
  sample[2*i+1]=(unsigned char)(((unsigned short)s)>>8);
 }
 a3dmix_init(m);
 assert(m->master_boost==5.0f);
 for(int i=0;i<16;i++){
  A3DMixVoice *v=&voices[i];
  a3dmix_voice_init(v);
  v->pcm=sample;v->bytes=sizeof(sample);v->channels=1;
  v->bits=16;v->rate=48000;v->active=1;v->looping=1;
  v->pos[2]=-1.0f;
  assert(a3dmix_add(m,v));
 }
 unsigned char out[A3DMIX_BLOCK*4];
 unsigned maxabs=0;
 for(int pass=0;pass<64;pass++){
  a3dmix_render(m,out,A3DMIX_BLOCK);
  for(unsigned i=0;i<sizeof(out);i+=2){
   unsigned u=out[i]|((unsigned)out[i+1]<<8);
   int x=u>=32768?(int)u-65536:(int)u;
   unsigned absx=(unsigned)(x<0?-x:x);
   if(absx>maxabs)maxabs=absx;
   /* Allow one bit of rounding wiggle against 0.95*32768=31129.6 */
   assert(absx<=31132);
  }
 }
 assert(m->clip_events>0);
 assert(m->limiter_active_frames>0);
 printf("PASS: default gain %.1f; synthetic 16-voice PCM peak=%u/32768, limiting events=%u, limited frames=%u\n",m->master_boost,maxabs,m->clip_events,m->limiter_active_frames);
 free(voices);free(m);
 return 0;
}
