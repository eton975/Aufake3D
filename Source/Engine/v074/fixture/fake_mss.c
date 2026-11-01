#define STDCALL __attribute__((stdcall))
int STDCALL fake_open(void *p){(void)p;return 0;}
int STDCALL fake_enum(void **n,void **p,char **name){(void)n;(void)p;(void)name;return 0;}
int STDCALL fake_other(void){return 17;}
