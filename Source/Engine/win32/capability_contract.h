/* Bounded capability-record writer, independent of the Win32 wrapper.
 * Capability records are little-endian DWORDs. Use byte access so callers with
 * older, shorter or unaligned records cannot trigger typed-struct overreads.
 * Preserve dwSize and all bytes beyond known, complete fields. Maxima refer
 * to one shared software voice pool, not separate 2D/3D hardware allocations.
 */
#ifndef A3D_CAPABILITY_CONTRACT_H
#define A3D_CAPABILITY_CONTRACT_H
static unsigned a3dcap_read32(const unsigned char*p){
 return (unsigned)p[0]|((unsigned)p[1]<<8)|((unsigned)p[2]<<16)|((unsigned)p[3]<<24);
}
static void a3dcap_write32(unsigned char*p,unsigned value){
 for(unsigned i=0;i<4;i++)p[i]=(unsigned char)(value>>(i*8));
}
/* 0 success, 1 NULL output, 2 record too short. hardware==1 describes no
 * physical accelerator. Software limits are supplied by the actual mixer. */
static unsigned a3dcap_fill(void *record,unsigned hardware,unsigned voices){
 if(!record)return 1;
 unsigned char *p=(unsigned char*)record;unsigned size=a3dcap_read32(p);
 unsigned minimum=hardware?16u:20u,words=hardware?9u:10u;
 if(size<minimum)return 2;
 for(unsigned word=1;word<words && word*4u+4u<=size;word++){
  unsigned value=0;
  if(!hardware){
   if(word==1)value=20;
   else if(word==5)value=2;
   else if(word==6)value=8000;
   else if(word==7)value=192000;
   else if(word==8||word==9)value=voices;
  }
  a3dcap_write32(p+word*4u,value);
 }
 return 0;
}
#endif
