#!/usr/bin/env python3
"""Run the patched 68000 ROM in a real headless libretro Genesis core.

The playthrough uses controller inputs only. Separate algorithm cases select
datasets through RAM and reload the native level to initialize them. Every
operation and result is then computed by the ROM, not by this frontend.
Separate floor probes seed Sonic's position and let native collision settle him.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import time

from probe import Emulator, save_state, load_state
from oracles import NAMES, ZONES, SORT, initial, sort_trace, operations, final
from template import load_template


def word(e, address):
    return int.from_bytes(e.ram(address, 2), 'big')


def state(e):
    r = e.ram(0xb400, 0x100)
    fields = ('version', 'room', 'algorithm', 'dataset', 'running', 'done',
              'phase', 'timer', 'comparisons', 'swaps', 'outer', 'index',
              'pass', 'pass_swapped', 'left', 'right', 'want_swap', 'message',
              'last_left', 'last_right', 'operations', 'state', 'target', 'low',
              'high', 'mid', 'event', 'result_len', 'auto_delay', 'mask')
    s = dict(zip(fields, struct.unpack('>30H', r[4:64])))
    s.update(magic=r[:4].decode('ascii'), values=list(r[0x40:0x48]),
             ids=list(r[0x48:0x50]), completed=int.from_bytes(r[0x60:0x62], 'big'),
             gates=int.from_bytes(r[0x62:0x64], 'big'),
             frames=int.from_bytes(r[0x6c:0x70], 'big'),
             last_action=int.from_bytes(r[0x70:0x72], 'big'),
             actions=int.from_bytes(r[0x72:0x74], 'big'))
    for key, offset in (('elapsed', 0x74), ('total_wait', 0x76), ('pending', 0x78), ('result_mask', 0x7a)):
        s[key] = int.from_bytes(r[offset:offset+2], 'big')
    for key, offset in (('aux', 0x50), ('initial', 0x58), ('queue', 0x80),
                        ('result', 0x88), ('graph', 0x90), ('parents', 0x98)):
        s[key] = list(r[offset:offset+8])
    for key, offset in (('waits', 0xa0), ('turnaround', 0xb0)):
        s[key] = list(struct.unpack('>4H', r[offset:offset+8]))
    s.update(zip(('minimum', 'width', 'base', 'end', 'write', 'pivot',
                  'stack_len', 'heap_size', 'root', 'child', 'building'),
                 struct.unpack('>11H', r[0xc0:0xd6])))
    return s


def matches(actual, expected, context):
    for key, value in expected.items():
        assert actual[key] == value, (context, key, actual[key], value)


def snap(e, out, name):
    e.image().save(out / (name + '.png'))
    s = state(e)
    s.update(x=word(e, 0xd008), y=word(e, 0xd00c), zone=word(e, 0xb2e0))
    (out / (name + '.json')).write_text(json.dumps(s, indent=2) + '\n')
    return s


def sequence(e, steps):
    for frames, buttons in steps:
        e.run(frames, buttons)


def move_to(e, target, jump=False):
    """Controller steering with RAM feedback, without writing player state."""
    e.run(2)
    if jump:
        # Cores return from retro_run at different points in the video frame.
        # Hold the press until the native player update has consumed it.
        for _ in range(8):
            e.run(1, ('A',))
            if e.ram(0xd022, 1)[0] & 2:
                break
        else:
            raise AssertionError(('Controller jump did not start', target))
    for frame in range(240):
        x = word(e, 0xd008)
        velocity = int.from_bytes(e.ram(0xd010, 2), 'big', signed=True) / 256
        airborne = bool(e.ram(0xd022, 1)[0] & 2)
        if frame > 5 and not airborne and abs(x-target) < 2 and abs(velocity) < 0.15:
            break
        predicted = x + velocity*abs(velocity)/(2*(0.09375 if airborne else 0.5))
        steer = () if abs(x-target) < 2 and abs(velocity) < 0.1 else (
            ('RIGHT',) if predicted < target else ('LEFT',))
        if jump and frame > 20 and not airborne and abs(x-target) > 8 and abs(velocity) < 0.35:
            # If the first jump lands against a solid switch, release and
            # jump again. This remains ordinary controller input.
            e.run(2, steer)
            e.run(4, steer+('A',))
            continue
        e.run(1, steer + (('A',) if jump and airborne else ()))
    else:
        raise AssertionError(('Controller could not reach target', target, x, velocity, airborne))
    e.run(2)


def static_check(rom, template=None):
    if not __debug__:
        raise ValueError('Validation checks require Python without -O or PYTHONOPTIMIZE.')
    b = rom.read_bytes()
    info = json.loads((rom.parent / 'BUILD_INFO.json').read_text())
    parent_path, p = load_template(template, recorded_path=info['parent']['path'])
    assert hashlib.sha256(p).hexdigest() == info['parent']['sha256']
    assert hashlib.sha256(b).hexdigest() == info['sha256']
    assert len(b) == len(p) == 2097152
    checksum = sum(struct.unpack('>'+str((len(b)-512)//2)+'H', b[512:])) & 65535
    assert checksum == int.from_bytes(b[0x18e:0x190], 'big')
    mask = bytearray(len(b))
    for patch in info['patches']:
        a, n = int(patch['address'], 16), patch['bytes']
        assert hashlib.sha256(p[a:a+n]).hexdigest() == patch['before_sha256']
        assert hashlib.sha256(b[a:a+n]).hexdigest() == patch['after_sha256']
        mask[a:a+n] = b'\x01' * n
    changed = sum(x != y for x, y in zip(b, p))
    assert all(x == y or mask[i] for i, (x, y) in enumerate(zip(b, p)))
    # Every replacement resource and hook is confined to a declared range.
    for name, digest in info['source_sha256'].items():
        assert hashlib.sha256((rom.parent/'source'/name).read_bytes()).hexdigest() == digest
    assets = info['assets']
    for asset in assets['extracted']:
        a, n = int(asset['address'], 16), asset['bytes']
        assert hashlib.sha256(p[a:a+n]).hexdigest() == asset['sha256']
        assert b[a:a+n] == p[a:a+n], asset['asset']
    # Font comes from SAGE's dialogue, with only its background made transparent.
    font = b''.join(p[0xE9B90+i*32:0xE9B90+(i+1)*32] for i in assets['font_tile_order'])
    font = bytes(((0 if v >> 4 == 12 else v >> 4) << 4) |
                 (0 if v & 15 == 12 else v & 15) for v in font)
    art = info['symbols']['tiles']
    assert b[art:art+len(font)] == font
    ring_start = len(font)+8*32
    assert b[art+ring_start:art+ring_start+44*32] == p[0xD725E:0xD725E+44*32]
    for zone, name, base, count in ((0, 'ghz', 0x59200, 63), (2, 'mz', 0x72F4C, 67),
                                    (1, 'lz', 0x65768, 57), (3, 'slz', 0x81B90, 50),
                                    (4, 'syz', 0x90434, 65), (5, 'sbz', 0x9E2B0, 67)):
        pointer = info['symbols'][name+'_chunks']
        assert b[pointer:pointer+count*512] == p[base:base+count*512]
        resource = 0x3850C+zone*16
        assert b[resource:resource+8] == p[resource:resource+8]  # original art/blocks
        assert b[resource+12:resource+16] == p[resource+12:resource+16]  # palette/music
        assert b[0x596C+zone*4:0x5970+zone*4] == p[0x596C+zone*4:0x5970+zone*4]
    for address, size in ((0x527C, 6), (0x8206, 6), (0x2A6A, 8), (0x7E72, 6), (0x922A, 6)):
        assert b[address:address+size] == p[address:address+size]
    # The parent's native results card queues C5 at this exact call site.
    assert p[0x10eca:0x10ed4] == bytes.fromhex('303c00c54eb90000248e')
    assert b[0x10eca:0x10ed4] == p[0x10eca:0x10ed4]
    return dict(sha256=info['sha256'], checksum=f'{checksum:04X}',
                parent_path=str(parent_path), parent_sha256=hashlib.sha256(p).hexdigest(),
                changed_bytes=changed, patch_count=len(info['patches']),
                source_files=len(info['source_sha256']), diff_scope='passed',
                native_asset_provenance='passed', completion_sfx='C5, native act-results cash register')


def playthrough(e, out):
    """Actual button input for all twelve routes and all four room controls."""
    checks = []
    e.run(900)
    matches(state(e), dict(magic='SAL2', version=0x0600, room=0, gates=0), 'boot')
    assert word(e, 0xb2e0) == 1
    snap(e, out, '01-hub')
    save_state(e, out/'hub.state')
    for algorithm, name in enumerate(NAMES):
        # Cross unselected solid switches with short jumps into the gaps.
        for gap in range(152, 96+112*algorithm, 112):
            move_to(e, gap, jump=True)
        move_to(e, 96+112*algorithm, jump=True)
        assert state(e)['gates'] & (1 << algorithm)
        snap(e, out, name+'-gate')
        sequence(e, [(10, ('A',)), (600, ())])
        assert word(e, 0xb2e0) == ZONES[algorithm]
        matches(state(e), initial(algorithm, 0), name+' entry')
        save_state(e, out/(name+'-entry.state'))
        snap(e, out, name+'-entry')

        move_to(e, 64, jump=True)
        e.run(160)
        matches(state(e), dict(last_action=12, operations=1, running=0, phase=0), name+' STEP')
        one_step = state(e)
        e.run(80)
        assert state(e)['operations'] == one_step['operations']
        move_to(e, 192, jump=True)
        e.run(90)
        matches(state(e), initial(algorithm, 0), name+' RESET')
        assert state(e)['last_action'] == 14

        # Cycle every built-in dataset through the native INPUT switch.
        for dataset in (1, 2, 3, 4, 0):
            move_to(e, 256, jump=True)
            e.run(10)
            matches(state(e), initial(algorithm, dataset), name+' INPUT')
            assert state(e)['last_action'] == 15

        move_to(e, 128, jump=True)
        assert state(e)['last_action'] == 13 and state(e)['running'] == 1
        if algorithm == 0:
            e.run(90)
            e.press('START')
            e.run(30)
            paused, sonic = state(e), e.ram(0xd000, 0x40)
            e.run(40)
            assert state(e) == paused and e.ram(0xd000, 0x40) == sonic
            e.press('START')
            e.run(30)
            assert state(e)['frames'] > paused['frames']
            move_to(e, 128, jump=True)
            e.run(160)
            matches(state(e), dict(running=0, phase=0), 'RUN toggle off')
            count = state(e)['operations']
            e.run(100)
            assert state(e)['operations'] == count
            move_to(e, 128, jump=True)
            assert state(e)['running'] == 1
            checks.append('Start freezes/resumes the player and algorithm; RUN toggles off/on')
        for _ in range(70):
            e.run(100)
            if state(e)['done']:
                break
        matches(state(e), final(algorithm, 0), name+' RUN result')
        assert e.ram(0xb740, 1) == b'\xc5', name+' completion sound'
        snap(e, out, name+'-complete')
        move_to(e, 224, jump=True)  # Land between RESET and INPUT.
        move_to(e, 320, jump=True)  # Clear INPUT without changing the selection.
        move_to(e, 400)
        sequence(e, [(16, ('A',)), (600, ())])
        matches(state(e), dict(room=0, completed=(1 << (algorithm+1))-1), name+' return')
        assert word(e, 0xb2e0) == 1
        snap(e, out, 'hub-after-'+name)
        checks.append(name+': gate/warp, STEP, RESET, all five INPUT selections, RUN, HUB/completion')
        print('controller', name, 'passed', flush=True)
    return checks


def monitor_check(e, s, algorithm):
    count = 4 if algorithm == 4 else 5 if algorithm == 5 else 8
    for i in range(count):
        address = 0xd500+0x40*i
        assert e.ram(address, 1) == b'\xe2'
        value = s['values'][i]
        # Alphabet indices 1..26, digits 27..36, dash 37.
        assert e.ram(address+0x2e, 1)[0] == (37 if value == 255 else 27+value), (algorithm, i, value)
        assert e.ram(address+0x33, 1)[0] == 1+s['ids'][i]


def algorithm_cases(e, out):
    results = []
    for algorithm, name in enumerate(NAMES):
        for dataset in range(5):
            load_state(e, out/(name+'-entry.state'))
            # Only select the problem and request a native reload. ResetWorld
            # must initialize every array, pointer and counter itself.
            e.poke(0xb40a, struct.pack('>H', dataset))
            e.poke(0xfe02, b'\x00\x01')
            e.run(700)
            matches(state(e), initial(algorithm, dataset), (name, dataset, 'reload'))
            monitor_check(e, state(e), algorithm)
            e.poke(0xb40c, b'\x00\x01')
            prior = state(e)
            observed, commits, exchanges = [], 0, 0
            if algorithm < 2:
                trace, expected_items = sort_trace(SORT[dataset], algorithm)
            else:
                steps = operations(algorithm, dataset)
            for frame in range(7000):
                e.run(1)
                s = state(e)
                matches(s, dict(magic='SAL2', version=0x0600, room=algorithm+1,
                                algorithm=algorithm, dataset=dataset), (name, dataset, 'frame'))
                assert s['running'] in (0, 1) and s['done'] in (0, 1)
                if algorithm < 2:
                    assert s['phase'] in (0, 2, 3)
                    assert sorted(s['ids']) == list(range(8))
                    assert sorted(zip(s['values'], s['ids'])) == sorted(zip(SORT[dataset], range(8)))
                    if s['operations'] != prior['operations']:
                        assert s['operations'] == prior['operations']+1
                        op = (s['left'], s['right'], s['last_left'], s['last_right'], s['want_swap'])
                        assert op == trace[len(observed)], (name, dataset, op)
                        assert s['comparisons'] == s['operations']
                        observed.append(op)
                    if s['values'] != prior['values'] or s['ids'] != prior['ids']:
                        assert prior['phase'] == 3 and prior['timer'] == 31
                        left, right = prior['left'], prior['right']
                        assert right == left+1 and prior['values'][left] > prior['values'][right]
                        for key in ('values', 'ids'):
                            wanted = prior[key][:]
                            wanted[left], wanted[right] = wanted[right], wanted[left]
                            assert s[key] == wanted
                        exchanges += 1
                    assert s['swaps'] == exchanges
                    if s['phase']:
                        assert 0 <= s['left'] < s['right'] < 8
                else:
                    animated = algorithm in (6, 7, 9, 10)
                    assert s['phase'] in ((0, 2, 3) if animated else (0, 4))
                    if 6 <= algorithm <= 10:
                        assert sorted(zip(s['values'], s['ids'])) == sorted(zip(SORT[dataset], range(8)))
                    else:
                        assert s['ids'] == list(range(8))
                    if s['operations'] != prior['operations']:
                        assert s['operations'] == prior['operations']+1
                        assert len(observed) < len(steps)
                        before, _ = steps[len(observed)]
                        matches(s, before, (name, dataset, 'operation', len(observed)))
                        observed.append(before)
                    if prior['phase'] and s['phase'] == 0:
                        assert prior['timer'] == (31 if prior['phase'] == 3 else 1)
                        if prior['phase'] == 2:
                            assert not prior['want_swap']
                        matches(s, steps[commits][1], (name, dataset, 'commit', commits))
                        commits += 1
                    elif s['values'] != prior['values'] or s['ids'] != prior['ids']:
                        raise AssertionError((name, dataset, 'Items changed outside a commit'))
                    if s['phase'] == 3:
                        assert 0 <= s['left'] < s['right'] < 8
                monitor_check(e, s, algorithm)
                if s['done']:
                    break
                prior = s
            else:
                raise AssertionError((name, dataset, 'algorithm timed out', s))
            matches(s, final(algorithm, dataset), (name, dataset, 'final'))
            assert e.ram(0xb740, 1) == b'\xc5', (name, dataset, 'completion sound')
            assert s['completed'] & (1 << algorithm)
            assert len(observed) == (len(trace) if algorithm < 2 else len(steps))
            if algorithm >= 2:
                assert commits == len(steps)
            result = dict(algorithm=name, dataset=dataset, operations=s['operations'],
                          comparisons=s['comparisons'], frames=frame+1, final=final(algorithm, dataset),
                          completion_sfx='C5', completion_once=True)
            results.append(result)
            e.run(2)
            snap(e, out, name+f'-dataset-{dataset}-result')
            e.poke(0xb740, b'\x00')
            e.run(120)
            assert e.ram(0xb740, 1) == b'\x00', (name, dataset, 'completion retriggered')
        print('five cases', name, 'passed', flush=True)
    return results


def manual_completion_checks(e, out):
    """Finish each demo with the real STEP switch and check the one-shot cue."""
    checks = []
    for algorithm, name in enumerate(NAMES):
        load_state(e, out/(name+'-entry.state'))
        expected = final(algorithm, 0)
        e.poke(0xb40c, b'\x00\x01')
        for _ in range(7000):
            s = state(e)
            if s['operations'] == expected['operations']-1 and not s['phase']:
                break
            e.run(1)
        else:
            raise AssertionError((name, 'could not pause before final operation'))
        e.poke(0xb40c, b'\x00\x00')
        e.poke(0xb740, b'\x00')
        move_to(e, 64, jump=True)
        e.run(120)
        matches(state(e), expected, (name, 'manual completion'))
        assert state(e)['last_action'] == 12
        assert e.ram(0xb740, 1) == b'\xc5'
        e.poke(0xb740, b'\x00')
        e.run(120)
        assert e.ram(0xb740, 1) == b'\x00'
        checks.append(dict(algorithm=name, final_operation='controller STEP',
                           completion_sfx='C5', completion_once=True, status='passed'))
    print('manual completion sounds passed', flush=True)
    return checks


def reload_checks(e, out):
    checks = []
    for algorithm, name in enumerate(NAMES):
        for next_act in (False, True):
            load_state(e, out/(name+'-entry.state'))
            zone = (ZONES[algorithm] & 0xff00) | 3 if next_act else ZONES[algorithm]
            e.poke(0xb2e0, struct.pack('>H', zone))
            e.poke(0xfe02, b'\x00\x01')
            e.run(700)
            matches(state(e), dict(room=0 if next_act else algorithm+1, operations=0), (name, next_act))
            assert word(e, 0xb2e0) == (1 if next_act else zone)
            checks.append(dict(algorithm=name, request=hex(zone), room=state(e)['room'],
                               method='injected native level request', status='passed'))
    return checks


def flat_room_checks(e, out, rom):
    """Probe native collision separately from the controller-only playthrough."""
    # The chunk lookup uses 8 interleaved 128-byte FG/BG rows. The engine
    # reuses part of the larger initialization clear range for other tables.
    info = json.loads((rom.parent/'BUILD_INFO.json').read_text())
    parent = Path(info['parent']['path']).read_bytes()
    results = []

    def place(x, floor):
        # Set an airborne position below the rings; gravity and the ROM's
        # collision engine must find the floor without help from this tool.
        e.poke(0xd008, struct.pack('>HHHH', x, 0, floor-40, 0))
        e.poke(0xd010, bytes(6))
        e.poke(0xd022, b'\x02')
        e.poke(0xd024, b'\x02')
        e.poke(0xd026, b'\x00')

    for room, name in enumerate(('hub',)+tuple(n+'-entry' for n in NAMES)):
        load_state(e, out/(name+'.state'))
        e.run(2)
        route = 1 if room == 0 else ZONES[room-1]
        zone, act = route >> 8, route & 255
        floor, fg_row = (960, 3) if zone == 0 else (640, 2)
        chunk = (64, 58, 68, 51, 66, 68)[zone]
        chunks = 6 if room == 0 else 3
        room_width = chunks*256
        camera_right, player_right = room_width-320, room_width-24
        camera_y = floor-192
        expected_bounds = struct.pack('>8H', 0, camera_right, camera_y, camera_y,
                                      0, camera_right, camera_y, camera_y)
        # Derive the background independently from the original ROM's table.
        bg = 0xD399C+struct.unpack_from('>H', parent, 0xD399C+zone*24+act*6+2)[0]
        width, height = (v+1 for v in parent[bg:bg+2])
        expected_layout = bytearray(0x400)
        for row in range(height):
            start = 0x40+row*0x80
            expected_layout[start:start+width] = parent[bg+2+row*width:bg+2+(row+1)*width]
        expected_layout[fg_row*0x80:fg_row*0x80+chunks] = bytes([chunk])*chunks
        expected_layout[(fg_row+1)*0x80:(fg_row+1)*0x80+chunks] = bytes([chunk+1])*chunks
        assert e.ram(0xa400, len(expected_layout)) == expected_layout
        assert e.ram(0xf720, 16) == expected_bounds
        objects = [e.ram(a, 1)[0] for a in range(0xd000, 0xf000, 0x40)]
        assert set(objects) <= {0, 1, 0xe0, 0xe1, 0xe2}
        counts = {hex(i): objects.count(i) for i in (1, 0xe0, 0xe1, 0xe2)}
        assert list(counts.values()) == ([1, 12, 12, 0] if room == 0 else [1, 4, 1, 8]), (name, counts)
        samples = []
        for x in list(range(16, player_right, 16)) + [player_right]:
            place(x, floor)
            e.run(40)
            y = word(e, 0xd00c)
            assert state(e)['room'] == room and e.ram(0xd024, 1) == b'\x02'
            assert y in (floor-29, floor-20), (name, x, y)
            assert not e.ram(0xd022, 1)[0] & 2, (name, x, 'still airborne')
            assert word(e, 0xf704) == camera_y
            assert e.ram(0xf720, 16) == expected_bounds
            samples.append([x, word(e, 0xd008), y])

        # Hold toward both room ends and jump there. These inputs verify the
        # native side clamps and streamed floor after the seeded floor probes.
        e.run(180, ('RIGHT',))
        e.run(60, ('A',))
        e.run(20)
        assert (word(e, 0xd008), word(e, 0xd00c)) == (player_right, floor-20)
        assert word(e, 0xf700) == camera_right and word(e, 0xf704) == camera_y
        assert e.ram(0xd024, 1) == b'\x02'
        snap(e, out, name+'-right-edge')

        # Restore the entry camera before the left-end run. Teleporting Sonic
        # behind the camera violates the native horizontal-scroll assumptions.
        load_state(e, out/(name+'.state'))
        e.run(2)
        move_to(e, 16, jump=True)
        e.run(180, ('LEFT',))
        e.run(60, ('A',))
        e.run(20)
        assert (word(e, 0xd008), word(e, 0xd00c)) == (16, floor-20)
        assert word(e, 0xf700) == 0 and word(e, 0xf704) == camera_y
        assert e.ram(0xd024, 1) == b'\x02'
        assert e.ram(0xf720, 16) == expected_bounds
        assert state(e)['room'] == room
        snap(e, out, name+'-left-edge')
        results.append(dict(room=name, objects=counts, floor_samples=samples,
                            player_end_limits=[16, player_right], camera_x=[0, camera_right],
                            floor_y=floor, camera_y=camera_y,
                            tileset=('Green Hill', 'Labyrinth', 'Marble', 'Star Light', 'Spring Yard', 'Scrap Brain')[zone],
                            native_background_layout=f'0x{bg:X}', status='passed'))
        print('floor', name, 'passed', flush=True)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('rom', type=Path)
    parser.add_argument('--template', type=Path, help='Exact SAGE parent ROM; overrides environment and manifest path')
    parser.add_argument('--core', type=Path, help='Libretro core; required unless --static-only')
    parser.add_argument('--static-only', action='store_true', help='Verify ROM, source, patches and assets without running an emulator')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if not args.static_only and args.core is None:
        parser.error('--core is required unless --static-only is selected')
    if args.static_only and args.core is not None:
        parser.error('--core and --static-only cannot be combined')
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = dict(rom=str(args.rom.resolve()), core=str(args.core.resolve()) if args.core else None,
                  mode='static' if args.static_only else 'full', static='pending',
                  controller_playthrough='not_requested' if args.static_only else 'pending')
    try:
        report['static'] = static_check(args.rom, args.template)
        if args.static_only:
            report['status'] = 'passed'
            return
        report['core_sha256'] = hashlib.sha256(args.core.read_bytes()).hexdigest()
        with Emulator(args.rom, core=args.core) as e:
            e.word_swap = True
            report['core_name'] = e.info.library_name.decode()
            report['core_version'] = e.info.library_version.decode()
            report['controller_playthrough'] = playthrough(e, args.out)
            report['algorithm_cases'] = algorithm_cases(e, args.out)
            report['manual_completion'] = manual_completion_checks(e, args.out)
            report['reload_checks'] = reload_checks(e, args.out)
            report['flat_rooms'] = flat_room_checks(e, args.out, args.rom)
            e.capture_audio = True
            e.run(60)
            pcm = struct.unpack('<'+'h'*(len(e.audio)//2), e.audio)
            assert max(pcm) > min(pcm)
            report['audio'] = dict(samples=len(pcm), min=min(pcm), max=max(pcm),
                                   sha256=hashlib.sha256(e.audio).hexdigest(), listening_test=False)
            report['callback_errors'] = e.callback_errors
            assert not e.callback_errors
        report['status'] = 'passed'
    except Exception as error:
        report['status'] = 'failed'
        report['error'] = repr(error)
        raise
    finally:
        report['elapsed_seconds'] = round(time.monotonic()-started, 3)
        (args.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({k: report[k] for k in ('status','core','elapsed_seconds')}), flush=True)


if __name__ == '__main__':
    main()
