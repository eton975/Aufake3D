/* v0.5.0 SOURCE COMMENTARY — Measured head-related impulse response interface
 * Looks up measured KEMAR HRIR coefficients and provides bounded filtering for the
 * mixer. Correct spatial orientation and sample/channel conventions are essential for
 * localization; impulse responses are not a universal anatomical fit.
 */
/* First measured, generic, non-individualized HRTF spatial renderer.
 * MIT KEMAR, 1994. Not authentic Aureal HRTF. One-shot direct convolution.
 * Listening probe uses broadband noise to expose direction-dependent notches.
 */
#ifndef A3D_MEASURED_HRTF_H
#define A3D_MEASURED_HRTF_H
#include "binaural_approx.h"
#include "measured_hrir_data.h"
typedef struct { int direction; float amplitude; unsigned taps; unsigned rate; } A3DMeasuredPick;
static A3DMeasuredPick a3d_measured_pick(const float src[3],const float lis[3],
 const float fwd[3],const float up[3],unsigned long coords,float volume,unsigned rate){
 float rx=fwd[1]*up[2]-fwd[2]*up[1];
 float ry=fwd[2]*up[0]-fwd[0]*up[2];
 float rz=fwd[0]*up[1]-fwd[1]*up[0];
 if(coords==A3D_LEFT_HANDED_CS){rx=-rx;ry=-ry;rz=-rz;}
 float dx=src[0]-lis[0],dy=src[1]-lis[1],dz=src[2]-lis[2];
 float front=dx*fwd[0]+dy*fwd[1]+dz*fwd[2];
 float left=-(dx*rx+dy*ry+dz*rz);
 float high=dx*up[0]+dy*up[1]+dz*up[2];
 float best=-1.0e30f;int besti=0;
 for(int i=0;i<A3D_MEASURED_DIRECTIONS;i++){
  float dot=front*a3d_mdir[i][0]+left*a3d_mdir[i][1]+high*a3d_mdir[i][2];
  if(dot>best){best=dot;besti=i;}
 }
 float denom=a3d_absf(dx)+a3d_absf(dy)+a3d_absf(dz)+0.01f;
 float gain=volume*0.50f/(1.0f+denom*0.1f);
 if(gain>0.50f)gain=0.50f;if(gain<0.0f)gain=0.0f;
 A3DMeasuredPick p={besti,gain,0,rate};
 if(rate==22050u)p.taps=A3D_TAPS_22050;
 if(rate==44100u)p.taps=A3D_TAPS_44100;
 if(rate==48000u)p.taps=A3D_TAPS_48000;
 return p;
}
static int a3d_measured_render(unsigned char *out,const unsigned char *pcm,
 unsigned frames,unsigned channels,unsigned bits,const A3DMeasuredPick *p){
 if(!p||!p->taps||p->direction<0||p->direction>=A3D_MEASURED_DIRECTIONS
  ||!out||!pcm||!frames||(channels!=1&&channels!=2)||(bits!=8&&bits!=16))return 0;
 const signed short *hl=0,*hr=0;
 if(p->rate==22050u){hl=a3d_mhrir_22050[p->direction][0];hr=a3d_mhrir_22050[p->direction][1];}
 else if(p->rate==44100u){hl=a3d_mhrir_44100[p->direction][0];hr=a3d_mhrir_44100[p->direction][1];}
 else if(p->rate==48000u){hl=a3d_mhrir_48000[p->direction][0];hr=a3d_mhrir_48000[p->direction][1];}
 else return 0;
 for(unsigned i=0;i<frames;i++){
  float sl=0.0f,sr=0.0f;
  unsigned ks=i+1u<p->taps?i+1u:p->taps;
  for(unsigned k=0;k<ks;k++){
   float v=a3d_pcm_mono_at(pcm,frames,channels,bits,(int)(i-k));
   sl+=v*((float)hl[k]);sr+=v*((float)hr[k]);
  }
  unsigned short l=(unsigned short)a3d_binaural_as16(sl*p->amplitude/32768.0f);
  unsigned short r=(unsigned short)a3d_binaural_as16(sr*p->amplitude/32768.0f);
  out[4*i]=(unsigned char)l;out[4*i+1]=(unsigned char)(l>>8);
  out[4*i+2]=(unsigned char)r;out[4*i+3]=(unsigned char)(r>>8);
 }
 return 1;
}
#endif
