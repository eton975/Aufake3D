/* v0.5.0 SOURCE COMMENTARY — Approximate binaural/HRTF helpers
 * Provides supporting stereo spatialisation calculations. Avoid confusing generic
 * binaural cues with a measured or hardware-accurate A3D renderer.
 */
/* Experimental analytical binaural cue renderer (v0.2.8).
 * This is deliberately NOT Aureal's measured HRTF, Wavetracing, SOFA,
 * partitioned convolution, or a production real-time mixer.
 *
 * Uses actual independent per-ear sample delays (ITD), direction-dependent
 * spectral head shadow (ILD), and weak rear/elevation spectral coloration.
 * All DSP uses the exact freestanding C source shared by Win32 and native tests.
 * Expected input: PCM 8/16-bit, mono/stereo, interleaved; output 16-bit stereo.
 * Caller must separately verify input/output lengths and own all buffers.
 */
#ifndef A3D_BINAURAL_APPROX_H
#define A3D_BINAURAL_APPROX_H
#include "spatial_stereo.h"
typedef struct {
 float lg, rg, pan, low_l, low_r, rear, elevation;
 unsigned delay_l, delay_r;
} A3DBinaural;
static float a3d_clamp01(float x){return x<0.0f?0.0f:(x>1.0f?1.0f:x);}
static A3DBinaural a3d_binaural_config(const float src[3],const float lis[3],
 const float forward[3],const float up[3],unsigned long coords,
 float source_gain,unsigned rate){
 A3DStereoGains g=a3d_stereo_gains(src,lis,forward,up,coords,source_gain);
 float dx=src[0]-lis[0],dy=src[1]-lis[1],dz=src[2]-lis[2];
 float d=a3d_absf(dx)+a3d_absf(dy)+a3d_absf(dz)+0.001f;
 float fb=(dx*forward[0]+dy*forward[1]+dz*forward[2])/d;
 float ud=(dx*up[0]+dy*up[1]+dz*up[2])/d;
 float abs_pan=a3d_absf(g.pan);
 unsigned delay=(unsigned)(a3d_clamp01(abs_pan)*0.00065f*(float)rate+0.5f);
 /* Hard limit in case caller supplies a hostile/invalid sample rate. */
 if(delay>96u)delay=96u;
 A3DBinaural c;
 c.lg=g.left;c.rg=g.right;c.pan=g.pan;
 c.delay_l=g.pan>0.0f?delay:0u;
 c.delay_r=g.pan<0.0f?delay:0u;
 c.low_l=g.pan>0.0f?0.90f*abs_pan:0.0f;
 c.low_r=g.pan<0.0f?0.90f*abs_pan:0.0f;
 c.rear=a3d_clamp01(-fb)*0.70f;
 c.elevation=a3d_clamp01(ud)*0.60f;
 return c;
}
static float a3d_pcm_mono_at(const unsigned char *input,unsigned frames,
 unsigned channels,unsigned bits,int frame){
 if(frame<0||(unsigned)frame>=frames)return 0.0f;
 unsigned bytes=bits/8u;
 unsigned at=(unsigned)frame*channels*bytes;
 float sum=0.0f;
 for(unsigned c=0;c<channels;c++){
  unsigned off=at+c*bytes;
  int sample;
  if(bits==8)sample=((int)input[off]-128)*256;
  else {unsigned raw=(unsigned)input[off]|((unsigned)input[off+1]<<8);
        sample=raw>=32768u?(int)raw-65536:(int)raw;}
  sum+=(float)sample;
 }
 return sum/(float)channels;
}
static short a3d_binaural_as16(float x){
 if(x>32767.0f)return 32767;
 if(x< -32768.0f)return -32768;
 return (short)x;
}
static float a3d_ear_filtered(const unsigned char *pcm,unsigned frames,
 unsigned channels,unsigned bits,int index,float low,float rear,float elevation){
 float x0=a3d_pcm_mono_at(pcm,frames,channels,bits,index);
 float x1=a3d_pcm_mono_at(pcm,frames,channels,bits,index-1);
 float x2=a3d_pcm_mono_at(pcm,frames,channels,bits,index-2);
 float x3=a3d_pcm_mono_at(pcm,frames,channels,bits,index-3);
 float x4=a3d_pcm_mono_at(pcm,frames,channels,bits,index-4);
 float head=(0.25f*x0+0.50f*x1+0.25f*x2);
 float v=(1.0f-low)*x0+low*head;
 /* Back-of-head cue (weak spectral damping); NOT a measured pinna HRTF. */
 float rear_filtered=0.125f*x0+0.25f*x1+0.25f*x2+0.25f*x3+0.125f*x4;
 v=(1.0f-rear)*v+rear*rear_filtered;
 /* Synthetic spectral notch for elevation: modest temporal-comb coloration. */
 float raised=0.85f*v-0.15f*x3;
 return (1.0f-elevation)*v+elevation*raised;
}
static int a3d_binaural_render(unsigned char *out,const unsigned char *pcm,
 unsigned frames,unsigned channels,unsigned bits,const A3DBinaural *c){
 if(!out||!pcm||!c||!frames||(channels!=1&&channels!=2)||(bits!=8&&bits!=16))return 0;
 for(unsigned i=0;i<frames;i++){
  int at=(int)i;
  float l=a3d_ear_filtered(pcm,frames,channels,bits,at-(int)c->delay_l,
      c->low_l,c->rear,c->elevation)*c->lg;
  float r=a3d_ear_filtered(pcm,frames,channels,bits,at-(int)c->delay_r,
      c->low_r,c->rear,c->elevation)*c->rg;
  unsigned short ls=(unsigned short)a3d_binaural_as16(l);
  unsigned short rs=(unsigned short)a3d_binaural_as16(r);
  out[4*i]=(unsigned char)ls;out[4*i+1]=(unsigned char)(ls>>8);
  out[4*i+2]=(unsigned char)rs;out[4*i+3]=(unsigned char)(rs>>8);
 }
 return 1;
}
#endif
