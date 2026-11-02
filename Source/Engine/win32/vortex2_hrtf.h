/* Aufake3D 0.9.0: AU8830-derived 56-tap binaural reference path.
 * Table provenance: user-supplied corrected register trace, see data/.
 *
 * FAST computes a bilinear 56-tap target once per 256-frame voice block,
 * then performs exactly 112 FIR MACs per sample plus two fractional delays.
 * REFERENCE uses the same FIR with the measured 64-sample coefficient and
 * ITD glides. Neither mode claims bit-exact AU8830 integer DSP arithmetic.
 * No heap, I/O, CRT math calls, trigonometry or interpolation in the
 * sample-inner convolution loop. The rendering worker owns voice state.
 */
#ifndef AUFAKE_VORTEX2_HRTF_H
#define AUFAKE_VORTEX2_HRTF_H
#include "vortex2_hrtf_table.h"
#define AUFAKE_V2_DELAY_SIZE 64u
#define AUFAKE_V2_PI 3.14159265358979323846f
#define AUFAKE_V2_RAD2DEG (180.0f/AUFAKE_V2_PI)

static float aufake_v2_abs(float x){return x<0.0f?-x:x;}
/* Fast atan2 approximation max error roughly 0.01 degrees; NOT a hardware
 * angle quantizer. Hardware-exact conversion is a future validation item. */
static float aufake_v2_atan2(float y,float x){
 const float quarter=0.7853981633974483f,threequarter=2.356194490192345f;
 float ay=aufake_v2_abs(y)+1.0e-12f,r,a;
 if(x>=0.0f){r=(x-ay)/(x+ay);a=quarter+(0.1963f*r*r-0.9817f)*r;}
 else {r=(x+ay)/(ay-x);a=threequarter+(0.1963f*r*r-0.9817f)*r;}
 return y<0.0f?-a:a;
}
static void aufake_v2_orientation(const float src[3],const float lis[3],
 const float fwd[3],const float up[3],unsigned long coords,float *az,float *el){
 float rx=fwd[1]*up[2]-fwd[2]*up[1];
 float ry=fwd[2]*up[0]-fwd[0]*up[2];
 float rz=fwd[0]*up[1]-fwd[1]*up[0];
 if(coords==A3D_LEFT_HANDED_CS){rx=-rx;ry=-ry;rz=-rz;}
 float x=src[0]-lis[0],y=src[1]-lis[1],z=src[2]-lis[2];
 float front=x*fwd[0]+y*fwd[1]+z*fwd[2];
 float right=x*rx+y*ry+z*rz;
 float high=x*up[0]+y*up[1]+z*up[2];
 *az=aufake_v2_atan2(right,front)*AUFAKE_V2_RAD2DEG;
 if(*az<0.0f)*az+=360.0f;
 if(*az>=360.0f)*az-=360.0f;
 *el=aufake_v2_atan2(high,a3d_sqrt(front*front+right*right))*AUFAKE_V2_RAD2DEG;
 if(*el< -45.0f)*el= -45.0f;
 if(*el> 90.0f)*el=90.0f;
}
/* Bilinear driver-like angle interpolation. 24 columns wrap at 360deg,
 * a single top pole at 90deg, elevations below -45 clamp (not extrapolate).
 * ITD is linearly interpolated in units of 1/512 output sample. */
static void aufake_v2_lookup(float az,float el,float coeff[2][56],float itd[2]){
 unsigned a=(unsigned)(az/15.0f);if(a>23u)a=23u;
 unsigned b=(a+1u)%24u;
 float wa=(az-15.0f*(float)a)/15.0f;
 if(wa<0.0f)wa=0.0f;if(wa>1.0f)wa=1.0f;
 unsigned e=(unsigned)((el+45.0f)/15.0f);if(e>8u)e=8u;
 float we=(el+45.0f-15.0f*(float)e)/15.0f;
 if(we<0.0f)we=0.0f;if(we>1.0f)we=1.0f;
 unsigned n0=e*24u+a,n1=e*24u+b;
 unsigned n2=e<8u?n0+24u:216u;
 unsigned n3=e<8u?n1+24u:216u;
 if(e==8u&&el>=90.0f){we=1.0f;}
 float w0=(1.0f-we)*(1.0f-wa),w1=(1.0f-we)*wa;
 float w2=we*(1.0f-wa),w3=we*wa;
 for(unsigned ear=0;ear<2u;ear++){
  for(unsigned k=0;k<56u;k++){
   coeff[ear][k]=w0*(float)aufake_v2_coeff[n0][ear][k]
       +w1*(float)aufake_v2_coeff[n1][ear][k]
       +w2*(float)aufake_v2_coeff[n2][ear][k]
       +w3*(float)aufake_v2_coeff[n3][ear][k];
  }
  itd[ear]=(w0*(float)aufake_v2_itd[n0][ear]
           +w1*(float)aufake_v2_itd[n1][ear]
           +w2*(float)aufake_v2_itd[n2][ear]
           +w3*(float)aufake_v2_itd[n3][ear])/512.0f;
 }
}
/* 64-slot circular fractional delay; the Vortex register word gives a 9-bit
 * fractional sample count. Linear interpolation is a practical approximation
 * until original chip interpolation/rounding can be validated. */
static float aufake_v2_delay(float line[64],unsigned cursor,float delay,float x){
 if(delay<0.0f)delay=0.0f;
 if(delay>40.0f)delay=40.0f;
 line[cursor]=x;
 unsigned whole=(unsigned)delay;
 float fract=delay-(float)whole;
 unsigned at=(cursor+64u-whole)&63u;
 return line[at]*(1.0f-fract)+line[(at+63u)&63u]*fract;
}
#endif
