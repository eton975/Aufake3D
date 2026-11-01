#!/usr/bin/env python3
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
"""Read-only PE/strings inventory for Alice's Miles/Aureal load path.
No executable code from the input is run. No third-party Python packages required.
"""
import argparse,hashlib,json,pathlib,re,struct

def pe_imports(data):
    if data[:2]!=b'MZ': raise ValueError('MZ signature missing')
    pe=struct.unpack_from('<I',data,0x3c)[0]
    if data[pe:pe+4]!=b'PE\0\0': raise ValueError('PE signature missing')
    nsec=struct.unpack_from('<H',data,pe+6)[0]
    optsize=struct.unpack_from('<H',data,pe+20)[0]
    op=pe+24;magic=struct.unpack_from('<H',data,op)[0]
    if magic not in (0x10b,0x20b): raise ValueError('not supported PE')
    dr=op+(96 if magic==0x10b else 112)
    rva=struct.unpack_from('<I',data,dr+8)[0]
    so=op+optsize;sections=[]
    for i in range(nsec):
        p=so+i*40
        vsize,va,rawsize,raw=struct.unpack_from('<IIII',data,p+8)
        sections.append((va,va+max(vsize,rawsize),raw))
    def phys(addr):
        for a,b,o in sections:
            if a<=addr<b:return o+addr-a
        raise ValueError('unmapped RVA %#x'%addr)
    def cstr(p):
        j=data.find(b'\0',p,p+512)
        if j<0: raise ValueError('unterminated name')
        return data[p:j].decode('ascii','replace')
    imports=[]
    if not rva:return imports
    at=phys(rva)
    for _ in range(512):
        oft,t,fc,name,ft=struct.unpack_from('<IIIII',data,at);at+=20
        if not(any((oft,t,fc,name,ft))):break
        imports.append(cstr(phys(name)))
    return imports

def fingerprint(path):
    b=path.read_bytes()
    strings=re.findall(rb'[\x20-\x7e]{5,}',b)
    terms=[]
    for s in strings:
        low=s.lower()
        if any(k in low for k in (b'a3d',b'aureal',b'co',b'mss',b'geometry',b'reflection',b'wave')) and len(s)<180:
            if b'a3d' in low or b'aureal' in low or b'geometry' in low or b'reflection' in low:
                terms.append(s.decode('latin1'))
    return {'file':path.name,'size':len(b),'sha256':hashlib.sha256(b).hexdigest(),
            'imports':pe_imports(b),'a3d_clues':sorted(set(terms))[:80]}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('files',nargs='+',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path)
    a=p.parse_args();r=[]
    for f in a.files:
        try:r.append(fingerprint(f))
        except (ValueError,OSError,struct.error) as e:r.append({'file':str(f),'error':str(e)})
    result=json.dumps(r,indent=2)
    if a.out:a.out.write_text(result+'\n',encoding='utf-8')
    else:print(result)
