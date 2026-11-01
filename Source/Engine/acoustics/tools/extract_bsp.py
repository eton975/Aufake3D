#!/usr/bin/env python3
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
"""List or extract one BSP from a user-owned .pk3 ZIP archive without unpacking other assets."""
import argparse
from pathlib import Path
from zipfile import ZipFile

p = argparse.ArgumentParser()
p.add_argument('pk3', type=Path)
p.add_argument('--list', action='store_true')
p.add_argument('--map', help='Exact archive member name, e.g. maps/level.bsp')
p.add_argument('--output', type=Path, help='Destination for the selected BSP')
a = p.parse_args()
with ZipFile(a.pk3) as z:
    names = [n for n in z.namelist() if n.lower().endswith('.bsp')]
    if a.list or not a.map:
        print('\n'.join(names) if names else 'No .bsp members found')
    else:
        if a.map not in names:
            p.error('Map not found; use --list to display valid map names')
        if a.output is None:
            p.error('--output is required with --map')
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with z.open(a.map) as source, a.output.open('wb') as output:
            import shutil
            shutil.copyfileobj(source, output)
        print(f'Extracted {a.map} to {a.output}')
