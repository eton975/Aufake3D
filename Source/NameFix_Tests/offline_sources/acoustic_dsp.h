/* v0.5.0 SOURCE COMMENTARY — Acoustic DSP helpers
 * Lightweight functions for environmental reflection and reverb approximations. Not
 * equivalent to the original Aureal hardware convolution or complete A3D 2.0
 * Wavetracing feature set.
 */
/* Geometry-conditioned effects for v0.3.0 prototype. This is early-reflection
 * and occlusion DSP, NOT a full room reverb, diffraction or native A3D engine.
 * Output: stereo 16-bit little-endian, in place, initially contains HRTF direct
 * path for source_frames, followed by zeroed tail frames.
 */
#ifndef A3D_ACOUSTIC_DSP_H
#define A3D_ACOUSTIC_DSP_H
#include "acoustic_scene.h"
#include "binaural_approx.h"
static int a3d_s16_read(const unsigned char*p){unsigned v=(unsigned)p[0]|((unsigned)p[1]<<8);return v>=32768u?(int)v-65536:(int)v;}
static void a3d_s16_write(unsigned char*p,float v){unsigned short s=(unsigned short)a3d_binaural_as16(v);p[0]=(unsigned char)s;p[1]=(unsigned char)(s>>8);}
static unsigned a3d_early_tail(const A3DPaths*paths,unsigned rate,float delay_scale){
 unsigned max=0;for(unsigned j=0;j<paths->n_early;j++){
  float d=paths->early[j].delay_sec*delay_scale;
  if(d<0)d=0;if(d>0.4f)d=0.4f;
  unsigned n=(unsigned)(d*(float)rate+0.5f)+1u;if(n>max)max=n;
 }return max;
}
static void a3d_apply_scene_dsp(unsigned char*stereo,unsigned output_frames,
 const unsigned char*pcm,unsigned source_frames,unsigned channels,unsigned bits,
 unsigned rate,const A3DPaths*paths,float ref_gain,float delay_scale,
 const float listener_pos[3],const float forward[3],const float up[3],unsigned coords){
 if(!stereo||!paths||!pcm||source_frames>output_frames)return;
 /* Direct path: preserve low frequencies while damping high frequencies
  * for a sound occluded by one or more polygon materials. */
 if(paths->intersections){
  float lo=a3d_clampf(paths->direct_low,0,1),hi=a3d_clampf(paths->direct_high,0,1);
  for(unsigned ch=0;ch<2;ch++){
   float smooth=0;
   for(unsigned i=0;i<source_frames;i++){
    unsigned off=4*i+2*ch;
    float v=(float)a3d_s16_read(stereo+off);
    smooth=0.75f*smooth+0.25f*v;
    a3d_s16_write(stereo+off,hi*v+(lo-hi)*smooth);
   }
  }
 }
 ref_gain=a3d_clampf(ref_gain,0.0f,2.0f);
 delay_scale=a3d_clampf(delay_scale,0.0f,4.0f);
 for(unsigned j=0;j<paths->n_early;j++){
  A3DEarly r=paths->early[j];
  float seconds=a3d_clampf(r.delay_sec*delay_scale,0,0.4f);
  unsigned delay=(unsigned)(seconds*(float)rate+0.5f);
  float bounce[3]={r.point.x,r.point.y,r.point.z};
  A3DStereoGains g=a3d_stereo_gains(bounce,listener_pos,forward,up,coords,1.0f);
  float sum=g.left+g.right+0.00001f;
  float left=ref_gain*r.gain*2.0f*g.left/sum;
  float right=ref_gain*r.gain*2.0f*g.right/sum;
  for(unsigned i=0;i<source_frames;i++){
   unsigned oi=i+delay;if(oi>=output_frames)break;
   float v=a3d_pcm_mono_at(pcm,source_frames,channels,bits,(int)i);
   float vl=(float)a3d_s16_read(stereo+4*oi)+v*left;
   float vr=(float)a3d_s16_read(stereo+4*oi+2)+v*right;
   a3d_s16_write(stereo+4*oi,vl);a3d_s16_write(stereo+4*oi+2,vr);
  }
 }
}
#endif
