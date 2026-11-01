/* v0.5.0 SOURCE COMMENTARY — Regression test / harness
 * Exercises the release implementation or checks its ABI/packaging contract. Do not
 * treat fixture success as proof of native Wine or retail-game compatibility.
 */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "../win32/stream_core.h"
int main(void){
 A3DScene*s=calloc(1,sizeof(*s));A3DFrame*f=calloc(1,sizeof(*f));A3DMix*m=calloc(1,sizeof(*m));
 assert(s&&f&&m);a3d_scene_init(s);a3dmix_init(m);
 s->record_target=f;
 a3d_scene_begin(s,3);a3d_scene_vertex(s,0,-2,-2);a3d_scene_vertex(s,0,2,-2);a3d_scene_vertex(s,0,0,2);
 assert(f->count==1&&s->staged.count==0);
 s->record_target=0;
 s->staged.tris[s->staged.count++]=f->tris[0];a3d_scene_flush(s);
 s->global_flags=A3D_SCENE_OCCLUSIONS|A3D_SCENE_REFLECTIONS;
 A3DPaths p;a3d_trace(s,a3d_v3(-3,0,0),a3d_v3(3,0,0),&p);
 assert(p.intersections==1);
 /* Geometric occlusion must actually attenuate the running stream. */
 unsigned char pcm[256*2];for(unsigned i=0;i<256;i++){pcm[2*i]=0;pcm[2*i+1]=32;}
 A3DMixVoice*v=calloc(1,sizeof(*v));assert(v);
 a3dmix_voice_init(v);v->pcm=pcm;v->bytes=sizeof(pcm);v->rate=48000;v->channels=1;v->bits=16;v->active=1;v->pos[0]=-3;
 m->listener[0]=3;m->scene=s;assert(a3dmix_add(m,v));
 unsigned char out[A3DMIX_BLOCK*4];a3dmix_render(m,out,A3DMIX_BLOCK);
 /* Scene removed, repeat exactly same sample from beginning with new voice */
 a3dmix_remove(m,v);a3dmix_voice_init(v);v->pcm=pcm;v->bytes=sizeof(pcm);v->rate=48000;v->channels=1;v->bits=16;v->active=1;v->pos[0]=-3;
 s->committed.count=0;a3dmix_init(m);m->listener[0]=3;m->scene=s;assert(a3dmix_add(m,v));
 unsigned char clear[A3DMIX_BLOCK*4];a3dmix_render(m,clear,A3DMIX_BLOCK);
 long long eno=0,eoc=0;
 for(unsigned i=0;i<sizeof(out);i++){eno+=(unsigned long long)clear[i]*clear[i];eoc+=(unsigned long long)out[i]*out[i];}
 assert(eno>eoc);printf("scene/core PASS: list capture and dynamic wall occlusion\n");
 free(v);free(s);free(f);free(m);return 0;
}
