/* v0.5.0 SOURCE COMMENTARY — Stereo/spatial mathematics
 * Contains lightweight direction and channel-gain primitives reused by the mixer.
 * Coordinate transforms, orientation normalization and clipping are audible correctness
 * concerns.
 */
/* Aureal-compatible positional STAGING math, no binaural HRTF yet.
 * A3D 2.x/3.x uses right-handed coordinates by default: X right, Y up,
 * Z toward viewer. Listener looking into scene therefore faces negative Z.
 * IA3d4::SetCoordinateSystem may explicitly request left-handed (1).
 * This helper is freestanding C and compiled in both the 32-bit DLL and
 * native regression tests to protect actual output L/R ordering.
 */
#ifndef A3D_SPATIAL_STEREO_H
#define A3D_SPATIAL_STEREO_H
#define A3D_RIGHT_HANDED_CS 0UL
#define A3D_LEFT_HANDED_CS 1UL
typedef struct {float left, right, pan;} A3DStereoGains;
static float a3d_absf(float x){return x<0.0f?-x:x;}
static A3DStereoGains a3d_stereo_gains(const float src[3],
                                      const float lis[3],
                                      const float forward[3],
                                      const float up[3],
                                      unsigned long coord_system,
                                      float source_gain){
 /* In an RH frame listener-right = forward CROSS up.
    In an LH frame listener-right = up CROSS forward.
    Up x forward was incorrect for the previous RH default and inverted the
    pan when Miles configured the listener facing -Z. */
 float rx=forward[1]*up[2]-forward[2]*up[1];
 float ry=forward[2]*up[0]-forward[0]*up[2];
 float rz=forward[0]*up[1]-forward[1]*up[0];
 if(coord_system==A3D_LEFT_HANDED_CS){rx=-rx;ry=-ry;rz=-rz;}
 float rn=a3d_absf(rx)+a3d_absf(ry)+a3d_absf(rz);
 /* Degenerate orientation should not unexpectedly flip the sound stage. */
 if(rn<0.000001f){rx=1.0f;ry=0.0f;rz=0.0f;rn=1.0f;}
 rx/=rn;ry/=rn;rz/=rn;
 float dx=src[0]-lis[0],dy=src[1]-lis[1],dz=src[2]-lis[2];
 float denom=a3d_absf(dx)+a3d_absf(dy)+a3d_absf(dz)+0.01f;
 float pan=(dx*rx+dy*ry+dz*rz)/denom;
 if(pan>1.0f)pan=1.0f;else if(pan< -1.0f)pan=-1.0f;
 /* Kept identical to v0.2.6 loudness policy; only side assignment changes. */
 float amplitude=source_gain*0.50f/(1.0f+denom*0.1f);
 if(amplitude>0.50f)amplitude=0.50f;
 if(amplitude<0.0f)amplitude=0.0f;
 A3DStereoGains out;
 out.left=amplitude*(1.0f-(pan>0.0f?pan*0.80f:0.0f));
 out.right=amplitude*(1.0f+(pan<0.0f?pan*0.80f:0.0f));
 out.pan=pan;
 return out;
}
#endif
