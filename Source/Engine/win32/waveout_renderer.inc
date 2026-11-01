/* v0.5.0 SOURCE COMMENTARY — waveOut renderer initialization
 * Bridges the A3D audio objects and streaming output. Pay attention to sample format,
 * buffer lifetimes and startup/shutdown ordering when investigating latency or stutter.
 */
/* Experimental process-wide WinMM streaming backend.
 * Native Windows and Wine both provide winmm.dll. One shared output device
 * mixes multiple sources; see stream_core.h and stream_winmm.inc.
 * This is NOT original Aureal DSP or a production-complete A3D2 emulator.
 */
typedef void* HMODULE;
IMPORT HMODULE WINAPI LoadLibraryA(const char*);
IMPORT void* WINAPI GetProcAddress(HMODULE,const char*);
typedef DWORD (WINAPI *WaveOpen)(HANDLE*,DWORD,const WaveFmt*,DWORD,DWORD,DWORD);
typedef DWORD (WINAPI *WaveHeaderOp)(HANDLE,WaveHeader*,DWORD);
typedef DWORD (WINAPI *WaveHandleOp)(HANDLE);
typedef struct {DWORD type,value,reserved;} WaveTime;
typedef DWORD (WINAPI *WaveGetPosition)(HANDLE,WaveTime*,DWORD);
static WaveOpen wopen=0;
static WaveHeaderOp wprep=0,wwrite=0,wunprep=0;
static WaveHandleOp wreset=0,wclose=0;
static WaveGetPosition wposition=0;
static HMODULE winmm_lib=0;
static int load_winmm(void){
 if(wopen&&wprep&&wwrite&&wunprep&&wreset&&wclose)return 1;
 if(!winmm_lib)winmm_lib=LoadLibraryA("winmm.dll");
 if(!winmm_lib)return 0;
 wopen=(WaveOpen)GetProcAddress(winmm_lib,"waveOutOpen");
 wprep=(WaveHeaderOp)GetProcAddress(winmm_lib,"waveOutPrepareHeader");
 wwrite=(WaveHeaderOp)GetProcAddress(winmm_lib,"waveOutWrite");
 wunprep=(WaveHeaderOp)GetProcAddress(winmm_lib,"waveOutUnprepareHeader");
 wreset=(WaveHandleOp)GetProcAddress(winmm_lib,"waveOutReset");
 wclose=(WaveHandleOp)GetProcAddress(winmm_lib,"waveOutClose");
 wposition=(WaveGetPosition)GetProcAddress(winmm_lib,"waveOutGetPosition"); /* optional */
 return wopen&&wprep&&wwrite&&wunprep&&wreset&&wclose;
}
#include "spatial_stereo.h"
#include "binaural_approx.h"
#include "measured_hrtf.h"
#include "acoustic_dsp.h"
#include "stream_winmm.inc"
