/* v0.5.0 SOURCE COMMENTARY — Geometry interface helper definitions
 * Contains geometry helper declarations/data structures used by the A3D scene
 * interface; preserve layout and calling convention where exposed through vtables.
 */
/* IA3dList, independently implemented from the documented API contract.
 * Recorded triangles are fully transformed at definition time, not on Call.
 * Limit 2048 triangles per list and 2048 in the committed frame.
 */
typedef struct A3DList A3DList;
struct A3DList {
 void **vt; volatile long ref;
 DWORD magic,finished,recording,enable_bounds;
 A3DFrame *frame;
 unsigned saved_stack,saved_primitive,saved_vcount,saved_mode,saved_tag;
 float saved_matrices[A3D_SCENE_MAX_STACK][16];
 float saved_reflect[2],saved_trans[2];
};
static const DWORD a3d_list_magic=0x314c3341ul;
static const GUID iid_list=G(0xc398e564,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static A3DList *current_list=0;
static ULONG WINAPI list_add(A3DList*x){return (ULONG)InterlockedIncrement(&x->ref);}
static ULONG WINAPI list_rel(A3DList*x){
 long n=InterlockedDecrement(&x->ref);
 if(n==0){
  if(x==current_list){a3d_scene.record_target=0;current_list=0;}
  if(x->frame)HeapFree(GetProcessHeap(),0,x->frame);
  x->magic=0;HeapFree(GetProcessHeap(),0,x);
 }
 return (ULONG)n;
}
static HRESULT WINAPI list_qi(A3DList*x,const GUID*i,void**o){
 if(!o)return E_POINTER;*o=0;
 if(eqguid(i,&iid_unk)||eqguid(i,&iid_list)){*o=x;list_add(x);return S_OK;}
 return E_NOINTERFACE;
}
/* Begin recording into a private frame and save the current matrix and
 * scene metadata. Call/End cannot leak their temporary transform state back
 * into live geometry submission. `list_end` returns polygon COUNT on
 * success (not S_OK); Quake III 1.17 relies on that ABI behaviour. */
static HRESULT WINAPI list_begin(A3DList*x){
 if(!x||x->magic!=a3d_list_magic||x->finished||current_list)return E_FAIL;
 ensure_scene();x->frame->count=0;
 x->frame->polygons=0;
 x->saved_stack=a3d_scene.stack_level;
 x->saved_primitive=a3d_scene.primitive;x->saved_vcount=a3d_scene.vcount;
 x->saved_mode=a3d_scene.mode;x->saved_tag=a3d_scene.tag;
 for(unsigned i=0;i<A3D_SCENE_MAX_STACK;i++)for(unsigned j=0;j<16;j++)x->saved_matrices[i][j]=a3d_scene.matrix[i][j];
 for(unsigned j=0;j<2;j++){x->saved_reflect[j]=a3d_scene.reflect[j];x->saved_trans[j]=a3d_scene.trans[j];}
 x->recording=1;current_list=x;a3d_scene.record_target=x->frame;
 if(trace_detail())logline("IA3dList.Begin recording");return S_OK;
}
static HRESULT WINAPI list_end(A3DList*x){
 if(!x||x!=current_list||!x->recording)return E_FAIL;
 a3d_scene.record_target=0;current_list=0;x->recording=0;x->finished=1;
 a3d_scene.stack_level=x->saved_stack;a3d_scene.primitive=x->saved_primitive;
 a3d_scene.vcount=x->saved_vcount;a3d_scene.mode=x->saved_mode;a3d_scene.tag=x->saved_tag;
 for(unsigned i=0;i<A3D_SCENE_MAX_STACK;i++)for(unsigned j=0;j<16;j++)a3d_scene.matrix[i][j]=x->saved_matrices[i][j];
 for(unsigned j=0;j<2;j++){a3d_scene.reflect[j]=x->saved_reflect[j];a3d_scene.trans[j]=x->saved_trans[j];}
 /* Aureal API specifies a successful End returns nNumPolygons, not S_OK.
  * Quake III 1.17 depends on exactly this convention for acoustic lists. */
 if(trace_detail())logline("IA3dList.End recorded polygons");
 return (HRESULT)x->frame->polygons;
}
static HRESULT WINAPI list_call(A3DList*x){
 if(!x||x->magic!=a3d_list_magic||!x->finished||current_list)return E_FAIL;
 ensure_scene();
 if(a3d_scene.staged.count+x->frame->count>A3D_SCENE_MAX_TRI)return E_FAIL;
 for(unsigned j=0;j<x->frame->count;j++)a3d_scene.staged.tris[a3d_scene.staged.count++]=x->frame->tris[j];
 a3d_scene.staged.polygons+=x->frame->polygons;
 /* IMPORTANT ABI CONTRACT: IA3dList::Call returns the number of executed
  * POLYGONS, not HRESULT S_OK (zero). Quake III 1.17 at 0x0042d02f sums the
  * values returned by Call until its geometry budget is reached. Returning 0
  * erroneously makes Quake III iterate past valid list pointers into its own
  * 0xABABABAB sentinel, causing a deterministic access violation. */
 return (HRESULT)x->frame->polygons;
}
static HRESULT WINAPI list_bounds(A3DList*x){if(!x||x->magic!=a3d_list_magic)return E_FAIL;x->enable_bounds=1;return S_OK;}
static void *list_vt[]={ (void*)list_qi,(void*)list_add,(void*)list_rel,
 (void*)list_begin,(void*)list_end,(void*)list_call,(void*)list_bounds };
static HRESULT WINAPI g_NewList(Geom*g,void**out){
 (void)g;if(!out)return E_POINTER;*out=0;
 A3DList*x=(A3DList*)HeapAlloc(GetProcessHeap(),8,sizeof(*x));if(!x)return (HRESULT)0x8007000EL;
 x->frame=(A3DFrame*)HeapAlloc(GetProcessHeap(),8,sizeof(A3DFrame));
 if(!x->frame){HeapFree(GetProcessHeap(),0,x);return (HRESULT)0x8007000EL;}
 x->vt=list_vt;x->ref=1;x->magic=a3d_list_magic;
 *out=x;if(trace_detail())logline("IA3dGeom.NewList => S_OK");return S_OK;
}
