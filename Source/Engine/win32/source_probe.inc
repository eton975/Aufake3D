/* v0.5.0 SOURCE COMMENTARY — Per-sound IA3dSource object and PCM buffer lifecycle
 * Implements source creation/state, wave format negotiation, Lock/Unlock and
 * positional-property methods. The mixer gets a playback-side snapshot of streaming
 * buffers so game writes do not temporarily silence audio. Validate allocation sizes
 * and lock offsets before modifying buffer code; preserve locking protocol.
 */
/* IA3dSource COM ABI with PCM storage and shared software spatial playback.
 * The renderer approximates geometry/HRTF behavior; not all vendor methods
 * or cursor events are implemented. See stream_core.h and stream_winmm.inc. */
#include "stream_core.h"
typedef struct Source Source;
typedef struct WaveFmt { WORD tag,channels; DWORD rate,avg_bytes; WORD block_align,bits,extra; } WaveFmt;
typedef struct WaveHeader {char*lpData;DWORD dwBufferLength,dwBytesRecorded,dwUser,dwFlags,dwLoops;void*lpNext;DWORD reserved;} WaveHeader;
struct Source {
 void **vt;volatile long ref;
 DWORD magic,flags,wave_size,wave_pos,render_mode,type,transform_mode;
 unsigned char *pcm;
 unsigned char *play_pcm; /* mixer reads this copy; Miles writes to pcm */
 WaveFmt format;
 DWORD has_format,locked,lock_at,lock_bytes;
 float pos[3],vel[3],angles[3],ori[6],cone[3],minmax[2],gain,pitch,doppler,distance,eq,priority,time,reflect_delay,reflect_gain;
 /* Experimental SDK-style stereo pan, zero-effect until explicitly set. */
 float pan_values[2]; DWORD pan_set;
 DWORD sample_id;
 DWORD staff_pcm_sig,staff_last_gain_milli;
 DWORD minmax_mode;
 DWORD event_codes[8];HANDLE event_handles[8];DWORD event_count;
 /* waveOut prototype state: ownership remains with this source. */
 HANDLE waveout; unsigned char *stereo; DWORD stereo_bytes;
 WaveHeader header;DWORD wave_prepared;
 DWORD resume_after_lock;
 DWORD play_repositioned; /* Rewind / SetWavePosition explicitly requests a new start */
 DWORD render_serial; /* generation for worker-owned snapshots; changed on restart/seek */
 DWORD pcm_update_serial; /* increments when a client commits new samples */
 DWORD last_play_pcm_serial; /* distinguish duplicate Play from changed sample */
 DWORD waveout_play_origin; /* device samples when this voice started */
 DWORD waveout_play_valid; /* only use device position if queried at start */
 long long dma_clock_origin; /* QPC tick counter at Play / reposition */
 DWORD dma_clock_base; /* byte offset into circular ring at origin */
 DWORD dma_clock_valid;
 /* Fixed-size, stateful streaming voice, owned by this COM object. */
 A3DMixVoice mix;
 /* Set only under mixer lock. Allows Stop on an already detached voice
  * to avoid blocking behind expensive HRTF work. */
 volatile long in_mixer;
};
#include "staff_diag.inc"
#include "weapon_signatures_v0612.inc"
#define A3D_FROMWRITECURSOR 1UL
#define A3D_ENTIREBUFFER 2UL
#define MAX_PCM_BYTES (64UL*1024UL*1024UL)
#define E_INVALIDARG ((HRESULT)0x80070057L)
#define E_OUTOFMEMORY ((HRESULT)0x8007000EL)
static void sr_copy(void *dst,const void *src,DWORD n){unsigned char*d=(unsigned char*)dst;const unsigned char*s=(const unsigned char*)src;for(DWORD i=0;i<n;i++)d[i]=s[i];}
static void sr_logu(const char *tag,DWORD value){
 char b[112],hex[]="0123456789abcdef";int p=0;while(*tag&&p<85)b[p++]=*tag++;
 b[p++]=' ';b[p++]='0';b[p++]='x';
 for(int n=7;n>=0;n--)b[p++]=hex[(value>>(n*4))&15];
 b[p]=0;logline(b);
}
static volatile long next_source_id=0;
/* Hotfix 5: Quake III's 87,164 Stop calls in one capture used to open,
 * append and close the diagnostic file EACH time. Count without disk I/O. */
static volatile long sr_stop_calls=0;
/* Aggregated lifecycle diagnostics: no file I/O in game/audio callbacks. */
static volatile long sr_stop_noop_calls=0;
static volatile long sr_stop_active_calls=0;
static volatile long sr_stop_inactive_registered_calls=0;
static volatile long sr_play_active_restarts=0;
/* HF7: active playback requests must not automatically reset a voice. */
static volatile long sr_play_active_requests=0;
static volatile long sr_play_preserved_looped=0;
static volatile long sr_play_preserved_single=0;
static volatile long sr_play_restarts_changed_pcm=0;
static volatile long sr_play_restarts_mode_change=0;
static volatile long sr_play_restarts_legacy=0;
static void sr_audio_stop(Source*s);
static void sr_free_pcm(Source*s){
 sr_audio_stop(s);
 if(s->play_pcm){HeapFree(GetProcessHeap(),0,s->play_pcm);s->play_pcm=0;}
 if(s->pcm){HeapFree(GetProcessHeap(),0,s->pcm);s->pcm=0;}
 s->wave_size=0;s->wave_pos=0;s->pcm_update_serial=0;s->last_play_pcm_serial=0;s->play_repositioned=0;s->locked=0;s->lock_at=0;s->lock_bytes=0;
}

#include "waveout_renderer.inc"
static const DWORD source_magic=0x53524333UL;
static const GUID iid_source=G(0xc398e562,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static void* source_vt[];
static ULONG WINAPI sr_add(Source*s){return (ULONG)InterlockedIncrement(&s->ref);}
static ULONG WINAPI sr_rel(Source*s){long n=InterlockedDecrement(&s->ref);if(n==0){staff_record(STAFF_EVENT_RELEASE,s->sample_id,s->staff_pcm_sig,staff_milli(s->gain),staff_milli(s->priority),0,0,0);sr_free_pcm(s);s->magic=0;HeapFree(GetProcessHeap(),0,s);}return (ULONG)n;}
static HRESULT WINAPI sr_qi(Source*s,const GUID*i,void**o){if(!o)return E_POINTER;*o=0;logguid("IA3dSource.QueryInterface",i);if(eqguid(i,&iid_unk)||eqguid(i,&iid_source)){*o=s;sr_add(s);return S_OK;}return E_NOINTERFACE;}
static HRESULT WINAPI sr_loadfile(Source*s,const char*path){(void)s;(void)path;logline("IA3dSource.LoadWaveFile unsupported");return E_NOTIMPL;}
static HRESULT WINAPI sr_loadwave(Source*s,const void*data,DWORD len){(void)s;(void)data;(void)len;logline("IA3dSource.LoadWaveData unsupported: use SetWaveFormat/AllocateWaveData/Lock");return E_NOTIMPL;}
/* REVIEW NOTE — sr_allocwave: Wave-buffer allocation: validate requested byte count and ensure any prior buffer lifetime is handled safely. */
static HRESULT WINAPI sr_allocwave(Source*s,int len){
 if(!s->has_format){logline("IA3dSource.AllocateWaveData rejected: format missing");return E_FAIL;}
 if(len<=0 || (DWORD)len>MAX_PCM_BYTES){logline("IA3dSource.AllocateWaveData rejected: invalid length");return E_INVALIDARG;}
 sr_free_pcm(s);
 s->pcm=(unsigned char*)HeapAlloc(GetProcessHeap(),8,(DWORD)len);
 if(!s->pcm){logline("IA3dSource.AllocateWaveData: out of memory");return E_OUTOFMEMORY;}
 s->wave_size=(DWORD)len;
 if(s->format.bits==8){for(DWORD i=0;i<s->wave_size;i++)s->pcm[i]=128;}
 sr_logu("IA3dSource.AllocateWaveData bytes",s->wave_size);
 return S_OK;
}
static HRESULT WINAPI sr_freewave(Source*s){sr_free_pcm(s);logline("IA3dSource.FreeWaveData");return S_OK;}
/* REVIEW NOTE — sr_setformat: PCM format negotiation: update sample format only when the incoming structure is well-formed and supported. */
static HRESULT WINAPI sr_setformat(Source*s,const void*fmt){
 if(!fmt)return E_POINTER;
 if(s->pcm){logline("IA3dSource.SetWaveFormat refused: buffer already allocated");return E_FAIL;}
 WaveFmt f={0};
 /* WAVEFORMATEX is 18 bytes, with cbSize at offset 16. The legacy Miles
  * provider may pass the 16-byte PCM WAVEFORMAT structure. Read only the
  * common 16-byte prefix; PCM has no required extension data. */
 sr_copy(&f,fmt,16);
 if(f.tag!=1 || f.channels<1 || f.channels>2 || f.rate<1000 || f.rate>192000 ||
    (f.bits!=8 && f.bits!=16) || f.block_align!=(WORD)(f.channels*(f.bits/8))){
  logline("IA3dSource.SetWaveFormat rejected: unsupported PCM format");return E_INVALIDARG;
 }
 f.extra=0;s->format=f;s->has_format=1;
 sr_logu("IA3dSource.SetWaveFormat rate",f.rate);
 sr_logu("IA3dSource.SetWaveFormat channels",f.channels);
 sr_logu("IA3dSource.SetWaveFormat bits",f.bits);
 return S_OK;
}
static HRESULT WINAPI sr_getformat(Source*s,void*fmt){if(!fmt)return E_POINTER;if(!s->has_format)return E_FAIL;sr_copy(fmt,&s->format,18);return S_OK;}
static DWORD WINAPI sr_wavesize(Source*s){return s->wave_size;}
static HRESULT WINAPI sr_gettype(Source*s,DWORD*type){if(!type)return E_POINTER;*type=s->type;return S_OK;}
/* REVIEW NOTE — sr_lock: Source write lock: Miles receives writable regions; mixer playback state should remain coherent while the game refills audio. */
/* Miles game-facing DMA-style write lock. This API returns sample regions
 * to the caller; the game writes them before sr_unlock publishes the update.
 * Do not expose newly written samples to the asynchronous render worker until
 * the unlock path validates ownership/length and updates the source serial.
 * A rejected nested lock must not create a second writable mapping. */
static HRESULT WINAPI sr_lock(Source*s,DWORD at,DWORD bytes,void**a,DWORD*an,void**b,DWORD*bn,DWORD flags){
 /* Quake III Arena 1.17 locks its entire, contiguous A3D output buffer
  * with the optional second-region outputs set to NULL. Rejecting these
  * NULLs used to return E_POINTER, and Quake's wrapper then incorrectly
  * reported a successful lock and forwarded a garbage DMA pointer to its
  * mixer. Only the first-region outputs are mandatory. */
 if(!a||!an)return E_POINTER;
 *a=0;*an=0;
 if(b)*b=0;
 if(bn)*bn=0;
 if(!s->pcm || !s->wave_size){logline("IA3dSource.Lock rejected: no PCM buffer");return E_FAIL;}
 if(flags & ~(A3D_ENTIREBUFFER|A3D_FROMWRITECURSOR))return E_INVALIDARG;
 if(flags & A3D_ENTIREBUFFER){at=0;bytes=s->wave_size;}
 else {if(flags & A3D_FROMWRITECURSOR)at=s->wave_pos;if(at>=s->wave_size||bytes==0||bytes>s->wave_size)return E_INVALIDARG;}
 DWORD first=s->wave_size-at;
 if(first>bytes)first=bytes;
 /* A ring-wrap really does need two output regions. Do not partially lock
  * a source, alter caller state, or silently truncate the requested data. */
 if(bytes>first && (!b||!bn))return E_POINTER;
 /* Lock's state check and claim must be atomic relative to other callers.
  * Previously the check was outside mix_cs, so concurrent Lock calls could
  * both succeed on the same source. Continue to reject a second Lock rather
  * than silently extending/overwriting a caller's writable region. The
  * render worker reads a separate playback-side PCM snapshot. */
 mix_enter();
 if(s->locked){
  DWORD held_at=s->lock_at,held_bytes=s->lock_bytes;
  mix_leave();
  logline("IA3dSource.Lock rejected: already locked");
  sr_logu("IA3dSource.Lock busy_source",s->sample_id);
  sr_logu("IA3dSource.Lock busy_at",at);
  sr_logu("IA3dSource.Lock busy_bytes",bytes);
  sr_logu("IA3dSource.Lock held_at",held_at);
  sr_logu("IA3dSource.Lock held_bytes",held_bytes);
  return E_FAIL;
 }
 *a=s->pcm+at;*an=first;
 if(bytes>first){*b=s->pcm;*bn=bytes-first;}
 s->locked=1;s->lock_at=at;s->lock_bytes=bytes;
 mix_leave();
 if(trace_detail())sr_logu("IA3dSource.Lock bytes",bytes);
 return S_OK;
}
/* REVIEW NOTE — sr_unlock: Source unlock: commit buffer writes for the real-time mixer without stopping/restarting the playing voice. */
/* Complete the game write transaction. The source lock state, PCM window
 * and render serial determine which bytes can be consumed by the audio worker.
 * For snapshot rendering, stale serials must be discarded rather than
 * committed against a Source that was stopped/released in the meantime. */
static HRESULT WINAPI sr_unlock(Source*s,void*a,DWORD an,void*b,DWORD bn){
 if(!s->locked||!s->pcm)return E_FAIL;
 DWORD first=s->wave_size-s->lock_at;
 if(first>s->lock_bytes)first=s->lock_bytes;
 if(a!=s->pcm+s->lock_at || an!=first ||
    (s->lock_bytes>first?(b!=s->pcm || bn!=s->lock_bytes-first):(b!=0||bn!=0))){
  logline("IA3dSource.Unlock rejected: pointers/lengths differ from Lock");return E_INVALIDARG;
 }
 /* Commit only the changed region. The render thread never reads Miles'
  * writable front buffer, preventing streaming Lock/Unlock from muting it. */
 DWORD hash=2166136261UL;
 int detail=trace_detail();
 mix_enter();
 for(DWORD i=0;i<s->lock_bytes;i++){
  DWORD off=(s->lock_at+i)%s->wave_size;
  unsigned char byte=s->pcm[off];
  if(s->play_pcm)s->play_pcm[off]=byte;
  if(detail){hash^=byte;hash*=16777619UL;}
 }
 s->pcm_update_serial++;
 s->wave_pos=(s->lock_at+s->lock_bytes)%s->wave_size;
 s->locked=0;s->lock_at=0;s->lock_bytes=0;
 mix_leave();
 if(detail){sr_logu("IA3dSource.Unlock source_id",s->sample_id);
  sr_logu("IA3dSource.Unlock checksum_FNV1a",hash);}
 return S_OK;
}
static HRESULT WINAPI sr_play(Source*s,int repeat){return sr_audio_play(s,repeat);}
static HRESULT WINAPI sr_stop(Source*s){
 if(staff_enabled()){staff_record(s->in_mixer?STAFF_EVENT_STOP:STAFF_EVENT_STOP_IDLE,s->sample_id,s->staff_pcm_sig,staff_milli(s->gain),staff_milli(s->priority),s->mix.active,0,0);}
 sr_audio_stop(s);
 InterlockedIncrement(&sr_stop_calls);
 if(trace_detail())logline("IA3dSource.Stop");
 return S_OK;
}
static HRESULT WINAPI sr_rewind(Source*s){
 mix_enter();s->wave_pos=0;s->time=0;s->mix.cursor=0;s->play_repositioned=1;s->render_serial++;
 if(s->waveout_play_valid){DWORD now=0;if(mixer_played_frames(&now))s->waveout_play_origin=now;}
 mix_leave();return S_OK;
}
static HRESULT WINAPI sr_settime(Source*s,float t){if(t<0)return E_INVALIDARG;mix_enter();s->time=t;s->play_repositioned=1;s->render_serial++;if(s->has_format)s->mix.cursor=(double)(t*s->format.rate);
 if(s->dma_clock_valid&&mix_qpc)mix_qpc(&s->dma_clock_origin);
 if(s->wave_size&&s->has_format)
  s->dma_clock_base=((DWORD)(t*s->format.rate)*s->format.block_align)%s->wave_size;
 mix_leave();return S_OK;}
static HRESULT WINAPI sr_gettime(Source*s,float*t){if(!t)return E_POINTER;*t=s->time;return S_OK;}
static HRESULT WINAPI sr_setwavepos(Source*s,DWORD p){if(s->wave_size&&p>=s->wave_size)return E_INVALIDARG;mix_enter();s->wave_pos=p;s->play_repositioned=1;s->render_serial++;if(s->format.block_align)s->mix.cursor=(double)p/s->format.block_align;
 if(s->dma_clock_valid&&mix_qpc)mix_qpc(&s->dma_clock_origin);
 s->dma_clock_base=p;mix_leave();return S_OK;}
static HRESULT WINAPI sr_getwavepos(Source*s,DWORD*p){
 if(!p)return E_POINTER;
 mix_enter();
 /* Quake III's original A3D path expects a hardware-progressing ring cursor.
  * The renderer may jump forward in 256-frame blocks or stall behind Wine.
  * A wall-clock cursor can give the game a stable independent DMA position.
  * Explicit opt-in only, to avoid changing Alice's legacy behaviour. */
 if(s->dma_clock_valid&&s->wave_size&&mix_qpc&&mix_qpc_freq>0){
  long long now=0;
  if(mix_qpc(&now)&&now>=s->dma_clock_origin){
   double elapsed=(double)(now-s->dma_clock_origin)/((double)mix_qpc_freq);
   double frames=elapsed*(double)s->format.rate;
   if(frames>=0.0&&frames<2147483647.0){
    DWORD advanced=(DWORD)frames*s->format.block_align;
    *p=(advanced+s->dma_clock_base)%s->wave_size;
    mix_leave();return S_OK;
   }
  }
 }
 /* Quake III's software DMA queries this frequently. The old cursor was
  * advanced as soon as the worker RENDERED audio, sometimes >100 ms ahead
  * of playback on Wine. Opt-in hardware timing instead prevents the game
  * from painting PCM against a future rather than audible ring position.
  * The default remains the old render cursor for Alice compatibility. */
 if(mixer_use_play_cursor()&&s->waveout_play_valid&&s->mix.active&&s->wave_size){
  DWORD now=0;
  if(mixer_played_frames(&now)){
   DWORD delta=now-s->waveout_play_origin; /* unsigned wrap-safe */
   double source_frames=((double)delta*(double)s->format.rate)/A3DMIX_RATE;
   if(source_frames<4294967296.0){
    DWORD off=((DWORD)source_frames*s->format.block_align)%s->wave_size;
    *p=off;mix_leave();return S_OK;
   }
  }
 }
 /* A3D position is a byte offset INSIDE the circular DMA buffer. Never
  * expose a monotonically increasing absolute byte count: early Quake III
  * assumes the value has already wrapped, as real DirectSound hardware does. */
 *p=s->wave_size ? ((DWORD)(s->mix.cursor*s->format.block_align)%s->wave_size) : 0u;
 mix_leave();return S_OK;
}
/* REVIEW NOTE — sr_setpos: Source world position: updates listener-relative rendering and can expose coordinate-system errors. */
static HRESULT WINAPI sr_setpos(Source*s,float a,float b,float c){s->pos[0]=a;s->pos[1]=b;s->pos[2]=c;mixer_update_voice(s);if(trace_detail())log3("IA3dSource.SetPosition3f",a,b,c);return S_OK;}
static HRESULT WINAPI sr_getpos(Source*s,float*a,float*b,float*c){return copy3out(s->pos,a,b,c);}
static HRESULT WINAPI sr_setposv(Source*s,const float*v){return v?sr_setpos(s,v[0],v[1],v[2]):E_POINTER;}
static HRESULT WINAPI sr_getposv(Source*s,float*v){return copy3in(v,s->pos);}
static HRESULT WINAPI sr_setangles(Source*s,float a,float b,float c){s->angles[0]=a;s->angles[1]=b;s->angles[2]=c;return S_OK;}
static HRESULT WINAPI sr_getangles(Source*s,float*a,float*b,float*c){return copy3out(s->angles,a,b,c);}
static HRESULT WINAPI sr_setanglesv(Source*s,const float*v){return v?sr_setangles(s,v[0],v[1],v[2]):E_POINTER;}
static HRESULT WINAPI sr_getanglesv(Source*s,float*v){return copy3in(v,s->angles);}
static HRESULT WINAPI sr_setori6(Source*s,float a,float b,float c,float d,float e,float f){float v[6]={a,b,c,d,e,f};for(int i=0;i<6;i++)s->ori[i]=v[i];return S_OK;}
static HRESULT WINAPI sr_getori6(Source*s,float*a,float*b,float*c,float*d,float*e,float*f){if(!a||!b||!c||!d||!e||!f)return E_POINTER;*a=s->ori[0];*b=s->ori[1];*c=s->ori[2];*d=s->ori[3];*e=s->ori[4];*f=s->ori[5];return S_OK;}
static HRESULT WINAPI sr_setori6v(Source*s,const float*v){if(!v)return E_POINTER;for(int i=0;i<6;i++)s->ori[i]=v[i];return S_OK;}
static HRESULT WINAPI sr_getori6v(Source*s,float*v){if(!v)return E_POINTER;for(int i=0;i<6;i++)v[i]=s->ori[i];return S_OK;}
static HRESULT WINAPI sr_setvel(Source*s,float a,float b,float c){s->vel[0]=a;s->vel[1]=b;s->vel[2]=c;mixer_update_voice(s);return S_OK;}
static HRESULT WINAPI sr_getvel(Source*s,float*a,float*b,float*c){return copy3out(s->vel,a,b,c);}
static HRESULT WINAPI sr_setvelv(Source*s,const float*v){return v?sr_setvel(s,v[0],v[1],v[2]):E_POINTER;}
static HRESULT WINAPI sr_getvelv(Source*s,float*v){return copy3in(v,s->vel);}
static HRESULT WINAPI sr_setcone(Source*s,float a,float b,float c){s->cone[0]=a;s->cone[1]=b;s->cone[2]=c;return S_OK;}
static HRESULT WINAPI sr_getcone(Source*s,float*a,float*b,float*c){return copy3out(s->cone,a,b,c);}
static HRESULT WINAPI sr_setminmax(Source*s,float a,float b,DWORD mode){if(!(a>0.0f)||b<a||mode>1u)return E_INVALIDARG;s->minmax[0]=a;s->minmax[1]=b;s->minmax_mode=mode;mixer_update_voice(s);return S_OK;}
static HRESULT WINAPI sr_getminmax(Source*s,float*a,float*b,DWORD*mode){if(!a||!b||!mode)return E_POINTER;*a=s->minmax[0];*b=s->minmax[1];*mode=s->minmax_mode;return S_OK;}
#define SR_SF(name,field) static HRESULT WINAPI sr_set##name(Source*s,float x){s->field=x;return S_OK;}
#define SR_GF(name,field) static HRESULT WINAPI sr_get##name(Source*s,float*x){if(!x)return E_POINTER;*x=s->field;return S_OK;}
#define SR_SD(name,field) static HRESULT WINAPI sr_set##name(Source*s,DWORD x){s->field=x;return S_OK;}
#define SR_GD(name,field) static HRESULT WINAPI sr_get##name(Source*s,DWORD*x){if(!x)return E_POINTER;*x=s->field;return S_OK;}
static HRESULT WINAPI sr_setgain(Source*s,float x){
 s->gain=x;
 if(staff_enabled()){
  DWORD m=staff_milli(x),last=s->staff_last_gain_milli;
  if(last==0xffffffffu || m>last+75u || m+75u<last || m==0){
   s->staff_last_gain_milli=m;
   staff_record(STAFF_EVENT_GAIN,s->sample_id,s->staff_pcm_sig,m,staff_milli(s->priority),s->mix.active,0,0);
  }
 }
 mixer_update_voice(s);return S_OK;
}
SR_GF(gain,gain)
static HRESULT WINAPI sr_setpitch(Source*s,float x){s->pitch=x;mixer_update_voice(s);return S_OK;}
SR_GF(pitch,pitch)
static HRESULT WINAPI sr_setdoppler(Source*s,float x){if(!(x>=0.0f))return E_INVALIDARG;s->doppler=x;mixer_update_voice(s);return S_OK;}
SR_GF(doppler,doppler)
static HRESULT WINAPI sr_setdistance(Source*s,float x){if(!(x>=0.0f))return E_INVALIDARG;s->distance=x;mixer_update_voice(s);return S_OK;}
SR_GF(distance,distance)
SR_SF(eq,eq) SR_GF(eq,eq)
static HRESULT WINAPI sr_setpriority(Source*s,float x){
 s->priority=x;
 staff_record(STAFF_EVENT_PRIO,s->sample_id,s->staff_pcm_sig,staff_milli(s->gain),staff_milli(x),s->mix.active,0,0);
 return S_OK;
}
SR_GF(priority,priority)
SR_SD(render,render_mode) SR_GD(render,render_mode)
static HRESULT WINAPI sr_settransform(Source*s,DWORD x){if(x>1u)return E_INVALIDARG;s->transform_mode=x;mixer_update_voice(s);return S_OK;}
SR_GD(transform,transform_mode)
SR_SF(refdelay,reflect_delay) SR_GF(refdelay,reflect_delay)
SR_SF(refgain,reflect_gain) SR_GF(refgain,reflect_gain)
static HRESULT WINAPI sr_audibility(Source*s,float*x){(void)s;if(!x)return E_POINTER;*x=0;return E_NOTIMPL;}
static HRESULT WINAPI sr_occlusion(Source*s,float*x){(void)s;if(!x)return E_POINTER;*x=0;return E_NOTIMPL;}
static HRESULT WINAPI sr_status(Source*s,DWORD*x){if(!x)return E_POINTER;mix_enter();*x=(s->mix.active?1u:0u)|(s->mix.active&&s->mix.looping?4u:0u);mix_leave();return S_OK;}
/* V0.9.2 research: actual source pan values were previously E_NOTIMPL.
 * Controlled generic opt-in preserves the bit-identical default Alice/Quake
 * audio path while allowing historical 2D pan adapters to be investigated.
 * Pan values are per-output-channel linear gains (no guessed game mapping).
 * This is not yet certified against the original Descent 3 retail binary. */
static int sr_pan_feature(void){
 static int enabled=-1;
 if(enabled<0){char flag[8]={0};DWORD n=GetEnvironmentVariableA("A3D_ENABLE_PAN_VALUES",flag,sizeof(flag));
  enabled=(n==1u && flag[0]=='1')?1:0;
 }
 return enabled;
}
static HRESULT WINAPI sr_setpan(Source*s,DWORD n,const float*values){
 if(!sr_pan_feature())return E_NOTIMPL;
 if(!values)return E_POINTER;
 if(n!=1u && n!=2u)return E_INVALIDARG;
 float left=values[0],right=n==2u?values[1]:values[0];
 if(!(left>=0.0f&&left<=1.0f&&right>=0.0f&&right<=1.0f))return E_INVALIDARG;
 s->pan_values[0]=left;s->pan_values[1]=right;s->pan_set=1u;
 mixer_update_voice(s);return S_OK;
}
static HRESULT WINAPI sr_getpan(Source*s,DWORD n,float*values){
 if(!sr_pan_feature())return E_NOTIMPL;
 if(!values)return E_POINTER;
 if(n!=1u && n!=2u)return E_INVALIDARG;
 values[0]=s->pan_set?s->pan_values[0]:1.0f;
 if(n==2u)values[1]=s->pan_set?s->pan_values[1]:1.0f;
 return S_OK;
}
/* The original Miles 6.0b A3D2 provider calls SetWaveEvent four times
 * during buffer creation (IDs 0x4000, 0x4001, 0, 1) and checks the last
 * HRESULT. The contract below stores registrations, but is NOT yet a
 * fully implemented event-delivery system. Do not signal arbitrary handles.
 */
static HRESULT WINAPI sr_setevent(Source*s,DWORD event,HANDLE h){
 mix_enter();
 for(DWORD i=0;i<s->event_count;i++){
  if(s->event_codes[i]==event){s->event_handles[i]=h;mix_leave();sr_logu("IA3dSource.SetWaveEvent replaced",event);return S_OK;}
 }
 if(s->event_count>=8){mix_leave();return E_FAIL;}
 s->event_codes[s->event_count]=event;s->event_handles[s->event_count]=h;s->event_count++;mix_leave();
 sr_logu("IA3dSource.SetWaveEvent registered",event);
 return S_OK;
}
static HRESULT WINAPI sr_clearevents(Source*s){mix_enter();s->event_count=0;mix_leave();logline("IA3dSource.ClearWaveEvents");return S_OK;}

/* ABI vtable indices (name, index) are independently checked in tests. */
static void* source_vt[]={
 (void*)sr_qi /* 0 QueryInterface */,
 (void*)sr_add /* 1 AddRef */,
 (void*)sr_rel /* 2 Release */,
 (void*)sr_loadfile /* 3 LoadWaveFile */,
 (void*)sr_loadwave /* 4 LoadWaveData */,
 (void*)sr_allocwave /* 5 AllocateWaveData */,
 (void*)sr_freewave /* 6 FreeWaveData */,
 (void*)sr_setformat /* 7 SetWaveFormat */,
 (void*)sr_getformat /* 8 GetWaveFormat */,
 (void*)sr_wavesize /* 9 GetWaveSize */,
 (void*)sr_gettype /* 10 GetType */,
 (void*)sr_lock /* 11 Lock */,
 (void*)sr_unlock /* 12 Unlock */,
 (void*)sr_play /* 13 Play */,
 (void*)sr_stop /* 14 Stop */,
 (void*)sr_rewind /* 15 Rewind */,
 (void*)sr_settime /* 16 SetWaveTime */,
 (void*)sr_gettime /* 17 GetWaveTime */,
 (void*)sr_setwavepos /* 18 SetWavePosition */,
 (void*)sr_getwavepos /* 19 GetWavePosition */,
 (void*)sr_setpos /* 20 SetPosition3f */,
 (void*)sr_getpos /* 21 GetPosition3f */,
 (void*)sr_setposv /* 22 SetPosition3fv */,
 (void*)sr_getposv /* 23 GetPosition3fv */,
 (void*)sr_setangles /* 24 SetOrientationAngles3f */,
 (void*)sr_getangles /* 25 GetOrientationAngles3f */,
 (void*)sr_setanglesv /* 26 SetOrientationAngles3fv */,
 (void*)sr_getanglesv /* 27 GetOrientationAngles3fv */,
 (void*)sr_setori6 /* 28 SetOrientation6f */,
 (void*)sr_getori6 /* 29 GetOrientation6f */,
 (void*)sr_setori6v /* 30 SetOrientation6fv */,
 (void*)sr_getori6v /* 31 GetOrientation6fv */,
 (void*)sr_setvel /* 32 SetVelocity3f */,
 (void*)sr_getvel /* 33 GetVelocity3f */,
 (void*)sr_setvelv /* 34 SetVelocity3fv */,
 (void*)sr_getvelv /* 35 GetVelocity3fv */,
 (void*)sr_setcone /* 36 SetCone */,
 (void*)sr_getcone /* 37 GetCone */,
 (void*)sr_setminmax /* 38 SetMinMaxDistance */,
 (void*)sr_getminmax /* 39 GetMinMaxDistance */,
 (void*)sr_setgain /* 40 SetGain */,
 (void*)sr_getgain /* 41 GetGain */,
 (void*)sr_setpitch /* 42 SetPitch */,
 (void*)sr_getpitch /* 43 GetPitch */,
 (void*)sr_setdoppler /* 44 SetDopplerScale */,
 (void*)sr_getdoppler /* 45 GetDopplerScale */,
 (void*)sr_setdistance /* 46 SetDistanceModelScale */,
 (void*)sr_getdistance /* 47 GetDistanceModelScale */,
 (void*)sr_seteq /* 48 SetEq */,
 (void*)sr_geteq /* 49 GetEq */,
 (void*)sr_setpriority /* 50 SetPriority */,
 (void*)sr_getpriority /* 51 GetPriority */,
 (void*)sr_setrender /* 52 SetRenderMode */,
 (void*)sr_getrender /* 53 GetRenderMode */,
 (void*)sr_audibility /* 54 GetAudibility */,
 (void*)sr_occlusion /* 55 GetOcclusionFactor */,
 (void*)sr_status /* 56 GetStatus */,
 (void*)sr_setpan /* 57 SetPanValues */,
 (void*)sr_getpan /* 58 GetPanValues */,
 (void*)sr_setevent /* 59 SetWaveEvent */,
 (void*)sr_clearevents /* 60 ClearWaveEvents */,
 (void*)sr_settransform /* 61 SetTransformMode */,
 (void*)sr_gettransform /* 62 GetTransformMode */,
 (void*)sr_setrefdelay /* 63 SetReflectionDelayScale */,
 (void*)sr_getrefdelay /* 64 GetReflectionDelayScale */,
 (void*)sr_setrefgain /* 65 SetReflectionGainScale */,
 (void*)sr_getrefgain /* 66 GetReflectionGainScale */
};
static HRESULT source_new(DWORD flags,void**out){
 if(!out)return E_POINTER;*out=0;
 Source*s=(Source*)HeapAlloc(GetProcessHeap(),8,sizeof(Source));
 if(!s)return E_FAIL;
 s->vt=source_vt;s->ref=1;s->magic=source_magic;s->flags=flags;
 s->sample_id=(DWORD)InterlockedIncrement(&next_source_id);
 s->staff_last_gain_milli=0xffffffffu;
 s->reflect_gain=1.0f;s->reflect_delay=1.0f;s->gain=1.0f;s->pitch=1.0f;s->doppler=1.0f;s->distance=1.0f;
 s->priority=1.0f;s->minmax[0]=1.0f;s->minmax[1]=1000.0f;
 *out=s;
 staff_record(STAFF_EVENT_NEW,s->sample_id,0,staff_milli(s->gain),staff_milli(s->priority),0,0,flags);
 sr_logu("IA3d4.NewSource sample_id",s->sample_id);return S_OK;
}

/* Clone a stopped source's buffer and 3D properties, rather than sharing
 * mutable storage with the original. COM identity and events remain separate. */
static HRESULT source_duplicate(Source*src,void**out){
 if(!out)return E_POINTER;*out=0;
 if(!src||src->magic!=source_magic)return E_INVALIDARG;
 HRESULT hr=source_new(src->flags,out);if(hr!=S_OK)return hr;
 Source*dst=(Source*)*out;
 dst->format=src->format;dst->has_format=src->has_format;
 dst->gain=src->gain;dst->pitch=src->pitch;dst->doppler=src->doppler;
 dst->distance=src->distance;dst->eq=src->eq;dst->priority=src->priority;
 dst->render_mode=src->render_mode;dst->transform_mode=src->transform_mode;
 dst->reflect_delay=src->reflect_delay;dst->reflect_gain=src->reflect_gain;
 for(unsigned i=0;i<3;i++){dst->pos[i]=src->pos[i];dst->vel[i]=src->vel[i];}
 for(unsigned i=0;i<6;i++)dst->ori[i]=src->ori[i];
 for(unsigned i=0;i<2;i++)dst->minmax[i]=src->minmax[i];
 if(src->pcm && src->wave_size){
  dst->pcm=(unsigned char*)HeapAlloc(GetProcessHeap(),0,src->wave_size);
  if(!dst->pcm){sr_rel(dst);*out=0;return E_OUTOFMEMORY;}
  dst->wave_size=src->wave_size;
  sr_copy(dst->pcm,src->pcm,src->wave_size);
 }
 logline("IA3d4.DuplicateSource: independent PCM copy");return S_OK;
}
