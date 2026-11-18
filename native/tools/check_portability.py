#!/usr/bin/env python3
"""Exercise the release CLI from relocated sources and verify unchanged output."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

from template import load_template

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', type=Path)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    template, _ = load_template(args.template)
    reference = args.reference.resolve()
    reference_payload = reference.parent/'payload.bin'
    expected_rom, expected_payload = digest(reference), digest(reference_payload)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = dict(status='running', reference=str(reference), template=str(template), cases=[])
    try:
        source = out/'relocated source'
        for directory in ('native/src', 'native/tools', 'native/assets'):
            shutil.copytree(ROOT/directory, source/directory, ignore=shutil.ignore_patterns('__pycache__'))
        for name in ('native/README.md', 'SOURCE_LINEAGE.json', 'tools/headless.py'):
            (source/name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, source/name)
        caller = out/'caller directory'
        caller.mkdir()
        good = caller/'parent ROM.bin'
        shutil.copyfile(template, good)
        bad = caller/'wrong parent.bin'
        data = bytearray(good.read_bytes())
        data[-1] ^= 1
        bad.write_bytes(data)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        for key in ('SONIC_LAB_TEMPLATE', 'PYTHONOPTIMIZE'):
            env.pop(key, None)

        def run(name, tool, arguments, *, overrides=None, error=None, optimized=False):
            command = [sys.executable] + (['-O'] if optimized else [])
            command += [str(source/'native/tools'/tool)] + list(map(str, arguments))
            result = subprocess.run(command, cwd=caller, env=dict(env, **(overrides or {})),
                                    text=True, capture_output=True)
            log = out/(name+'.log')
            log.write_text(result.stdout+result.stderr)
            passed = (result.returncode == 0 if error is None else
                      result.returncode != 0 and error in result.stdout+result.stderr)
            report['cases'].append(dict(name=name, passed=passed, returncode=result.returncode, log=log.name))
            if not passed:
                raise RuntimeError(f'{name} failed; see {log}')

        def assets():
            return {str(p.relative_to(source)): digest(p)
                    for p in (source/'native/assets').rglob('*') if p.is_file()}

        original_assets = assets()
        for tool in ('build.py', 'assets.py'):
            stem = tool[:-3]
            run(stem+'-wrong-parent', tool, ['--template', bad], error='Wrong SAGE template')
            run(stem+'-wrong-parent-optimized', tool, ['--template', bad],
                error='Wrong SAGE template', optimized=True)
            run(stem+'-missing-parent', tool, ['--template', 'missing parent.bin'], error='Cannot read SAGE template')
            run(stem+'-optimized', tool, ['--template', good], error='without -O', optimized=True)
        run('missing-assembler', 'build.py', ['--template', good],
            overrides={'PATH': ''}, error='vasmm68k_mot is required on PATH')
        if assets() != original_assets or (source/'native/builds').exists():
            raise RuntimeError('A failed preflight changed assets or created build output')
        report['preflight_preserved_assets_and_builds'] = True

        run('build-cli-relative-override', 'build.py', ['--template', good.name],
            overrides={'SONIC_LAB_TEMPLATE': 'missing parent.bin'})
        run('build-env-relative', 'build.py', [], overrides={'SONIC_LAB_TEMPLATE': good.name})
        builds = sorted((source/'native/builds').iterdir())
        if len(builds) != 2 or assets() != original_assets:
            raise RuntimeError('Expected two builds with byte-identical generated assets')
        report['rebuilds'] = []
        for build in builds:
            info = json.loads((build/'BUILD_INFO.json').read_text())
            rom = build/info['rom']
            if rom.read_bytes() != reference.read_bytes() or (build/'payload.bin').read_bytes() != reference_payload.read_bytes():
                raise RuntimeError(f'Rebuild differs from reference: {build}')
            if info['parent']['path'] != str(good):
                raise RuntimeError('Parent path was not normalized before changing working directory')
            report['rebuilds'].append(dict(path=str(build.relative_to(out)), sha256=digest(rom),
                                           payload_sha256=digest(build/'payload.bin'), byte_identical=True))
        report['assets_byte_identical'] = True

        # Simulate a package whose recorded original parent no longer exists.
        manifest = builds[0]/'BUILD_INFO.json'
        info = json.loads(manifest.read_text())
        info['parent']['path'] = str(caller/'missing original parent.bin')
        manifest.write_text(json.dumps(info, indent=2)+'\n')
        moved_rom = builds[0]/info['rom']
        other_rom = builds[1]/info['rom']

        def validate(name, rom=moved_rom, extra=(), overrides=None, error=None, optimized=False):
            directory = out/name
            run(name, 'validate.py', [rom, '--static-only', '--out', directory, *extra],
                overrides=overrides, error=error, optimized=optimized)
            result = json.loads((directory/'report.json').read_text())
            if result['status'] != ('passed' if error is None else 'failed'):
                raise RuntimeError(f'{name}: incorrect report status')
            if result['mode'] != 'static' or result['controller_playthrough'] != 'not_requested':
                raise RuntimeError(f'{name}: static mode incorrectly reports gameplay coverage')

        validate('moved-manifest-needs-template', error='Cannot read SAGE template')
        validate('validate-cli-relative-override', extra=['--template', good.name],
                 overrides={'SONIC_LAB_TEMPLATE': 'missing parent.bin'})
        validate('validate-env-relative', overrides={'SONIC_LAB_TEMPLATE': good.name})
        validate('validate-manifest-fallback', rom=other_rom)
        validate('validate-wrong-explicit-parent', rom=other_rom,
                 extra=['--template', bad], error='Wrong SAGE template')
        validate('validate-optimized', extra=['--template', good], error='without -O', optimized=True)
        run('full-mode-requires-core', 'validate.py', [other_rom, '--out', out/'no-core'], error='--core is required')

        # Check that static-only mode still catches corrupted ROMs and source snapshots.
        corrupt = out/'corrupt release'
        shutil.copytree(builds[1], corrupt)
        corrupt_rom = corrupt/other_rom.name
        original_rom = corrupt_rom.read_bytes()
        data = bytearray(original_rom)
        data[-1] ^= 1
        corrupt_rom.write_bytes(data)
        validate('reject-corrupt-rom', rom=corrupt_rom, error='AssertionError')
        corrupt_rom.write_bytes(original_rom)
        with (corrupt/'source/native/src/lab.asm').open('a') as stream:
            stream.write('\n; unexpected source change\n')
        validate('reject-corrupt-source', rom=corrupt_rom, error='AssertionError')
        report.update(status='passed', rom_sha256=expected_rom, payload_sha256=expected_payload)
    except Exception as error:
        report.update(status='failed', error=repr(error))
        raise
    finally:
        report['elapsed_seconds'] = round(time.monotonic()-started, 3)
        (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(dict(status=report['status'], cases=len(report['cases']), report=str(out/'report.json'))))


if __name__ == '__main__':
    main()
