# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
"""Generate ABI-correct stdcall stubs for the documented IA3dGeom vtable.
All unknown operations return E_NOTIMPL; accepted triangle vertices log exact IEEE float bits.
"""
from pathlib import Path
# Name, number of 32-bit arguments after `this`, special implementation.
methods=[
 ('Enable',1,''),('Disable',1,''),('IsEnabled',1,'bool'),
 ('SetOcclusionMode',1,''),('GetOcclusionMode',1,''),
 ('SetReflectionMode',1,''),('GetReflectionMode',1,''),
 ('SetReflectionGainScale',1,''),('GetReflectionGainScale',1,''),
 ('SetReflectionDelayScale',1,''),('GetReflectionDelayScale',1,''),
 ('PushMatrix',0,'zero'),('PopMatrix',0,'zero'),('LoadIdentity',0,''),
 ('LoadMatrix',1,''),('GetMatrix',1,''),('MultMatrix',1,''),
 ('Translate3f',3,''),('Translate3fv',1,''),('Rotate3f',4,''),('Rotate3fv',2,''),
 ('Scale3f',3,''),('Scale3fv',1,''),
 ('Begin',1,'begin'),('End',0,'end'),('Vertex3f',3,'vertex'),('Vertex3fv',1,'vecptr'),
 ('Normal3f',3,''),('Normal3fv',1,''),('Tag',1,''),
 ('SetOpeningFactorf',1,''),('SetOpeningFactorfv',1,''),
 ('NewMaterial',1,'out'),('BindMaterial',1,''),('NewList',1,'out'),
 ('BindListener',0,''),('BindSource',1,''),('NewEnvironment',1,'out'),
 ('BindEnvironment',1,''),('SetRenderMode',1,''),('GetRenderMode',1,''),
 ('SetPolygonBloatFactor',1,''),('GetPolygonBloatFactor',1,''),
 ('SetReflectionUpdateInterval',1,''),('GetReflectionUpdateInterval',1,''),
 ('SetOcclusionUpdateInterval',1,''),('GetOcclusionUpdateInterval',1,'')]
head='''/* IA3dGeom partial diagnostic implementation. Derived independently from ABI layout. */
typedef struct Geom Geom;
struct Geom {void **vt; volatile long ref; DWORD primitive;};
static HRESULT WINAPI gqi(Geom*,const GUID*,void**);
static ULONG WINAPI gadd(Geom*g){return (ULONG)InterlockedIncrement(&g->ref);}
static ULONG WINAPI grel(Geom*g){long n=InterlockedDecrement(&g->ref);if(n<1){g->ref=1;return 1;}return (ULONG)n;}
static const GUID iid_geom=G(0xc398e561,0xd90b,0x11d1,0x90,0xfb,0,0x60,0x08,0xa1,0xf4,0x41);
static void hexval(char*p,DWORD v){const char h[]="0123456789abcdef";for(int i=0;i<8;i++)p[i]=h[(v>>(28-4*i))&15];}
static void log3(const char*prefix,float a,float b,float c){
 union {float f;DWORD v;} x,y,z;
 x.f=a;y.f=b;z.f=c;
 char str[96];int i=0;
 while(prefix[i]&&i<48){str[i]=prefix[i];i++;}
 str[i++]=' ';hexval(str+i,x.v);i+=8;str[i++]=' ';
 hexval(str+i,y.v);i+=8;str[i++]=' ';
 hexval(str+i,z.v);i+=8;str[i]=0;
 logline(str);
}
static void gvertex(float a,float b,float c){log3("IA3dGeom.Vertex3f",a,b,c);}

'''
parts=[head]
for name,n,kind in methods:
 args=', '.join('DWORD x'+str(i) for i in range(n))
 arglist=', '+args if args else ''
 if kind=='vertex':arglist=', float a, float b, float c'
 if kind=='vecptr':arglist=', float *v'
 ret='BOOL' if kind=='bool' else ('ULONG' if kind=='zero' else 'HRESULT')
 body='(void)g;'+''.join('(void)x%d;'%i for i in range(n))
 if kind=='begin':body='g->primitive=x0;char m[]="IA3dGeom.Begin 00000000";hexval(m+15,x0);logline(m);return S_OK;'
 elif kind=='end':body='(void)g;logline("IA3dGeom.End");return S_OK;'
 elif kind=='vertex':body='(void)g;gvertex(a,b,c);return S_OK;'
 elif kind=='vecptr':body='(void)g;if(!v)return E_POINTER;gvertex(v[0],v[1],v[2]);return S_OK;'
 elif kind=='out':body='(void)g;if(x0)*(void**)(unsigned long)x0=0;logline("IA3dGeom.'+name+' not implemented");return E_NOTIMPL;'
 else:
  if name.startswith('Get') and n==1: body+='if(x0)*(DWORD*)(unsigned long)x0=0;'
  if kind=='bool' or kind=='zero':body+='return 0;'
  else:body+='return E_NOTIMPL;'
 parts.append('static %s WINAPI g_%s(Geom*g%s){%s}\n'%(ret,name,arglist,body))
parts.append('static void* geom_vt[]={ (void*)gqi,(void*)gadd,(void*)grel,\n')
for name,_,_ in methods:parts.append(' (void*)g_%s,\n'%name)
parts.append('};\nstatic Geom geom={geom_vt,1,0};\n')
parts.append('''static HRESULT WINAPI gqi(Geom*g,const GUID*i,void**o){
 if(!o)return E_POINTER;*o=0;logguid("IA3dGeom.QueryInterface",i);
 if(eqguid(i,&iid_unk)||eqguid(i,&iid_geom)){*o=g;gadd(g);return S_OK;}
 return E_NOINTERFACE;
}
''')
Path('win32/geom_trace.inc').write_text(''.join(parts))
print('IA3dGeom methods incl IUnknown:',len(methods)+3)
