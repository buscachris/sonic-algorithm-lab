#!/usr/bin/env python3
"""Capture unedited gameplay frames from a controller-driven tour of v0.6.

The ROM computes every result. This script reads its debug state to steer
Sonic and choose useful frames; it does not write RAM or restore save states.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "native/tools"))
from probe import Emulator
from oracles import NAMES, ZONES, final, initial
from validate import matches, move_to, sequence, state, word


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interesting(s, algorithm):
    if s["done"]:
        return False
    if algorithm in (0, 1, 7, 9, 10):
        return s["phase"] == 3 and s["timer"] >= 14
    minimum = {2: 1, 3: 4, 4: 4, 5: 4, 6: 3, 8: 4, 11: 2}[algorithm]
    return s["operations"] >= minimum and s["phase"] != 0 and s["timer"] >= 12


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "docs/screenshots")
    args = parser.parse_args()
    if not __debug__:
        parser.error("Run without -O or PYTHONOPTIMIZE; captures use assertions.")
    lineage = json.loads((ROOT / "SOURCE_LINEAGE.json").read_text())
    if sha256(args.rom) != lineage["source_rom_sha256"]:
        parser.error("The ROM must match the documented v0.6 source release.")
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("Use an empty output directory; existing captures are preserved.")
    args.out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    report = dict(
        created_utc=datetime.now(timezone.utc).isoformat(),
        rom=args.rom.name,
        rom_sha256=sha256(args.rom),
        core_sha256=sha256(args.core),
        capture_script_sha256=sha256(Path(__file__)),
        method="Fresh boot; controller input only; RAM read for steering and assertions",
        image_processing="None: PNGs are the native emulator video frames",
        screenshots=[],
    )

    def capture(e, name, description):
        picture = e.image()
        path = args.out / (name + ".png")
        picture.save(path)
        s = state(e)
        report["screenshots"].append(dict(
            file=path.name, description=description, sha256=sha256(path),
            width=picture.width, height=picture.height, frame=e.frames,
            state={key: s[key] for key in (
                "room", "algorithm", "dataset", "running", "done", "phase",
                "operations", "comparisons", "swaps", "completed", "values", "ids")},
        ))

    try:
        with Emulator(args.rom, core=args.core) as e:
            e.word_swap = True
            report["core"] = e.info.library_name.decode()
            report["core_version"] = e.info.library_version.decode()
            e.run(900)
            matches(state(e), dict(magic="SAL2", version=0x0600, room=0, gates=0), "boot")
            capture(e, "hub", "The Green Hill hub before visiting its twelve stations")
            for algorithm, name in enumerate(NAMES):
                for gap in range(152, 96 + 112 * algorithm, 112):
                    move_to(e, gap, jump=True)
                move_to(e, 96 + 112 * algorithm, jump=True)
                assert state(e)["gates"] & (1 << algorithm)
                if algorithm == 11:
                    capture(e, "hub-right", "The right end of the hub and the LINEAR station")
                sequence(e, [(10, ("A",)), (600, ())])
                assert word(e, 0xb2e0) == ZONES[algorithm]
                matches(state(e), initial(algorithm, 0), name + " entry")
                move_to(e, 128, jump=True)
                assert state(e)["running"] == 1
                for _ in range(7000):
                    if interesting(state(e), algorithm):
                        break
                    assert not state(e)["done"], name + " completed before its progress capture"
                    e.run(1)
                else:
                    raise AssertionError(name + " progress frame not reached")
                e.run(2)
                capture(e, name, name + ": an operation in progress on the default input")
                for _ in range(70):
                    if state(e)["done"]:
                        break
                    e.run(100)
                matches(state(e), final(algorithm, 0), name + " result")
                assert e.ram(0xb740, 1) == b"\xc5", name + " completion cue"
                capture(e, name + "-complete", name + ": completed result on the default input")
                move_to(e, 224, jump=True)
                move_to(e, 320, jump=True)
                move_to(e, 400)
                sequence(e, [(16, ("A",)), (600, ())])
                matches(state(e), dict(room=0, completed=(1 << (algorithm + 1)) - 1), name + " return")
                print("Captured " + name, flush=True)
            capture(e, "hub-complete", "All twelve algorithms completed in one controller-driven tour")
            assert not e.callback_errors
            report["completed_algorithms"] = 12
            report["status"] = "passed"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = repr(error)
        raise
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        (args.out / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({key: report[key] for key in ("status", "elapsed_seconds")}), flush=True)


if __name__ == "__main__":
    main()
