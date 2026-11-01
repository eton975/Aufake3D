/* v0.6.12 RELEASE DSP CONTRACT
 * PCM -> per-source attenuation/Doppler/HRTF/early reflections -> protected
 * weapon and background buses -> optional background duck -> late reverb
 * -> master gain -> stereo-linked limiter -> interleaved signed 16-bit PCM.
 * The clarity bypass follows the original summation path. Protected voices
 * keep their spatial processing; recognition never directly boosts a source.
 * Queue latency is configured outside this allocator-free DSP unit.
 */
/* v0.5.0 SOURCE COMMENTARY — Game-independent PCM spatial audio mixer
 * Implements per-voice sample reads, time/pitch stepping, directional filtering,
 * distance attenuation, Doppler, early reflections, late reverb and stereo output
 * limiting. Audio runs in 256-frame blocks at 48 kHz with a configurable, 128-slot voice pool. The
 * 5.0 master-gain default is user-selected; dynamic limiting may lower peaks and
 * perceived dynamic range.
 */
/* Copyright 2026, original independent implementation. MIT license.
 * Portable fixed-block multivoice renderer, no OS dependencies or allocation.
 * Not an exact Aureal AU8830 implementation. All coordinates are in scene units.
 */
#ifndef A3D_STREAM_CORE_H
#define A3D_STREAM_CORE_H
#include "measured_hrtf.h"
#include "hrtf_fast24_window.h"
#include "acoustic_scene.h"
#define A3DMIX_RATE 48000u
#define A3DMIX_BLOCK 256u
/* Hotfix 5: Quake III 1.17 creates at least 68 A3D source objects. The old
 * 24-voice ceiling rejected valid sources and dropped their sounds. Reserve
 * 128 pointer slots, but let users cap runtime voices for A/B comparisons.
 * The fixed pointer array is allocation capacity, NOT 128 simultaneous DSP
 * computations unless the game actually starts that many sources. */
#define A3DMIX_VOICES 128u
#define A3DMIX_HISTORY 348u
#define A3DMIX_FIR 96u /* bounded-cost early portion of measured MIT KEMAR HRIR */
#define A3DMIX_EARLY_RING 16384u
#define A3DMIX_REVERB_RING 8192u

typedef struct {
 const unsigned char *pcm;
 unsigned bytes,rate,channels,bits;
 float pos[3],vel[3],gain,pitch;
 float min_dist,max_dist,distance_scale,doppler_scale,doppler_factor;
 unsigned max_distance_behavior,head_relative;
 double cursor;
 unsigned active,looping;
 /* v0.6.12: conservative metadata-based weapon class, unchanged HRTF. */
 unsigned weapon_protected;
 float h[A3DMIX_HISTORY];
 unsigned hist_cursor;
 float early[A3DMIX_EARLY_RING];
 unsigned early_cursor;
 unsigned long played_frames;
 /* Optional progress to be reported by the COM wrapper. */
 unsigned ended;
 void *owner; /* Win32 wrapper-only event context */
 A3DPaths cached_paths;
 unsigned cache_valid,cache_age,cache_scene_revision;
 float cache_src[3],cache_lis[3];
 int prev_hrir_direction;
 unsigned hrir_initialized;
 /* Optional bounded, worker-owned PCM capture. The source's actual byte count
  * and cursor still describe the complete ring; sample_at maps a frame into
  * this immutable capture when it is present. Never dereference game PCM in
  * the render worker when a capture is active. */
 const unsigned char *pcm_window;
 unsigned pcm_window_start,pcm_window_frames;
} A3DMixVoice;
typedef struct {
 A3DMixVoice *v[A3DMIX_VOICES];
 float listener[3],forward[3],up[3],listener_vel[3];
 float distance_scale,doppler_scale,units_per_meter,output_gain;
 /* Experimental listening-calibration controls, defaults are v0.4.2. */
 float direct_trim,distance_strength,early_reflection_trim;
 /* Global post-spatialization loudness, same factor on both stereo channels. */
 float master_boost,limiter_gain;
 /* Opt-in game-specific weapon clarity: dry stereo buses + smooth enemy duck. */
 unsigned weapon_clarity; unsigned short_sfx_declick; float clarity_bg_gain; unsigned clarity_duck_frames;
 float clarity_weapon_l[A3DMIX_BLOCK],clarity_weapon_r[A3DMIX_BLOCK];
 unsigned distance_enabled,doppler_enabled;
 unsigned coords,frames_rendered,underruns,clip_events,hrtf_taps,limiter_active_frames;
 unsigned voice_limit,voice_peak,voice_rejections,voice_additions;
 /* HF9: acoustic geometry is computationally expensive when 2,000+ scene
  * triangles are resubmitted on every game frame. Rate-limit expensive
  * tracing; keep HRTF, PCM, and per-source playback untouched. */
 unsigned geometry_enabled,geometry_retrace_blocks;
 unsigned geometry_trace_calls,geometry_cache_hits,geometry_deferred_revisions;
 unsigned geometry_disabled_voice_blocks;
 float rv_l[A3DMIX_REVERB_RING],rv_r[A3DMIX_REVERB_RING];
 unsigned rv_cursor;
 float reverb_wet;
 const A3DScene *scene;
 float ref_gain,ref_delay;
} A3DMix;
static void a3dmix_zero(void *dst,unsigned long bytes){unsigned char*p=(unsigned char*)dst;for(unsigned long i=0;i<bytes;i++)p[i]=0;}
/* REVIEW NOTE — a3dmix_init: Master DSP defaults, including the 5.0 master boost selected in v0.4.7, are initialized here. */
/* Default policy, NOT a promise of physical AU8830 equivalence:
 * 48 kHz processing, stereo HRTF, 48 measured-tap default, boost 5.0 with
 * linked limiter, and opt-out short-SFX edge envelope. The voice pool is
 * bounded and no heap allocation belongs in the 256-frame render loop. */
static void a3dmix_init(A3DMix*m){a3dmix_zero(m,sizeof(*m));m->forward[2]=-1.0f;m->up[1]=1.0f;m->reverb_wet=0.14f;m->ref_gain=1.0f;m->ref_delay=1.0f;m->distance_scale=1.0f;m->doppler_scale=1.0f;m->units_per_meter=1.0f;m->output_gain=1.0f;m->hrtf_taps=48u;m->direct_trim=1.0f;m->distance_strength=1.0f;m->early_reflection_trim=1.0f;m->master_boost=5.0f;m->short_sfx_declick=1u;m->limiter_gain=1.0f;m->clarity_bg_gain=1.0f;m->voice_limit=A3DMIX_VOICES;m->geometry_enabled=1u;m->geometry_retrace_blocks=8u;}
static void a3dmix_voice_init(A3DMixVoice*v){a3dmix_zero(v,sizeof(*v));v->gain=1.0f;v->pitch=1.0f;v->min_dist=1.0f;v->max_dist=1000.0f;v->distance_scale=1.0f;v->doppler_scale=1.0f;v->doppler_factor=1.0f;}
/* REVIEW NOTE — a3dmix_add: Voice registration: bounded to A3DMIX_VOICES; a full pool must not corrupt existing sources. */
static int a3dmix_add(A3DMix*m,A3DMixVoice*v){
 /* Registered voices remain address-stable. Duplicated Play must not consume
  * an extra slot; a source must be stopped/released before its memory dies. */
 for(unsigned i=0;i<A3DMIX_VOICES;i++)if(m->v[i]==v)return 1;
 unsigned cap=m->voice_limit;
 if(!cap||cap>A3DMIX_VOICES)cap=A3DMIX_VOICES;
 for(unsigned i=0;i<cap;i++)if(!m->v[i]){
  m->v[i]=v;m->voice_additions++;
  unsigned used=0;
  for(unsigned j=0;j<A3DMIX_VOICES;j++)if(m->v[j])used++;
  if(used>m->voice_peak)m->voice_peak=used;
  return 1;
 }
 m->voice_rejections++;
 return 0;
}
static void a3dmix_remove(A3DMix*m,A3DMixVoice*v){for(unsigned i=0;i<A3DMIX_VOICES;i++)if(m->v[i]==v)m->v[i]=0;}
/* Read a PCM frame either from the game-provided ring or from an immutable
 * captured window. The latter is worker-safe when the wrapper has copied
 * mutable game samples; keep the byte/stride bounds check before every read.
 * Returns a signed sample approximation; it does not advance playback. */
static int a3dmix_sample_at(const A3DMixVoice*v,unsigned frame){
 unsigned stride=v->channels*(v->bits/8u);
 unsigned off=frame*stride;
 if(!stride||off+stride>v->bytes)return 0;
 const unsigned char *pcm=v->pcm;
 if(v->pcm_window){
  unsigned total=v->bytes/stride;
  if(!total)return 0;
  unsigned first=v->pcm_window_start;
  unsigned delta=frame>=first?frame-first:frame+total-first;
  if(delta>=v->pcm_window_frames)return 0;
  pcm=v->pcm_window;off=delta*stride;
 }
 int a=(v->bits==16)?((int)pcm[off]|((int)pcm[off+1]<<8)):((int)pcm[off]-128)*256;
 if(v->bits==16&&a>=32768)a-=65536;
 if(v->channels==2){
  unsigned o=off+v->bits/8u;
  int b=(v->bits==16)?((int)pcm[o]|(int)pcm[o+1]<<8):((int)pcm[o]-128)*256;
  if(v->bits==16&&b>=32768)b-=65536;
  a=(a+b)/2;
 }
 return a;
}
/* v0.8.12: A bounded edge envelope for very short, non-looping PCM sources.
 * The discontinuity can originate at a game's sample edge or when the game
 * rapidly restarts an interface sound. This does NOT smooth every PCM block,
 * alter any HRTF coefficient, or touch dialogue (>300 ms) and looped audio.
 * The input PCM and original source cursor are never rewritten.
 * Entirely reversible via A3D_SHORT_SFX_DECLICK=0, initialized by the host.
 * 32 output frames at 48 kHz = 0.667 ms; only start/end edges are attenuated. */
/* Conservative edge discontinuity mitigation. Applies ONLY to short,
 * nonlooping sources selected by the checks inside this function; it must not
 * shorten Cheshire Cat dialogue or alter looping ambience. This is a small
 * sound-quality mitigation, not evidence that the WaveOut timing cause was
 * eliminated. Disable with A3D_SHORT_SFX_DECLICK=0 for a controlled baseline. */
static float a3dmix_short_sfx_envelope(const A3DMix*m,const A3DMixVoice*v){
 if(!m->short_sfx_declick||v->looping||!v->rate||!v->channels||!v->bits||!v->bytes)return 1.0f;
 unsigned stride=v->channels*(v->bits/8u);
 if(!stride)return 1.0f;
 unsigned total=v->bytes/stride;
 if(!total)return 1.0f;
 /* Keep speech and longer effects sample-identical. Use 64-bit for safety. */
 if((unsigned long long)total*1000u > (unsigned long long)v->rate*300u)return 1.0f;
 float gain=1.0f;
 if(v->played_frames<32u)gain=(float)v->played_frames/32.0f;
 float remaining=(float)total-(float)v->cursor;
 float rate=v->pitch*v->doppler_factor*(float)v->rate/(float)A3DMIX_RATE;
 if(rate>0.0001f){
  float tail=remaining/(32.0f*rate);
  if(tail<gain)gain=tail;
 }
 if(gain<0.0f)gain=0.0f;
 if(gain>1.0f)gain=1.0f;
 return gain;
}
/* REVIEW NOTE — a3dmix_next: Sample-cursor stepping: handles voice playback and effective pitch; preserve buffer and loop bounds. */
static float a3dmix_next(A3DMixVoice*v){
 if(!v->active||!v->pcm||!v->channels||!v->rate||!v->bits)return 0;
 unsigned frames=v->bytes/(v->channels*(v->bits/8u));
 if(!frames){v->active=0;v->ended=1;return 0;}
 if(v->cursor >= (double)frames){
  if(v->looping){while(v->cursor >= (double)frames)v->cursor-=frames;}
  else {v->active=0;v->ended=1;return 0;}
 }
 unsigned ix=(unsigned)v->cursor;
 unsigned next=(ix+1<frames)?ix+1:(v->looping?0:ix);
 float frac=(float)(v->cursor-(double)ix);
 float x=(1.0f-frac)*(float)a3dmix_sample_at(v,ix)+frac*(float)a3dmix_sample_at(v,next);
 float step=(float)v->rate/A3DMIX_RATE*v->pitch*v->doppler_factor;
 if(step<0.1f)step=0.1f;if(step>8.0f)step=8.0f;
 v->cursor+=(double)step;v->played_frames++;
 return x/32768.0f;
}
static int a3dmix_s16(float x){
 if(x>0.98f)return 32112;
 if(x< -0.98f)return -32112;
 return (int)(x*32767.0f);
}
static float a3dmix_abs(float x){return x<0?-x:x;}
/* A3D 2/3 documented range behavior: 6 dB reduction per doubled
 * effective distance after the source minimum, stopped at maximum. */
/* REVIEW NOTE — a3dmix_distance_gain: Distance law: combines min/max distance and optional strength setting; geometry may additionally attenuate sources. */
static float a3dmix_distance_gain(const A3DMix*m,const A3DMixVoice*v,float d){
 if(!m->distance_enabled)return 1.0f;
 float min=v->min_dist>0.0001f?v->min_dist:0.0001f;
 float max=v->max_dist>=min?v->max_dist:min;
 if(d>=max && v->max_distance_behavior==1u)return 0.0f; /* A3D_MUTE */
 if(d<=min)return 1.0f;
 if(d>max)d=max;
 float scale=m->distance_scale*v->distance_scale;
 if(scale<0.0f)scale=0.0f;if(scale>10000.0f)scale=10000.0f;
 return min/(min+(d-min)*scale);
}
/* Radial Doppler, source and listener velocities in world units/second.
 * Positive listener radial velocity towards the source raises pitch. */
/* REVIEW NOTE — a3dmix_doppler: Doppler: projects velocities along source/listener radial direction and clamps extreme ratios. */
static float a3dmix_doppler(const A3DMix*m,const A3DMixVoice*v,const float src[3],const float lis[3]){
 if(!m->doppler_enabled||v->head_relative)return 1.0f;
 float delta[3],dd=0;
 for(unsigned i=0;i<3;i++){delta[i]=src[i]-lis[i];dd+=delta[i]*delta[i];}
 float distance=a3d_sqrt(dd);if(distance<0.001f)return 1.0f;
 float scale=m->doppler_scale*v->doppler_scale;
 if(scale<=0.0f)return 1.0f;if(scale>100.0f)scale=100.0f;
 float units=m->units_per_meter>0.0001f?m->units_per_meter:1.0f;
 float v_src=0,v_lis=0;
 for(unsigned i=0;i<3;i++){float unit=delta[i]/distance;v_src+=v->vel[i]*unit;v_lis+=m->listener_vel[i]*unit;}
 /* Keep user-provided velocities from producing zero/negative denominators. */
 float src_speed=scale*v_src/units,lis_speed=scale*v_lis/units;
 if(src_speed< -306.0f)src_speed= -306.0f;if(src_speed>306.0f)src_speed=306.0f;
 if(lis_speed< -306.0f)lis_speed= -306.0f;if(lis_speed>306.0f)lis_speed=306.0f;
 float factor=(340.0f+lis_speed)/(340.0f+src_speed);
 if(factor<0.5f)factor=0.5f;if(factor>2.0f)factor=2.0f;
 return factor;
}
/* Deterministic block renderer; scene and voice properties are snapshots during
 * the call. The host must serialize it against source edits/removals. */
/* REVIEW NOTE — a3dmix_render: Critical per-block mixer: sum direct binaural audio, reflections, and reverb then apply stereo-linked limiting before PCM output. */
/* Render a bounded block of interleaved stereo PCM from registered voices.
 * Spatialization, reflections, protected-voice mixing, master gain and linked
 * limiting are composed here. The WinMM thread decides queue depth; this
 * routine must not call WaveOut or perform file I/O. */
static void a3dmix_render(A3DMix*m,unsigned char*out,unsigned frames){
 if(!out||frames>A3DMIX_BLOCK)return;
 float left[A3DMIX_BLOCK],right[A3DMIX_BLOCK];
 float *weapon_l=m->clarity_weapon_l,*weapon_r=m->clarity_weapon_r;
 unsigned active_voices=0;
 for(unsigned n=0;n<frames;n++){left[n]=0;right[n]=0;weapon_l[n]=0;weapon_r[n]=0;}
 for(unsigned vi=0;vi<A3DMIX_VOICES;vi++){
  A3DMixVoice*v=m->v[vi];if(!v||!v->active)continue;
  active_voices++;
  /* Head-relative sources live in listener-local axes; avoid world BSP
   * occlusion for sounds anchored to the player or interface. */
  const float origin[3]={0,0,0},local_front[3]={0,0,-1},local_up[3]={0,1,0};
  const float *spos=v->pos,*lpos=v->head_relative?origin:m->listener;
  const float *front=v->head_relative?local_front:m->forward;
  const float *up=v->head_relative?local_up:m->up;
  float d[3],dist2=0;
  for(unsigned j=0;j<3;j++){d[j]=spos[j]-lpos[j];dist2+=d[j]*d[j];}
  float dist=a3d_sqrt(dist2);
  float amplitude=v->gain*m->output_gain;
  if(amplitude<0.0f)amplitude=0.0f;if(amplitude>1.0f)amplitude=1.0f;
  A3DMeasuredPick pick=a3d_measured_pick(spos,lpos,front,up,m->coords,amplitude,A3DMIX_RATE);
  if(m->distance_enabled){
   /* Blend A3D distance roll-off for research, leaving A3D_MUTE semantics
    * untouched; the default strength of 1.0 retains v0.4.2 behaviour. */
   float dg=a3dmix_distance_gain(m,v,dist);
   if(dg<=0.0f && v->max_distance_behavior==1u)
    pick.amplitude=0.0f;
   else pick.amplitude=0.5f*amplitude*(1.0f-m->distance_strength+m->distance_strength*dg);
  }
  /* Reference amplitude for reflected paths: source volume, master gain,
   * and distance attenuation must apply to reflections as well.  Prior
   * revisions omitted these factors, so a quiet/distant source could have
   * disproportionately loud reflections and seem disconnected from its origin.
   * Retain the pre-trim level: DIRECT_TRIM intentionally affects direct only.
   */
  const float reflected_amplitude=pick.amplitude;
  pick.amplitude*=m->direct_trim;
  v->doppler_factor=a3dmix_doppler(m,v,spos,lpos);
  const signed short *hl=a3d_mhrir_48000[pick.direction][0],*hr=a3d_mhrir_48000[pick.direction][1];
  if(!v->hrir_initialized){v->prev_hrir_direction=pick.direction;v->hrir_initialized=1;}
  const signed short *old_l=a3d_mhrir_48000[v->prev_hrir_direction][0],
                     *old_r=a3d_mhrir_48000[v->prev_hrir_direction][1];
  A3DPaths paths;paths.intersections=paths.n_early=0;paths.direct_low=paths.direct_high=1.0f;
  if(m->scene&&!v->head_relative&&m->geometry_enabled){
   float change=0.0f;
   for(unsigned k=0;k<3;k++){
    float ds=v->pos[k]-v->cache_src[k],dl=m->listener[k]-v->cache_lis[k];
    change+=ds*ds+dl*dl;
   }
   /* Historical bug: Flush increments revision every frame even when
    * Quake III re-sends the same 2,048 triangles. This forced an O(triangles)
    * trace for EVERY voice on EVERY 256-frame audio block. In busy scenes
    * audio blocks took >45ms against a 5.33ms playback deadline.
    *
    * With HF9's default 8-block cache, geometry revision invalidations
    * are coalesced for <= ~42.7ms, except where a source or listener moves
    * significantly. Dynamic HRTF position filtering still updates every
    * block; only reflected/occluded acoustic paths are cached. The legacy
    * immediate-revision mode remains available by choosing interval 0. */
   unsigned ttl=m->geometry_retrace_blocks;
   unsigned age_limit=ttl>4u?ttl:4u;
   int revision_changed=v->cache_scene_revision!=m->scene->revision;
   int outdated=!v->cache_valid||v->cache_age>=age_limit||change>0.0625f||
                (!ttl && revision_changed);
   if(outdated){
    a3d_trace(m->scene,a3d_v3(v->pos[0],v->pos[1],v->pos[2]),
              a3d_v3(m->listener[0],m->listener[1],m->listener[2]),&v->cached_paths);
    m->geometry_trace_calls++;
    v->cache_scene_revision=m->scene->revision;v->cache_valid=1;v->cache_age=0;
    for(unsigned k=0;k<3;k++){v->cache_src[k]=v->pos[k];v->cache_lis[k]=m->listener[k];}
   }else {
    v->cache_age++;m->geometry_cache_hits++;
    if(revision_changed)m->geometry_deferred_revisions++;
   }
   paths=v->cached_paths;
  }else if(m->scene&&!v->head_relative&&!m->geometry_enabled){
   m->geometry_disabled_voice_blocks++;
  }
  float lo=paths.direct_low,hi=paths.direct_high;
  /* Precompute stereo direction gains for each first-order reflection. */
  float rg[A3D_SCENE_MAX_REFLECT][2];unsigned rd[A3D_SCENE_MAX_REFLECT];
  for(unsigned k=0;k<paths.n_early;k++){
   float p[3]={paths.early[k].point.x,paths.early[k].point.y,paths.early[k].point.z};
   A3DStereoGains sg=a3d_stereo_gains(p,m->listener,m->forward,m->up,m->coords,1.0f);
   const float reflected_gain=paths.early[k].gain*m->ref_gain*
       reflected_amplitude*m->early_reflection_trim;
   rg[k][0]=sg.left*reflected_gain;
   rg[k][1]=sg.right*reflected_gain;
   float d=paths.early[k].delay_sec*m->ref_delay;
   if(d<0)d=0;if(d>0.32f)d=0.32f;
   rd[k]=(unsigned)(d*A3DMIX_RATE+0.5f);
  }
  /* The measured 48kHz HRIR contains an initial acoustic propagation delay.
   * Its main impulse is usually around samples 35-80; selecting the FIRST
   * 24 taps nearly mutes the signal. For the low-CPU diagnostic mode only,
   * use a 24-tap window containing the highest combined ear energy.
   * Keep each coefficient's ORIGINAL history index: this preserves the
   * interaural time difference and propagation delay instead of shifting
   * both ears' impulses earlier. 48/96-tap modes are untouched by HF3a. */
  unsigned new_start=(m->hrtf_taps==24u)?a3d_mhrir_fast24_starts[pick.direction]:0u;
  unsigned old_start=(m->hrtf_taps==24u)?a3d_mhrir_fast24_starts[v->prev_hrir_direction]:0u;
  float lowpass=0.0f;
  for(unsigned n=0;n<frames;n++){
   float x=a3dmix_next(v);
   x*=a3dmix_short_sfx_envelope(m,v);
   v->h[v->hist_cursor]=x;
   float l=0,r=0;
   for(unsigned k=0;k<m->hrtf_taps && k<A3DMIX_FIR;k++){
    unsigned nk=new_start+k;
    unsigned nh=v->hist_cursor+A3DMIX_HISTORY-nk;
    if(nh>=A3DMIX_HISTORY)nh-=A3DMIX_HISTORY;
    float q=v->h[nh];
    if(v->prev_hrir_direction!=pick.direction && n<48u){
     unsigned ok=old_start+k;
     unsigned oh=v->hist_cursor+A3DMIX_HISTORY-ok;
     if(oh>=A3DMIX_HISTORY)oh-=A3DMIX_HISTORY;
     float oldq=v->h[oh];
     float blend=(float)(n+1u)/48.0f;
     l+=(1.0f-blend)*oldq*(float)old_l[ok]+blend*q*(float)hl[nk];
     r+=(1.0f-blend)*oldq*(float)old_r[ok]+blend*q*(float)hr[nk];
    }else{l+=q*(float)hl[nk];r+=q*(float)hr[nk];}
   }
   v->hist_cursor++;
   if(v->hist_cursor==A3DMIX_HISTORY)v->hist_cursor=0;
   l=l*pick.amplitude/32768.0f;r=r*pick.amplitude/32768.0f;
   if(paths.intersections){
    lowpass=0.88f*lowpass+0.12f*x;
    /* Direct-path low/high band approximation. */
    float ratio=hi+(lo-hi)*a3dmix_abs(lowpass)/(a3dmix_abs(x)+0.0001f);
    if(ratio>1)ratio=1;if(ratio<0)ratio=0;
    l*=ratio;r*=ratio;
   }
   v->early[v->early_cursor]=x;
   for(unsigned k=0;k<paths.n_early;k++){
    unsigned idx=(v->early_cursor+A3DMIX_EARLY_RING-rd[k])&(A3DMIX_EARLY_RING-1u);
    float q=v->early[idx];l+=q*rg[k][0];r+=q*rg[k][1];
   }
   v->early_cursor=(v->early_cursor+1)&(A3DMIX_EARLY_RING-1u);
   if(m->weapon_clarity && v->weapon_protected){weapon_l[n]+=l;weapon_r[n]+=r;}
   else {left[n]+=l;right[n]+=r;}
  }
  v->prev_hrir_direction=pick.direction;
 }
 /* Bounded, stereo-decorrelated late reverb with two feedback delay lines.
  * This is a generic effect, not a reconstruction of Aureal's reverb model. */
 for(unsigned n=0;n<frames;n++){
  /* v0.6.12: Never boost weapon sources. Protect their relative level by
   * gently ducking only non-weapon sources when the protected signal is
   * audible AND four or more voices compete. No hard level switches.
   * Attack ~6 ms; release ~200 ms at 48 kHz; max ~3.7 dB background duck.
   * With the switch off, the old mixer runs sample-identically.
   */
  if(m->weapon_clarity){
   float wp=a3dmix_abs(weapon_l[n]);
   if(a3dmix_abs(weapon_r[n])>wp)wp=a3dmix_abs(weapon_r[n]);
   float target=(active_voices>=4u && wp>0.0015f)?0.65f:1.0f;
   if(m->clarity_bg_gain>target){m->clarity_bg_gain-=0.00125f;if(m->clarity_bg_gain<target)m->clarity_bg_gain=target;}
   else if(m->clarity_bg_gain<target){m->clarity_bg_gain+=0.00004f;if(m->clarity_bg_gain>target)m->clarity_bg_gain=target;}
   if(m->clarity_bg_gain<0.999f)m->clarity_duck_frames++;
   left[n]=left[n]*m->clarity_bg_gain+weapon_l[n];
   right[n]=right[n]*m->clarity_bg_gain+weapon_r[n];
  }
  unsigned p=m->rv_cursor;
  unsigned a=(p+A3DMIX_REVERB_RING-1679u)&(A3DMIX_REVERB_RING-1u);
  unsigned b=(p+A3DMIX_REVERB_RING-2137u)&(A3DMIX_REVERB_RING-1u);
  float input=(left[n]+right[n])*0.5f;
  float ra=m->rv_l[a],rb=m->rv_r[b];
  m->rv_l[p]=input*0.35f+ra*0.66f;
  m->rv_r[p]=input*0.35f+rb*0.64f;
  left[n]+=m->reverb_wet*ra;right[n]+=m->reverb_wet*rb;
  m->rv_cursor=(p+1)&(A3DMIX_REVERB_RING-1u);
  /* v0.4.5: boost the COMPLETE spatial scene, not just the dry sound.
   * A stereo-linked peak limiter prevents the hard saturation of v0.4.4.
   * Shared gain preserves L/R directional and reflected/direct relationships.
   * Fast attack and slow recovery; sample state survives across blocks.
   */
  float out_l=left[n]*m->master_boost,out_r=right[n]*m->master_boost;
  float peak=a3dmix_abs(out_l);
  if(a3dmix_abs(out_r)>peak)peak=a3dmix_abs(out_r);
  float max_gain=peak>0.95f?0.95f/peak:1.0f;
  if(max_gain<m->limiter_gain){m->limiter_gain=max_gain;m->clip_events++;}
  else if(m->limiter_gain<max_gain){
   m->limiter_gain+=(m->weapon_clarity?0.00020f:0.00010f); /* quicker recovery, same peak ceiling in clarity mode */
   if(m->limiter_gain>max_gain)m->limiter_gain=max_gain;
  }
  if(m->limiter_gain<0.999f)m->limiter_active_frames++;
  int l=a3dmix_s16(out_l*m->limiter_gain),r=a3dmix_s16(out_r*m->limiter_gain);
  unsigned short u=(unsigned short)l,w=(unsigned short)r;
  out[4*n]=(unsigned char)u;out[4*n+1]=(unsigned char)(u>>8);
  out[4*n+2]=(unsigned char)w;out[4*n+3]=(unsigned char)(w>>8);
 }
 m->frames_rendered+=frames;
}
#endif
