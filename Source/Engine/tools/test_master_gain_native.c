/* v0.5.0 SOURCE COMMENTARY — Regression test / harness
 * Exercises the release implementation or checks its ABI/packaging contract. Do not
 * treat fixture success as proof of native Wine or retail-game compatibility.
 */
/* v0.4.5 gain and linked peak-limiter regression. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "../win32/stream_core.h"
static unsigned long long render(float boost,unsigned *maxabs,unsigned *limited){
 A3DMix*m=calloc(1,sizeof(*m));A3DMixVoice*v=calloc(1,sizeof(*v));assert(m&&v);
 static unsigned char sample[1024];
 for(unsigned i=0;i<512;i++){short x=(short)((i%2)?-18000:18000);sample[2*i]=x&255;sample[2*i+1]=((unsigned short)x)>>8;}
 a3dmix_init(m);a3dmix_voice_init(v);assert(m->master_boost==5.0f&&m->limiter_gain==1.0f);
 m->master_boost=boost;m->reverb_wet=0;
 v->pcm=sample;v->bytes=sizeof(sample);v->channels=1;v->bits=16;v->rate=48000;v->active=1;v->looping=1;
 v->pos[0]=1;v->pos[2]=-0.5f;
 assert(a3dmix_add(m,v));
 unsigned char out[A3DMIX_BLOCK*4];a3dmix_render(m,out,A3DMIX_BLOCK);
 unsigned long long sum=0;*maxabs=0;
 for(unsigned i=0;i<sizeof(out);i+=2){unsigned u=out[i]|((unsigned)out[i+1]<<8);int x=u>=32768?(int)u-65536:(int)u;unsigned av=(unsigned)(x<0?-x:x);if(av>*maxabs)*maxabs=av;sum+=av;}
 *limited=m->clip_events;free(v);free(m);return sum;
}
static void stress_limiter(void){
 A3DMix*m=calloc(1,sizeof(*m));A3DMixVoice *voices=calloc(12,sizeof(*voices));assert(m&&voices);
 static unsigned char samples[1024];
 for(unsigned k=0;k<512;k++){short x=30000;samples[2*k]=x&255;samples[2*k+1]=x>>8;}
 a3dmix_init(m);m->master_boost=2.5f;m->reverb_wet=0;
 for(int i=0;i<12;i++){
  A3DMixVoice*v=&voices[i];a3dmix_voice_init(v);v->pcm=samples;v->bytes=sizeof(samples);
  v->channels=1;v->bits=16;v->rate=48000;v->active=1;v->looping=1;v->pos[2]=-1;
  assert(a3dmix_add(m,v));
 }
 unsigned char out[A3DMIX_BLOCK*4];a3dmix_render(m,out,A3DMIX_BLOCK);
 unsigned max=0;for(unsigned i=0;i<sizeof(out);i+=2){
  unsigned u=out[i]|(out[i+1]<<8);int x=(u>=32768)?(int)u-65536:(int)u;
  unsigned a=(unsigned)(x<0?-x:x);if(a>max)max=a;
 }
 assert(m->clip_events>0 && max<=31200);
 printf("limiter stress PASS: limited=%u peak=%u/32767 gain=%.3f\n",m->clip_events,max,m->limiter_gain);
 free(voices);free(m);
}
int main(void){
 stress_limiter();
 unsigned m1,m15,m25,c1,c15,c25;
 unsigned long long base=render(1.0f,&m1,&c1),loud=render(1.5f,&m15,&c15),hot=render(2.5f,&m25,&c25);
 assert(base>0 && loud>base && hot>loud);
 assert(loud*100>base*135 && loud*100<base*165);
 assert(m25<=32112 && m15<=32112);
 printf("master boost PASS: 1.0=%llu, 1.5=%llu, 2.5=%llu; peak=%u/%u/%u, limiter=%u/%u/%u\n",base,loud,hot,m1,m15,m25,c1,c15,c25);
 return 0;
}
