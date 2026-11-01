/* Shared Win32 x86 declarations for v0.7.0-alpha activation launchers. */
#define STDCALL __stdcall
#define DLLIMPORT __declspec(dllimport)
typedef void *HANDLE;
typedef void *LPVOID;
typedef unsigned long DWORD;
typedef unsigned int UINT;
typedef int BOOL;
typedef unsigned long SIZE_T;
typedef const char *LPCSTR;
typedef char *LPSTR;
typedef unsigned char BYTE;
#define FALSE 0
#define CREATE_SUSPENDED 0x00000004u
#define MEM_COMMIT 0x00001000u
#define MEM_RESERVE 0x00002000u
#define PAGE_EXECUTE_READWRITE 0x40u
#define WAIT_INFINITE 0xffffffffu
#define STD_OUTPUT_HANDLE ((DWORD)-11)
#define STD_ERROR_HANDLE ((DWORD)-12)

typedef struct {
  DWORD cb; LPSTR lpReserved; LPSTR lpDesktop; LPSTR lpTitle;
  DWORD dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars;
  DWORD dwFillAttribute, dwFlags;
  unsigned short wShowWindow, cbReserved2;
  BYTE *lpReserved2;
  HANDLE hStdInput, hStdOutput, hStdError;
} STARTUPINFOA;
typedef struct {
  HANDLE hProcess; HANDLE hThread; DWORD dwProcessId; DWORD dwThreadId;
} PROCESS_INFORMATION;

DLLIMPORT DWORD STDCALL GetModuleFileNameA(HANDLE, LPSTR, DWORD);
DLLIMPORT LPSTR STDCALL GetCommandLineA(void);
DLLIMPORT BOOL STDCALL CreateProcessA(LPCSTR, LPSTR, LPVOID, LPVOID, BOOL, DWORD,
                                      LPVOID, LPCSTR, STARTUPINFOA *, PROCESS_INFORMATION *);
DLLIMPORT BOOL STDCALL ReadProcessMemory(HANDLE, LPCSTR, LPVOID, SIZE_T, SIZE_T *);
DLLIMPORT BOOL STDCALL WriteProcessMemory(HANDLE, LPVOID, LPCSTR, SIZE_T, SIZE_T *);
DLLIMPORT LPVOID STDCALL VirtualAllocEx(HANDLE, LPVOID, SIZE_T, DWORD, DWORD);
DLLIMPORT BOOL STDCALL VirtualProtectEx(HANDLE, LPVOID, SIZE_T, DWORD, DWORD *);
DLLIMPORT BOOL STDCALL FlushInstructionCache(HANDLE, LPCSTR, SIZE_T);
DLLIMPORT DWORD STDCALL ResumeThread(HANDLE);
DLLIMPORT DWORD STDCALL WaitForSingleObject(HANDLE, DWORD);
DLLIMPORT BOOL STDCALL GetExitCodeProcess(HANDLE, DWORD *);
DLLIMPORT BOOL STDCALL TerminateProcess(HANDLE, UINT);
DLLIMPORT BOOL STDCALL CloseHandle(HANDLE);
DLLIMPORT HANDLE STDCALL GetStdHandle(DWORD);
DLLIMPORT BOOL STDCALL WriteFile(HANDLE, LPCSTR, DWORD, DWORD *, LPVOID);
DLLIMPORT void STDCALL ExitProcess(UINT);

static DWORD slen(const char *s) { DWORD n=0; while(s[n])n++;return n; }
static void out(HANDLE h,const char *s) { DWORD n=0;WriteFile(h,s,slen(s),&n,0); }

static void u32(BYTE *p,DWORD n){p[0]=(BYTE)n;p[1]=(BYTE)(n>>8);p[2]=(BYTE)(n>>16);p[3]=(BYTE)(n>>24);}
