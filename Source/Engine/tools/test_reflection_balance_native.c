/* v0.5.0 SOURCE COMMENTARY — Regression test / harness
 * Exercises the release implementation or checks its ABI/packaging contract. Do not
 * treat fixture success as proof of native Wine or retail-game compatibility.
 */
/* Regression: source/master gain and distance affect early reflected sound. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "../win32/stream_core.h"
static unsigned long long energy(short gainx, int mute, float early_trim, unsigned *outpaths){
 A3DMix *m=calloc(1,sizeof(*m));A3DMixVoice *v=calloc(1,sizeof(*v));A3DScene*s=calloc(1,sizeof(*s));assert(m&&v&&s);
 a3dmix_init(m);a3dmix_voice_init(v);a3d_scene_init(s);
 s->global_flags=A3D_SCENE_REFLECTIONS;
 a3d_scene_begin(s,3);
 a3d_scene_vertex(s,0,-3,-3);a3d_scene_vertex(s,0,3,-3);a3d_scene_vertex(s,0,0,3);
 a3d_scene_flush(s);
 A3DPaths paths;a3d_trace(s,a3d_v3(2,0,-1),a3d_v3(2,0,1),&paths);
 *outpaths=paths.n_early;
 assert(paths.n_early>0);
 m->scene=s;m->listener[0]=2;m->listener[2]=1;
 m->reverb_wet=0;m->early_reflection_trim=early_trim;
 m->distance_enabled=mute?1:0;
 static unsigned char samples[2048];
 for(unsigned i=0;i<1024;i++){short sample=(short)((int)((i%31)*200)-3000);samples[2*i]=(unsigned char)sample;samples[2*i+1]=(unsigned char)(sample>>8);}
 v->pcm=samples;v->bytes=sizeof(samples);v->channels=1;v->bits=16;v->rate=48000;v->active=1;v->looping=1;
 v->gain=(float)gainx/1000.0f;
 v->pos[0]=2;v->pos[2]=-1;
 v->max_distance_behavior=mute?1:0;v->max_dist=1.5f;
 assert(a3dmix_add(m,v));
 unsigned long long e=0;
 for(int block=0;block<8;block++){
  unsigned char out[A3DMIX_BLOCK*4];a3dmix_render(m,out,A3DMIX_BLOCK);
  for(unsigned i=0;i<sizeof(out);i+=2){unsigned u=out[i]|out[i+1]<<8;int n=u>=32768?(int)u-65536:(int)u;e+=(unsigned long long)(n<0?-n:n);}
 }
 free(v);free(m);free(s);return e;
}
int main(void){unsigned p=0;
 unsigned long long silence=energy(0,0,1,&p),normal=energy(500,0,1,&p),louder=energy(1000,0,1,&p),muted=energy(500,1,1,&p),dry=energy(500,0,0,&p);
 assert(p>0 && silence==0 && muted==0 && normal>dry && louder>normal);
 printf("reflection balance PASS: paths=%u silence=%llu normal=%llu loud=%llu mute=%llu noearly=%llu\n",p,silence,normal,louder,muted,dry);return 0;
}
