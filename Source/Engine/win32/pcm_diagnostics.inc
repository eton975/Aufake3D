/* Opt-in PCM diagnostics. No file I/O on the audio thread. */
#define A3D_CAPTURE_BYTES (48000u*4u*8u)
static unsigned char capture_pcm[A3D_CAPTURE_BYTES];
static DWORD capture_bytes=0,diag_peak=0,diag_nonzero=0,diag_input_peak=0;
static char capture_path[512];
static void diag_start(void){capture_bytes=diag_peak=diag_nonzero=diag_input_peak=0;capture_path[0]=0;DWORD n=GetEnvironmentVariableA("A3D_CAPTURE_WAV",capture_path,sizeof(capture_path));if(n>=sizeof(capture_path))capture_path[0]=0;}
static void diag_block(const unsigned char *pcm,DWORD bytes){
 for(DWORD i=0;i+1<bytes;i+=2){int v=(int)(short)((unsigned)pcm[i]|((unsigned)pcm[i+1]<<8));DWORD a=(DWORD)(v<0?-v:v);if(a>diag_peak)diag_peak=a;if(a)diag_nonzero++;}
 if(capture_path[0]&&capture_bytes<A3D_CAPTURE_BYTES){DWORD n=bytes;if(n>A3D_CAPTURE_BYTES-capture_bytes)n=A3D_CAPTURE_BYTES-capture_bytes;for(DWORD i=0;i<n;i++)capture_pcm[capture_bytes+i]=pcm[i];capture_bytes+=n;}
}
static void diag_u32(unsigned char*b,DWORD v){for(unsigned i=0;i<4;i++)b[i]=(unsigned char)(v>>(i*8));}
static void diag_finish(void){
 sr_logu("A3D.PCM.output_peak_s16",diag_peak);sr_logu("A3D.PCM.nonzero_samples",diag_nonzero);sr_logu("A3D.PCM.input_peak_s16",diag_input_peak);
 if(!capture_path[0])return;unsigned char h[44]={'R','I','F','F',0,0,0,0,'W','A','V','E','f','m','t',' ',16,0,0,0,1,0,2,0,0x80,0xbb,0,0,0,0xee,2,0,4,0,16,0,'d','a','t','a',0,0,0,0};diag_u32(h+4,36+capture_bytes);diag_u32(h+40,capture_bytes);
 HANDLE f=CreateFileA(capture_path,0x40000000u,3,0,2,128,0);if(f==INVALID_HANDLE_VALUE){logline("A3D.PCM.capture open failed");return;}DWORD done=0;WriteFile(f,h,44,&done,0);WriteFile(f,capture_pcm,capture_bytes,&done,0);CloseHandle(f);sr_logu("A3D.PCM.capture_bytes",capture_bytes);
}
