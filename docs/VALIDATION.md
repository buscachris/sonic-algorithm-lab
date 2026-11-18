# Validation and reproducibility

This publication preserves the verified v0.6 game from the portable-tools
release `2026-11-18_01-32-55_062634Z_sage-lab`. The GitHub checkout was rebuilt
from source with freshly extracted assets. Its ROM and payload are byte-for-byte
identical to that release.

| Artifact | SHA-256 |
| --- | --- |
| Required parent ROM | `952955f9a171636862f88bf6f64aa00a049abe5b8aaab7a8e63275bacdf445cd` |
| v0.6 game ROM | `bef8ef1a565ddd7a334794417d090c26ad361bd102c69add13114bab265cfc2d` |
| Assembled lab payload | `5b3bd9546ee2c79244958d8b3d395e064d47809669af96d45b6d248a68a5d6ad` |

The game is 2,097,152 bytes with Genesis checksum `$8138`. The builder records
53 patches; 214,112 bytes differ from the exact parent. The original engine
and native assets outside the documented patch scope remain intact.

## Checks performed for this publication

- **Fresh source build:** the checkout reproduced the reference ROM and payload
  exactly. See [publication.json](validation/publication.json) for hashes and
  the source files included in that build.
- **Static validation:** verified the ROM and parent hashes, checksum, source
  snapshot, patch boundaries, asset provenance, and completion sound hook.
  See [publication-static.json](validation/publication-static.json).
- **Fresh gameplay capture:** one controller-driven tour entered, ran, and
  completed all twelve default examples, checked their initial and final states,
  checked native sound ID `$C5`, returned through each HUB ring, and accumulated
  all twelve completion flags. It produced 27 unedited 320 × 224 screenshots.
  See the [gallery](GALLERY.md) and [capture manifest](screenshots/manifest.json).

The tour used Genesis Plus GX `v1.7.4 c858c9c`. It read RAM to steer Sonic and
verify state, but did not write RAM or restore save states. The captured ROM
is the hash-identical portable-tools release. Image hashes and frame numbers
are recorded in the manifest. Capturing the tour also exercised the new
[capture script](../tools/capture_gallery.py).

## Existing validation retained with the source

These original reports are copied unchanged, with their hashes and original
project paths recorded in [evidence.json](validation/evidence.json). Absolute
paths refer to the original validation machine. ROMs, save states, and the older
test screenshots referenced by those reports are not included in Git.

| Run | Result | Evidence |
| --- | --- | --- |
| v0.6 full suite · Genesis Plus GX `v1.7.4 c858c9c` | Passed | [genesis-plus-gx.json](validation/genesis-plus-gx.json) |
| v0.6 full suite · BlastEm `0.6.3-pre` | Passed | [blastem.json](validation/blastem.json) |
| Portable tools · 20 relocation and invalid-input cases | Passed | [portability.json](validation/portability.json) |

Each original emulator suite included:

- A controller playthrough of all twelve rooms, STEP, RESET, five INPUT choices,
  RUN, return rings, and cumulative completion. Native Start pause/resume and
  RUN pause/resume were also checked in the bubble room.
- **60 algorithm/input cases** checked against independent Python references,
  including intermediate decisions, final results, counters, monitor identities,
  stability where applicable, and the exact exchange commit frame.
- **Twelve manual completions** finishing the last operation by landing on STEP.
  Automatic and manual completion checked sound ID `$C5` and one-shot behavior.
- **24 native reload checks** covering retry and unsupported-act routing.
- **659 floor probes** across the hub and twelve rooms, with native gravity and
  collision, plus controller checks of both horizontal limits and end jumps.
- Static checks of native assets and patch scope, and nonconstant PCM output.

The independent case tests, manual-completion setup, reload checks, and floor
probes use RAM seeding or restored room-entry states. They are distinct from
the controller playthrough and the new controller-only capture tour.

The portability checks rebuilt relocated sources with paths containing spaces,
tested explicit and environment template selection, rejected incorrect inputs,
verified failure reports, and detected source/ROM corruption. The relocated
ROMs and payloads were byte-identical to v0.6.

The full two-core suites were **not rerun for this documentation publication**:
the game code and resulting binaries are unchanged. The new build, static
validation, and twelve-room capture were run separately as described above.

## Practical limits

The sound checks establish that the game queues the native act-results cue
once and that the core emits audio. They do not substitute for human listening.
Real-console behavior and listening quality remain untested. Results apply to
the exact ROM and core hashes in the reports; a different base template is
rejected by the builder.

For the commands to build, validate, and recapture, see the
[README](../README.md#verify-and-capture) and [native guide](../native/README.md#validation).
