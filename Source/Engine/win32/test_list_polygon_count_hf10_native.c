/* Native (Linux) regression for original Aureal IA3dList::End/Call counts.
 * The actual vtable implementation is included and exercised, with only Win32
 * allocator/atomic stubs. The game binary 1.17 at 0x0042d02f ADDs the return
 * from Call to its geometry count; returning S_OK=0 crashes at a sentinel. */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
typedef unsigned long DWORD;
typedef unsigned long ULONG;
typedef long HRESULT;
typedef struct { uint32_t a,b,c,d;} GUID;
#define WINAPI
#define S_OK 0
#define E_FAIL (-1)
#define E_POINTER (-2)
#define E_NOINTERFACE (-3)
#define G(a,b,c,d,e,f,g,h,i,j,k) ((GUID){0,0,0,0})
static const GUID iid_unk={0,0,0,0};
static int eqguid(const GUID*a,const GUID*b){return !memcmp(a,b,sizeof(*a));}
static long InterlockedIncrement(volatile long*x){return ++*x;}
static long InterlockedDecrement(volatile long*x){return --*x;}
static void *GetProcessHeap(void){return NULL;}
static void* HeapAlloc(void*h,unsigned z,size_t n){(void)h;(void)z;return calloc(1,n);}
static int HeapFree(void*h,unsigned z,void*p){(void)h;(void)z;free(p);return 1;}
static int trace_detail(void){return 0;}
static void logline(const char*s){(void)s;}
#include "acoustic_scene.h"
typedef struct Geom Geom;
struct Geom{void **vt;volatile long ref;DWORD primitive;};
static A3DScene a3d_scene;
static int a3d_scene_ready=0;
static void ensure_scene(void){if(!a3d_scene_ready){a3d_scene_init(&a3d_scene);a3d_scene_ready=1;}}
#include "geometry_lists.inc"
#define CHECK(x) do{if(!(x)){fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x);return 1;}}while(0)
static void triangle(void){a3d_scene_begin(&a3d_scene,3);a3d_scene_vertex(&a3d_scene,0,0,0);a3d_scene_vertex(&a3d_scene,1,0,0);a3d_scene_vertex(&a3d_scene,0,1,0);}
static void quad(void){a3d_scene_begin(&a3d_scene,4);a3d_scene_vertex(&a3d_scene,0,0,0);a3d_scene_vertex(&a3d_scene,1,0,0);a3d_scene_vertex(&a3d_scene,1,1,0);a3d_scene_vertex(&a3d_scene,0,1,0);}
int main(void){
 ensure_scene();Geom g={0};A3DList *l=NULL;
 CHECK(g_NewList(&g,(void**)&l)==S_OK && l);
 CHECK(l->vt==list_vt && list_call(l)==E_FAIL);
 CHECK(list_begin(l)==S_OK);
 triangle();quad();triangle();
 CHECK(l->frame->count==4); /* 2 triangles + 1 quad => 4 internal triangles */
 CHECK(l->frame->polygons==3); /* But only three A3D API polygons */
 CHECK(list_end(l)==3);
 CHECK(list_call(l)==3);
 CHECK(a3d_scene.staged.count==4 && a3d_scene.staged.polygons==3);
 CHECK(list_call(l)==3);
 CHECK(a3d_scene.staged.count==8 && a3d_scene.staged.polygons==6);
 CHECK(list_begin(l)==E_FAIL);
 CHECK(list_rel(l)==0);
 /* Empty finished list legitimately yields zero, but must never be
  * inserted as a nonempty rendered list by game code. */
 l=NULL;CHECK(g_NewList(&g,(void**)&l)==0 && l);
 CHECK(list_begin(l)==0);CHECK(list_end(l)==0);CHECK(list_call(l)==0);
 CHECK(list_rel(l)==0);
 a3d_scene_clear(&a3d_scene);CHECK(a3d_scene.staged.polygons==0);
 puts("PASS: IA3dList End/Call return polygon counts, quad counts once, COM vtable slots correct");
 return 0;
}
