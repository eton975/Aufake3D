/* Tests actual current source-cursor math, not the Windows sound device.
 * Detects gross 44.1-kHz to 48-kHz playback-speed/cutoff drift.
 */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "stream_core.h"
static unsigned char pcm[44100*2];
static void single(unsigned rate,unsigned expected){
 A3DMixVoice v; a3dmix_voice_init(&v);
 v.pcm=pcm;v.bytes=sizeof(pcm);v.rate=rate;v.bits=16;v.channels=1;v.active=1;
 unsigned frames=0;
 while(v.active && frames<60000){(void)a3dmix_next(&v);frames++;}
 assert(v.ended && !v.active);
 unsigned difference=frames>expected?frames-expected:expected-frames;
 assert(difference<=2);
 printf("PCM source rate=%u playback frames=%u expected=%u PASS\n",rate,frames,expected);
}
int main(void){
 single(44100,48001);
 single(48000,44101);
 return 0;
}
