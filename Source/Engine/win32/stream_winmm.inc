/* v0.5.0 SOURCE COMMENTARY — Windows waveOut streaming driver
 * Connects the software mixer to the Windows/Wine waveOut device. The playback worker
 * maintains output queue depth and synchronizes source-buffer updates. Underflow and
 * thread scheduling under Wine remain game-dependent.
 */
/* Shared 48-kHz / 16-bit stereo waveOut engine, experimental Win32/Wine.
 * One device and one worker thread for all A3D PCM sources. No external CRT.
 * The lock protects the voice list and sample lifetime. It does not yet
 * implement all A3D cursor events or exact DMA-style streaming semantics.
 */
#include "stream_core.h"
typedef struct { void *debug; long count,recursion; void *owner,*semaphore; unsigned long spin; } A3DCriticalSection;
IMPORT void WINAPI InitializeCriticalSection(A3DCriticalSection*);
IMPORT void WINAPI EnterCriticalSection(A3DCriticalSection*);
IMPORT void WINAPI LeaveCriticalSection(A3DCriticalSection*);
IMPORT long WINAPI InterlockedCompareExchange(volatile long*,long,long);
IMPORT long WINAPI InterlockedExchange(volatile long*,long);
IMPORT void* WINAPI CreateThread(void*,DWORD,DWORD (WINAPI*)(void*),void*,DWORD,DWORD*);
IMPORT DWORD WINAPI WaitForSingleObject(HANDLE,DWORD);
IMPORT void WINAPI Sleep(DWORD);
IMPORT BOOL WINAPI SetEvent(HANDLE);
IMPORT HANDLE WINAPI CreateEventA(void*,BOOL,BOOL,const char*);
IMPORT BOOL WINAPI SetThreadPriority(HANDLE,int);
/* Completion notification lets the WaveOut worker refill promptly instead of
 * waiting for a fixed polling interval. Auto-reset events coalesce signals;
 * the worker always checks ALL completed headers after each wake. */
#define A3D_CALLBACK_EVENT 0x00050000UL

static A3DCriticalSection mix_cs;
static volatile long mix_cs_state=0;
static A3DMix mixer;
static void staff_poll_marks(A3DMix *mix){
 if(!staff_enabled())return;
 DWORD now=GetTickCount();
 if((long)(now-staff_next_mark_at)<0)return;
 staff_next_mark_at=now+300u;
 const char *flags[2]={"A3D_STAFF_GOOD.flag","A3D_STAFF_BAD.flag"};
 for(int index=0;index<2;index++){
  if(GetFileAttributesA(flags[index])==0xffffffffu)continue;
  if(!DeleteFileA(flags[index]))continue;
  DWORD kind=index?STAFF_EVENT_BAD:STAFF_EVENT_GOOD;
  staff_record(kind,0,0,0,0,0,staff_milli(mix->limiter_gain),mix->clip_events);
  /* Capture all currently registered voices at the marker time. */
  mix_enter();
  for(unsigned i=0;i<A3DMIX_VOICES;i++){
   A3DMixVoice*v=mixer.v[i];
   if(!v||!v->active||!v->owner)continue;
   Source*s=(Source*)v->owner;
   staff_record(STAFF_EVENT_ACTIVE,s->sample_id,s->staff_pcm_sig,
    staff_milli(s->gain),staff_milli(s->priority),1,
    staff_milli(mixer.limiter_gain),s->wave_size);
  }
  mix_leave();
 }
}

static HANDLE mix_waveout=0,mix_thread=0;
static volatile long mix_running=0;
static HANDLE mix_wave_event=0;
static int mix_event_mode=0;
static DWORD mix_event_wakes=0,mix_poll_timeouts=0;
static int mix_latency_trace=0;
/* v0.8.12–0.8.14 compatible timing controls: keep PCM, queue size,
 * thread priority and A3D2 adapter independent of diagnostic settings.
 * The default is now periodic position polling every four worker wakes,
 * based on Alice 2011 listening tests. No position-derived seek is allowed. */
static int mix_position_probe=0; /* waveOutGetPosition advisory call */
static int mix_listener_age_probe=0; /* QPC listener age measurement */
static DWORD mix_position_probe_calls=0;
/* v0.8.12: Windows A/B tests showed periodic waveOutGetPosition is a
 * necessary condition for clean Alice 2011 dialogue on the test host.
 * Both Sleep(0) and Sleep(1) controls failed. This is a deliberately
 * conservative WinMM compatibility pump; NOT proof of the driver's internal
 * completion mechanism. Keep the worker-side call outside the mixer lock. */
static DWORD mix_position_probe_valid=0,mix_position_probe_invalid=0;
static unsigned mix_position_interval=4u; /* in worker wakes: 1,2,4,8,16 */
static int mix_schedule_test=0; /* 0=none,1=Sleep(0),2=Sleep(1) instead of poll */
static int mix_profile_probe=0;
static DWORD mix_probe_max_us=0,mix_probe_total_us=0;
static DWORD mix_completed_headers=0,mix_header_flags_anomalies=0;
static DWORD mix_position_consecutive_errors=0,mix_position_max_consecutive_errors=0;


static DWORD mix_render_us_max=0,mix_slow_5ms=0,mix_slow_10ms=0;
/* Opt-in thread CPU observations for the single worst wall-clock DSP block.
 * Windows may quantize CPU time; this is advisory, not proof of preemption. */
static DWORD mix_worst_block_cpu_us=0,mix_worst_block_nonrunning_us=0;
typedef struct {DWORD low,high;} A3DWinFileTime;
typedef HANDLE (WINAPI *A3DGetCurrentThread)(void);
typedef BOOL (WINAPI *A3DGetThreadTimes)(HANDLE,A3DWinFileTime*,A3DWinFileTime*,A3DWinFileTime*,A3DWinFileTime*);
static A3DGetCurrentThread mix_current_thread=0;
static A3DGetThreadTimes mix_get_thread_times=0;
static unsigned long long mix_thread_cpu_100ns(void){
 if(!mix_latency_trace||!mix_get_thread_times||!mix_current_thread)return 0;
 A3DWinFileTime a={0,0},b={0,0},k={0,0},u={0,0};
 if(!mix_get_thread_times(mix_current_thread(),&a,&b,&k,&u))return 0;
 return (((unsigned long long)k.high<<32)|k.low)+
        (((unsigned long long)u.high<<32)|u.low);
}
typedef int (WINAPI *A3DQueryPerf)(long long*);
typedef DWORD (WINAPI *A3DGetTick)(void);
static A3DGetTick mix_tick=0;
/* v0.6.6: trace statistics require explicit opt-in; never write per-block logs. */
static long long mix_listener_update_at=0;
static unsigned long long mix_listener_age_total_us=0;
static DWORD mix_listener_age_max_us=0,mix_listener_age_samples=0;
static DWORD mix_pos_samples=0,mix_pos_unsupported=0;
static DWORD mix_playback_ahead_max_frames=0,mix_playback_ahead_min_frames=0xffffffffUL;
static unsigned long long mix_playback_ahead_total_frames=0;
/* Adaptive header target is OPT-IN, bounded by the proven profile ceiling.
 * No changes are made to header size, waveOut device settings or ring cursors. */
static int mix_adaptive=0;
static unsigned mix_target_headers=3u,mix_min_headers=3u,mix_start_headers=3u;
static DWORD mix_early_recoveries=0,mix_low_headroom_samples=0;
static DWORD mix_last_early_recovery_ms=0;
static unsigned mix_low_headroom_streak=0;
static DWORD mix_last_adjust_ms=0,mix_last_underrun_ms=0;
static DWORD mix_adjust_down=0,mix_adjust_up=0;
static A3DQueryPerf mix_qpc=0;
static long long mix_qpc_freq=0;
/* QPC is resolved dynamically so the DLL needs no new static import stubs. */
static void mix_setup_clock(void){
 HMODULE k=LoadLibraryA("kernel32.dll");
 if(!k)return;
 A3DQueryPerf frequency=(A3DQueryPerf)GetProcAddress(k,"QueryPerformanceFrequency");
 mix_qpc=(A3DQueryPerf)GetProcAddress(k,"QueryPerformanceCounter");
 mix_tick=(A3DGetTick)GetProcAddress(k,"GetTickCount");
 mix_current_thread=(A3DGetCurrentThread)GetProcAddress(k,"GetCurrentThread");
 mix_get_thread_times=(A3DGetThreadTimes)GetProcAddress(k,"GetThreadTimes");
 if(!frequency||!mix_qpc||!frequency(&mix_qpc_freq)||mix_qpc_freq<=0)
  {mix_qpc=0;mix_qpc_freq=0;}
}

/* WinMM waveOut fragments of 256 frames are only ~5.3 ms at 48 kHz.
 * Wine's host audio and Python/graphics-heavy desktop can exhibit scheduling
 * jitter approaching that interval. Queue 512-frame headers by default,
 * each made of two unchanged 256-frame HRTF render calls. Keep the old
 * 256-frame path selectable for A/B testing, and a 1024-frame option for
 * diagnosing Wine backend scheduling issues. */
#define MIX_BUFFERS 12u
#define MIX_SUBBLOCKS_MAX 4u
static unsigned mix_subblocks=2u; /* 256, 512, or 1024 frames per header */
/* Quake III's DMA ring is being rewritten while we render.  Do NOT render
 * a full 12-header queue ahead of its write cursor: that can consume stale
 * PCM even if waveOut's playback stream never technically underruns.
 * Default to about 32ms of ahead audio; allow deliberate A/B control. */
static unsigned mix_queue_limit=3u;
/* Snapshot renderer is opt-in until real games validate it. The proven legacy
 * path stays selectable (Alice 2011 uses it in the supplied launchers). */
static int mix_snapshot_mode=0;
static DWORD mix_snapshot_blocks=0,mix_snapshot_stale_commits=0;
static DWORD mix_snapshot_scene_copies=0,mix_snapshot_pcm_bytes_max=0;
static DWORD mix_snapshot_pcm_total_bytes=0;
static DWORD mix_snapshot_pcm_total_voices=0;
static DWORD mix_snapshot_pcm_frames_max=0;
static DWORD mix_snapshot_capture_us_max=0,mix_snapshot_commit_us_max=0;
/* Profiling is kept on the worker. It adds no per-call instrumentation to
 * the hot Quake III game-facing COM path. */
/* Measure only a RECENT listener update; an idle camera is not latency. */
static void mix_measure_listener_age(void){
 if(!mix_listener_age_probe||!mix_qpc||!mix_qpc_freq||!mix_listener_update_at)return;
 long long now=0;
 if(!mix_qpc(&now)||now<mix_listener_update_at)return;
 unsigned long long delta=(unsigned long long)(now-mix_listener_update_at);
 if(delta> (unsigned long long)mix_qpc_freq/2u)return; /* >= 500 ms old */
 DWORD us=(DWORD)((double)delta*1000000.0/(double)mix_qpc_freq);
 if(us>mix_listener_age_max_us)mix_listener_age_max_us=us;
 mix_listener_age_total_us+=us;mix_listener_age_samples++;
}
static void mix_time_max(DWORD *value,long long begin,long long end){
 if(mix_qpc && mix_qpc_freq>0 && end>=begin){
  DWORD us=(DWORD)(1000000.0*(double)(end-begin)/(double)mix_qpc_freq);
  if(us>*value)*value=us;
 }
}
#define MIX_CAPTURE_FRAMES (A3DMIX_BLOCK*8u+2u)
#define MIX_CAPTURE_STRIDE 4u
/* These are global rather than stack objects: each voice has a large FIR /
 * reflection history, and the wave worker must not exhaust its thread stack. */
static A3DMix mix_render_state;
static A3DScene mix_render_scene;
static A3DMixVoice mix_render_voice[A3DMIX_VOICES];
static unsigned char mix_render_pcm[A3DMIX_VOICES][MIX_CAPTURE_FRAMES*MIX_CAPTURE_STRIDE];
static DWORD mix_shadow_id[A3DMIX_VOICES],mix_shadow_serial[A3DMIX_VOICES];
static Source *mix_capture_owner[A3DMIX_VOICES];
static DWORD mix_capture_id[A3DMIX_VOICES],mix_capture_serial[A3DMIX_VOICES];
static DWORD mix_capture_oldcursor[A3DMIX_VOICES];
static DWORD mix_scene_revision=0;

static DWORD mix_headers_submitted=0;
static DWORD mix_queue_highwater=0;
static DWORD mix_queue_empty_events=0;
static int mix_last_queue_nonzero=0;
#define WHDR_DONE 0x1u
static unsigned char mix_pcm[MIX_BUFFERS][A3DMIX_BLOCK*4*MIX_SUBBLOCKS_MAX];
static WaveHeader mix_headers[MIX_BUFFERS];
static unsigned mix_prepared=0;
static unsigned char mix_header_outstanding[MIX_BUFFERS];
/* Boundary-only discontinuity detector: diagnostic counts, no PCM changes. */
static int mix_last_pcm_left=0,mix_last_pcm_right=0,mix_last_pcm_valid=0;
static DWORD mix_pcm_boundary_max_step=0,mix_pcm_boundary_large_steps=0;
static DWORD mix_pcm_boundary_blocks=0;
/* Fixed-size metadata ring; NO file I/O, allocation or user callbacks on worker. */
#define MIX_METRIC_EVENTS 64u
static struct {DWORD tick,kind,value;} mix_metric_events[MIX_METRIC_EVENTS];
static unsigned mix_metric_event_next=0,mix_metric_event_count=0;
static char mix_metrics_path[512];
static void mix_metric_event(DWORD kind,DWORD value){
 unsigned i=mix_metric_event_next++ % MIX_METRIC_EVENTS;
 mix_metric_events[i].tick=mix_tick?mix_tick():0;
 mix_metric_events[i].kind=kind;
 mix_metric_events[i].value=value;
 if(mix_metric_event_count<MIX_METRIC_EVENTS)mix_metric_event_count++;
}
static int mix_pcm_i16(const unsigned char*p){return (short)((unsigned)p[0]|((unsigned)p[1]<<8));}
static void mix_pcm_boundary_check(const unsigned char *pcm){
 int left=mix_pcm_i16(pcm),right=mix_pcm_i16(pcm+2);
 if(mix_last_pcm_valid){
  int ld=left-mix_last_pcm_left,rd=right-mix_last_pcm_right;
  unsigned la=(unsigned)(ld<0?-ld:ld),ra=(unsigned)(rd<0?-rd:rd);
  DWORD peak=la>ra?la:ra;
  if(peak>mix_pcm_boundary_max_step)mix_pcm_boundary_max_step=peak;
  if(peak>12000u){mix_pcm_boundary_large_steps++;mix_metric_event(2u,peak);}
 }
 const unsigned char *last=pcm+(A3DMIX_BLOCK-1u)*4u;
 mix_last_pcm_left=mix_pcm_i16(last);
 mix_last_pcm_right=mix_pcm_i16(last+2);
 mix_last_pcm_valid=1;mix_pcm_boundary_blocks++;
}
/* Close-time metrics are separate from A3D_LOG: never write on worker. */
static void mix_metric_write(HANDLE f,const char *key,DWORD value){
 char b[96];DWORD n=0,written=0;while(key[n]&&n<60u){b[n]=key[n];n++;}
 b[n++]='=';
 char rev[12];unsigned digits=0;
 do{rev[digits++]=(char)('0'+value%10u);value/=10u;}while(value&&digits<sizeof(rev));
 while(digits)b[n++]=rev[--digits];b[n++]='\r';b[n++]='\n';
 WriteFile(f,b,n,&written,0);
}
static void mix_write_metrics(void){
 if(!mix_metrics_path[0])return;
 HANDLE f=CreateFileA(mix_metrics_path,0x40000000u,3,0,2,128,0);
 if(f==INVALID_HANDLE_VALUE)return;
 mix_metric_write(f,"position_probe_enabled",(DWORD)mix_position_probe);
 mix_metric_write(f,"position_interval_wakes",mix_position_interval);
 mix_metric_write(f,"schedule_test_mode",(DWORD)mix_schedule_test);
 mix_metric_write(f,"probe_profile_enabled",(DWORD)mix_profile_probe);
 mix_metric_write(f,"position_calls",mix_position_probe_calls);
 mix_metric_write(f,"position_valid",mix_position_probe_valid);
 mix_metric_write(f,"position_invalid",mix_position_probe_invalid);
 mix_metric_write(f,"position_max_consecutive_errors",mix_position_max_consecutive_errors);
 mix_metric_write(f,"probe_max_us",mix_probe_max_us);
 mix_metric_write(f,"probe_total_us",mix_probe_total_us);
 mix_metric_write(f,"headers_submitted",mix_headers_submitted);
 mix_metric_write(f,"headers_completed",mix_completed_headers);
 mix_metric_write(f,"header_anomalies",mix_header_flags_anomalies);
 mix_metric_write(f,"queue_empty_events",mix_queue_empty_events);
 mix_metric_write(f,"max_queued_headers",mix_queue_highwater);
 mix_metric_write(f,"event_wakes",mix_event_wakes);
 mix_metric_write(f,"poll_timeouts",mix_poll_timeouts);
 mix_metric_write(f,"pcm_boundary_blocks",mix_pcm_boundary_blocks);
 mix_metric_write(f,"pcm_boundary_max_step",mix_pcm_boundary_max_step);
 mix_metric_write(f,"pcm_boundary_large_steps",mix_pcm_boundary_large_steps);
 mix_metric_write(f,"event_ring_count",mix_metric_event_count);
 /* Last 64 event records: kind 1=queue empty, 2=PCM step >12000. */
 for(unsigned j=0;j<mix_metric_event_count;j++){
  unsigned k=(mix_metric_event_next-mix_metric_event_count+j)%MIX_METRIC_EVENTS;
  char name[40]="event";name[5]=(char)('0'+(j/10u)%10u);name[6]=(char)('0'+j%10u);name[7]=0;
  mix_metric_write(f,name,mix_metric_events[k].kind);
  name[7]='_';name[8]='t';name[9]=0;
  mix_metric_write(f,name,mix_metric_events[k].tick);
  name[8]='v';mix_metric_write(f,name,mix_metric_events[k].value);
 }
 CloseHandle(f);
}

#include "pcm_diagnostics.inc"
static void mix_enter(void){
 if(mix_cs_state!=2){
  if(InterlockedCompareExchange(&mix_cs_state,1,0)==0){
   InitializeCriticalSection(&mix_cs);a3dmix_init(&mixer);
   /* An adjustable limit distinguishes missing voices from CPU saturation.
    * Default 128, or use A3D_VOICE_LIMIT=24 to reproduce the old ceiling. */
   mixer.voice_limit=(unsigned)a3d_tuning_env("A3D_VOICE_LIMIT",(float)A3DMIX_VOICES,8.0f,(float)A3DMIX_VOICES);
   /* Configure from the process environment at FIRST audio activity too:
    * older callers can begin playback without calling IA3d4.Init first. */
   mixer.master_boost=a3d_tuning_env("A3D_MASTER_GAIN",5.0f,0.1f,5.0f);
   {char opt[8]={0};DWORD n=GetEnvironmentVariableA("A3D_WEAPON_CLARITY",opt,sizeof(opt));
    mixer.weapon_clarity=(n==1u&&opt[0]=='1')?1u:0u;}
   /* UI one-shot declicking is a separate short-PCM guard, never an HRTF
    * or WaveOut timing change. Allow opt-out for unanticipated game content. */
   {char edge[8]={0};DWORD n=GetEnvironmentVariableA("A3D_SHORT_SFX_DECLICK",edge,sizeof(edge));
    mixer.short_sfx_declick=(n==1u&&edge[0]=='0')?0u:1u;}
   sr_logu("A3D.Clarity.enabled",mixer.weapon_clarity);
   sr_logu("A3D.ShortSFX.declick_enabled",mixer.short_sfx_declick);
   {
    char raw[32]={0};DWORD n=GetEnvironmentVariableA("A3D_MASTER_GAIN",raw,sizeof(raw));
    if(n>0 && n<sizeof(raw)){
     char line[90]="A3D.MasterGain.requested=";unsigned at=25u;
     /* 25 == length of fixed prefix; no shared CRT required. */
     for(DWORD i=0;i<n&&at<sizeof(line)-1;i++)line[at++]=raw[i];
     line[at]=0;logline(line);
    }else if(n>=sizeof(raw))logline("A3D.MasterGain.requested too long; default used");
    else logline("A3D.MasterGain.requested unset; default used");
   }
   sr_logu("A3D.MasterGain.start.x1000",(DWORD)(mixer.master_boost*1000.0f+0.5f));
   InterlockedExchange(&mix_cs_state,2);
  }else{while(mix_cs_state!=2)Sleep(1);}
 }
 EnterCriticalSection(&mix_cs);
}
static void mix_leave(void){LeaveCriticalSection(&mix_cs);}
/* Copy only game-modifiable controls.  DSP histories, limiter envelope,
 * geometry cache, reverb and read cursors live solely on the worker. */
/* Copy mixer controls into worker-owned state; preserve persistent DSP histories. */
static void mix_shadow_globals(void){
 mix_measure_listener_age();
 A3DMix *d=&mix_render_state,*a=&mixer;
 for(unsigned k=0;k<3;k++){
  d->listener[k]=a->listener[k];d->forward[k]=a->forward[k];
  d->up[k]=a->up[k];d->listener_vel[k]=a->listener_vel[k];
 }
 d->distance_scale=a->distance_scale;d->doppler_scale=a->doppler_scale;
 d->units_per_meter=a->units_per_meter;d->output_gain=a->output_gain;
 d->direct_trim=a->direct_trim;d->distance_strength=a->distance_strength;
 d->early_reflection_trim=a->early_reflection_trim;
 d->master_boost=a->master_boost;d->weapon_clarity=a->weapon_clarity;d->short_sfx_declick=a->short_sfx_declick;d->distance_enabled=a->distance_enabled;
 d->doppler_enabled=a->doppler_enabled;d->coords=a->coords;
 d->hrtf_taps=a->hrtf_taps;d->geometry_enabled=a->geometry_enabled;
 d->geometry_retrace_blocks=a->geometry_retrace_blocks;
 d->reverb_wet=a->reverb_wet;d->ref_gain=a->ref_gain;d->ref_delay=a->ref_delay;
 d->voice_limit=a->voice_limit;
 if(a->scene){
  const A3DScene *source=a->scene;
  if(mix_scene_revision!=source->revision ||
     mix_render_scene.committed.count!=source->committed.count ||
     mix_render_scene.committed.polygons!=source->committed.polygons){
   /* Only the committed scene is read by a3d_trace(); never copy staged
    * geometry or the game's record_target pointer into the worker. */
   mix_render_scene.committed.count=source->committed.count;
   mix_render_scene.committed.polygons=source->committed.polygons;
   sr_copy(mix_render_scene.committed.tris,source->committed.tris,
           source->committed.count*sizeof(A3DTri));
   mix_scene_revision=source->revision;
   mix_snapshot_scene_copies++;
  }
  mix_render_scene.revision=source->revision;
  mix_render_scene.global_flags=source->global_flags;
  d->scene=&mix_render_scene;
 }else d->scene=0;
}
/* Copy source controls including weapon metadata without resetting playback history. */
static void mix_shadow_voice_controls(A3DMixVoice *d,const A3DMixVoice *a){
 for(unsigned k=0;k<3;k++){d->pos[k]=a->pos[k];d->vel[k]=a->vel[k];}
 d->gain=a->gain;d->pitch=a->pitch;
 d->min_dist=a->min_dist;d->max_dist=a->max_dist;
 d->distance_scale=a->distance_scale;d->doppler_scale=a->doppler_scale;
 d->max_distance_behavior=a->max_distance_behavior;
 d->head_relative=a->head_relative;d->looping=a->looping;
 d->weapon_protected=a->weapon_protected;
 d->bytes=a->bytes;d->rate=a->rate;d->channels=a->channels;
 d->bits=a->bits;d->owner=0; /* never touch Source outside mix_cs */
}
/* Capture at most 2050 input frames. a3dmix_next clamps the per-output-frame
 * advance to 8, so 256 output frames can consume no more than 2048 input
 * frames. Two extra frames account for interpolation and a wrap boundary. */
/* Compute the exact mixer sample-rate step BEFORE copying PCM, using the
 * same listener, source and Doppler inputs as a3dmix_render().  A maximum
 * 2050-frame copy was previously made for EVERY active source on EVERY 256
 * output frames, even if the source advanced e.g. 59 frames at 11025 Hz.
 * Shorter captures reduce time under the global game-facing mixer lock.
 * The +4 guard protects the fractional starting cursor, interpolation and
 * floating-point rounding. The allocation is still bounded to 2050 frames. */
/* Bound the immutable PCM window needed by the worker at the current playback rate. */
static unsigned mix_capture_frames_required(const A3DMix *m,const A3DMixVoice *v){
 const float *spos=v->pos;
 const float local[3]={0,0,0};
 const float *lpos=v->head_relative?local:m->listener;
 float doppler=a3dmix_doppler(m,v,spos,lpos);
 float step=(float)v->rate/(float)A3DMIX_RATE * v->pitch * doppler;
 if(step<0.1f)step=0.1f;
 if(step>8.0f)step=8.0f;
 unsigned count=(unsigned)((float)A3DMIX_BLOCK*step)+4u;
 if(count>MIX_CAPTURE_FRAMES)count=MIX_CAPTURE_FRAMES;
 if(count<4u)count=4u;
 return count;
}
/* Capture bounded game PCM while holding the shared lock so rendering can run unlocked. */
static void mix_shadow_pcm(unsigned index,const A3DMixVoice *a,A3DMixVoice *d){
 unsigned stride=a->channels*(a->bits/8u);
 unsigned total=(stride&&a->bytes)?a->bytes/stride:0;
 d->pcm_window=0;d->pcm_window_frames=0;d->pcm=0;
 if(!a->pcm || !total || stride>MIX_CAPTURE_STRIDE)return;
 unsigned base=(unsigned)d->cursor%total;
 unsigned char *dst=mix_render_pcm[index];
 unsigned frames=mix_capture_frames_required(&mix_render_state,d);
 unsigned n=0,frame=base;
 while(n<frames){
  unsigned count=total-frame;
  if(count>frames-n)count=frames-n;
  sr_copy(dst+n*stride,a->pcm+frame*stride,count*stride);
  n+=count;frame=0;
 }
 unsigned bytes=frames*stride;
 if(bytes>mix_snapshot_pcm_bytes_max)mix_snapshot_pcm_bytes_max=bytes;
 if(frames>mix_snapshot_pcm_frames_max)mix_snapshot_pcm_frames_max=frames;
 if(mix_snapshot_pcm_total_bytes>0xffffffffu-bytes ||
    mix_snapshot_pcm_total_voices==0xffffffffu){
  mix_snapshot_pcm_total_bytes>>=1;
  mix_snapshot_pcm_total_voices>>=1;
 }
 mix_snapshot_pcm_total_bytes+=bytes;
 mix_snapshot_pcm_total_voices++;
 d->pcm=dst;d->pcm_window=dst;d->pcm_window_start=base;
 d->pcm_window_frames=frames;
}
/* The only shared work is a bounded input snapshot and a very short playback
 * cursor/event commit.  The entire HRTF, geometry and reverb DSP runs with
 * NO mixer critical section held. */
/* Render from an immutable worker snapshot; reconcile progress with live sources afterward. */
static void mix_render_snapshot(unsigned char *out){
 long long snap_start=0,snap_end=0;
 mix_enter();
 if(mix_qpc)mix_qpc(&snap_start);
 mix_shadow_globals();
 for(unsigned i=0;i<A3DMIX_VOICES;i++){
  A3DMixVoice *a=mixer.v[i];
  mix_render_state.v[i]=0;mix_capture_owner[i]=0;
  if(!a||!a->active||!a->pcm||!a->owner||!a->bytes)continue;
  Source *owner=(Source*)a->owner;
  if(!owner->in_mixer)continue;
  A3DMixVoice *d=&mix_render_voice[i];
  DWORD id=owner->sample_id,serial=owner->render_serial;
  if(mix_shadow_id[i]!=id||mix_shadow_serial[i]!=serial){
   /* One-time copying of source initialization, including DSP histories. */
   *d=*a;
   mix_shadow_id[i]=id;mix_shadow_serial[i]=serial;
  }
  mix_shadow_voice_controls(d,a);
  d->active=a->active;
  mix_capture_oldcursor[i]=(DWORD)(a->cursor*(a->channels*(a->bits/8u)));
  mix_capture_owner[i]=owner;mix_capture_id[i]=id;
  mix_capture_serial[i]=serial;
  mix_shadow_pcm(i,a,d);
  if(d->pcm)mix_render_state.v[i]=d;
 }
 if(mix_qpc && mix_qpc(&snap_end))
  mix_time_max(&mix_snapshot_capture_us_max,snap_start,snap_end);
 mix_leave();
 long long started=0,stopped=0;
 unsigned long long cpu_started=mix_thread_cpu_100ns();
 if(mix_qpc)mix_qpc(&started);
 for(unsigned i=0;i<A3DMIX_VOICES;i++){
  A3DMixVoice *v=mix_render_state.v[i];
  if(v&&v->active&&v->pcm&&v->bytes&&v->channels&&v->bits){
   unsigned nf=v->bytes/(v->channels*(v->bits/8u));
   if(nf){int val=a3dmix_sample_at(v,((unsigned)v->cursor)%nf);
    DWORD peak=(DWORD)(val<0?-val:val);if(peak>diag_input_peak)diag_input_peak=peak;}
  }
 }
 a3dmix_render(&mix_render_state,out,A3DMIX_BLOCK);
 staff_sample(&mix_render_state);
 diag_block(out,A3DMIX_BLOCK*4u);
 if(mix_qpc&&mix_qpc(&stopped)&&stopped>=started){
  DWORD us=(DWORD)(1000000.0*(double)(stopped-started)/(double)mix_qpc_freq);
  if(us>mix_render_us_max){
   mix_render_us_max=us;
   unsigned long long cpu_finished=mix_thread_cpu_100ns();
   DWORD cpu_us=(cpu_started && cpu_finished>=cpu_started)?
     (DWORD)((cpu_finished-cpu_started)/10u):0u;
   mix_worst_block_cpu_us=cpu_us;
   mix_worst_block_nonrunning_us=(cpu_us<=us)?us-cpu_us:0u;
  }
  if(us>=5333u)mix_slow_5ms++;
  if(us>=10000u)mix_slow_10ms++;
 }
 mix_enter();
 if(mix_qpc)mix_qpc(&snap_start);
 for(unsigned i=0;i<A3DMIX_VOICES;i++){
  Source *s=mix_capture_owner[i];
  if(!s)continue;
  /* Check the pointer against the live slot BEFORE dereferencing it. A
   * Source can be stopped/released while the worker renders offline. */
  A3DMixVoice *a=mixer.v[i];
  if(!a || a->owner!=s){mix_snapshot_stale_commits++;continue;}
  if(!s->in_mixer || s->sample_id!=mix_capture_id[i] ||
     s->render_serial!=mix_capture_serial[i]){
   mix_snapshot_stale_commits++;continue;
  }
  A3DMixVoice *v=&mix_render_voice[i];
  unsigned stride=v->channels*(v->bits/8u);
  unsigned old=v->bytes?mix_capture_oldcursor[i]%v->bytes:0;
  unsigned now=v->bytes?((DWORD)(v->cursor*stride))%v->bytes:0;
  a->cursor=v->cursor;a->active=v->active;
  for(DWORD ev=0;ev<s->event_count;ev++){
   DWORD point=s->event_codes[ev];HANDLE hnd=s->event_handles[ev];
   if(!hnd)continue;
   if(point==0xffffffffUL){if(v->ended)SetEvent(hnd);}
   else if(point<v->bytes&&old!=now &&
    ((old<now&&old<=point&&point<now)||
     (old>now&&(point>=old||point<now))))SetEvent(hnd);
  }
  if(v->ended)v->ended=0;
 }
 /* Expose diagnostics to the normal shutdown reporting path. */
 mixer.frames_rendered=mix_render_state.frames_rendered;
 mixer.clip_events=mix_render_state.clip_events;
 mixer.limiter_active_frames=mix_render_state.limiter_active_frames;
 mixer.clarity_duck_frames=mix_render_state.clarity_duck_frames;
 mixer.geometry_trace_calls=mix_render_state.geometry_trace_calls;
 mixer.geometry_cache_hits=mix_render_state.geometry_cache_hits;
 mixer.geometry_deferred_revisions=mix_render_state.geometry_deferred_revisions;
 mixer.geometry_disabled_voice_blocks=mix_render_state.geometry_disabled_voice_blocks;
 mix_snapshot_blocks++;
 if(mix_qpc && mix_qpc(&snap_end))
  mix_time_max(&mix_snapshot_commit_us_max,snap_start,snap_end);
 mix_leave();
}
/* GetPosition is advisory. It can be delayed, wrap, or be unavailable under
 * Wine. Log plausible position-derived queue ages; never use it to seek or
 * overwrite previously rendered audio. */
/* Convert supported waveOut clock units to frames; reject implausible queue distance. */
/* Read WinMM's position, accepting only documented MMTIME forms handled
 * below. On query failure, do not reinterpret samples, seek voices, shrink
 * output buffers or infer a device underrun from a single position result.
 * The successful query itself may influence host timing; its return value is
 * advisory when adaptive scheduling is disabled (as in the release profile). */
static int mix_sample_playback_position(DWORD *ahead_out){
 if(!wposition||!mix_waveout)return 0;
 WaveTime t={2u,0u,0u};
 if(wposition(mix_waveout,&t,sizeof(t))){
  if(mix_latency_trace)mix_pos_unsupported++;
  return 0;
 }
 DWORD played=0;
 if(t.type==2u)played=t.value;
 else if(t.type==4u)played=t.value/4u;
 else if(t.type==1u)played=(DWORD)((double)t.value*(double)A3DMIX_RATE/1000.0);
 else {if(mix_latency_trace)mix_pos_unsupported++;return 0;}
 DWORD submitted=(DWORD)(mix_headers_submitted*A3DMIX_BLOCK*mix_subblocks);
 DWORD ahead=submitted-played; /* wrap-safe if both share the same epoch */
 if(ahead> MIX_BUFFERS*A3DMIX_BLOCK*MIX_SUBBLOCKS_MAX*2u){
  if(mix_latency_trace)mix_pos_unsupported++;
  return 0;
 }
 if(ahead_out)*ahead_out=ahead;
 if(mix_latency_trace){
  if(ahead<mix_playback_ahead_min_frames)mix_playback_ahead_min_frames=ahead;
  if(ahead>mix_playback_ahead_max_frames)mix_playback_ahead_max_frames=ahead;
  mix_playback_ahead_total_frames+=ahead;mix_pos_samples++;
 }
 return 1;
}
/* Optional queue governor. Fixed release launchers disable it to keep six headers. */
static void mix_update_adaptive(unsigned queued,int just_underran){
 if(!mix_adaptive||!mix_tick)return;
 DWORD now=mix_tick();
 if(just_underran){
  /* Recover immediately, then hold the raised target long enough to observe
   * host scheduling jitter before considering another reduction. */
  unsigned old=mix_target_headers;
  if(mix_target_headers<mix_queue_limit){
   mix_target_headers+=2u;
   if(mix_target_headers>mix_queue_limit)mix_target_headers=mix_queue_limit;
  }
  if(mix_target_headers!=old)mix_adjust_up++;
  mix_last_underrun_ms=now;
  mix_last_adjust_ms=now;
  return;
 }
 (void)queued;
 /* First reduction after twelve seconds; never reduce within 20 seconds of
  * starvation. This is an intentionally conservative research governor. */
 if(mix_target_headers>mix_min_headers &&
    (DWORD)(now-mix_last_adjust_ms)>=12000u &&
    (DWORD)(now-mix_last_underrun_ms)>=20000u){
  mix_target_headers--;mix_adjust_down++;mix_last_adjust_ms=now;
 }
}
/* v0.6.5: Advise the governor when playable audio is almost gone.
 * A single reported position is not trustworthy on all Wine/WinMM devices:
 * demand two consecutive warnings, at most once per 1000 ms. Bad or
 * unsupported positions never influence scheduling. Rendering still uses
 * completed-header flags and does not seek/replace pending samples. */
static void mix_watch_headroom(unsigned queued,int valid,DWORD ahead){
 if(!mix_adaptive||!mix_tick||!mix_headers_submitted||!valid){
  mix_low_headroom_streak=0;return;
 }
 DWORD now=mix_tick();
 unsigned header_frames=A3DMIX_BLOCK*mix_subblocks;
 if(queued<=1u && ahead<header_frames &&
    mix_headers_submitted>=mix_start_headers*3u){
  mix_low_headroom_samples++;
  if(mix_low_headroom_streak<3u)mix_low_headroom_streak++;
  if(mix_low_headroom_streak>=2u &&
     (DWORD)(now-mix_last_early_recovery_ms)>=1000u &&
     mix_target_headers<mix_queue_limit){
   mix_target_headers++;
   mix_adjust_up++;mix_early_recoveries++;
   mix_last_early_recovery_ms=now;
   mix_last_underrun_ms=now;mix_last_adjust_ms=now;
   mix_low_headroom_streak=0;
  }
 }else mix_low_headroom_streak=0;
}
/* Own waveOut submission and buffer reuse; never submit a buffer still owned by the device. */
/* Worker state machine:
 *  (1) inspect WHDR_DONE across the header pool, release completed ownership;
 *  (2) optionally query playback position OUTSIDE mix_cs (advisory only);
 *  (3) render one 256-frame subblock at a time, holding the mixer lock only
 *      for operations that read/write mutable Source/voice state;
 *  (4) submit prepared headers to WaveOut and wait for completion notification.
 * MIX_BUFFERS is capacity, not the fixed number queued; the normal target is
 * set by the launcher. Never refill a header while WinMM still owns it.
 * Position polling every fourth worker wake was experimentally necessary for
 * Alice 2011 dialogue on the tested Windows host, not universally proven to
 * fix WinMM internals. Sleep(0)/Sleep(1) did not reproduce the benefit.
 * See Docs/WAVEOUT_WORKER_CONTRACT.md for actual evidence and caveats. */
static DWORD WINAPI mixer_thread_run(void*ctx){
 (void)ctx;
 while(mix_running){
  /* The 12 prepared headers are a reusable POOL, not a request to render
   * 12 headers of future game audio immediately.  Count the in-flight
   * waveOut headers before rendering anything. */
  unsigned queued=0;
  for(unsigned j=0;j<MIX_BUFFERS;j++){
   if(!(*(volatile DWORD*)&mix_headers[j].dwFlags&WHDR_DONE)){
    queued++;
    if(!mix_header_outstanding[j])mix_header_flags_anomalies++;
   }else if(mix_header_outstanding[j]){
    mix_header_outstanding[j]=0;
    mix_completed_headers++;
   }
  }
  if(queued>mix_queue_highwater)mix_queue_highwater=queued;
  int underrun=(mix_headers_submitted && queued==0 && mix_last_queue_nonzero);
  if(underrun){mix_queue_empty_events++;mix_metric_event(1u,queued);}
  mix_last_queue_nonzero=(queued!=0);
  mix_update_adaptive(queued,underrun);
  staff_poll_marks(&mixer);
  /* Always use the same wake cadence for poll vs scheduling control.
   * Position queries run OUTSIDE the mixer lock, never alter PCM/queue. */
  if(((mix_poll_timeouts+mix_event_wakes)&(mix_position_interval-1u))==0u){
   if(mix_position_probe){
    DWORD ahead=0;
    long long begin=0,end=0;
    if(mix_profile_probe&&mix_qpc)mix_qpc(&begin);
    mix_position_probe_calls++;
    int valid=mix_sample_playback_position(&ahead);
    if(valid){mix_position_probe_valid++;mix_position_consecutive_errors=0;}
    else{
     mix_position_probe_invalid++;
     if(mix_position_consecutive_errors<0xffffffffu)mix_position_consecutive_errors++;
     if(mix_position_consecutive_errors>mix_position_max_consecutive_errors)
      mix_position_max_consecutive_errors=mix_position_consecutive_errors;
    }
    mix_watch_headroom(queued,valid,ahead);
    if(mix_profile_probe&&mix_qpc&&mix_qpc(&end)&&end>=begin){
     DWORD us=(DWORD)(1000000.0*(double)(end-begin)/(double)mix_qpc_freq);
     if(us>mix_probe_max_us)mix_probe_max_us=us;
     mix_probe_total_us+=us;
    }
   }else if(mix_schedule_test){
    Sleep(mix_schedule_test==1?0u:1u);
   }
  }
  for(unsigned i=0;i<MIX_BUFFERS;i++){
   if(queued>=mix_target_headers)break;

   if(!mix_running)break;
   WaveHeader*h=&mix_headers[i];
   /* All headers start with DONE until their first submission. */
   if(!(*(volatile DWORD*)&h->dwFlags&WHDR_DONE))continue;
   /* Keep individual rendering blocks small for HRTF DSP, but group their
    * resulting samples into fewer, longer WaveOut submissions. The mixer
    * lock is released between subblocks so the game can refill its DMA ring. */
   for(unsigned sub=0;sub<mix_subblocks;sub++){
   if(mix_snapshot_mode){
    mix_render_snapshot(mix_pcm[i]+sub*A3DMIX_BLOCK*4u);
    mix_pcm_boundary_check(mix_pcm[i]+sub*A3DMIX_BLOCK*4u);
    continue;
   }
   mix_enter();
   mix_measure_listener_age();
   DWORD old_cursor[A3DMIX_VOICES];
   for(unsigned vi=0;vi<A3DMIX_VOICES;vi++){
    A3DMixVoice*v=mixer.v[vi];
    old_cursor[vi]=v?(DWORD)v->cursor*(v->channels*(v->bits/8u)):0;
   }
   long long started=0,stopped=0;
   if(mix_qpc)mix_qpc(&started);
   for(unsigned dv=0;dv<A3DMIX_VOICES;dv++){A3DMixVoice *v=mixer.v[dv];if(v&&v->active&&v->pcm&&v->channels&&v->bits){unsigned nf=v->bytes/(v->channels*(v->bits/8u));if(nf){int val=a3dmix_sample_at(v,((unsigned)v->cursor)%nf);DWORD a=(DWORD)(val<0?-val:val);if(a>diag_input_peak)diag_input_peak=a;}}}
   a3dmix_render(&mixer,mix_pcm[i]+sub*A3DMIX_BLOCK*4u,A3DMIX_BLOCK);
   mix_pcm_boundary_check(mix_pcm[i]+sub*A3DMIX_BLOCK*4u);
   staff_sample(&mixer);
   diag_block(mix_pcm[i]+sub*A3DMIX_BLOCK*4u,A3DMIX_BLOCK*4u);
   if(mix_qpc&&mix_qpc(&stopped)&&stopped>=started){
    /* Report DSP cost without writing files on the realtime thread.
     * 256 frames at 48 kHz last 5333 us; 10 ms indicates serious lag. */
    DWORD us=(DWORD)(1000000.0*(double)(stopped-started)/(double)mix_qpc_freq);
    if(us>mix_render_us_max)mix_render_us_max=us;
    if(us>=5333u)mix_slow_5ms++;
    if(us>=10000u)mix_slow_10ms++;
   }
   for(unsigned vi=0;vi<A3DMIX_VOICES;vi++){
    A3DMixVoice*v=mixer.v[vi];if(!v||!v->owner||!v->bytes)continue;
    Source*s=(Source*)v->owner;
    unsigned old=old_cursor[vi]%v->bytes;
    unsigned now=((DWORD)v->cursor*(v->channels*(v->bits/8u)))%v->bytes;
    for(DWORD ev=0;ev<s->event_count;ev++){
     DWORD point=s->event_codes[ev];HANDLE hnd=s->event_handles[ev];
     if(!hnd)continue;
     if(point==0xffffffffUL){
      if(v->ended)SetEvent(hnd);
     }else if(point<v->bytes && old!=now &&
       ((old<now && old<=point && point<now) ||
        (old>now && (point>=old || point<now)))){
       /* A3D's SDK accepts byte-offset event points. Experimental cursor
        * notifications are signalled after crossing the registered point. */
       SetEvent(hnd);
     }
    }
    /* Signal STOP only once, even if the mixer keeps an inactive voice. */
    if(v->ended){v->ended=0;}
   }
   mix_leave();
   }
   h->dwFlags&=~WHDR_DONE;
   DWORD e=wwrite(mix_waveout,h,sizeof(*h));
   if(e){sr_logu("A3D.Mixer.waveOutWrite.error",e);InterlockedExchange(&mix_running,0);break;}
   mix_header_outstanding[i]=1;
   queued++;
   mix_headers_submitted++;
   if(queued>mix_queue_highwater)mix_queue_highwater=queued;
   mix_last_queue_nonzero=1;
  }
  if(mix_event_mode && mix_wave_event){
   /* Timed wait covers Wine hosts that fail to signal completion events.
    * Events avoid systematically wasting the 2 ms polling window. */
   if(WaitForSingleObject(mix_wave_event,2u)==0u)mix_event_wakes++;
   else mix_poll_timeouts++;
  }else Sleep(2);
 }
 return 0;
}
static unsigned sr_play_active_policy(void);
/* Read bounded environment controls and start the one shared output device and worker. */
static int mixer_start(void){
 if(mix_waveout)return 1;
 if(!load_winmm())return 0;
 /* This selection is intentionally made only when the output device starts;
  * modifying the number of samples in a prepared waveOut header is unsafe. */
 {
  char opt[8]={0};DWORD n=GetEnvironmentVariableA("A3D_WAVEOUT_SUBBLOCKS",opt,sizeof(opt));
  mix_subblocks=(n==1 && opt[0]=='1')?1u:(n==1 && opt[0]=='4')?4u:2u;
 }
 /* Keep the default ahead latency near 32ms, independent of header size.
  * To diagnose hostile Wine/PipeWire scheduling, override with a count
  * from 2 through 12; higher values reduce scheduling pressure but can
  * reintroduce stale DMA-ring playback. */
 mix_queue_limit=(mix_subblocks==1u)?6u:((mix_subblocks==4u)?2u:3u);
 {
  char opt[8]={0};DWORD n=GetEnvironmentVariableA("A3D_WAVEOUT_QUEUE_HEADERS",opt,sizeof(opt));
  if(n==1&&opt[0]>='2'&&opt[0]<='9')mix_queue_limit=(unsigned)(opt[0]-'0');
  else if(n==2&&opt[0]=='1'&&opt[1]>='0'&&opt[1]<='2')
   mix_queue_limit=10u+(unsigned)(opt[1]-'0');
 }
 mix_setup_clock();
 /* Off by default; a user's existing known-good launchers behave exactly
  * like v0.6.3 unless they explicitly enable the experiment. */
 {
  char opt[8]={0};DWORD n=GetEnvironmentVariableA("A3D_LATENCY_TRACE",opt,sizeof(opt));
  mix_latency_trace=(n==1 && opt[0]=='1');
  n=GetEnvironmentVariableA("A3D_WAVEOUT_ADAPTIVE",opt,sizeof(opt));
  mix_adaptive=(n==1 && opt[0]=='1');
  /* Reliability CANDIDATE: position polling ON by default, independent of
   * tracing; user-proven successful condition in tests 2 and 5.
   * Unlike A3D_WAVEOUT_PLAY_CURSOR, this is advisory, not a DMA cursor. */
  mix_position_probe=1;
  mix_listener_age_probe=mix_latency_trace?1:0;
  char probe[8]={0};
  n=GetEnvironmentVariableA("A3D_WAVEOUT_POSITION_PROBE",probe,sizeof(probe));
  if(n==1u&&(probe[0]=='0'||probe[0]=='1'))
   mix_position_probe=(probe[0]=='1')?1:0;
  char age[8]={0};
  n=GetEnvironmentVariableA("A3D_LISTENER_AGE_PROBE",age,sizeof(age));
  if(n==1u&&(age[0]=='0'||age[0]=='1'))
   mix_listener_age_probe=(age[0]=='1')?1:0;
  /* Parse only supported power-of-two wake periods, default four. */
  mix_position_interval=4u;
  char interval[8]={0};n=GetEnvironmentVariableA("A3D_WAVEOUT_POSITION_INTERVAL",interval,sizeof(interval));
  if(n==1u&&(interval[0]=='1'||interval[0]=='2'||interval[0]=='4'||interval[0]=='8'))
   mix_position_interval=(unsigned)(interval[0]-'0');
  if(n==2u&&interval[0]=='1'&&interval[1]=='6')mix_position_interval=16u;
  mix_schedule_test=0;
  char sched[12]={0};n=GetEnvironmentVariableA("A3D_WAVEOUT_SCHEDULE_TEST",sched,sizeof(sched));
  if(n==5u&&sched[0]=='y'&&sched[1]=='i'&&sched[2]=='e'&&sched[3]=='l'&&sched[4]=='d')mix_schedule_test=1;
  if(n==6u&&sched[0]=='s'&&sched[1]=='l'&&sched[2]=='e'&&sched[3]=='e'&&sched[4]=='p'&&sched[5]=='1')mix_schedule_test=2;
  /* Scheduling controls are meaningful only if polling has been disabled. */
  if(mix_position_probe)mix_schedule_test=0;
  char profile[8]={0};n=GetEnvironmentVariableA("A3D_WAVEOUT_PROFILE",profile,sizeof(profile));
  mix_profile_probe=(n==1u&&profile[0]=='1'&&mix_qpc&&mix_qpc_freq>0)?1:0;
  mix_metrics_path[0]=0;
  n=GetEnvironmentVariableA("A3D_WAVEOUT_METRICS_FILE",mix_metrics_path,sizeof(mix_metrics_path));
  if(n==0||n>=sizeof(mix_metrics_path))mix_metrics_path[0]=0;
  mix_position_probe_calls=0;mix_position_probe_valid=0;mix_position_probe_invalid=0;
  mix_probe_max_us=0;mix_probe_total_us=0;
  mix_completed_headers=0;mix_header_flags_anomalies=0;
  mix_position_consecutive_errors=0;mix_position_max_consecutive_errors=0;
  for(unsigned j=0;j<MIX_BUFFERS;j++)mix_header_outstanding[j]=0;
  mix_pcm_boundary_max_step=0;mix_pcm_boundary_large_steps=0;mix_pcm_boundary_blocks=0;
  mix_last_pcm_left=0;mix_last_pcm_right=0;mix_last_pcm_valid=0;
  mix_metric_event_count=0;mix_metric_event_next=0;
  mix_min_headers=mix_queue_limit;
  mix_start_headers=mix_queue_limit;
  if(mix_adaptive){
   /* A distinct start target lets a low-latency profile begin with 4
    * small headers while retaining 8 as an emergency ceiling. */
   char initial[8]={0};n=GetEnvironmentVariableA("A3D_WAVEOUT_START_HEADERS",initial,sizeof(initial));
   unsigned start=0;
   if(n==1&&initial[0]>='2'&&initial[0]<='9')start=(unsigned)(initial[0]-'0');
   else if(n==2&&initial[0]=='1'&&initial[1]>='0'&&initial[1]<='2')
    start=10u+(unsigned)(initial[1]-'0');
   if(start>=2u&&start<=mix_queue_limit)mix_start_headers=start;
   char floor[8]={0};n=GetEnvironmentVariableA("A3D_WAVEOUT_MIN_HEADERS",floor,sizeof(floor));
   unsigned value=0;
   if(n==1&&floor[0]>='2'&&floor[0]<='9')value=(unsigned)(floor[0]-'0');
   else if(n==2&&floor[0]=='1'&&floor[1]>='0'&&floor[1]<='2')
    value=10u+(unsigned)(floor[1]-'0');
   if(value>=2u&&value<=mix_start_headers)mix_min_headers=value;
   else mix_min_headers=mix_start_headers;
  }
  mix_target_headers=mix_start_headers;
  mix_last_adjust_ms=mix_tick?mix_tick():0;
  mix_last_underrun_ms=mix_last_adjust_ms;
  mix_adjust_up=0;mix_adjust_down=0;
  mix_early_recoveries=0;mix_low_headroom_samples=0;
  mix_low_headroom_streak=0;
  /* Nonzero initial timestamp enforces the first warning cooldown. */
  mix_last_early_recovery_ms=mix_last_adjust_ms;
 }
 mix_listener_update_at=0;mix_listener_age_total_us=0;
 mix_listener_age_max_us=0;mix_listener_age_samples=0;
 mix_pos_samples=0;mix_pos_unsupported=0;
 mix_playback_ahead_total_frames=0;mix_playback_ahead_max_frames=0;
 mix_playback_ahead_min_frames=0xffffffffUL;
 diag_start();
 mix_headers_submitted=0;
 mix_event_wakes=0;mix_poll_timeouts=0;
 mix_render_us_max=0;mix_slow_5ms=0;mix_slow_10ms=0;
 mix_worst_block_cpu_us=0;mix_worst_block_nonrunning_us=0;
 /* Clock was already prepared before adaptive settings were read. */
 {
  char opt[8]={0};GetEnvironmentVariableA("A3D_RENDER_SNAPSHOT",opt,sizeof(opt));
  mix_snapshot_mode=(opt[0]=='1'&&opt[1]==0);
  mix_snapshot_blocks=0;mix_snapshot_stale_commits=0;
  mix_snapshot_scene_copies=0;mix_snapshot_pcm_bytes_max=0;
  mix_snapshot_pcm_total_bytes=0;mix_snapshot_pcm_total_voices=0;
  mix_snapshot_pcm_frames_max=0;
  mix_snapshot_capture_us_max=0;mix_snapshot_commit_us_max=0;
  mix_scene_revision=0;
  if(mix_snapshot_mode){
   a3dmix_init(&mix_render_state);
   a3dmix_zero(&mix_render_scene,sizeof(mix_render_scene));
   a3dmix_zero(mix_shadow_id,sizeof(mix_shadow_id));
   a3dmix_zero(mix_shadow_serial,sizeof(mix_shadow_serial));
   logline("A3D.Render snapshot mode: HRTF/geometry/reverb OUTSIDE game mixer lock");
  }
 }
 mix_queue_highwater=0;
 mix_queue_empty_events=0;
 mix_last_queue_nonzero=0;
 WaveFmt format={1,2,A3DMIX_RATE,A3DMIX_RATE*4u,4,16,0};
 /* Default to event-driven completion under Wine and native Windows.
  * If the backend rejects CALLBACK_EVENT, fall back to the proven polling
  * path. A3D_WAVEOUT_EVENT=0 disables this experimental backend entirely. */
 char event_opt[8]={0};GetEnvironmentVariableA("A3D_WAVEOUT_EVENT",event_opt,sizeof(event_opt));
 mix_event_mode=0;mix_wave_event=0;
 if(event_opt[0]!='0'||event_opt[1]){
  mix_wave_event=CreateEventA(0,0,0,0); /* automatic reset */
  if(mix_wave_event)mix_event_mode=1;
 }
 DWORD e=wopen(&mix_waveout,0xffffffffUL,&format,
               mix_event_mode?(DWORD)mix_wave_event:0u,0u,
               mix_event_mode?A3D_CALLBACK_EVENT:0u);
 if(e&&mix_event_mode){
  CloseHandle(mix_wave_event);mix_wave_event=0;mix_event_mode=0;
  e=wopen(&mix_waveout,0xffffffffUL,&format,0,0,0);
 }
 if(e){mix_waveout=0;sr_logu("A3D.Mixer.waveOutOpen.error",e);return 0;}
 {typedef DWORD (WINAPI *DiagCaps)(DWORD,void*,DWORD);typedef DWORD (WINAPI *DiagVol)(HANDLE,DWORD*);typedef DWORD (WINAPI *DiagID)(HANDLE,DWORD*);
 DiagCaps caps=(DiagCaps)GetProcAddress(winmm_lib,"waveOutGetDevCapsA");DiagVol vol=(DiagVol)GetProcAddress(winmm_lib,"waveOutGetVolume");DiagID id=(DiagID)GetProcAddress(winmm_lib,"waveOutGetID");unsigned char c[52]={0};DWORD value=0;
 if(caps&&!caps((DWORD)mix_waveout,c,sizeof(c))){logline("A3D.Output.device_name");logline((const char*)c+8);}
 if(vol){DWORD r=vol(mix_waveout,&value);sr_logu("A3D.Output.volume_query_result",r);if(!r)sr_logu("A3D.Output.volume_LR",value);}
 if(id&&!id(mix_waveout,&value))sr_logu("A3D.Output.device_id",value);}
 mix_prepared=0;
 for(unsigned i=0;i<MIX_BUFFERS;i++){
  WaveHeader*h=&mix_headers[i];a3dmix_zero(h,sizeof(*h));
  h->lpData=(char*)mix_pcm[i];h->dwBufferLength=A3DMIX_BLOCK*4u*mix_subblocks;
  e=wprep(mix_waveout,h,sizeof(*h));
  if(e){sr_logu("A3D.Mixer.waveOutPrepare.error",e);goto fail;}
  mix_prepared++;h->dwFlags|=WHDR_DONE;
 }
 InterlockedExchange(&mix_running,1);
 mix_thread=CreateThread(0,0,mixer_thread_run,0,0,0);
 if(!mix_thread){InterlockedExchange(&mix_running,0);goto fail;}
 /* ABOVE_NORMAL is deliberately modest: priority scheduling can prevent
  * a heavily loaded OpenGL/demo thread from starving the output worker. */
 char priority_opt[8]={0};GetEnvironmentVariableA("A3D_WAVEOUT_PRIORITY",priority_opt,sizeof(priority_opt));
 int priority=(priority_opt[0]=='0'&&!priority_opt[1])?0:
              (priority_opt[0]=='2'&&!priority_opt[1])?2:1;
 if(priority)SetThreadPriority(mix_thread,priority);
 sr_logu("A3D.Mixer.waveOut.event_mode",(DWORD)mix_event_mode);
 sr_logu("A3D.Mixer.waveOut.thread_priority",(DWORD)priority);
 sr_logu("A3D.Mixer.waveOut.frames_per_header",A3DMIX_BLOCK*mix_subblocks);
 sr_logu("A3D.Mixer.waveOut.total_buffered_frames",A3DMIX_BLOCK*mix_subblocks*MIX_BUFFERS);
 sr_logu("A3D.Mixer.waveOut.queue_limit_headers",mix_queue_limit);
 sr_logu("A3D.Latency.adaptive_enabled",(DWORD)mix_adaptive);
 sr_logu("A3D.Latency.adaptive_min_headers",mix_min_headers);
 sr_logu("A3D.Latency.start_headers",mix_start_headers);
 sr_logu("A3D.Latency.trace_enabled",(DWORD)mix_latency_trace);
 sr_logu("A3D.Latency.position_probe_enabled",(DWORD)mix_position_probe);
 sr_logu("A3D.Latency.position_interval_wakes",mix_position_interval);
 sr_logu("A3D.Latency.schedule_test_mode",(DWORD)mix_schedule_test);
 sr_logu("A3D.Latency.listener_age_probe_enabled",(DWORD)mix_listener_age_probe);
 sr_logu("A3D.Mixer.waveOut.queue_limit_frames",A3DMIX_BLOCK*mix_subblocks*mix_queue_limit);
 sr_logu("A3D.Mixer.voice_limit",mixer.voice_limit);
 sr_logu("A3D.Mixer.snapshot_enabled",(DWORD)mix_snapshot_mode);
 logline("A3D.HF7: preserve active Play cursor + lifecycle diagnostics enabled");
 logline("A3D.HF9: adaptive geometry trace cache + A/B bypass enabled");
 sr_logu("A3D.Mixer.active_play_policy",sr_play_active_policy());
 logline("A3D.Mixer started: grouped WaveOut headers, 48kHz stereo device");
 return 1;
fail:
 wreset(mix_waveout);
 for(unsigned i=0;i<mix_prepared;i++)wunprep(mix_waveout,&mix_headers[i],sizeof(WaveHeader));
 wclose(mix_waveout);mix_waveout=0;mix_prepared=0;
 if(mix_wave_event){CloseHandle(mix_wave_event);mix_wave_event=0;}
 mix_event_mode=0;return 0;
}
/* Return samples actually reported played by waveOut (not samples rendered
 * and enqueued by our worker). Quake III uses this to schedule DMA writes.
 * Optional: A3D_WAVEOUT_PLAY_CURSOR=1. An unsupported waveOut position
 * response must NOT corrupt the existing render-cursor fallback. */
static int mixer_played_frames(DWORD*frames){
 if(!mix_waveout||!frames||!wposition)return 0;
 WaveTime t={2u,0u,0u}; /* WinMM TIME_SAMPLES */
 if(wposition(mix_waveout,&t,sizeof(t)))return 0;
 if(t.type==2u){*frames=t.value;return 1;}
 if(t.type==4u){*frames=t.value/4u;return 1;} /* stereo 16-bit output */
 if(t.type==1u){*frames=(DWORD)(((double)t.value*A3DMIX_RATE)/1000.0);return 1;}
 return 0;
}
static int mixer_use_play_cursor(void){
 static int choice=-1;
 if(choice<0){char opt[8]={0};GetEnvironmentVariableA("A3D_WAVEOUT_PLAY_CURSOR",opt,sizeof(opt));choice=(opt[0]=='1' && opt[1]==0)?1:0;}
 return choice;
}
/* Called only when there can be no racing call from a game thread.
 * If the thread doesn't terminate, intentionally retain its resources. */
/* Stop the worker before releasing device buffers and source state. */
/* Teardown contract: stop worker before unpreparing WaveOut headers or
 * releasing PCM/Source storage. Optional metrics are flushed outside the
 * realtime worker. Avoid waiting while holding the mixer critical section. */
static void mixer_shutdown(void){
 if(!mix_waveout)return;
 InterlockedExchange(&mix_running,0);
 if(mix_wave_event)SetEvent(mix_wave_event);
 if(mix_thread){
  DWORD result=WaitForSingleObject(mix_thread,5000);
  if(result!=0){logline("A3D.Mixer thread failed to stop; resources retained");return;}
  CloseHandle(mix_thread);mix_thread=0;
 }
 diag_finish();
 staff_dump();
 weapon_capture_dump();
 sr_logu("A3D.Mixer.frames_rendered",mixer.frames_rendered);
 sr_logu("A3D.Mixer.waveOut.headers_submitted",mix_headers_submitted);
 sr_logu("A3D.Mixer.waveOut.max_queued_headers",mix_queue_highwater);
 sr_logu("A3D.Mixer.waveOut.queue_empty_events",mix_queue_empty_events);
 sr_logu("A3D.Latency.final_target_headers",mix_target_headers);
 sr_logu("A3D.Latency.adaptive_reductions",mix_adjust_down);
 sr_logu("A3D.Latency.adaptive_recoveries",mix_adjust_up);
 sr_logu("A3D.Latency.early_headroom_recoveries",mix_early_recoveries);
 sr_logu("A3D.Latency.low_headroom_samples",mix_low_headroom_samples);
 if(mix_latency_trace){
  sr_logu("A3D.Latency.listener_position_updates",(DWORD)listener_pos_updates);
  sr_logu("A3D.Latency.listener_orientation6_updates",(DWORD)listener_orientation6_updates);
  sr_logu("A3D.Latency.listener_euler_updates",(DWORD)listener_euler_updates);
  sr_logu("A3D.Latency.listener_velocity_updates",(DWORD)listener_velocity_updates);
  sr_logu("A3D.Latency.listener_recent_age_samples",mix_listener_age_samples);
  sr_logu("A3D.Latency.listener_recent_age_max_us",mix_listener_age_max_us);
  sr_logu("A3D.Latency.listener_recent_age_avg_us",mix_listener_age_samples?
    (DWORD)((double)mix_listener_age_total_us/(double)mix_listener_age_samples):0);
  sr_logu("A3D.Latency.wave_position_samples",mix_pos_samples);
  sr_logu("A3D.Latency.wave_position_unusable",mix_pos_unsupported);
  sr_logu("A3D.Latency.ahead_min_frames",mix_pos_samples?mix_playback_ahead_min_frames:0);
  sr_logu("A3D.Latency.ahead_max_frames",mix_playback_ahead_max_frames);
  sr_logu("A3D.Latency.ahead_avg_frames",mix_pos_samples?
    (DWORD)((double)mix_playback_ahead_total_frames/(double)mix_pos_samples):0);
 }
 sr_logu("A3D.Mixer.waveOut.event_wakes",mix_event_wakes);
 sr_logu("A3D.Mixer.waveOut.poll_timeouts",mix_poll_timeouts);
 sr_logu("A3D.Latency.position_probe_calls",mix_position_probe_calls);
 sr_logu("A3D.Latency.position_probe_valid",mix_position_probe_valid);
 sr_logu("A3D.Latency.position_probe_invalid",mix_position_probe_invalid);
 sr_logu("A3D.Mixer.waveOut.completed_headers",mix_completed_headers);
 sr_logu("A3D.Mixer.waveOut.header_flag_anomalies",mix_header_flags_anomalies);
 sr_logu("A3D.Mixer.pcm_boundary_large_steps",mix_pcm_boundary_large_steps);
 sr_logu("A3D.Mixer.DSP.max_block_us",mix_render_us_max);
 if(mix_latency_trace){
  sr_logu("A3D.Mixer.DSP.worst_block_thread_cpu_us",mix_worst_block_cpu_us);
  sr_logu("A3D.Mixer.DSP.worst_block_nonrunning_est_us",mix_worst_block_nonrunning_us);
  sr_logu("A3D.Mixer.DSP.thread_cpu_time_available",(DWORD)(mix_get_thread_times!=0));
 }
 sr_logu("A3D.Mixer.snapshot.blocks",mix_snapshot_blocks);
 sr_logu("A3D.Mixer.snapshot.stale_commits",mix_snapshot_stale_commits);
 sr_logu("A3D.Mixer.snapshot.scene_copies",mix_snapshot_scene_copies);
 sr_logu("A3D.Mixer.snapshot.max_pcm_capture_bytes",mix_snapshot_pcm_bytes_max);
 sr_logu("A3D.Mixer.snapshot.max_pcm_capture_frames",mix_snapshot_pcm_frames_max);
 sr_logu("A3D.Mixer.snapshot.avg_pcm_capture_bytes",mix_snapshot_pcm_total_voices?
  (DWORD)(mix_snapshot_pcm_total_bytes/mix_snapshot_pcm_total_voices):0u);
 sr_logu("A3D.Mixer.snapshot.voices_captured",mix_snapshot_pcm_total_voices);
 sr_logu("A3D.Mixer.snapshot.capture_max_us",mix_snapshot_capture_us_max);
 sr_logu("A3D.Mixer.snapshot.commit_max_us",mix_snapshot_commit_us_max);
 sr_logu("A3D.Mixer.DSP.blocks_over_5333us",mix_slow_5ms);
 sr_logu("A3D.Mixer.DSP.blocks_over_10000us",mix_slow_10ms);
 sr_logu("A3D.Mixer.voice_peak",mixer.voice_peak);
 sr_logu("A3D.Mixer.voice_additions",mixer.voice_additions);
 sr_logu("A3D.Mixer.voice_rejections",mixer.voice_rejections);
 sr_logu("A3D.Mixer.HF9.geometry_enabled",mixer.geometry_enabled);
 sr_logu("A3D.Mixer.HF9.retrace_blocks",mixer.geometry_retrace_blocks);
 sr_logu("A3D.Mixer.HF9.geometry_trace_calls",mixer.geometry_trace_calls);
 sr_logu("A3D.Mixer.HF9.geometry_cache_hits",mixer.geometry_cache_hits);
 sr_logu("A3D.Mixer.HF9.geometry_deferred_revisions",mixer.geometry_deferred_revisions);
 sr_logu("A3D.Mixer.HF9.geometry_disabled_voice_blocks",mixer.geometry_disabled_voice_blocks);
 sr_logu("A3D.Mixer.source_stop_calls",(DWORD)sr_stop_calls);
 sr_logu("A3D.Mixer.source_stop_noops",(DWORD)sr_stop_noop_calls);
 sr_logu("A3D.Mixer.source_stop_active",(DWORD)sr_stop_active_calls);
 sr_logu("A3D.Mixer.source_stop_ended",(DWORD)sr_stop_inactive_registered_calls);
 sr_logu("A3D.Mixer.source_play_active_restarts",(DWORD)sr_play_active_restarts);
 sr_logu("A3D.Mixer.source_play_active_requests",(DWORD)sr_play_active_requests);
 sr_logu("A3D.Mixer.source_play_preserved_looped",(DWORD)sr_play_preserved_looped);
 sr_logu("A3D.Mixer.source_play_preserved_single",(DWORD)sr_play_preserved_single);
 sr_logu("A3D.Mixer.source_play_restarts_changed_pcm",(DWORD)sr_play_restarts_changed_pcm);
 sr_logu("A3D.Mixer.source_play_restarts_mode_change",(DWORD)sr_play_restarts_mode_change);
 sr_logu("A3D.Mixer.source_play_restarts_other",(DWORD)sr_play_restarts_legacy);
 sr_logu("A3D.Mixer.limiter_active_frames",mixer.limiter_active_frames);
 sr_logu("A3D.Clarity.duck_frames",mixer.clarity_duck_frames);
 sr_logu("A3D.Mixer.limiter_peak_events",mixer.clip_events);
 /* All worker counters are stable after the worker thread is joined. */
 mix_write_metrics();
 wreset(mix_waveout);
 for(unsigned i=0;i<mix_prepared;i++)wunprep(mix_waveout,&mix_headers[i],sizeof(WaveHeader));
 wclose(mix_waveout);mix_waveout=0;mix_prepared=0;
 if(mix_wave_event){CloseHandle(mix_wave_event);mix_wave_event=0;}
 mix_event_mode=0;
 logline("A3D.Mixer stopped");
}
static void sr_audio_stop(Source*s){
 /* Quake III 1.17 calls Stop on many already-idle A3D objects on every
  * game update (118,614 calls in one 38 s HF5 trace). Do NOT acquire the
  * global mixer mutex for a voice which is not in the renderer's pool:
  * that mutex is held for up to a whole HRTF block. The game is allowed to
  * call Stop repeatedly, so the detached state must be an inexpensive no-op.
  * All structural writes to in_mixer occur under mix_cs; Play and Stop are
  * invoked sequentially by normal A3D clients. */
 if(!s->in_mixer){InterlockedIncrement(&sr_stop_noop_calls);return;}
 mix_enter();
 if(s->in_mixer){
  if(s->mix.active)InterlockedIncrement(&sr_stop_active_calls);
  else InterlockedIncrement(&sr_stop_inactive_registered_calls);
  s->mix.active=0;
  a3dmix_remove(&mixer,&s->mix);
  InterlockedExchange(&s->in_mixer,0);
 }else InterlockedIncrement(&sr_stop_noop_calls);
 mix_leave();
}
/* A forward declaration is used by the mixer startup log. */
/* HF7: A3D Play requests are issued to the resource manager, not a command
 * to rebuild the voice and start sample 0 on *every* request. Quake III
 * generated 2,998 active Play calls in its HF6 trace; prior builds reset the
 * HRTF history and PCM cursor for all 2,998, audibly truncating sounds.
 *
 * Policy 0: legacy always-restart (A/B or title compatibility).
 * Policy 1: preserve unchanged mode on already-playing LOOPED sources.
 * Policy 2 (default): also preserve SINGLE sources whose PCM data is
 * unchanged since the prior Play. A caller that rewrites a one-shot PCM
 * before Play will still deliberately retrigger its newly loaded sound.
 * All policies permit Stop+Play, explicit reposition+Play (below), and
 * Play(mode change) to restart. Note that some games retrigger identical
 * one-shots without Stop; policy 1 or 0 is the escape hatch for them.
 */
static unsigned sr_play_active_policy(void){
 static int choice=-1;
 if(choice<0){
  char mode[8]={0};DWORD n=GetEnvironmentVariableA("A3D_PLAY_ACTIVE_POLICY",mode,sizeof(mode));
  choice=(n==1&&mode[0]=='0')?0:(n==1&&mode[0]=='1')?1:2;
 }
 return (unsigned)choice;
}
static int sr_play_can_preserve(unsigned policy,int active,int same_mode,int looped,int pcm_unchanged,int positioned){
 if(!active||!same_mode||positioned||policy==0u)return 0;
 if(looped)return 1;
 return (policy>=2u&&pcm_unchanged);
}
/* Bind source playback to the shared mixer and classify known PCM signatures. */
static HRESULT sr_audio_play(Source*s,int looping){
 if(!s->has_format||!s->pcm||s->locked||!s->wave_size)return E_FAIL;
 /* Lazy shadow allocation. Only the game-facing PCM buffer is writable. */
 if(!s->play_pcm){
  s->play_pcm=(unsigned char*)HeapAlloc(GetProcessHeap(),0,s->wave_size);
  if(!s->play_pcm)return E_OUTOFMEMORY;
 }
 mix_enter();
 /* Avoid a large PCM copy, decoder reset, and sample-cursor rewind when the
  * resource manager simply renews an active source's play request. Unlock
  * already commits changed streaming PCM to the separate rendering buffer.
  * Check while holding mix_cs: audio worker and source transitions share it. */
 if(s->in_mixer && s->mix.active){
  unsigned mode=looping?1u:0u;
  unsigned same_mode=(s->mix.looping==mode);
  unsigned unchanged=(s->last_play_pcm_serial==s->pcm_update_serial);
  unsigned policy=sr_play_active_policy();
  InterlockedIncrement(&sr_play_active_requests);
  if(sr_play_can_preserve(policy,1,same_mode,mode,unchanged,s->play_repositioned)){
   staff_record(STAFF_EVENT_KEEP,s->sample_id,s->staff_pcm_sig,staff_milli(s->gain),staff_milli(s->priority),1,0,(DWORD)mode);
   if(mode)InterlockedIncrement(&sr_play_preserved_looped);
   else InterlockedIncrement(&sr_play_preserved_single);
   mix_leave();return S_OK;
  }
  staff_record(STAFF_EVENT_RESTART,s->sample_id,s->staff_pcm_sig,staff_milli(s->gain),staff_milli(s->priority),1,0,((DWORD)!same_mode<<1)|(DWORD)!unchanged);
  if(!same_mode)InterlockedIncrement(&sr_play_restarts_mode_change);
  else if(!unchanged)InterlockedIncrement(&sr_play_restarts_changed_pcm);
  else InterlockedIncrement(&sr_play_restarts_legacy);
 }
 sr_copy(s->play_pcm,s->pcm,s->wave_size);
 if(staff_enabled()||mixer.weapon_clarity)
  s->staff_pcm_sig=staff_fingerprint(s->play_pcm,s->wave_size);
 if(!mixer_start()){mix_leave();return E_FAIL;}
 /* Copy raw source PCM for v0.6.11 analysis, never on the audio worker. */
 weapon_capture_play(s->sample_id,s->play_pcm,s->wave_size,s->format.rate,
  s->format.channels,s->format.bits,s->gain,s->priority,s->staff_pcm_sig);
 s->waveout_play_valid=0;
 s->dma_clock_valid=0;s->dma_clock_base=0;
 {
  char dma_opt[8]={0};
  GetEnvironmentVariableA("A3D_Q3_DMA_CLOCK",dma_opt,sizeof(dma_opt));
  if(dma_opt[0]=='1'&&dma_opt[1]==0&&mix_qpc&&mix_qpc(&s->dma_clock_origin)){
   s->dma_clock_valid=1;
   logline("A3D.Mixer independent QPC DMA clock active");
  }
 }
 if(mixer_use_play_cursor()){
  DWORD now=0;
  if(mixer_played_frames(&now)){
   s->waveout_play_origin=now;
   s->waveout_play_valid=1;
   logline("A3D.Mixer WaveOut playback-cursor mode active");
  }else logline("A3D.Mixer WaveOut playback position unavailable; render-cursor fallback");
 }
 /* Restarting an already playing source legitimately truncates the old
  * waveform. Count this independently from explicit Stop, so footstep
  * truncation can be attributed to real game actions rather than guesses. */
 if(s->in_mixer && s->mix.active)
  InterlockedIncrement(&sr_play_active_restarts);
 A3DMixVoice*v=&s->mix;
 s->render_serial++;
 a3dmix_voice_init(v);
 v->pcm=s->play_pcm;v->bytes=s->wave_size;
 v->rate=s->format.rate;v->channels=s->format.channels;v->bits=s->format.bits;
 for(int i=0;i<3;i++)v->pos[i]=s->pos[i];
 v->gain=s->gain;v->pitch=s->pitch;v->looping=looping?1:0;v->active=1;v->owner=s;
 v->pan_values[0]=s->pan_values[0];v->pan_values[1]=s->pan_values[1];
 v->pan_set=s->pan_set;
 v->weapon_protected=mixer.weapon_clarity && a3d_weapon_is_known(s->staff_pcm_sig);
 for(int i=0;i<3;i++)v->vel[i]=s->vel[i];
 v->min_dist=s->minmax[0];v->max_dist=s->minmax[1];v->max_distance_behavior=s->minmax_mode;
 v->distance_scale=s->distance;v->doppler_scale=s->doppler;v->head_relative=(s->transform_mode==1u);
 s->last_play_pcm_serial=s->pcm_update_serial;
 s->play_repositioned=0;

 mixer.scene=&a3d_scene;
 for(int i=0;i<3;i++){mixer.listener[i]=listener.pos[i];mixer.forward[i]=listener.ori[i];mixer.up[i]=listener.ori[i+3];}
 mixer.coords=root.coords;
 mixer.distance_scale=root.distance;mixer.doppler_scale=root.doppler;
 mixer.units_per_meter=root.units;mixer.output_gain=root.gain;
 for(int i=0;i<3;i++)mixer.listener_vel[i]=listener.vel[i];
 mixer.ref_gain=g_ref_gain;mixer.ref_delay=g_ref_delay;
 if(!a3dmix_add(&mixer,v)){
  staff_record(STAFF_EVENT_REJECT,s->sample_id,s->staff_pcm_sig,staff_milli(s->gain),staff_milli(s->priority),0,0,s->wave_size);
  mix_leave();
  /* No blocking file I/O on the frequent Play path. The shutdown aggregate
   * reports all rejected voices, even with detailed logging disabled. */
  if(trace_detail())logline("A3D.Mixer rejected source: maximum active voices");
  return E_FAIL;
 }
 InterlockedExchange(&s->in_mixer,1);
 staff_record(STAFF_EVENT_PLAY,s->sample_id,s->staff_pcm_sig,staff_milli(s->gain),staff_milli(s->priority),1,0,s->wave_size);
 mix_leave();
 /* Previously each Play emitted five separately opened/closed log files.
  * During Quake III demos this is a material source of audio-thread jitter. */
 if(trace_detail()){
  sr_logu("IA3dSource.Play source_id",s->sample_id);
  sr_logu("IA3dSource.Play PCM_bytes",s->wave_size);
  log3("IA3dSource.Play.Position",s->pos[0],s->pos[1],s->pos[2]);
  log3("IA3dSource.Play.Listener",listener.pos[0],listener.pos[1],listener.pos[2]);
  logline("IA3dSource.Play queued on shared realtime mixer");
 }
 return S_OK;
}
static void mixer_update_voice(Source*s){
 mix_enter();for(int i=0;i<3;i++)s->mix.pos[i]=s->pos[i];
 s->mix.gain=s->gain;s->mix.pitch=s->pitch;
 for(int i=0;i<3;i++)s->mix.vel[i]=s->vel[i];
 s->mix.min_dist=s->minmax[0];s->mix.max_dist=s->minmax[1];
 s->mix.max_distance_behavior=s->minmax_mode;
 s->mix.distance_scale=s->distance;s->mix.doppler_scale=s->doppler;
 s->mix.pan_values[0]=s->pan_values[0];s->mix.pan_values[1]=s->pan_values[1];
 s->mix.pan_set=s->pan_set;
 s->mix.head_relative=(s->transform_mode==1u);
 mix_leave();
}
static void mixer_update_listener(void){
 mix_enter();for(int i=0;i<3;i++){
  mixer.listener[i]=listener.pos[i];mixer.forward[i]=listener.ori[i];mixer.up[i]=listener.ori[i+3];
  mixer.listener_vel[i]=listener.vel[i];
 }mixer.coords=root.coords;
 if(mix_listener_age_probe&&mix_qpc)mix_qpc(&mix_listener_update_at);
 mix_leave();
}
static void mixer_update_global(void){
 mix_enter();mixer.distance_scale=root.distance;mixer.doppler_scale=root.doppler;
 mixer.units_per_meter=root.units;mixer.output_gain=root.gain;mix_leave();
}
