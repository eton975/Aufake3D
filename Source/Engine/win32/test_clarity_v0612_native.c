/* v0.6.12 standalone native PCM test. No Wine, game, or sound output required.
 * Validate byte-identical bypass, bounded automatic duck and limiter safety.
 */
#include <stdio.h>
#include <string.h>
#include "stream_core.h"
static A3DMix a,b,c;
static A3DMixVoice voices[4];
static unsigned char samples[4][32768];
static unsigned char out_a[A3DMIX_BLOCK*4],out_b[A3DMIX_BLOCK*4];
static int fail(const char*reason){fprintf(stderr,"FAIL: %s\n",reason);return 1;}
static void setup(A3DMix *m,unsigned clarity,unsigned voice_count,unsigned protect){
 a3dmix_init(m);m->master_boost=5.0f;m->reverb_wet=0;
 m->weapon_clarity=clarity;
 for(unsigned i=0;i<voice_count;i++){
  /* Test voice state is reset between setups to ensure no DSP history leaks. */
  a3dmix_voice_init(&voices[i]);
  voices[i].pcm=samples[i];voices[i].rate=22050;voices[i].bytes=32768;
  voices[i].bits=16;voices[i].channels=1;voices[i].pos[2]=-1.0f;
  voices[i].head_relative=1;voices[i].active=1;voices[i].gain=0.7f;
  voices[i].weapon_protected=(i==0&&protect)?1u:0u;
  a3dmix_add(m,&voices[i]);
 }
}
static void gen_pcm(void){
 for(unsigned i=0;i<4;i++)for(unsigned n=0;n<16384;n++){
  /* Deterministic, amplitude-modulated tones without math.h linkage. */
  int x=((int)((n*(129u+13u*i)+i*1009u)%8191u)-4095);
  x*=2;unsigned short y=(unsigned short)(short)x;
  samples[i][2*n]=(unsigned char)y;samples[i][2*n+1]=(unsigned char)(y>>8);
 }
}
int main(void){
 gen_pcm();
 setup(&a,0,4,0);a3dmix_render(&a,out_a,256);
 setup(&b,0,4,1);a3dmix_render(&b,out_b,256);
 if(memcmp(out_a,out_b,sizeof(out_a)))return fail("bypass is not bit-exact");
 if(a.clarity_duck_frames||b.clarity_duck_frames)return fail("bypass altered counters");
 setup(&c,1,4,1);
 for(int i=0;i<6;i++)a3dmix_render(&c,out_b,256);
 if(c.clarity_duck_frames==0)return fail("protected source did not cause sidechain duck");
 if(c.clarity_bg_gain<0.649f || c.clarity_bg_gain>1.001f)return fail("duck gain out of bounds");
 if(c.limiter_gain<=0 || c.limiter_gain>1.001f)return fail("linked limiter gain out of bounds");
 for(unsigned n=0;n<256*2;n++){
  int sample=(int)(signed short)((unsigned)out_b[2*n] |((unsigned)out_b[2*n+1]<<8));
  if(sample>32112||sample< -32112)return fail("PCM sample beyond safety ceiling");
 }
 setup(&c,1,4,0);a3dmix_render(&c,out_b,256);
 if(c.clarity_duck_frames)return fail("unprotected audio was ducked");
 setup(&c,1,3,1);a3dmix_render(&c,out_b,256);
 if(c.clarity_duck_frames)return fail("quiet scene was ducked");
 puts("PASS: v0.6.12 bypass bit-exact, weapon duck active and bounded, low-voice bypass, PCM safe");
 return 0;
}
