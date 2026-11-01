/* v0.6.10 TEST BUILD: opt-in, RAM-only event trace for an A3D/Miles
 * sound suppressed by a busy scene. Never modifies signal/voice policy.
 * A3D_STAFF_DIAG=1 and A3D_LOG=1 required to get a useful report.
 * Mark GOOD and BAD via A3D_STAFF_GOOD.flag / A3D_STAFF_BAD.flag.
 * The worker polls flags only once / 300ms, and the ring is flushed solely
 * during normal mixer shutdown. The existing logline cap is <=1MiB.
 */
IMPORT long WINAPI InterlockedExchange(volatile long*,long);
static void sr_logu(const char*,DWORD);
IMPORT DWORD WINAPI GetTickCount(void);
IMPORT DWORD WINAPI GetFileAttributesA(const char*);
IMPORT BOOL WINAPI DeleteFileA(const char*);
#define STAFF_TRACE_CAP 4096u
#define STAFF_EVENT_PLAY 1u
#define STAFF_EVENT_KEEP 2u
#define STAFF_EVENT_STOP 3u
#define STAFF_EVENT_GAIN 4u
#define STAFF_EVENT_PRIO 5u
#define STAFF_EVENT_REJECT 6u
#define STAFF_EVENT_METER 7u
#define STAFF_EVENT_GOOD 8u
#define STAFF_EVENT_BAD 9u
#define STAFF_EVENT_ACTIVE 10u
#define STAFF_EVENT_RESTART 11u
#define STAFF_EVENT_NEW 12u
#define STAFF_EVENT_RELEASE 13u
#define STAFF_EVENT_UNLOCK 14u
#define STAFF_EVENT_STOP_IDLE 15u
#define STAFF_EVENT_BADPLAY 16u
typedef struct StaffEvent {
 volatile long ready;
 DWORD ms,kind,id,hash,gain,priority,active,limiter,extra;
} StaffEvent;
static StaffEvent staff_events[STAFF_TRACE_CAP];
static volatile long staff_head=0;
static int staff_gate=-1;
static DWORD staff_next_meter_at=0,staff_next_mark_at=0;
static DWORD staff_min_limiter=1000u,staff_max_active=0,staff_last_clip=0;
static int staff_enabled(void){
 if(staff_gate<0){char v[8]={0};DWORD n=GetEnvironmentVariableA("A3D_STAFF_DIAG",v,sizeof(v));
  staff_gate=(n==1&&v[0]=='1')?1:0;}
 return staff_gate;
}
static DWORD staff_milli(float f){
 if(!(f>=0.0f))return 0u;
 if(f>1000.0f)return 1000000u;
 return (DWORD)(f*1000.0f+0.5f);
}
/* Fast bounded source fingerprint, not a cryptographic sound identity.
 * Same fingerprint across calls is suggestive; no match is not proof of
 * a different sound (streaming buffers can be rewritten in-place). */
static DWORD staff_fingerprint(const unsigned char*data,DWORD size){
 DWORD h=2166136261u;
 if(!data)return 0;
 if(size>4096u)size=4096u;
 for(DWORD i=0;i<size;i++){h^=data[i];h*=16777619u;}
 return h;
}
static void staff_record(DWORD kind,DWORD id,DWORD hash,DWORD gain,
 DWORD priority,DWORD active,DWORD limiter,DWORD extra){
 if(!staff_enabled())return;
 long ticket=InterlockedIncrement(&staff_head);
 StaffEvent*e=&staff_events[((unsigned long)(ticket-1))%STAFF_TRACE_CAP];
 /* The ring is consumed only after the worker has exited, and the COM
  * source lifecycle is normally serialised by the game/mixer lock. */
 e->ready=0;e->ms=GetTickCount();e->kind=kind;e->id=id;
 e->hash=hash;e->gain=gain;e->priority=priority;
 e->active=active;e->limiter=limiter;e->extra=extra;
 InterlockedExchange(&e->ready,ticket);
}
static char *staff_appendhex(char *p,DWORD n){
 static const char h[]="0123456789abcdef";
 for(int k=7;k>=0;k--)*p++=h[(n>>(k*4))&15];
 return p;
}
static void staff_dump(void){
 if(!staff_enabled())return;
 logline("A3D.StaffDiagnostic V1: all numeric fields are hexadecimal; test-build only");
 logline("A3D.StaffDiagnostic fields: ms kind source_id pcm_fnv1a gain_x1000 priority_x1000 active limiter_x1000 extra");
 logline("A3D.StaffDiagnostic kinds: 1=PLAY 2=KEEP 3=STOP 4=GAIN 5=PRIO 6=REJECT 7=METER 8=GOOD 9=BAD 10=ACTIVE 11=RESTART 12=NEW 13=RELEASE 14=UNLOCK 15=STOP_IDLE 16=BADPLAY");
 logline("A3D.StaffDiagnostic METER: active=max sampled, limiter=minimum x1000, extra=limiter peak event delta; PLAY extra=PCM bytes; ACTIVE extra=PCM bytes");
 unsigned long head=(unsigned long)staff_head;
 unsigned long first=head>STAFF_TRACE_CAP?head-STAFF_TRACE_CAP:0u;
 sr_logu("A3D.StaffDiagnostic.events_total",(DWORD)head);
 sr_logu("A3D.StaffDiagnostic.events_retained",(DWORD)(head-first));
 for(unsigned long n=first;n<head;n++){
  StaffEvent *e=&staff_events[n%STAFF_TRACE_CAP];
  if((unsigned long)e->ready!=n+1u)continue;
  char line[160];char*p=line;
  const char*tag="A3D.Staff.E ";while(*tag)*p++=*tag++;
  DWORD values[]={e->ms,e->kind,e->id,e->hash,e->gain,e->priority,e->active,e->limiter,e->extra};
  for(unsigned k=0;k<sizeof(values)/sizeof(values[0]);k++){
   p=staff_appendhex(p,values[k]);if(k+1<sizeof(values)/sizeof(values[0]))*p++=' ';
  }
  *p=0;logline(line);
 }
 logline("A3D.StaffDiagnostic END");
}
/* v0.6.11: opt-in source-buffer capture for *offline* matching against 100
 * privately supplied weapon WAVs. No file access during playback. Each
 * source Play copies at most 16 KiB, into a bounded 256-slot RAM ring.
 * Only 16-bit mono data is stored; others are skipped (never mislabeled).
 * All records are dumped only at orderly mixer shutdown.
 * Binary format: 8-byte magic A3DWPC11, uint32 count, uint32 bytes_per_slot,
 * then [10x uint32 metadata, up to 16384 PCM bytes padded to slot length].
 * Each slot: ms, source_id, rate, channels, bits, copied_bytes, gain_x1000,
 * priority_x1000, pcm_hash, original_pcm_bytes.
 * IMPORTANT: source-buffer snapshots may contain copyrighted game audio.
 * Do not bundle captures in public distributions or upload them publicly.
 */
#define WEAPON_CAPTURE_SLOTS 256u
#define WEAPON_CAPTURE_BYTES 16384u
#define WEAPON_CAPTURE_META_WORDS 10u
typedef struct WeaponCapture {
 DWORD ms,id,rate,channels,bits,bytes,gain,priority,hash,source_bytes;
 unsigned char pcm[WEAPON_CAPTURE_BYTES];
} WeaponCapture;
static WeaponCapture weapon_capture_ring[WEAPON_CAPTURE_SLOTS];
static const unsigned char weapon_padding_zeros[512]={0};
static volatile long weapon_capture_head=0;
static int weapon_capture_gate=-1;
static int weapon_capture_enabled(void){
 if(weapon_capture_gate<0){char s[8]={0};DWORD n=GetEnvironmentVariableA("A3D_WEAPON_CAPTURE",s,sizeof(s));
 weapon_capture_gate=(n==1&&s[0]=='1'&&staff_enabled())?1:0;}
 return weapon_capture_gate;
}
static void weapon_capture_play(DWORD id,const unsigned char*pcm,DWORD bytes,
 DWORD rate,DWORD channels,DWORD bits,float gain,float priority,DWORD sig){
 if(!weapon_capture_enabled()||!pcm||!bytes||channels!=1||bits!=16)return;
 /* Called inside the same source/mixer lock used for other state changes. */
 long n=InterlockedIncrement(&weapon_capture_head);
 WeaponCapture*c=&weapon_capture_ring[((unsigned long)(n-1))%WEAPON_CAPTURE_SLOTS];
 c->ms=GetTickCount();c->id=id;c->rate=rate;c->channels=channels;c->bits=bits;
 c->bytes=bytes<WEAPON_CAPTURE_BYTES?bytes:WEAPON_CAPTURE_BYTES;
 c->gain=staff_milli(gain);c->priority=staff_milli(priority);
 c->hash=sig;c->source_bytes=bytes;
 for(DWORD i=0;i<c->bytes;i++)c->pcm[i]=pcm[i];
}
static void weapon_capture_dump(void){
 if(!weapon_capture_enabled())return;
 char name[512];
 DWORD n=GetEnvironmentVariableA("A3D_WEAPON_CAPTURE_PATH",name,sizeof(name));
 if(n==0||n>=sizeof(name)){
  const char*name_default="a3d-v0611-weapon-capture.bin";unsigned i=0;
  while(name_default[i]&&i<sizeof(name)-1){name[i]=name_default[i];i++;}
  name[i]=0;
 }
 /* Write only after mixer thread shutdown. The buffer is bounded to 4.20 MiB. */
 HANDLE file=CreateFileA(name,GENERIC_WRITE,FILE_SHARE_READ,0,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
 if(file==INVALID_HANDLE_VALUE){logline("A3D.WeaponCapture ERROR: unable to write capture file");return;}
 const unsigned char magic[8]={'A','3','D','W','P','C','1','1'};
 DWORD count=(DWORD)weapon_capture_head;
 if(count>WEAPON_CAPTURE_SLOTS)count=WEAPON_CAPTURE_SLOTS;
 DWORD stride=WEAPON_CAPTURE_BYTES;
 DWORD wrote=0;BOOL ok=WriteFile(file,magic,8,&wrote,0)&&wrote==8;
 if(ok)ok=WriteFile(file,&count,4,&wrote,0)&&wrote==4;
 if(ok)ok=WriteFile(file,&stride,4,&wrote,0)&&wrote==4;
 DWORD begin=((DWORD)weapon_capture_head)>count?((DWORD)weapon_capture_head)-count:0;

 for(DWORD i=0;ok&&i<count;i++){
  WeaponCapture*c=&weapon_capture_ring[(begin+i)%WEAPON_CAPTURE_SLOTS];
  ok=WriteFile(file,c,WEAPON_CAPTURE_META_WORDS*4u,&wrote,0)&&wrote==WEAPON_CAPTURE_META_WORDS*4u;
  if(ok)ok=WriteFile(file,c->pcm,c->bytes,&wrote,0)&&wrote==c->bytes;
  DWORD padding=WEAPON_CAPTURE_BYTES-c->bytes;
  while(ok&&padding){DWORD part=padding>sizeof(weapon_padding_zeros)?sizeof(weapon_padding_zeros):padding;
   ok=WriteFile(file,weapon_padding_zeros,part,&wrote,0)&&wrote==part;padding-=part;}
 }
 CloseHandle(file);
 if(ok){logline("A3D.WeaponCapture V1: bounded raw mono PCM captured to sidecar; upload privately");
  sr_logu("A3D.WeaponCapture.records",count);
 }else logline("A3D.WeaponCapture ERROR: partial sidecar written");
}
static void staff_poll_marks(A3DMix*);
/* Worker-only periodic meter, no disk writes; called after a DSP subblock. */
static void staff_sample(A3DMix*m){
 if(!staff_enabled())return;
 DWORD now=GetTickCount();
 DWORD lim=staff_milli(m->limiter_gain);
 if(lim<staff_min_limiter)staff_min_limiter=lim;
 DWORD count=0;
 for(unsigned i=0;i<A3DMIX_VOICES;i++)if(m->v[i]&&m->v[i]->active)count++;
 if(count>staff_max_active)staff_max_active=count;
 if((long)(now-staff_next_meter_at)>=0){
  DWORD events=m->clip_events-staff_last_clip;
  staff_record(STAFF_EVENT_METER,0,0,0,0,staff_max_active,staff_min_limiter,events);
  staff_last_clip=m->clip_events;
  staff_next_meter_at=now+500u;
  staff_max_active=0;staff_min_limiter=1000u;
 }
}
