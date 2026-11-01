#include <stdio.h>
typedef unsigned int DWORD; typedef unsigned char BYTE;
static void u32(BYTE *p,DWORD n){p[0]=(BYTE)n;p[1]=(BYTE)(n>>8);p[2]=(BYTE)(n>>16);p[3]=(BYTE)(n>>24);}
static void put8(BYTE *buf,DWORD *at,BYTE b){buf[(*at)++]=b;}
static void put32(BYTE *buf,DWORD *at,DWORD v){u32(buf+*at,v);*at+=4;}
static void rel32(BYTE *buf,DWORD pos,DWORD instr_addr,DWORD dest){u32(buf+pos,dest-(instr_addr+pos+4));}
static DWORD gen_stub(BYTE *b,DWORD base){
  DWORD n=0,jumps[5],rel_to_end_1,rel_to_end_2,fb;
  const BYTE name[]="Aureal A3D 2.0 (TM)"; /* 20 bytes incl NUL */
  DWORD i;
  /* Test one byte at a time: no four-byte read past short cvar strings. */
  put8(b,&n,0x8a);put8(b,&n,0x03); /* mov al, [ebx] */
  put8(b,&n,0x0c);put8(b,&n,0x20); /* or al, 0x20 */
  put8(b,&n,0x3c);put8(b,&n,0x61); /* cmp al, 'a' */
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[0]=n;put32(b,&n,0);
  put8(b,&n,0x80);put8(b,&n,0x7b);put8(b,&n,0x01);put8(b,&n,0x33); /* [ebx+1]=='3' */
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[1]=n;put32(b,&n,0);
  put8(b,&n,0x8a);put8(b,&n,0x43);put8(b,&n,0x02); /* mov al,[ebx+2] */
  put8(b,&n,0x0c);put8(b,&n,0x20); /* lowercase */
  put8(b,&n,0x3c);put8(b,&n,0x64); /* 'd' */
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[2]=n;put32(b,&n,0);
  put8(b,&n,0x80);put8(b,&n,0x7b);put8(b,&n,0x03);put8(b,&n,0x32); /* '2' */
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[3]=n;put32(b,&n,0);
  put8(b,&n,0x80);put8(b,&n,0x7b);put8(b,&n,0x04);put8(b,&n,0x00); /* NUL */
  put8(b,&n,0x0f);put8(b,&n,0x85);jumps[4]=n;put32(b,&n,0);
  /* Copy "Aureal A3D 2.0 (TM)" into the 32-byte provider-name
   * local buffer at [esp+0x20] (no stack change). */
  for(i=0;i<20;i+=4){
    put8(b,&n,0xc7);put8(b,&n,0x44);put8(b,&n,0x24);
    put8(b,&n,(BYTE)(0x20+i));
    put8(b,&n,name[i]);put8(b,&n,name[i+1]);put8(b,&n,name[i+2]);put8(b,&n,name[i+3]);
  }
  /* The stock A3D Interactive provider uses classification 5. */
  put8(b,&n,0xbe);put32(b,&n,5);
  put8(b,&n,0xe9);rel_to_end_1=n;put32(b,&n,0);
  fb=n;
  for(i=0;i<5;i++)rel32(b,jumps[i],base,base+fb);
  /* Fallback for ANY other unrecognised setting: retain original "unknown". */
  {const BYTE old[] = {0x8b,0x0d,0x70,0xa4,0x51,0x00,
                       0x8b,0x15,0x74,0xa4,0x51,0x00,
                       0x89,0x4c,0x24,0x20,
                       0x89,0x54,0x24,0x24};
   for(i=0;i<sizeof(old);i++)put8(b,&n,old[i]);}
  put8(b,&n,0xe9);rel_to_end_2=n;put32(b,&n,0);
  rel32(b,rel_to_end_1,base,0x0046f27au);
  rel32(b,rel_to_end_2,base,0x0046f27au);
  return n;
}


int main(){BYTE b[256];DWORD n=gen_stub(b,0x20000000u);printf("%u\n",n);FILE *f=fopen("stub.bin","wb");fwrite(b,1,n,f);fclose(f);return 0;}
