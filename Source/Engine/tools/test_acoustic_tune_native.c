/* v0.5.0 SOURCE COMMENTARY — Regression test / harness
 * Exercises the release implementation or checks its ABI/packaging contract. Do not
 * treat fixture success as proof of native Wine or retail-game compatibility.
 */
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include "../win32/stream_core.h"
static unsigned long energy(const unsigned char *pcm,unsigned frames){
 unsigned long total=0;
 for(unsigned i=0;i<frames*4;i+=2){unsigned x=pcm[i]|((unsigned)pcm[i+1]<<8);int y=(x>=32768)?(int)x-65536:(int)x;total+=(unsigned long)(y<0?-y:y);}
 return total;
}
static unsigned long render(float trim,float strength,float wet){
 A3DMix*m=(A3DMix*)calloc(1,sizeof(*m));A3DMixVoice*v=(A3DMixVoice*)calloc(1,sizeof(*v));assert(m&&v);
 unsigned char src[512*2],out[A3DMIX_BLOCK*4];
 for(unsigned i=0;i<512;i++){int x=(int)(i%24)*30-360;unsigned short t=(unsigned short)(short)x;src[2*i]=(unsigned char)t;src[2*i+1]=(unsigned char)(t>>8);}
 a3dmix_init(m);a3dmix_voice_init(v);m->direct_trim=trim;m->distance_strength=strength;m->reverb_wet=wet;m->distance_enabled=1;
 v->pcm=src;v->bytes=sizeof(src);v->rate=48000;v->channels=1;v->bits=16;v->active=1;v->looping=1;
 v->pos[2]=-4.0f;v->min_dist=1;v->max_dist=20;
 assert(a3dmix_add(m,v));a3dmix_render(m,out,A3DMIX_BLOCK);
 unsigned long ret=energy(out,A3DMIX_BLOCK);
 free(v);free(m);return ret;
}
int main(void){
 A3DMix*m=(A3DMix*)calloc(1,sizeof(*m));A3DMixVoice*v=(A3DMixVoice*)calloc(1,sizeof(*v));assert(m&&v);
 a3dmix_init(m);a3dmix_voice_init(v);
 assert(m->direct_trim==1.0f && m->distance_strength==1.0f);
 assert(a3dmix_distance_gain(m,v,4)==1.0f); /* distance disabled */
 unsigned long baseline=render(1,1,0),louder=render(2,1,0),closer=render(1,0.5f,0);
 assert(baseline>0 && louder>baseline && closer>baseline);
 unsigned long dry=render(1,1,0),wet=render(1,1,0.14f);
 assert(dry==wet);/* reverberation starts later than one 256-frame block */
 printf("acoustic-tune PASS: baseline=%lu boosted=%lu softened=%lu\n",baseline,louder,closer);
 free(v);free(m);return 0;
}
