/* Native source-pool regression for Quake III + other A3D games.
 * Checks 128-slot capacity, rejection accounting, duplicate Play behavior,
 * Stop/Release recovery, and a configurable 24-voice compatibility limit.
 * No Wine required; no audio device is opened. */
#include <stdio.h>
#include "stream_core.h"
static A3DMix m;
static A3DMixVoice v[129];
static int fail(const char *message){fprintf(stderr,"FAIL: %s\n",message);return 1;}
int main(void){
 a3dmix_init(&m);
 if(A3DMIX_VOICES!=128u||m.voice_limit!=128u)return fail("capacity or default limit");
 for(unsigned i=0;i<128u;i++){
  a3dmix_voice_init(&v[i]);
  if(!a3dmix_add(&m,&v[i]))return fail("premature pool rejection");
 }
 if(m.voice_peak!=128u||m.voice_additions!=128u||m.voice_rejections)
  return fail("incorrect peak/add/rejection counters");
 if(!a3dmix_add(&m,&v[75])||m.voice_additions!=128u)
  return fail("duplicate Play consumed another slot");
 if(a3dmix_add(&m,&v[128])||m.voice_rejections!=1u)
  return fail("pool overflow not rejected safely");
 a3dmix_remove(&m,&v[42]);
 if(!a3dmix_add(&m,&v[128])||m.voice_additions!=129u)
  return fail("removed voice slot not reusable");
 a3dmix_init(&m);m.voice_limit=24u;
 for(unsigned i=0;i<24u;i++)if(!a3dmix_add(&m,&v[i]))return fail("24-voice control");
 if(a3dmix_add(&m,&v[24])||m.voice_peak!=24u||m.voice_rejections!=1u)
  return fail("voice limit override ignored");
 puts("PASS: 128-voice allocation, overflow, duplicate, recycling, and 24-voice control");
 return 0;
}
