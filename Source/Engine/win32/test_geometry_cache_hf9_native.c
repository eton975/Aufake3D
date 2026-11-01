/* HF9 regression: geometry scene updates must not force expensive acoustic
 * retracing every 256-frame block. HRTF and source playback continue.
 * Test both legacy behaviour and geometry bypass without Wine. */
#include <stdio.h>
#include "stream_core.h"
static A3DMix m;
static A3DMixVoice v;
static A3DScene scene;
static unsigned char pcm[1024];
static unsigned char output[A3DMIX_BLOCK*4];
static int fail(const char*name){fprintf(stderr,"FAIL %s\n",name);return 1;}
static void setup(unsigned enabled,unsigned interval){
 a3dmix_init(&m);a3dmix_voice_init(&v);a3d_scene_init(&scene);
 scene.global_flags=A3D_SCENE_OCCLUSIONS|A3D_SCENE_REFLECTIONS;
 scene.mode=scene.global_flags;
 m.scene=&scene;m.reverb_wet=0;m.master_boost=0.1f;
 m.geometry_enabled=enabled;m.geometry_retrace_blocks=interval;
 v.pcm=pcm;v.bytes=sizeof(pcm);v.rate=48000u;v.channels=1u;
 v.bits=16u;v.active=1u;v.looping=1u;v.pos[2]=-2.0f;
 a3dmix_add(&m,&v);
}
static void blocks(unsigned n){
 for(unsigned i=0;i<n;i++){
  scene.revision++; /* game Flush may occur once or more per block */
  a3dmix_render(&m,output,A3DMIX_BLOCK);
 }
}
int main(void){
 setup(1u,8u);blocks(24u);
 if(m.geometry_trace_calls!=3u)return fail("adaptive trace count");
 if(m.geometry_deferred_revisions==0u||m.geometry_cache_hits==0u)
  return fail("geometry cache never hit");
 if(m.frames_rendered!=24u*A3DMIX_BLOCK)return fail("audio rendering changed");
 printf("HF9 adaptive: traces %u, cache hits %u, deferred revisions %u\n",
   m.geometry_trace_calls,m.geometry_cache_hits,m.geometry_deferred_revisions);
 setup(1u,0u);blocks(24u);
 if(m.geometry_trace_calls!=24u)return fail("legacy mode not preserved");
 setup(0u,8u);blocks(24u);
 if(m.geometry_trace_calls||m.geometry_disabled_voice_blocks!=24u)
  return fail("disabled geometry should not trace");
 setup(1u,8u);blocks(2u);
 v.pos[0]=2.0f;blocks(1u);
 if(m.geometry_trace_calls!=2u)return fail("source movement did not invalidate cache");
 puts("PASS: HF9 adaptive, legacy, bypass and movement invalidation");
 return 0;
}
