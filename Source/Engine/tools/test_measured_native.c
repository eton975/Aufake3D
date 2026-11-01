/* v0.5.0 SOURCE COMMENTARY — Regression test / harness
 * Exercises the release implementation or checks its ABI/packaging contract. Do not
 * treat fixture success as proof of native Wine or retail-game compatibility.
 */
/* Host-native test of actual MIT KEMAR impulse-response spatializer. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "../win32/measured_hrtf.h"
#define N 512
static int s16(const unsigned char *s,int n,int ear){unsigned k=(unsigned)(4*n+ear*2);unsigned raw=(unsigned)s[k]|((unsigned)s[k+1]<<8);return (int16_t)raw;}
static int maxi(const unsigned char *s,int ear){int max=0;for(int i=0;i<N;i++){int x=s16(s,i,ear);if(x<0)x=-x;if(x>max)max=x;}return max;}
static unsigned long long energy(const unsigned char *s,int ear){unsigned long long x=0;for(int i=0;i<N;i++){int a=s16(s,i,ear);x+=(long long)a*a;}return x;}
int main(void){
 const float lis[3]={0,0,0},fwd[3]={0,0,-1},up[3]={0,1,0};
 const float front[3]={0,0,-6},back[3]={0,0,6},hi[3]={0,6,0},left[3]={-6,0,0},right[3]={6,0,0};
 A3DMeasuredPick f=a3d_measured_pick(front,lis,fwd,up,0,1,22050);
 A3DMeasuredPick b=a3d_measured_pick(back,lis,fwd,up,0,1,22050);
 A3DMeasuredPick h=a3d_measured_pick(hi,lis,fwd,up,0,1,22050);
 A3DMeasuredPick l=a3d_measured_pick(left,lis,fwd,up,0,1,22050);
 A3DMeasuredPick r=a3d_measured_pick(right,lis,fwd,up,0,1,22050);
 assert(f.direction!=b.direction&&f.direction!=h.direction&&b.direction!=h.direction);
 assert(l.direction!=r.direction);assert(f.taps==160);
 unsigned char pcm[N*2]={0},lo[N*4]={0},ro[N*4]={0},fo[N*4]={0},bo[N*4]={0},ho[N*4]={0};
 pcm[0]=0x10;pcm[1]=0x27;
 assert(a3d_measured_render(lo,pcm,N,1,16,&l));
 assert(a3d_measured_render(ro,pcm,N,1,16,&r));
 assert(a3d_measured_render(fo,pcm,N,1,16,&f));
 assert(a3d_measured_render(bo,pcm,N,1,16,&b));
 assert(a3d_measured_render(ho,pcm,N,1,16,&h));
 assert(energy(lo,0)>energy(lo,1)*2); assert(energy(ro,1)>energy(ro,0)*2);
 assert(maxi(lo,0)>maxi(lo,1));assert(maxi(ro,1)>maxi(ro,0));
 assert(memcmp(fo,bo,sizeof(fo))!=0 && memcmp(fo,ho,sizeof(fo))!=0);
 for(unsigned i=0;i<N;i++)pcm[2*i]=(unsigned char)i;
 A3DMeasuredPick k44=a3d_measured_pick(front,lis,fwd,up,0,1,44100);
 A3DMeasuredPick k48=a3d_measured_pick(front,lis,fwd,up,0,1,48000);
 assert(k44.taps==320&&k48.taps==348);
 assert(a3d_measured_render(fo,pcm,N,1,16,&k44));
 assert(a3d_measured_render(fo,pcm,N,1,16,&k48));
 A3DMeasuredPick wrong=a3d_measured_pick(front,lis,fwd,up,0,1,32000);
 assert(wrong.taps==0); assert(!a3d_measured_render(fo,pcm,N,1,16,&wrong));
 A3DBinaural fallback=a3d_binaural_config(front,lis,fwd,up,0,1,32000);
 assert(a3d_binaural_render(fo,pcm,N,1,16,&fallback));
 printf("PASS measured MIT KEMAR: directions (front/back/up), binaural L/R, distinct IRs, 22050/44100/48000, unsupported-rate fallback\n");
 return 0;
}
