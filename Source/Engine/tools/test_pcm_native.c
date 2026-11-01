/* v0.5.0 SOURCE COMMENTARY — Regression test / harness
 * Exercises the release implementation or checks its ABI/packaging contract. Do not
 * treat fixture success as proof of native Wine or retail-game compatibility.
 */
/* Host-native regression for the cross-platform logic in source_probe.inc.
   This does not replace Wine COM/Miles tests or test audio output. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
typedef uint32_t DWORD;
typedef uint16_t WORD;
typedef int32_t HRESULT;
typedef uint32_t ULONG;
typedef void* HANDLE;
typedef struct { DWORD d1;WORD d2,d3;unsigned char d4[8]; } GUID;
#define G(a,b,c,d,e,f,g,h,i,j,k) {a,b,c,{d,e,f,g,h,i,j,k}}
#define WINAPI
#define S_OK ((HRESULT)0)
#define E_FAIL ((HRESULT)0x80004005UL)
#define E_POINTER ((HRESULT)0x80004003UL)
#define E_NOTIMPL ((HRESULT)0x80004001UL)
#define E_NOINTERFACE ((HRESULT)0x80004002UL)
static const GUID iid_unk = G(0,0,0,0,0,0,0,0,0,0,0);
static void *GetProcessHeap(void){return 0;}
static void *HeapAlloc(void *heap,DWORD flags,DWORD size){(void)heap;return (flags & 8)?calloc(1,size):malloc(size);}
static int HeapFree(void *heap,DWORD flags,void *p){(void)heap;(void)flags;free(p);return 1;}
static long InterlockedIncrement(volatile long*p){return ++*p;}
static long InterlockedDecrement(volatile long*p){return --*p;}
static void logline(const char*s){(void)s;}
static void logguid(const char*s,const GUID*g){(void)s;(void)g;}
static void log3(const char*s,float x,float y,float z){(void)s;(void)x;(void)y;(void)z;}
static int eqguid(const GUID*a,const GUID*b){return !memcmp(a,b,sizeof(*a));}
static HRESULT copy3out(const float*src,float*a,float*b,float*c){if(!a||!b||!c)return E_POINTER;*a=src[0];*b=src[1];*c=src[2];return S_OK;}
static HRESULT copy3in(float*dst,const float*src){if(!dst)return E_POINTER;memcpy(dst,src,12);return S_OK;}
#include "../win32/source_probe.inc"
#define CHECK(x) do {if(!(x)){fprintf(stderr,"FAIL %s at line %d\n",#x,__LINE__);return 1;}} while(0)
int main(void){
 void *obj=0;
 CHECK(source_new(0,&obj)==S_OK && obj);
 Source*s=(Source*)obj;
 CHECK(sr_allocwave(s,100)==E_FAIL);
 WaveFmt f={1,1,22050,22050,1,8,0};
 CHECK(sr_setformat(s,&f)==S_OK);
 WaveFmt g={0};CHECK(sr_getformat(s,&g)==S_OK && g.rate==22050 && g.bits==8);
 CHECK(sr_allocwave(s,2048)==S_OK && sr_wavesize(s)==2048);
 void *a=0,*b=0; DWORD an=0,bn=0;
 CHECK(sr_lock(s,100,200,&a,&an,&b,&bn,A3D_ENTIREBUFFER)==S_OK);
 CHECK(a==s->pcm && an==2048 && b==0 && bn==0);
 CHECK(s->locked==1 && sr_lock(s,0,10,&a,&an,&b,&bn,0)==E_FAIL);
 /* A failed Lock clears outputs. Reacquire expected old range from source state. */
 a=s->pcm;an=2048;b=0;bn=0;
 memset(a,128,an);
 CHECK(sr_unlock(s,a,an,b,bn)==S_OK);
 CHECK(sr_lock(s,2040,32,&a,&an,&b,&bn,0)==S_OK);
 CHECK(an==8 && bn==24 && a==s->pcm+2040 && b==s->pcm);
 CHECK(sr_unlock(s,a,an+1,b,bn)==E_INVALIDARG);
 memset(a,2,an);memset(b,3,bn);
 CHECK(sr_unlock(s,a,an,b,bn)==S_OK);
 CHECK(sr_lock(s,10,5,&a,&an,&b,&bn,0)==S_OK);
 CHECK(an==5 && bn==0);
 CHECK(sr_unlock(s,a,an,b,bn)==S_OK);
 CHECK(sr_setformat(s,&f)==E_FAIL);
 CHECK(sr_play(s,0)==E_NOTIMPL);
 CHECK(sr_freewave(s)==S_OK && sr_wavesize(s)==0);
 CHECK(sr_setformat(s,&f)==S_OK);
 CHECK(sr_allocwave(s,-1)==E_INVALIDARG);
 CHECK(sr_allocwave(s,MAX_PCM_BYTES+1UL)==E_INVALIDARG);
 CHECK(sr_allocwave(s,128)==S_OK);
 CHECK(sr_lock(s,0,0,&a,&an,&b,&bn,A3D_ENTIREBUFFER)==S_OK && an==128);
 CHECK(sr_unlock(s,a,an,b,bn)==S_OK);
 CHECK(sr_rel(s)==0);
 printf("PASS: format, allocation, full lock, wrap lock, unlock, error paths, free and release\n");
 return 0;
}
