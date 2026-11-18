# Sonic Algorithm Lab — twelve native stages, v0.6

A playable Mega Drive / Genesis ROM built from the local **Sonic the Hedgehog
1 @ SAGE 2010** template. Twelve 68000 implementations run inside the original
engine, with its movement, collision, zone artwork, backgrounds and music.

| Hub switch | Algorithm | Zone | What the demonstration shows |
| --- | --- | --- | --- |
| BUBBLE | Bubble sort | Green Hill | Adjacent comparisons, animated exchanges, early exit after an unchanged pass. |
| INSERT | Insertion sort | Marble | Each key moves left into the sorted prefix through adjacent exchanges. |
| SEARCH | Binary search | Spring Yard | Target, inclusive bounds, midpoint, remaining candidates and found/absent result. |
| BFS | Breadth-first search | Labyrinth | FIFO queue, discovered vertices, distances, inspected edges and a shortest A-to-H path. |
| CPU | Priority scheduling | Star Light | Selected job, remaining burst, execution order, elapsed time and waiting times. |
| MEMORY | First-fit allocation | Scrap Brain | Request sizes, block scans, remaining free space and allocation/failure results. |
| SELECT | Selection sort | Green Hill | Suffix scans, minimum selection and exchanges into the sorted prefix. |
| ODDEVEN | Odd-even sort | Marble | Alternating even and odd adjacent pairs, stopping after an unchanged round. |
| MERGE | Bottom-up merge sort | Spring Yard | Run widths, source cursors, stable buffer writes and completed merges. |
| QUICK | Quicksort | Labyrinth | Last-element pivots, Lomuto partitions, exchanges and pending ranges. |
| HEAP | Heap sort | Star Light | Max-heap construction, child comparisons, sifting and extraction. |
| LINEAR | Linear search | Scrap Brain | Left-to-right checks in an unsorted array and the first matching index. |

These are the twelve demonstrations implemented in this ROM.

## Play

Open `Sonic Algorithm Lab - SAGE Engine.bin` in a Genesis emulator. It starts
in the Green Hill hub. Use the D-pad to move, A/B/C to jump and Start to pause.
Keyboard bindings depend on the emulator. Move right to find all twelve stations;
jump over the raised switches along the way. Land on a labeled switch to open
its ring, then jump into that ring to enter the corresponding room.

| Room switch | Action |
| --- | --- |
| STEP | Perform one comparison, exchange, merge write, graph operation, CPU tick or block check. |
| RUN / PAUSE | Toggle automatic stepping; an operation already in progress finishes. |
| RESET | Restore the selected input, clear its counters and stop. |
| INPUT | Select the next of five examples and reset. |

Jump off a switch and land again to activate it again. The numbered monitors,
letter identities, ring markers and six-row HUD display live algorithm state.
A dash means an unknown distance or failed allocation, according to the room;
`?` means an allocation request is pending. Jump over the switches to the right
and enter the **HUB** ring to return. Completion flags survive resets and room
changes until a power cycle. A room entry starts a fresh run of the current
input selection; INPUT selection persists between rooms. A retry reloads the
same example. An unsupported native act request returns to the hub. Finishing
any algorithm plays the original act-clear cash-register **KACHING**, once per
run, including a run finished with STEP.

## Algorithm rules and examples

All seven sorts use five eight-element arrays covering mixed, reverse, nearly
sorted, sorted and repeated values. Bubble, insertion, odd-even and merge
preserve the original A–H identity order of equal values. Selection, quicksort
and heap sort may reorder equal values. Monitor letters always travel with
their original values.

Bubble sort exits after an unchanged pass. Insertion sort moves each key left
through adjacent exchanges. Their default results use 25 comparisons / 15
exchanges and 20 comparisons / 15 exchanges, respectively.

Selection sort scans the remaining suffix for its first strict minimum, then
exchanges it into the front position. The exchange is a separate STEP. It
always makes 28 comparisons; self-exchanges are omitted. Odd-even sort checks
the four even pairs and then the three odd pairs in each round, stopping only
after a complete round with no exchanges.

Merge sort combines runs of width 1, 2 and 4. One STEP writes one item to the
buffer, choosing the left item on a tie. The main monitor row updates when a
whole merged segment is ready; the HUD shows intermediate buffer values and
identities. CMP counts comparisons with both runs nonempty; WRITE counts all
24 buffer writes, including copies from an exhausted run's partner.

Quicksort uses Lomuto partitioning with the last element as pivot and a
less-than-or-equal comparison. Pivot placement is a separate STEP. An explicit
range stack processes the right partition before the left; self-exchanges do
not count as exchanges. Heap sort builds a max heap from the bottom up, then
extracts its maximum to the end. Each child comparison, sift exchange and
extraction is a separate STEP.

Binary search operates on sorted arrays with inclusive low/high bounds and a
rounded-down midpoint. It can return any matching occurrence for duplicates.
Its five examples cover a middle match, first element, last element, missing
target and repeated values. The default finds target 6 at zero-based index 5
in two comparisons; letters A–H identify the corresponding monitors.

Linear search checks an unsorted array from left to right and stops at the
first equal value. Examples cover middle, first and last matches, an absent
target and duplicates. The default finds 5 at zero-based index 4 after five
comparisons. This demonstration searches numeric values and stops at the first
match.

BFS uses eight vertices, directed adjacency bitsets, an actual FIFO queue,
ascending neighbor order and discovery-time marking. STEP either dequeues a
vertex or examines one existing edge. Parent links reconstruct a shortest
path when H is first discovered. Examples cover a branching graph, cycle,
unreachable H, shortcut and merging branches. The default finds A–C–F–H
(three edges). Unreachable vertices keep an unknown distance.

Priority scheduling is **nonpreemptive**, with all four jobs arriving at time
zero. Lower priority numbers run first; original burst length, then job ID,
break ties. One STEP executes one time unit. The five inputs exercise mixed
priorities, reversed priorities, all-equal priorities, exact ties and a long
first job. The default order is D–B–A–C, finishing at time 12 with total waiting
time 11. Per-job turnaround times are also recorded in lab state.

First-fit allocation scans blocks A–E from the beginning for each of four
requests. A successful allocation subtracts the request from that block's free
space. A failed request leaves all blocks unchanged. There is no deallocation
or coalescing. The five inputs cover mixed fits/failures, exact fits, reuse of
a split block, fragmentation and zero-size free blocks. Default assignments
are B–E–A–failure after 13 checks, leaving capacities 0, 3, 2, 3, 2. Small
integer units keep every quantity readable on the native monitors.

`native/tools/oracles.py` contains the independent reference algorithms and
all 60 fixtures. `native/src/algorithms.asm` and `native/src/expanded.asm`
contain the implementations the console actually executes. The host frontend
never supplies their answers.

## Native engine and assets

Each algorithm room is 768 pixels wide; the hub is 1536 pixels wide to fit all
twelve stations. Flat floors use each zone's original terrain blocks, with
safe horizontal limits and a fixed vertical camera. Native
backgrounds, parallax, palettes, music and collision are retained. Original
level objects and events are disabled; Labyrinth's water is below the room.
Only Sonic, lab switches, warp rings and numbered monitors remain.

All artwork comes from the local SAGE template: pressure switches, giant and
small rings, item monitors and the outlined dialogue font. Only the font's
solid dialogue background is made transparent. The monitor body is copied
out of the HUD's VRAM range before the window is drawn. No generated artwork
or custom-drawn tiles are used. `native/assets/provenance.json` records source
locations; `SOURCE_LINEAGE.json` records the v0.6 source checkpoint and exact
direct ROM parent.

Completion uses native sound ID `$C5`, the same ID queued by the template's
act-results routine at `$10ECA` through `$248E`. The original sound data and
driver are preserved. The lab queues it once when the completion state is set.

## Rebuild

Requirements: Python 3 and `vasmm68k_mot` on PATH. From the source root
containing `native/` and `tools/`:

```sh
python3 native/tools/build.py
```

To select the template path (also supported by `assets.py` and `validate.py`):

```sh
python3 native/tools/build.py --template '/path/to/Sonic SAGE 2010.bin'
```

The environment variable remains supported:

```sh
SONIC_LAB_TEMPLATE='/path/to/Sonic SAGE 2010.bin' python3 native/tools/build.py
```

`--template` takes precedence over `SONIC_LAB_TEMPLATE`. Relative paths are
resolved from the directory where you run the command, even when the source
is elsewhere. Without either override, validation uses the parent path in
`BUILD_INFO.json`; building uses the original local archive path. Supply an
override when moving a release to another machine. A missing or incorrect
explicit template fails instead of falling back to a different file.

The builder requires this exact 2 MiB parent SHA-256:

```text
952955f9a171636862f88bf6f64aa00a049abe5b8aaab7a8e63275bacdf445cd
```

Template and assembler checks run before generated assets or build outputs
are changed. Run the tools without Python's `-O` flag or `PYTHONOPTIMIZE`,
because their internal checks use assertions.

Each build creates a new timestamped directory with the ROM, assembly listing,
payload, complete source snapshot and `BUILD_INFO.json`. The manifest records
the parent, child hashes, source hashes and every patched range. Existing ROMs
and checkpoints are never overwritten. Lab code/data begin in unused ROM
padding at `$120000`; custom object IDs are `$E0`–`$E2`, and lab state occupies
`$FFB400`–`$FFB4FF`.

## Validation

To verify the ROM hash, checksum, source snapshot, patch boundaries and native
assets without an emulator or Pillow:

```sh
python3 native/tools/validate.py '/path/to/build/Sonic Algorithm Lab - SAGE Engine.bin' \
  --template '/path/to/Sonic SAGE 2010.bin' --static-only --out '/path/to/new-static-check'
```

Keep the ROM beside its `BUILD_INFO.json` and `source/` directory. Each check
writes `report.json` to a new output directory, including failures during
template, static or core checks. Static mode does not test gameplay or audio.

The headless frontend requires Pillow and a libretro Genesis core. It runs the
real ROM without opening a desktop emulator:

```sh
python3 native/tools/validate.py '/path/to/build/Sonic Algorithm Lab - SAGE Engine.bin' \
  --template '/path/to/Sonic SAGE 2010.bin' \
  --core '/path/to/genesis_plus_gx_libretro.so' --out '/path/to/new-check-directory'
```

## Portable tools revision

The 2026-11-18 tools revision keeps the v0.6 assembly, assets and game unchanged.
It adds consistent template selection, early input checks and static-only
verification. Run its relocation regression checks with:

```sh
python3 native/tools/check_portability.py \
  --template '/path/to/Sonic SAGE 2010.bin' \
  --reference '/path/to/v0.6-build/Sonic Algorithm Lab - SAGE Engine.bin' \
  --out '/path/to/new-portability-check'
```

The reference build must include `payload.bin`. The checks rebuild from a
source directory containing spaces, use template paths relative to another
working directory, verify relocated manifests, reject invalid inputs and
compare both the ROM and payload byte-for-byte with the reference build.

The validator checks the checksum, parent/child hashes, complete patch scope,
packaged source hashes, native asset provenance and preserved engine calls.
A controller-only playthrough visits all twelve rooms, exercises STEP, RESET,
all five INPUT choices, RUN, return rings and cumulative completion. It also
checks native Start pause/resume and RUN pause/resume in the bubble room.

A separate set of 60 cases restores room-entry states, selects a dataset in
RAM and requests a native reload. The ROM initializes the problem and performs
every operation. Independent references check each intermediate decision,
commit, final result and counters; sorting additionally checks object identity,
stability where applicable and the exact frame on which each exchange takes
effect. Monitor mappings are checked throughout. Twenty-four injected native
level requests check retry and unsupported-act routing.

All 60 automatic runs check that completion queues `$C5` and does not queue it
again while idle. Twelve additional tests run each demo to its last operation,
stop automatic stepping through lab state, and finish by landing on STEP with
controller input. They check the same completion cue and one-shot behavior.
Static checks also confirm the template's act-results call and sound queue
remain intact.

Separate collision probes seed Sonic above 95 hub positions and 47 positions
in each of twelve algorithm rooms (659 total), then let native gravity and
collision settle him. Controller inputs check
both room boundaries and jumping at each end. Active maps, original background
layouts, object lists and camera bounds are checked. Screenshots record all
results and room ends. These RAM-seeded probes are distinct from the normal
controller playthrough.

Read the [validation notes and reports](../docs/VALIDATION.md) for the published
build's results and the distinction between original validation and publication
checks. Audio verification checks nonconstant PCM output, not listening quality.
Real-console behavior and human listening have not been tested.

The SAGE engine and Sonic assets come from the user's local template; this
is an unofficial modification. The package includes the lab code, labels,
monitor behavior, builder, source lineage and validation tools.
