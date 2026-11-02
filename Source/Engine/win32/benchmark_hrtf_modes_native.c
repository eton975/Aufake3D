/* Optional standalone offline performance benchmark (not a CI pass/fail metric).
 * cc -O2 -I Source/Engine/win32 Source/Engine/win32/benchmark_hrtf_modes_native.c -lm -o hrtfbench
 * Benchmarks direct DSP with identical sources, buffers and fixed listener.
 */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "stream_core.h"
#define BENCH_VOICES 32u
static unsigned bench_voices=8u;
#define BENCH_BLOCKS 200u
static A3DMix m;
static A3DMixVoice v[BENCH_VOICES];
static unsigned char pcm[8192],out[1024];
static void setup(unsigned mode){
 a3dmix_init(&m);m.hrtf_mode=mode;m.hrtf_taps=mode?56u:48u;
 m.master_boost=1.0f;m.reverb_wet=0.0f;m.geometry_enabled=0u;
 for(unsigned i=0;i<bench_voices;i++){
  a3dmix_voice_init(&v[i]);
  v[i].active=1u;v[i].looping=1u;v[i].pos[0]=(float)(i%4u)-1.5f;
  v[i].pos[2]=-(float)(i/4u+2u);v[i].pcm=pcm;v[i].bytes=sizeof(pcm);
  v[i].rate=48000u;v[i].bits=16u;v[i].channels=1u;
  a3dmix_add(&m,&v[i]);
 }
}
int main(int argc,char**argv){
 if(argc>1){
  char *end=0;unsigned long n=strtoul(argv[1],&end,10);
  if(!argv[1][0]||*end||n<1u||n>BENCH_VOICES){
   fprintf(stderr,"Usage: hrtfbench [voice_count: 1..32]\n");return 2;
  }
  bench_voices=(unsigned)n;
 }
 for(unsigned i=0;i<sizeof(pcm);i+=2){pcm[i]=(unsigned char)i;pcm[i+1]=(unsigned char)(i>>4);}
 const char *names[3]={"legacy48","fast56","reference56"};
 for(unsigned mode=0;mode<3;mode++){
  setup(mode);
  /* Warm up data and DSP state before measuring. */
  for(unsigned n=0;n<10u;n++)a3dmix_render(&m,out,256u);
  clock_t start=clock();
  for(unsigned n=0;n<BENCH_BLOCKS;n++)a3dmix_render(&m,out,256u);
  clock_t end=clock();
  double seconds=(double)(end-start)/(double)CLOCKS_PER_SEC;
  printf("%s: %.4f s CPU for %u voices x %u frames (%.1f simulated voice sec); CPU/render ratio %.3f\n",
    names[mode],seconds,bench_voices,BENCH_BLOCKS*256u,
    bench_voices*(BENCH_BLOCKS*256.0)/48000.0,
    seconds/((BENCH_BLOCKS*256.0)/48000.0));
 }
 return 0;
}
