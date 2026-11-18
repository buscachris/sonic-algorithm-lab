#!/usr/bin/env python3
"""Read-only exploration of the local SAGE template in a headless Genesis core."""
from pathlib import Path
import ctypes as C
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from headless import Emulator

TEMPLATE = Path('/home/anon/sonic-hacks-archive/sonic-1-at-sage-2010/Sonic the Hedgehog 1 @ SAGE 2010 (S1 Hack).bin')


def attach_state_api(e):
    e.core.retro_serialize_size.argtypes = []
    e.core.retro_serialize_size.restype = C.c_size_t
    e.core.retro_serialize.argtypes = [C.c_void_p, C.c_size_t]
    e.core.retro_serialize.restype = C.c_bool
    e.core.retro_unserialize.argtypes = [C.c_void_p, C.c_size_t]
    e.core.retro_unserialize.restype = C.c_bool


def save_state(e, path):
    attach_state_api(e)
    n = e.core.retro_serialize_size()
    buf = C.create_string_buffer(n)
    assert e.core.retro_serialize(buf, n)
    Path(path).write_bytes(buf.raw)


def load_state(e, path):
    attach_state_api(e)
    b = Path(path).read_bytes()
    buf = C.create_string_buffer(b)
    assert e.core.retro_unserialize(buf, len(b))


def boot_hub(e):
    e.word_swap = True
    e.run(2402)
    e.run(2, ('START',))
    e.run(242)
    e.run(2, ('START',))
    e.run(302)
    r = e.ram(0, 65536)
    assert r[0xf600] == 0xc and r[0xb2e0:0xb2e2] == b'\x07\x00', (r[0xf600], r[0xb2e0:0xb2e2])


def describe(e):
    r = e.ram(0, 65536)
    w = lambda a: int.from_bytes(r[a:a+2], 'big')
    objects = []
    for a in range(0xd000, 0xf000, 0x40):
        if r[a]:
            objects.append(dict(slot=f'{a:04x}', id=f'{r[a]:02x}', routine=r[a+0x24],
                                subtype=r[a+0x28], x=w(a+8), y=w(a+12),
                                art=f'{w(a+2):04x}', mapping=f'{int.from_bytes(r[a+4:a+8], "big"):06x}'))
    return dict(frame=e.frames, mode=r[0xf600], zone=w(0xb2e0),
                x=w(0xd008), y=w(0xd00c), camera=[w(0xf700),w(0xf704)],
                bounds=[w(a) for a in range(0xf720,0xf730,2)], objects=objects)


def capture(e, out, name):
    out.mkdir(parents=True, exist_ok=True)
    e.image().resize((640,448)).save(out / (name + '.png'))
    (out / (name + '.ram')).write_bytes(e.ram(0, 65536))
    d = describe(e)
    (out / (name + '.json')).write_text(json.dumps(d, indent=2)+'\n')
    print(json.dumps(d), flush=True)


if __name__ == '__main__':
    out = ROOT / 'native/research/hub-route'
    state = out / 'parent-hub.state'
    out.mkdir(parents=True, exist_ok=True)
    with Emulator(TEMPLATE) as e:
        e.word_swap = True
        if state.exists():
            load_state(e, state)
            e.run(1)
        else:
            boot_hub(e)
            save_state(e, state)
        capture(e, out, 'hub')
        direction = sys.argv[1].upper() if len(sys.argv)>1 else 'RIGHT'
        for i in range(1, 13):
            e.run(45, (direction,))
            capture(e, out, f'{direction.lower()}-{i:02}')
        save_state(e, out / (direction.lower() + '-end.state'))
