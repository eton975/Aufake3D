/* v0.5.0 SOURCE COMMENTARY — Engineering/research utility
 * Supports repeatable data generation, audio tests, game-file analysis, or Wine
 * probing. Inspect command-line arguments and preserve user-owned game files.
 */
/* Offscreen throughput probe: no OS/Wine device; not a latency guarantee. */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "../win32/stream_core.h"
int main(void){
 A3DMix*m=calloc(1,sizeof(*m));if(!m)return 1;a3dmix_init(m);m->reverb_wet=0.14f;
 A3DMixVoice*v=calloc(A3DMIX_VOICES,sizeof(*v));if(!v)return 1;
 unsigned char *pcm=calloc(4096,1);if(!pcm)return 1;
 for(unsigned i=0;i<A3DMIX_VOICES;i++){
  a3dmix_voice_init(&v[i]);v[i].pcm=pcm;v[i].bytes=4096;v[i].channels=1;v[i].bits=16;v[i].rate=22050;v[i].pos[0]=(float)((int)i-12);v[i].pos[2]=-5.0f;v[i].active=1;v[i].looping=1;a3dmix_add(m,&v[i]);
 }
 unsigned char out[A3DMIX_BLOCK*4];clock_t start=clock();
 for(unsigned n=0;n<300;n++)a3dmix_render(m,out,A3DMIX_BLOCK);
 double sec=(double)(clock()-start)/(double)CLOCKS_PER_SEC;
 printf("24-source stream benchmark: 300 x 256 frames = 1.60 sec of audio, CPU %.3f sec, ratio %.3f\n",sec,sec/1.60);
 free(pcm);free(v);free(m);return 0;
}
