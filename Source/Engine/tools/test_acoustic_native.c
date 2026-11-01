/* v0.5.0 SOURCE COMMENTARY — Regression test / harness
 * Exercises the release implementation or checks its ABI/packaging contract. Do not
 * treat fixture success as proof of native Wine or retail-game compatibility.
 */
/* Standalone geometry + DSP regression tests, no hardware or Wine necessary. */
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../win32/acoustic_scene.h"
#include "../win32/acoustic_dsp.h"
static int near(float a,float b){return fabsf(a-b)<0.002f;}
static A3DScene *scene(void){A3DScene*s=(A3DScene*)calloc(1,sizeof(A3DScene));assert(s);a3d_scene_init(s);return s;}
static void wall(A3DScene*s,float z,float r,float t){
 s->reflect[0]=s->reflect[1]=r;s->trans[0]=s->trans[1]=t;
 a3d_scene_begin(s,A3D_SCENE_QUADS);
 a3d_scene_vertex(s,-4,-4,z);a3d_scene_vertex(s,4,-4,z);
 a3d_scene_vertex(s,4,4,z);a3d_scene_vertex(s,-4,4,z);
 assert(s->staged.count==2);
}
static void test_geometry(void){
 A3DScene*s=scene();A3DPaths p;
 s->global_flags=A3D_SCENE_OCCLUSIONS|A3D_SCENE_REFLECTIONS;
 wall(s,0,0.8f,0.15f);a3d_scene_flush(s);
 assert(s->committed.count==2);
 a3d_trace(s,a3d_v3(0,0,-1),a3d_v3(0,0,1),&p);
 assert(p.intersections>0);assert(p.direct_low<0.2f);assert(p.direct_high<0.2f);
 assert(p.n_early==0);
 a3d_trace(s,a3d_v3(-1,0,-1),a3d_v3(1,0,-1),&p);
 assert(p.intersections==0);assert(p.n_early>0);
 assert(p.early[0].delay_sec>0.0f&&p.early[0].delay_sec<0.03f);
 assert(fabsf(p.early[0].point.z)<0.01f);
 /* Regression: clear must not affect the last committed frame until flush. */
 a3d_scene_clear(s);assert(s->committed.count==2);a3d_scene_flush(s);
 assert(s->committed.count==0);
 a3d_trace(s,a3d_v3(0,0,-1),a3d_v3(0,0,1),&p);
 assert(!p.intersections&&!p.n_early);
 free(s);
}
static void test_transforms(void){
 A3DScene*s=scene();float t[16];a3d_identity(t);t[12]=3;t[13]=4;t[14]=5;
 a3d_matmul(s->matrix[0],t);
 A3DV3 p=a3d_transform(s->matrix[0],a3d_v3(1,2,3));
 assert(near(p.x,4)&&near(p.y,6)&&near(p.z,8));
 a3d_scene_begin(s,A3D_SCENE_TRIANGLES);
 a3d_scene_vertex(s,0,0,0);a3d_scene_vertex(s,1,0,0);a3d_scene_vertex(s,0,1,0);
 assert(s->staged.count==1);assert(near(s->staged.tris[0].v[0].x,3));
 free(s);
}
static void test_audio(void){
 A3DScene*s=scene();s->global_flags=A3D_SCENE_OCCLUSIONS|A3D_SCENE_REFLECTIONS;
 wall(s,0,0.9f,0.1f);a3d_scene_flush(s);
 A3DPaths p;unsigned rate=22050;
 a3d_trace(s,a3d_v3(-1,0,-1),a3d_v3(1,0,-1),&p);
 assert(p.n_early);
 unsigned src_frames=4096,tail=a3d_early_tail(&p,rate,1.0f);
 assert(tail>1&&tail<rate/5);
 unsigned char *source=(unsigned char*)calloc(src_frames,2);
 unsigned char *out=(unsigned char*)calloc(src_frames+tail,4);
 assert(source&&out);
 source[0]=0xFF;source[1]=0x1F; /* one 8191 impulse */
 float lp[]={1,0,-1},fwd[]={0,0,-1},up[]={0,1,0};
 a3d_apply_scene_dsp(out,src_frames+tail,source,src_frames,1,16,rate,&p,1,1,lp,fwd,up,0);
 int nonzero=0;for(unsigned i=1;i<src_frames+tail;i++){
  if(a3d_s16_read(out+4*i)!=0 || a3d_s16_read(out+4*i+2)!=0)nonzero++;
 }
 assert(nonzero>0);/* Reflection must create a delayed, nonzero impulse. */
 free(out);free(source);
 /* Occlusion must attenuate the high-frequency / impulse direct path. */
 a3d_trace(s,a3d_v3(0,0,-1),a3d_v3(0,0,1),&p);
 unsigned char sample[]={0xff,0x7f,0xff,0x7f};
 unsigned char out2[]={0xff,0x7f,0xff,0x7f};
 a3d_apply_scene_dsp(out2,1,sample,1,1,16,rate,&p,1,1,lp,fwd,up,0);
 assert(abs(a3d_s16_read(out2))<32767);
 free(s);
}
int main(void){test_geometry();test_transforms();test_audio();puts("A3D acoustic geometry + DSP: 3 tests PASS");return 0;}
