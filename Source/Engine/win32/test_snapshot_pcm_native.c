/* Standalone Linux/offline test: bounded PCM snapshot and full-buffer render
 * must give byte-identical output for looped/non-looped/stereo/mono inputs. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "stream_core.h"
#define CAP (A3DMIX_BLOCK*8u+2u)
static A3DMix m1,m2;
static A3DScene scene;
static A3DMixVoice a,b;
static unsigned char data[22003*4],window[CAP*4],out1[1024],out2[1024];
static int run(unsigned frames,unsigned channels,unsigned bits,int looping,double start,float pitch){
 unsigned stride=channels*(bits/8u);
 unsigned size=frames*stride;
 for(unsigned n=0;n<size;n++)data[n]=(unsigned char)((n*61u+(n>>3))&255u);
 a3dmix_init(&m1);a3dmix_init(&m2);
 a3d_scene_init(&scene);
 scene.global_flags=A3D_SCENE_OCCLUSIONS|A3D_SCENE_REFLECTIONS;
 a3d_scene_begin(&scene,A3D_SCENE_TRIANGLES);
 a3d_scene_vertex(&scene,-8,-8,-2);
 a3d_scene_vertex(&scene,8,-8,-2);
 a3d_scene_vertex(&scene,0,8,-2);
 a3d_scene_flush(&scene);
 m1.scene=&scene;m2.scene=&scene;
 a3dmix_voice_init(&a);a3dmix_voice_init(&b);
 a.pcm=data;a.bytes=size;a.channels=channels;a.rate=48000;a.bits=bits;
 a.pitch=pitch;a.gain=0.8f;a.cursor=start;a.looping=looping;a.active=1;
 a.pos[0]=2.1f;a.pos[2]=-4.0f;
 a3dmix_add(&m1,&a);
 b=a;
 unsigned base=(unsigned)start%frames;
 for(unsigned n=0;n<CAP;n++){
  unsigned frame=(base+n)%frames;
  for(unsigned k=0;k<stride;k++)window[n*stride+k]=data[frame*stride+k];
 }
 b.pcm=window;b.pcm_window=window;b.pcm_window_start=base;
 b.pcm_window_frames=CAP;
 a3dmix_add(&m2,&b);
 a3dmix_render(&m1,out1,256);
 a3dmix_render(&m2,out2,256);
 int diff=memcmp(out1,out2,sizeof(out1)) || a.active!=b.active || a.cursor!=b.cursor;
 if(diff)fprintf(stderr,"FAIL total=%u channels=%u bits=%u loop=%d cursor=%.3f pitch=%f\n",frames,channels,bits,looping,start,pitch);
 return diff;
}
int main(void){
 unsigned fail=0,cases=0;
 for(unsigned ch=1;ch<=2;ch++)for(unsigned bits=8;bits<=16;bits+=8)
 for(unsigned n=0;n<2;n++){
  unsigned frames=n?22003u:48u;
  for(unsigned l=0;l<2;l++)for(unsigned p=0;p<4;p++){
   float pitch[]={0.1f,1.0f,4.5f,8.0f};
   double starts[]={0.0,31.25,22002.0};
   for(unsigned x=0;x<3;x++){
    double st=starts[x];if(st>=frames)st=(double)frames-1.0;
    fail+=run(frames,ch,bits,(int)l,st,pitch[p]);cases++;
   }
  }
 }
 printf("snapshot PCM parity: %u cases, %u failures\n",cases,fail);
 return fail?1:0;
}
