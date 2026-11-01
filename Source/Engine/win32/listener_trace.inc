/* v0.5.0 SOURCE COMMENTARY — IA3dListener state
 * Receives world-space listener position, orientation and velocity. Listener changes
 * are propagated to the software spatial mixer; vectors and handedness must be
 * interpreted consistently with the chosen A3D coordinate system.
 */
/* IA3dListener partial state tracker, position/orientation/velocity only. */
typedef struct Listener Listener;
typedef struct {
 HRESULT (WINAPI*qi)(Listener*,const GUID*,void**);
 ULONG (WINAPI*add)(Listener*); ULONG (WINAPI*rel)(Listener*);
 HRESULT (WINAPI*SetPosition3f)(Listener*,float,float,float);
 HRESULT (WINAPI*GetPosition3f)(Listener*,float*,float*,float*);
 HRESULT (WINAPI*SetPosition3fv)(Listener*,const float*);
 HRESULT (WINAPI*GetPosition3fv)(Listener*,float*);
 HRESULT (WINAPI*SetOrientationAngles3f)(Listener*,float,float,float);
 HRESULT (WINAPI*GetOrientationAngles3f)(Listener*,float*,float*,float*);
 HRESULT (WINAPI*SetOrientationAngles3fv)(Listener*,const float*);
 HRESULT (WINAPI*GetOrientationAngles3fv)(Listener*,float*);
 HRESULT (WINAPI*SetOrientation6f)(Listener*,float,float,float,float,float,float);
 HRESULT (WINAPI*GetOrientation6f)(Listener*,float*,float*,float*,float*,float*,float*);
 HRESULT (WINAPI*SetOrientation6fv)(Listener*,const float*);
 HRESULT (WINAPI*GetOrientation6fv)(Listener*,float*);
 HRESULT (WINAPI*SetVelocity3f)(Listener*,float,float,float);
 HRESULT (WINAPI*GetVelocity3f)(Listener*,float*,float*,float*);
 HRESULT (WINAPI*SetVelocity3fv)(Listener*,const float*);
 HRESULT (WINAPI*GetVelocity3fv)(Listener*,float*);
} ListenerVtbl;
struct Listener{const ListenerVtbl*vt; volatile long ref;float pos[3],angles[3],ori[6],vel[3];};
/* Monotonic counters only: no synchronous file logging per game frame. */
static volatile long listener_pos_updates=0,listener_orientation6_updates=0;
static volatile long listener_euler_updates=0,listener_velocity_updates=0;
static const GUID iid_listener=G(0xc398e563,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static ULONG WINAPI ladd(Listener*p){return (ULONG)InterlockedIncrement(&p->ref);}
static ULONG WINAPI lrel(Listener*p){long n=InterlockedDecrement(&p->ref);if(n<1){p->ref=1;return 1;}return (ULONG)n;}
static HRESULT WINAPI lqi(Listener*p,const GUID*i,void**o){if(!o)return E_POINTER;*o=0;logguid("IA3dListener.QueryInterface",i);if(eqguid(i,&iid_unk)||eqguid(i,&iid_listener)){*o=p;ladd(p);return S_OK;}return E_NOINTERFACE;}
static HRESULT copy3in(float *dest,const float*src){if(!src)return E_POINTER;for(int i=0;i<3;i++)dest[i]=src[i];return S_OK;}
static HRESULT copy3out(const float*src,float*a,float*b,float*c){if(!a||!b||!c)return E_POINTER;*a=src[0];*b=src[1];*c=src[2];return S_OK;}
/* Listener positions/orientations are values supplied by the GAME API.
 * They may correspond to the camera, character or a hybrid transform in a
 * third-person title; do not silently replace them with avatar coordinates. */
static HRESULT WINAPI lspos(Listener*l,float a,float b,float c){l->pos[0]=a;l->pos[1]=b;l->pos[2]=c;InterlockedIncrement(&listener_pos_updates);mixer_update_listener();if(trace_detail()){logline("IA3dListener.SetPosition3f");log3("IA3dListener.Position",a,b,c);}return S_OK;}
static HRESULT WINAPI lgpos(Listener*l,float*a,float*b,float*c){return copy3out(l->pos,a,b,c);}
static HRESULT WINAPI lsposv(Listener*l,const float*v){if(!v)return E_POINTER;return lspos(l,v[0],v[1],v[2]);}
static HRESULT WINAPI lgposv(Listener*l,float*v){return copy3in(v,l->pos);}
static HRESULT WINAPI lsang(Listener*l,float a,float b,float c){l->angles[0]=a;l->angles[1]=b;l->angles[2]=c;
 InterlockedIncrement(&listener_euler_updates);
 /* Intentional: the Euler convention is not established from the SDK/game
  * trace yet. Applying a guessed rotation here could break known-good games.
  * Six-vector updates are authoritative in this experimental build. */
 return S_OK;}
static HRESULT WINAPI lgang(Listener*l,float*a,float*b,float*c){return copy3out(l->angles,a,b,c);}
static HRESULT WINAPI lsangv(Listener*l,const float*v){if(!v)return E_POINTER;return lsang(l,v[0],v[1],v[2]);}
static HRESULT WINAPI lgangv(Listener*l,float*v){return copy3in(v,l->angles);}
static HRESULT WINAPI ls6(Listener*l,float a,float b,float c,float d,float e,float f){
 float v[]={a,b,c,d,e,f};for(int i=0;i<6;i++)l->ori[i]=v[i];
 InterlockedIncrement(&listener_orientation6_updates);
 mixer_update_listener();
 if(trace_detail()){log3("IA3dListener.OrientationForward",a,b,c);
 log3("IA3dListener.OrientationUp",d,e,f);}
 return S_OK;
}
static HRESULT WINAPI lg6(Listener*l,float*a,float*b,float*c,float*d,float*e,float*f){if(!a||!b||!c||!d||!e||!f)return E_POINTER;*a=l->ori[0];*b=l->ori[1];*c=l->ori[2];*d=l->ori[3];*e=l->ori[4];*f=l->ori[5];return S_OK;}
static HRESULT WINAPI ls6v(Listener*l,const float*v){if(!v)return E_POINTER;return ls6(l,v[0],v[1],v[2],v[3],v[4],v[5]);}
static HRESULT WINAPI lg6v(Listener*l,float*v){if(!v)return E_POINTER;for(int i=0;i<6;i++)v[i]=l->ori[i];return S_OK;}
static HRESULT WINAPI lsvel(Listener*l,float a,float b,float c){l->vel[0]=a;l->vel[1]=b;l->vel[2]=c;InterlockedIncrement(&listener_velocity_updates);mixer_update_listener();return S_OK;}
static HRESULT WINAPI lgvel(Listener*l,float*a,float*b,float*c){return copy3out(l->vel,a,b,c);}
static HRESULT WINAPI lsvelv(Listener*l,const float*v){if(!v)return E_POINTER;return lsvel(l,v[0],v[1],v[2]);}
static HRESULT WINAPI lgvelv(Listener*l,float*v){return copy3in(v,l->vel);}
static const ListenerVtbl lv={lqi,ladd,lrel,lspos,lgpos,lsposv,lgposv,lsang,lgang,lsangv,lgangv,ls6,lg6,ls6v,lg6v,lsvel,lgvel,lsvelv,lgvelv};
static Listener listener={&lv,1,{0,0,0},{0,0,0},{0,0,-1,0,1,0},{0,0,0}};
