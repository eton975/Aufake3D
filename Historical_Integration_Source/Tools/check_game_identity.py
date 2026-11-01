#!/usr/bin/env python3
"""Aufake3D 0.8.11 read-only A3D2 game identity & runtime evidence audit.
Never claims true provider activation from static strings or display text alone.
"""
import argparse,hashlib,json,re,sys,time
from pathlib import Path
PROFILES={'alice2000':'alice.exe','alice2011':'alice.exe','quake3':'quake3.exe','halflife':'hl.exe'}
KNOWN_ALICE_2011='08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50'
CANONICAL='Aureal A3D 2.0 (TM)'
MARKERS=('a3d2','s_milesdriver','Aureal A3D 2.0','Aureal A3D Interactive','unknown provider','mssa3d2.m3d','IA3d5')
def sha(b):return hashlib.sha256(b).hexdigest()
def scan(b):
    lo=b.lower()
    # Separate ASCII and UTF-16LE matching. A hit is only a hint, not proof of a selector branch.
    return {word:{'ascii':lo.count(word.lower().encode('ascii')),
                  'utf16le':lo.count(word.lower().encode('utf-16le'))}
            for word in MARKERS}
def read_log(p):
    if p is None:return ''
    if not p.is_file():raise ValueError('Missing log: '+str(p))
    if p.stat().st_size>8*1024*1024:raise ValueError('Log exceeds 8 MiB; use trimmed report')
    return p.read_bytes().decode('utf8','replace')
def trace_evidence(t):
    # Choose the most recent traced STARTUP, so appended earlier sessions cannot yield a false pass.
    if not t:return {'trace_provided':False,'provider_verified':False,'name_upgrade_logged':False}
    t=t.replace('\r\n','\n').replace('\r','\n')
    s=t.rsplit('AIL_STARTUP_BEGIN',1)[-1] if 'AIL_STARTUP_BEGIN' in t else t
    m=re.search(r'^A3D2_ENUM_SELECTED_CANDIDATE\s+0x([0-9a-f]+)$',s,re.I|re.M)
    if not m:return {'trace_provided':True,'provider_verified':False,'reason':'No canonical A3D2 enum candidate in latest session'}
    handle=int(m.group(1),16)
    open_match=re.search(r'^AIL_OPEN_BEGIN_PROVIDER\s+0x([0-9a-f]+)$',s,re.I|re.M)
    open_rc=re.search(r'^AIL_OPEN_RETURN\s+0x([0-9a-f]+)$',s,re.I|re.M)
    listener=re.search(r'^AIL_OPEN_LISTENER_RETURN\s+0x([0-9a-f]+)$',s,re.I|re.M)
    canon_enum='AIL_ENUM_PROVIDER_NAME '+CANONICAL in s
    valid=bool(canon_enum and handle>0 and open_match and int(open_match.group(1),16)==handle
               and open_rc and int(open_rc.group(1),16)==0 and listener and int(listener.group(1),16)!=0)
    return {'trace_provided':True,'provider_verified':valid,'canonical_enumeration':canon_enum,
            'enumerated_handle':f'0x{handle:08X}','open_handle':f'0x{int(open_match.group(1),16):08X}' if open_match else None,
            'open_return':f'0x{int(open_rc.group(1),16):08X}' if open_rc else None,
            'listener_return':f'0x{int(listener.group(1),16):08X}' if listener else None,
            'name_upgrade_logged':'A3D2_DISPLAY_NAME_UPGRADED '+CANONICAL in s,
            'a3dapi_loaded':'A3DAPI_MODULE_PATH ' in s}
def collect(profile,exe,trace=None,console=None):
    if profile not in PROFILES:raise ValueError('Unknown profile')
    if not exe.is_file() or exe.name.lower()!=PROFILES[profile]:raise ValueError('Wrong or missing game executable')
    data=exe.read_bytes()
    # Do not carry local usernames/paths or proprietary EXE contents in the default report.
    console_t=read_log(console)
    evidence=trace_evidence(read_log(trace))
    displayed=bool(re.search(re.escape(CANONICAL)+r'\s+provider opened\.',console_t,re.I))
    unknown=bool(re.search(r'unknown\s+provider opened\.',console_t,re.I))
    return {'schema':'aufake3d-0811-game-audit-1','profile':profile,'sha256_exe':sha(data),
            'verified_known_alice2011_exe':profile=='alice2011' and sha(data)==KNOWN_ALICE_2011,
            'static_markers_not_proof':scan(data),
            'runtime':evidence,'console_provided':console is not None,
            'console_canonical_label_observed':displayed,'console_unknown_label_observed':unknown,
            'conclusion':('Provider VERIFIED by runtime trace' if evidence.get('provider_verified') else
                          'Provider NOT VERIFIED (static strings and display text are not enough)'),
            'caveat':'Alice 2000 naming has not yet been independently confirmed in a Windows/Wine run; do not assume the Alice 2011 proxy applies.' if profile=='alice2000' else
                     'Record Windows/Wine versions and actual listening results separately.'}
def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--profile',required=True,choices=PROFILES);a.add_argument('--game-exe',required=True,type=Path)
    a.add_argument('--trace',type=Path);a.add_argument('--console',type=Path)
    a.add_argument('--output',type=Path)
    q=a.parse_args()
    try:r=collect(q.profile,q.game_exe,q.trace,q.console)
    except (OSError,ValueError) as e:print('ERROR:',e,file=sys.stderr);return 2
    s=json.dumps(r,indent=2)
    if q.output:q.output.write_text(s+'\n',encoding='utf8')
    else:print(s)
    return 0 if r['runtime']['provider_verified'] else 3 # 'not proven' is a non-zero audit status
if __name__=='__main__':raise SystemExit(main())
