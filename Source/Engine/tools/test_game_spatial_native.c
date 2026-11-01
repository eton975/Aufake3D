/* v0.5.0 SOURCE COMMENTARY — Regression test / harness
 * Exercises the release implementation or checks its ABI/packaging contract. Do not
 * treat fixture success as proof of native Wine or retail-game compatibility.
 */
/* v0.4.1: deterministic integration math for actual game-fed PCM voices.
 * This does NOT claim any Alice gameplay or Wine functionality has been run.
 */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "../win32/stream_core.h"
static float absf(float v){return v<0?-v:v;}
static void near(float a,float b,float e){if(!(absf(a-b)<e)){fprintf(stderr,"expected %f near %f\n",a,b);abort();}}
static short rd16(const unsigned char*p,unsigned frame,unsigned ear){unsigned pos=frame*4+ear*2,raw=p[pos]|((unsigned)p[pos+1]<<8);return (short)(raw>=32768?((int)raw-65536):raw);}
int main(void){
 A3DMix*m=calloc(1,sizeof(*m));A3DMixVoice*v=calloc(1,sizeof(*v));assert(m&&v);
 a3dmix_init(m);a3dmix_voice_init(v);
 m->distance_enabled=1;v->min_dist=1;v->max_dist=10;
 near(a3dmix_distance_gain(m,v,0.5f),1,0.0001f);
 near(a3dmix_distance_gain(m,v,1),1,0.0001f);
 near(a3dmix_distance_gain(m,v,2),0.5f,0.0001f);
 near(a3dmix_distance_gain(m,v,4),0.25f,0.0001f);
 near(a3dmix_distance_gain(m,v,20),0.1f,0.0001f); /* A3D_AUDIBLE max cap */
 v->max_distance_behavior=1;
 near(a3dmix_distance_gain(m,v,10),0,0.0001f); /* A3D_MUTE */
 v->max_distance_behavior=0;m->distance_scale=0;
 near(a3dmix_distance_gain(m,v,8),1,0.0001f);
 m->distance_scale=1;v->distance_scale=2;
 near(a3dmix_distance_gain(m,v,2),1.0f/3.0f,0.0001f);
 m->distance_enabled=0;
 near(a3dmix_distance_gain(m,v,20000),1,0.0001f);
 m->doppler_enabled=1;m->units_per_meter=1;
 float source[3]={10,0,0},listener[3]={0,0,0};
 near(a3dmix_doppler(m,v,source,listener),1,0.0001f);
 v->vel[0]=-34;
 assert(a3dmix_doppler(m,v,source,listener)>1.10f); /* approaching */
 v->vel[0]=34;
 assert(a3dmix_doppler(m,v,source,listener)<0.93f); /* receding */
 v->doppler_scale=0;
 near(a3dmix_doppler(m,v,source,listener),1,0.0001f);
 v->doppler_scale=1;v->vel[0]=0;m->listener_vel[0]=34;
 assert(a3dmix_doppler(m,v,source,listener)>1.09f);
 m->doppler_enabled=0;near(a3dmix_doppler(m,v,source,listener),1,0.0001f);
 /* Real (but synthetic test) PCM is spatialized by the streaming core. */
 unsigned char pcm[1024];for(unsigned i=0;i<512;i++){unsigned short t=(unsigned short)(i%24*1000-11000);pcm[2*i]=(unsigned char)t;pcm[2*i+1]=(unsigned char)(t>>8);}
 a3dmix_init(m);a3dmix_voice_init(v);v->pcm=pcm;v->bytes=sizeof(pcm);
 v->rate=48000;v->bits=16;v->channels=1;v->active=1;v->gain=1;v->pos[0]=-2;v->pos[2]=-2;
 m->distance_enabled=1;assert(a3dmix_add(m,v));
 unsigned char out[A3DMIX_BLOCK*4];a3dmix_render(m,out,A3DMIX_BLOCK);
 long long L=0,R=0;for(unsigned i=0;i<A3DMIX_BLOCK;i++){long a=rd16(out,i,0),b=rd16(out,i,1);L+=a*a;R+=b*b;}
 assert(L>0&&R>0&&L!=R);
 /* Head relative is unchanged by world listener relocation/orientation. */
 a3dmix_init(m);a3dmix_voice_init(v);v->pcm=pcm;v->bytes=sizeof(pcm);v->rate=48000;v->channels=1;v->bits=16;v->active=1;v->pos[0]=-2;v->pos[2]=-2;v->head_relative=1;
 assert(a3dmix_add(m,v));a3dmix_render(m,out,A3DMIX_BLOCK);
 unsigned char baseline[A3DMIX_BLOCK*4];for(unsigned i=0;i<sizeof(out);i++)baseline[i]=out[i];
 a3dmix_init(m);a3dmix_voice_init(v);v->pcm=pcm;v->bytes=sizeof(pcm);v->rate=48000;v->channels=1;v->bits=16;v->active=1;v->pos[0]=-2;v->pos[2]=-2;v->head_relative=1;
 m->listener[0]=300;m->listener[1]=-70;m->forward[0]=1;m->forward[2]=0;m->up[1]=1;
 assert(a3dmix_add(m,v));a3dmix_render(m,out,A3DMIX_BLOCK);
 for(unsigned i=0;i<sizeof(out);i++)assert(baseline[i]==out[i]);
 printf("game-spatial core PASS: distance, Doppler, head-relative and PCM spatialization\n");
 free(v);free(m);return 0;
}
