/* v0.5.0 SOURCE COMMENTARY — Regression test / harness
 * Exercises the release implementation or checks its ABI/packaging contract. Do not
 * treat fixture success as proof of native Wine or retail-game compatibility.
 */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../win32/stream_core.h"
static short rd(const unsigned char*x,unsigned n,unsigned ch){unsigned i=4*n+2*ch;unsigned t=x[i]|((unsigned)x[i+1]<<8);return (short)(t>=32768?t-65536:t);}
static unsigned count_nonzero(const unsigned char*p,unsigned frames){unsigned n=0;for(unsigned i=0;i<frames*4;i++)if(p[i])n++;return n;}
int main(void){
 A3DMix*m=calloc(1,sizeof(*m));A3DMixVoice*v=calloc(1,sizeof(*v)),*w=calloc(1,sizeof(*w));
 assert(m&&v&&w);a3dmix_init(m);a3dmix_voice_init(v);a3dmix_voice_init(w);
 assert(m->reverb_wet>0&&m->reverb_wet<0.5f);
 unsigned char pcm[1024]={0};for(unsigned n=0;n<512;n++){short t=(short)((n%32)*500-7000);pcm[2*n]=(unsigned char)t;pcm[2*n+1]=(unsigned char)((unsigned short)t>>8);}
 v->pcm=pcm;v->bytes=sizeof(pcm);v->rate=48000;v->channels=1;v->bits=16;v->pos[0]=4;v->pos[2]=-2;v->active=1;v->looping=1;
 assert(a3dmix_add(m,v));assert(a3dmix_add(m,v));assert(m->v[1]==NULL);
 unsigned char out[A3DMIX_BLOCK*4];a3dmix_render(m,out,A3DMIX_BLOCK);
 assert(count_nonzero(out,A3DMIX_BLOCK)>0);assert(v->played_frames==A3DMIX_BLOCK);assert(v->cursor==A3DMIX_BLOCK);
 a3dmix_render(m,out,A3DMIX_BLOCK);assert(v->cursor==512.0);
 a3dmix_render(m,out,A3DMIX_BLOCK);assert(v->cursor==256.0);assert(v->active);
 v->active=0;w->pcm=pcm;w->bytes=sizeof(pcm);w->channels=1;w->bits=16;w->rate=24000;w->pos[0]=-4;w->pos[2]=-2;w->active=1;
 assert(a3dmix_add(m,w));a3dmix_render(m,out,A3DMIX_BLOCK);assert(w->cursor==128.0);
 a3dmix_render(m,out,A3DMIX_BLOCK);assert(w->cursor==256.0);
 a3dmix_remove(m,w);a3dmix_remove(m,v);assert(m->v[0]==NULL&&m->v[1]==NULL);
 unsigned before=m->frames_rendered;for(int i=0;i<6;i++)a3dmix_render(m,out,A3DMIX_BLOCK);assert(m->frames_rendered==before+6*A3DMIX_BLOCK);
 /* Test finite/strongly bounded late reverb; static voices are gone. */
 assert(m->clip_events<100);
 /* Test empty mixer gives complete silence with wet 0 and zeroed feedback. */
 a3dmix_init(m);m->reverb_wet=0;a3dmix_render(m,out,A3DMIX_BLOCK);assert(!count_nonzero(out,A3DMIX_BLOCK));
 /* Bad lengths do not overrun. */
 unsigned char guard[]={1,2,3,4};a3dmix_render(m,guard,A3DMIX_BLOCK+1);assert(guard[0]==1&&guard[3]==4);
 printf("stream_core PASS: voices, loops, sample rates, reverb, bounds\n");
 free(v);free(w);free(m);return 0;
}
