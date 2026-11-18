#!/usr/bin/env python3
"""Build an append-only child of the exact local Sonic @ SAGE 2010 template."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from template import PARENT_SHA256, TemplateError, load_template


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', type=Path, help='Exact SAGE parent ROM; overrides SONIC_LAB_TEMPLATE')
    args = parser.parse_args()
    try:
        template, parent = load_template(args.template)
    except TemplateError as error:
        parser.error(str(error))
    if not __debug__:
        parser.error('Build checks require Python without -O or PYTHONOPTIMIZE.')
    assembler = shutil.which('vasmm68k_mot')
    if assembler is None:
        parser.error('vasmm68k_mot is required on PATH; no assets or build outputs were changed.')
    subprocess.run([sys.executable, 'native/tools/assets.py', '--template', str(template)], cwd=ROOT, check=True)
    now = datetime.now(timezone.utc)
    out = ROOT / 'native/builds' / (now.strftime('%Y-%m-%d_%H-%M-%S_%fZ_') + 'sage-lab')
    out.mkdir(parents=True, exist_ok=False)
    command = [assembler, '-Fbin', '-m68000', '-L', str(out/'lab.lst'), '-o', str(out/'payload.bin'), 'native/src/lab.asm']
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    (out/'assembler.log').write_text(result.stdout+result.stderr)
    if result.returncode:
        print(result.stdout+result.stderr)
        raise SystemExit(result.returncode)
    payload = (out/'payload.bin').read_bytes()
    assert payload[:4] == b'SAL2'
    names = ('boot', 'init', 'frame', 'switch', 'ring', 'monitor', 'end', 'reset', 'step', 'load',
             'layout', 'ghz_chunks', 'mz_chunks', 'tiles', 'lz_chunks', 'slz_chunks', 'syz_chunks', 'sbz_chunks')
    symbols = dict(zip(names, struct.unpack('>18I', payload[4:76])))
    assert symbols['end'] == 0x120000 + len(payload)
    assert parent[0x120000:0x120000+len(payload)] == b'\xFF'*len(payload)
    child = bytearray(parent)
    patches = []

    def patch(address, data, purpose, expected=None):
        before = parent[address:address+len(data)]
        if expected is not None:
            assert before == bytes.fromhex(expected), (hex(address), before.hex(), expected)
        child[address:address+len(data)] = data
        patches.append(dict(address=f'0x{address:06X}', bytes=len(data), purpose=purpose,
                            before_sha256=hashlib.sha256(before).hexdigest(),
                            after_sha256=hashlib.sha256(data).hexdigest()))

    def jsr(name):
        return b'\x4e\xb9' + struct.pack('>I', symbols[name])

    def jmp(name):
        return b'\x4e\xf9' + struct.pack('>I', symbols[name])

    patch(0x120000, payload, 'Lab 68000 code, data, and additional art in unused FF padding')
    patch(0x392, b'\x4e\xf9'+struct.pack('>I', symbols['boot']), 'Boot directly into the Green Hill hub', '11fc0000f600')
    patch(0xB8C, b'\x4e\x75', 'Lab has no save menu; omit original SRAM/live-memory guard', '4a39')
    patch(0x4E14, b'\x4e\xf9'+struct.pack('>I', symbols['load'])+b'\x4e\x71'*4,
          'Unconfigured acts return to the lab hub at the start of native level loading',
          '4eb8148423fc00000000ffffb280')
    patch(0x5182, jsr('init'), 'Initialize lab after native map and collision load', '4eb900011a70')
    patch(0x5332, jsr('frame'), 'Run lab and native object updates together', '4eb900011a70')
    patch(0x5314, b'\x4e\x71'*2, 'Lab owns the window text instead of clearing dialogue row', '4eb81562')
    patch(0x5366, b'\x4e\x71'*2, 'Lab owns the window text instead of native dialogue queue', '4eb815c8')
    for i, name in enumerate(('switch', 'ring', 'monitor')):
        patch(0x11AB6+4*(0xE0+i), struct.pack('>I', symbols[name]), 'Unused object ID '+hex(0xE0+i)+' -> '+name, '00011eba')
    patch(0x93D2, jmp('layout'), 'Flat native foregrounds with original zone backgrounds', '47f8a400323c')
    patch(0x8226, b'\x4e\x71'*2, 'Keep room bounds fixed while preserving native background scrolling', '61001206')
    patch(0x121E4, b'\x4e\x75', 'Disable original object lists; only the lab stations are spawned', '7000')
    patch(0x5AE4, b'\x4e\x75', 'Disable end-of-act camera lock and signpost art loading', '0c39')
    patch(0x17D5A, b'\x4e\x71'*2, 'Keep Sonic inside the visible right edge of each flat room', '06400040')
    patch(0x546A, struct.pack('>H', 0x1000), 'Drain the LZ lab: water stays below the flat room', '00b8')
    patch(0x5420, b'\x4e\x71'*6, 'LZ lab omits native wind tunnels, waterslides and changing water heights',
          '610002526100035261000048')
    for zone, name in enumerate(('ghz_chunks', 'lz_chunks', 'mz_chunks', 'slz_chunks', 'syz_chunks', 'sbz_chunks')):
        resource = 0x3850C + zone*16
        data = parent[resource+8:resource+9] + struct.pack('>I', symbols[name])[1:]
        patch(resource+8, data, f'Zone {zone}: native background chunks plus flat foreground arrangement')
    for zone, act, spawn_x, floor_y in ((0, 0, 80, 960), (0, 1, 48, 960), (2, 0, 48, 640),
                                       (4, 0, 48, 640), (1, 0, 48, 640), (3, 0, 48, 640), (5, 0, 48, 640),
                                       (0, 2, 48, 960), (2, 1, 48, 640), (4, 1, 48, 640),
                                       (1, 1, 48, 640), (3, 1, 48, 640), (5, 1, 48, 640)):
        camera_y = floor_y-192
        width = 1536 if (zone, act) == (0, 1) else 768
        patch(0x7CF2+zone*48+act*12, struct.pack('>6H', 4, 0, width-320, camera_y, camera_y, 96),
              f'Zone {zone} act {act}: {width}px room and fixed vertical camera')
        patch(0x7F62+zone*16+act*4, struct.pack('>HH', spawn_x, floor_y-20),
              f'Zone {zone} act {act}: spawn above the native flat floor')
    title = b'SONIC ALGORITHM LAB / TWELVE NATIVE STAGES V0.6'
    patch(0x120, title.ljust(48,b' '), 'Domestic title')
    patch(0x150, title.ljust(48,b' '), 'International title')
    checksum = sum(struct.unpack('>'+str((len(child)-0x200)//2)+'H',child[0x200:])) & 65535
    patch(0x18E, struct.pack('>H',checksum), 'Genesis checksum')
    rom = out/'Sonic Algorithm Lab - SAGE Engine.bin'
    rom.write_bytes(child)
    sources = [p for directory in ('native/src','native/tools','native/assets')
               for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    sources += [ROOT/'tools/headless.py', ROOT/'native/README.md', ROOT/'SOURCE_LINEAGE.json']
    for p in sources:
        dest = out/'source'/p.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p,dest)
    manifest = dict(name='Sonic Algorithm Lab - SAGE Engine', version='0.6', created_utc=now.isoformat(),
        rom=rom.name, bytes=len(child), sha1=hashlib.sha1(child).hexdigest(), sha256=hashlib.sha256(child).hexdigest(),
        checksum=f'0x{checksum:04X}', parent=dict(path=str(template),bytes=len(parent),sha1=hashlib.sha1(parent).hexdigest(),sha256=PARENT_SHA256),
        payload=dict(start='0x120000',end=hex(symbols['end']),bytes=len(payload)),symbols=symbols,patches=patches,
        rooms=dict(width=768, camera_x=[0,448],
                   hub=dict(zone='0x0001', tileset='Green Hill', floor_y=960, camera_y=768,
                            width=1536, camera_x=[0,1216]),
                   bubble=dict(zone='0x0000', tileset='Green Hill', floor_y=960, camera_y=768),
                   insertion=dict(zone='0x0200', tileset='Marble', floor_y=640, camera_y=448),
                   binary_search=dict(zone='0x0400', tileset='Spring Yard', floor_y=640, camera_y=448),
                   breadth_first=dict(zone='0x0100', tileset='Labyrinth', floor_y=640, camera_y=448),
                   priority=dict(zone='0x0300', tileset='Star Light', floor_y=640, camera_y=448),
                   first_fit=dict(zone='0x0500', tileset='Scrap Brain', floor_y=640, camera_y=448),
                   selection=dict(zone='0x0002', tileset='Green Hill', floor_y=960, camera_y=768),
                   odd_even=dict(zone='0x0201', tileset='Marble', floor_y=640, camera_y=448),
                   merge=dict(zone='0x0401', tileset='Spring Yard', floor_y=640, camera_y=448),
                   quick=dict(zone='0x0101', tileset='Labyrinth', floor_y=640, camera_y=448),
                   heap=dict(zone='0x0301', tileset='Star Light', floor_y=640, camera_y=448),
                   linear=dict(zone='0x0501', tileset='Scrap Brain', floor_y=640, camera_y=448),
                   objects='Lab switches, warp rings and numbered monitors only'),
        completion_sound=dict(id='0xC5', name='Native act-results cash register',
                              original_call='0x10ECA', queue='0x248E', trigger='Once per completed run'),
        source_lineage=json.loads((ROOT/'SOURCE_LINEAGE.json').read_text()),
        assets=json.loads((ROOT/'native/assets/provenance.json').read_text()),
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        validation='pending')
    (out/'BUILD_INFO.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(rom)
    print('SHA256',manifest['sha256'])


if __name__ == '__main__':
    main()
