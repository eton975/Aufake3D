/* v0.5.0 SOURCE COMMENTARY — Runtime acoustic geometry scene
 * Stores and updates geometry/materials used for line-of-sight occlusion and reflection
 * paths. Observe scene commit/flush ownership: intermediate geometry must not become
 * visible to the mixer prematurely.
 */
/* A3D compatibility acoustic geometry core, v0.3.0 alpha.
 * Geometric occlusion + first-order specular reflections, independent of
 * Win32/ALSA. No allocation, recursion, external library, or CRT requirement.
 * Based on public A3D polygon modes 3=triangle, 4=quad. Not Aureal's code.
 * Unit assumption: metres; scene matrices column major.
 */
#ifndef A3D_ACOUSTIC_SCENE_H
#define A3D_ACOUSTIC_SCENE_H
#define A3D_SCENE_MAX_TRI 2048u
#define A3D_SCENE_MAX_REFLECT 4u
#define A3D_SCENE_OCCLUSIONS 0x40u
#define A3D_SCENE_REFLECTIONS 0x02u
#define A3D_SCENE_TRIANGLES 3u
#define A3D_SCENE_QUADS 4u
#define A3D_SCENE_MAX_STACK 16u
typedef struct {float x,y,z;} A3DV3;
typedef struct {A3DV3 v[3]; float reflect[2],trans[2]; unsigned flags,tag;} A3DTri;
/* Count original polygons separately: a quad produces two stored triangles. */
typedef struct {A3DTri tris[A3D_SCENE_MAX_TRI];unsigned count,polygons;} A3DFrame;
typedef struct {
 A3DFrame staged,committed;
 unsigned mode,global_flags,primitive,vcount,stack_level;
 A3DV3 verts[4];float reflect[2],trans[2];
 float matrix[A3D_SCENE_MAX_STACK][16];
 unsigned overflow_count,tag,revision;
 A3DFrame *record_target; /* Non-null only between IA3dList Begin/End. */
} A3DScene;
typedef struct {A3DV3 point;float gain,delay_sec;} A3DEarly;
typedef struct {float direct_low,direct_high;A3DEarly early[A3D_SCENE_MAX_REFLECT];unsigned n_early,intersections;} A3DPaths;
static float a3d_abs(float x){return x<0?-x:x;}
static float a3d_min(float a,float b){return a<b?a:b;}
static float a3d_max(float a,float b){return a>b?a:b;}
static float a3d_clampf(float x,float lo,float hi){return a3d_max(lo,a3d_min(hi,x));}
static float a3d_sqrt(float x){if(x<=0)return 0;float y=x>=1?x:1;for(int i=0;i<12;i++)y=0.5f*(y+x/y);return y;}
static A3DV3 a3d_v3(float x,float y,float z){A3DV3 v={x,y,z};return v;}
static A3DV3 a3d_plus(A3DV3 a,A3DV3 b){return a3d_v3(a.x+b.x,a.y+b.y,a.z+b.z);}
static A3DV3 a3d_minus(A3DV3 a,A3DV3 b){return a3d_v3(a.x-b.x,a.y-b.y,a.z-b.z);}
static A3DV3 a3d_scale(A3DV3 a,float b){return a3d_v3(a.x*b,a.y*b,a.z*b);}
static float a3d_dot(A3DV3 a,A3DV3 b){return a.x*b.x+a.y*b.y+a.z*b.z;}
static A3DV3 a3d_cross(A3DV3 a,A3DV3 b){return a3d_v3(a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x);}
static float a3d_norm(A3DV3 a){return a3d_sqrt(a3d_dot(a,a));}
static void a3d_identity(float *m){for(unsigned j=0;j<16;j++)m[j]=0;for(unsigned j=0;j<4;j++)m[j*5]=1;}
static void a3d_matmul(float *a,const float*b){float out[16];for(int col=0;col<4;col++)for(int row=0;row<4;row++){
 float sum=0;for(int k=0;k<4;k++)sum+=a[k*4+row]*b[col*4+k];out[col*4+row]=sum;
 }
 for(int i=0;i<16;i++)a[i]=out[i];}
static A3DV3 a3d_transform(const float *m,A3DV3 v){return a3d_v3(m[0]*v.x+m[4]*v.y+m[8]*v.z+m[12],m[1]*v.x+m[5]*v.y+m[9]*v.z+m[13],m[2]*v.x+m[6]*v.y+m[10]*v.z+m[14]);}
static void a3d_scene_init(A3DScene*s){s->staged.count=s->committed.count=0;s->staged.polygons=s->committed.polygons=0;s->mode=A3D_SCENE_OCCLUSIONS|A3D_SCENE_REFLECTIONS;s->global_flags=0;s->primitive=0;s->vcount=0;s->stack_level=0;s->overflow_count=0;s->revision=1;s->tag=0;s->record_target=0;s->reflect[0]=s->reflect[1]=0.55f;s->trans[0]=s->trans[1]=0.05f;a3d_identity(s->matrix[0]);}
static void a3d_scene_clear(A3DScene*s){s->staged.count=0;s->staged.polygons=0;s->vcount=0;s->primitive=0;}
static void a3d_scene_flush(A3DScene*s){s->revision++;s->committed.count=s->staged.count;s->committed.polygons=s->staged.polygons;for(unsigned i=0;i<s->staged.count;i++)s->committed.tris[i]=s->staged.tris[i];}
static void a3d_scene_begin(A3DScene*s,unsigned mode){s->primitive=mode&0xFu;s->vcount=0;}
static void a3d_scene_addtri(A3DScene*s,A3DV3 a,A3DV3 b,A3DV3 c){
 A3DFrame*f=s->record_target?s->record_target:&s->staged;
 if(f->count>=A3D_SCENE_MAX_TRI){s->overflow_count++;return;}
 A3DTri*t=&f->tris[f->count++];t->v[0]=a;t->v[1]=b;t->v[2]=c;
 t->reflect[0]=s->reflect[0];t->reflect[1]=s->reflect[1];t->trans[0]=s->trans[0];t->trans[1]=s->trans[1];t->flags=s->mode;t->tag=s->tag;
}
static void a3d_scene_vertex(A3DScene*s,float x,float y,float z){
 if(s->primitive!=A3D_SCENE_TRIANGLES&&s->primitive!=A3D_SCENE_QUADS)return;
 s->verts[s->vcount++]=a3d_transform(s->matrix[s->stack_level],a3d_v3(x,y,z));
 unsigned n=(s->primitive==A3D_SCENE_TRIANGLES)?3u:4u;
 if(s->vcount==n){
  A3DFrame*f=s->record_target?s->record_target:&s->staged;
  unsigned before=f->count;
  a3d_scene_addtri(s,s->verts[0],s->verts[1],s->verts[2]);
  if(n==4)a3d_scene_addtri(s,s->verts[0],s->verts[2],s->verts[3]);
  /* A submitted quad is ONE polygon, even though acoustics need two triangles.
   * Never count primitives that could not be recorded (capacity exhausted). */
  if(f->count>before)f->polygons++;
  s->vcount=0;
 }
}
/* Moller-Trumbore segment test. Exclude endpoints to avoid self-intersection. */
static int a3d_hit(A3DV3 a,A3DV3 b,const A3DTri*t,float*frac){
 A3DV3 d=a3d_minus(b,a),e1=a3d_minus(t->v[1],t->v[0]),e2=a3d_minus(t->v[2],t->v[0]),p=a3d_cross(d,e2);
 float det=a3d_dot(e1,p);if(a3d_abs(det)<1.e-7f)return 0;
 float inv=1.0f/det;A3DV3 q=a3d_minus(a,t->v[0]);float u=a3d_dot(q,p)*inv;
 if(u<0||u>1)return 0;A3DV3 r=a3d_cross(q,e1);float v=a3d_dot(d,r)*inv;
 if(v<0||u+v>1)return 0;float w=a3d_dot(e2,r)*inv;
 if(w<=1.e-4f||w>=0.9999f)return 0;*frac=w;return 1;
}
static int a3d_segment_blocked(A3DV3 a,A3DV3 b,const A3DFrame*f,int exclude){
 for(unsigned i=0;i<f->count;i++){if((int)i==exclude)continue;if(!(f->tris[i].flags&A3D_SCENE_OCCLUSIONS))continue;float h;if(a3d_hit(a,b,&f->tris[i],&h))return 1;}return 0;
}
static void a3d_trace(const A3DScene*s,A3DV3 source,A3DV3 listener,A3DPaths*out){
 out->direct_low=1;out->direct_high=1;out->n_early=0;out->intersections=0;
 if(!(s->global_flags&(A3D_SCENE_OCCLUSIONS|A3D_SCENE_REFLECTIONS)))return;
 A3DV3 delta=a3d_minus(listener,source);float direct=a3d_norm(delta);
 if(direct<0.001f)return;
 const A3DFrame*f=&s->committed;
 for(unsigned i=0;i<f->count;i++){
  const A3DTri*t=&f->tris[i];
  float frac;
  if((s->global_flags&A3D_SCENE_OCCLUSIONS)&&(t->flags&A3D_SCENE_OCCLUSIONS)&&a3d_hit(source,listener,t,&frac)){
   out->intersections++;
   out->direct_low*=a3d_clampf(t->trans[0],0,1);out->direct_high*=a3d_clampf(t->trans[1],0,1);
  }
  if(!(s->global_flags&A3D_SCENE_REFLECTIONS)||!(t->flags&A3D_SCENE_REFLECTIONS))continue;
  A3DV3 u=a3d_minus(t->v[1],t->v[0]),v=a3d_minus(t->v[2],t->v[0]);
  A3DV3 normal=a3d_cross(u,v);float nn=a3d_norm(normal);if(nn<1.e-5f)continue;
  normal=a3d_scale(normal,1.0f/nn);
  float ds=a3d_dot(a3d_minus(source,t->v[0]),normal);
  float dl=a3d_dot(a3d_minus(listener,t->v[0]),normal);
  if(ds*dl<=0.0001f)continue; /* Reflection only on same side. */
  A3DV3 mirror=a3d_minus(source,a3d_scale(normal,2.0f*ds));
  float tt; if(!a3d_hit(mirror,listener,t,&tt))continue;
  A3DV3 bounce=a3d_plus(mirror,a3d_scale(a3d_minus(listener,mirror),tt));
  A3DV3 p0=a3d_plus(source,a3d_scale(a3d_minus(bounce,source),0.0002f));
  A3DV3 p1=a3d_plus(listener,a3d_scale(a3d_minus(bounce,listener),0.0002f));
  if(a3d_segment_blocked(p0,bounce,f,(int)i)||a3d_segment_blocked(p1,bounce,f,(int)i))continue;
  float path=a3d_norm(a3d_minus(bounce,source))+a3d_norm(a3d_minus(bounce,listener));
  float reflect=a3d_clampf((t->reflect[0]+t->reflect[1])*0.5f,0,1);
  float gain=0.42f*reflect*direct/(path+0.01f);
  if(gain<0.001f)continue;
  A3DEarly entry={bounce,gain,(path-direct)/343.0f};
  if(entry.delay_sec<0)entry.delay_sec=0;
  unsigned j=0;while(j<out->n_early && out->early[j].gain>=gain)j++;
  if(j>=A3D_SCENE_MAX_REFLECT)continue;
  if(out->n_early<A3D_SCENE_MAX_REFLECT)out->n_early++;
  for(unsigned k=out->n_early-1;k>j;k--)out->early[k]=out->early[k-1];
  out->early[j]=entry;
 }
}
#endif
