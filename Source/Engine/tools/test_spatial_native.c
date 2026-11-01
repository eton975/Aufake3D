/* v0.5.0 SOURCE COMMENTARY — Regression test / harness
 * Exercises the release implementation or checks its ABI/packaging contract. Do not
 * treat fixture success as proof of native Wine or retail-game compatibility.
 */
/* Run on the host so tests exercise the SAME math compiled into the DLL. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "../win32/spatial_stereo.h"
static void test_pair(const float *left, const float *right, const float *front,
                      const float *up, unsigned long cs){
 const float origin[3]={0,0,0};
 A3DStereoGains a=a3d_stereo_gains(left,origin,front,up,cs,1.0f);
 A3DStereoGains b=a3d_stereo_gains(right,origin,front,up,cs,1.0f);
 assert(a.pan< -0.5f && b.pan>0.5f);
 assert(a.left>a.right*2.0f && b.right>b.left*2.0f);
 /* Check signed PCM bytes at exact waveOut interleaving offsets [L][R]. */
 int16_t al=(int16_t)(10000.0f*a.left),ar=(int16_t)(10000.0f*a.right);
 int16_t bl=(int16_t)(10000.0f*b.left),br=(int16_t)(10000.0f*b.right);
 unsigned char frame_a[4]={(unsigned char)al,(unsigned char)((uint16_t)al>>8),
                            (unsigned char)ar,(unsigned char)((uint16_t)ar>>8)};
 unsigned char frame_b[4]={(unsigned char)bl,(unsigned char)((uint16_t)bl>>8),
                            (unsigned char)br,(unsigned char)((uint16_t)br>>8)};
 int16_t la=(int16_t)((unsigned)frame_a[0]|((unsigned)frame_a[1]<<8));
 int16_t ra=(int16_t)((unsigned)frame_a[2]|((unsigned)frame_a[3]<<8));
 int16_t lb=(int16_t)((unsigned)frame_b[0]|((unsigned)frame_b[1]<<8));
 int16_t rb=(int16_t)((unsigned)frame_b[2]|((unsigned)frame_b[3]<<8));
 assert(la>ra && rb>lb);
}
int main(void){
 const float up[3]={0,1,0};
 const float rh_front[3]={0,0,-1};
 const float lh_front[3]={0,0,1};
 const float left[3]={-5,0,-2},right[3]={5,0,-2};
 test_pair(left,right,rh_front,up,A3D_RIGHT_HANDED_CS);
 /* Left-handed conversion: when facing +Z, +X remains to the right. */
 const float lh_left[3]={-5,0,2},lh_right[3]={5,0,2};
 test_pair(lh_left,lh_right,lh_front,up,A3D_LEFT_HANDED_CS);
 /* Listener rotated to face +X: in RH, +Z is to the listener's right. */
 const float toward_x[3]={1,0,0};
 const float rot_left[3]={2,0,-5},rot_right[3]={2,0,5};
 test_pair(rot_left,rot_right,toward_x,up,A3D_RIGHT_HANDED_CS);
 /* Centre stays balanced. */
 const float origin[3]={0,0,0}, center[3]={0,0,-5};
 A3DStereoGains c=a3d_stereo_gains(center,origin,rh_front,up,0,1.0f);
 assert(c.pan==0.0f && c.left==c.right);
 puts("PASS: RH, LH, rotated camera, centre and PCM L/R byte ordering");
 return 0;
}
