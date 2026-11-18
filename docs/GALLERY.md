# Gameplay gallery

These 27 screenshots are native **320 × 224** emulator frames from one fresh
boot of the verified v0.6 ROM on Genesis Plus GX. The capture script used
controller inputs to visit and finish every room. It read RAM to steer Sonic
and check results; it did not write RAM, restore save states, or edit the images.

| Hub at the start | Later stations on the right | All twelve completed |
| --- | --- | --- |
| ![Hub before entering any algorithm room](screenshots/hub.png) | ![The LINEAR station at the right end of the hub](screenshots/hub-right.png) | ![Hub counter showing 12 of 12 completed](screenshots/hub-complete.png) |

Each pair below shows an operation in progress and the completed default input.
The sorting monitors carry A–H identities with their original values.

| Demonstration | In progress | Completed |
| --- | --- | --- |
| Bubble sort · Green Hill | ![Bubble sort exchanging adjacent monitors](screenshots/bubble.png) | ![Bubble sort completed](screenshots/bubble-complete.png) |
| Insertion sort · Marble | ![Insertion sort moving its key left](screenshots/insertion.png) | ![Insertion sort completed](screenshots/insertion-complete.png) |
| Binary search · Spring Yard | ![Binary search narrowing its candidate range](screenshots/binary.png) | ![Binary search finding 6 at index 5](screenshots/binary-complete.png) |
| Breadth-first search · Labyrinth | ![BFS inspecting an edge](screenshots/bfs.png) | ![BFS finding the path A C F H](screenshots/bfs-complete.png) |
| Priority scheduling · Star Light | ![Priority scheduler executing a job](screenshots/priority.png) | ![Priority scheduler completing D B A C at time 12](screenshots/priority-complete.png) |
| First-fit allocation · Scrap Brain | ![First-fit inspecting a block for the next request](screenshots/first-fit.png) | ![First-fit completing three allocations and one failure](screenshots/first-fit-complete.png) |
| Selection sort · Green Hill | ![Selection sort scanning for a minimum](screenshots/selection.png) | ![Selection sort completed](screenshots/selection-complete.png) |
| Odd-even sort · Marble | ![Odd-even sort exchanging an adjacent pair](screenshots/odd-even.png) | ![Odd-even sort completed](screenshots/odd-even-complete.png) |
| Merge sort · Spring Yard | ![Merge sort writing a merged run to its buffer](screenshots/merge.png) | ![Merge sort completed](screenshots/merge-complete.png) |
| Quicksort · Labyrinth | ![Quicksort placing a pivot](screenshots/quick.png) | ![Quicksort completed](screenshots/quick-complete.png) |
| Heap sort · Star Light | ![Heap sort exchanging a parent and child](screenshots/heap.png) | ![Heap sort completed](screenshots/heap-complete.png) |
| Linear search · Scrap Brain | ![Linear search checking an unsorted value](screenshots/linear.png) | ![Linear search finding 5 at index 4](screenshots/linear-complete.png) |

The [capture manifest](screenshots/manifest.json) records the ROM, core, and
script hashes, each frame number and image hash, and the algorithm state at
capture. The [capture script](../tools/capture_gallery.py) verifies each room's
initial and final state against the independent references, checks completion
sound ID `$C5`, and confirms all twelve completion flags on returning to the hub.

See the [README](../README.md#verify-and-capture) to reproduce the tour and the
[native guide](../native/README.md#algorithm-rules-and-examples) for the exact
algorithm rules behind each view.
