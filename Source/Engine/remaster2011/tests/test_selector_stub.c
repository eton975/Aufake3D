/* Runs the ACTUAL bridge's machine-code generator on Linux without Wine.
 * This catches broken rel32 jumps and overwritten provider-buffer bytes.
 * It does NOT execute Win32 child-process hooks or test retail gameplay.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#define __declspec(x)
#define __stdcall
#define mainCRTStartup unused_windows_entry
#include "../alice_a3d2011_bridge.c"
static uint32_t load32(const unsigned char *b) {
    return (uint32_t)b[0] | ((uint32_t)b[1]<<8) | ((uint32_t)b[2]<<16) | ((uint32_t)b[3]<<24);
}
static int check(int yes, const char *what) {
    if (!yes) fprintf(stderr, "FAIL: %s\n", what);
    return !yes;
}
int main(void){
    unsigned char b[256]={0},name[20]={0};
    const uint32_t base=0x30000000;
    unsigned n=gen_stub(b,base),i,k=0,jump_count=0,conditional=0,success=0,fallback=0,bad=0;
    bad|=check(n>50 && n<256,"stub size");
    for(i=0;i+5<=n;i++){
        if(b[i]==0xc7 && b[i+1]==0x44 && b[i+2]==0x24 && b[i+3]>=0x20 && b[i+3]<0x34){
            unsigned pos=b[i+3]-0x20;
            if(pos%4==0 && pos+4<=20){memcpy(name+pos,b+i+4,4);k++;}
        }
        if(b[i]==0x0f && b[i+1]==0x85){
            uint32_t dest=base+i+6+load32(b+i+2);
            bad|=check(dest>=base && dest<base+n,"conditional fallback target");
            conditional++;
        }
        if(b[i]==0xe9){
            uint32_t dest=base+i+5+load32(b+i+1);
            if(dest==REMASTER_SUCCESS_ADDRESS)success++;
            if(dest==REMASTER_FALLBACK_ADDRESS)fallback++;
            jump_count++;
        }
    }
    bad|=check(!memcmp(name,"Aureal A3D 2.0 (TM)",20),"A3D2 provider name");
    bad|=check(k==5,"exactly five name stores");
    bad|=check(conditional==5,"all five a3d2 string tests");
    bad|=check(success==1 && fallback==1,"branch destinations");
    /* mov esi,5 appears once and branch must not change EBP. */
    {unsigned seq=0;for(i=0;i+5<=n;i++)if(!memcmp(b+i,"\xbe\x05\0\0\0",5))seq++;
     bad|=check(seq==1,"Aureal class id 5");}
    printf("stub=%u bytes, fallback tests=%u, jumps=%u, name-stores=%u, failures=%d\n",n,conditional,jump_count,k,bad);
    return bad?1:0;
}
