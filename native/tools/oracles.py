"""Independent problem fixtures and conventional reference algorithms.

These run only in the validator. The ROM computes its own answers on the 68000.
The operation records let tests check intermediate decisions, not just results.
"""
from copy import deepcopy

NAMES = ('bubble', 'insertion', 'binary', 'bfs', 'priority', 'first-fit',
         'selection', 'odd-even', 'merge', 'quick', 'heap', 'linear')
ZONES = (0x0000, 0x0200, 0x0400, 0x0100, 0x0300, 0x0500,
         0x0002, 0x0201, 0x0401, 0x0101, 0x0301, 0x0501)
SORT = [
    [6, 3, 8, 1, 5, 2, 7, 4], [8, 7, 6, 5, 4, 3, 2, 1],
    [1, 2, 3, 5, 4, 6, 8, 7], list(range(1, 9)),
    [3, 1, 3, 2, 1, 2, 3, 1],
]
BINARY = [(list(range(1, 9)), target) for target in (6, 1, 8)] + [
    ([1, 2, 3, 5, 6, 7, 8, 9], 4), ([1, 1, 2, 3, 3, 3, 7, 9], 3)]
LINEAR = [(SORT[0], target) for target in (5, 6, 4, 9)] + [(SORT[4], 1)]
GRAPHS = [
    [0x06, 0x18, 0x20, 0x40, 0x40, 0x80, 0x80, 0x00],
    [0x02, 0x14, 0x09, 0x20, 0x20, 0x40, 0x80, 0x02],
    [0x06, 0x08, 0x08, 0x01, 0x20, 0x40, 0x10, 0x00],
    [0x06, 0x08, 0x80, 0x10, 0x20, 0x40, 0x80, 0x00],
    [0x06, 0x18, 0x18, 0x20, 0x20, 0x40, 0x80, 0x00],
]
PRIORITY = [
    ([4, 2, 5, 1], [2, 1, 3, 1]), ([2, 3, 1, 4], [4, 3, 2, 1]),
    ([5, 2, 4, 1], [1, 1, 1, 1]), ([3, 3, 1, 1], [2, 2, 1, 1]),
    ([9, 1, 2, 3], [1, 4, 3, 2]),
]
FIRST_FIT = [
    ([1, 5, 2, 3, 6], [2, 4, 1, 4]), ([2, 4, 1, 3, 5], [2, 4, 1, 3]),
    ([9, 2, 1, 1, 1], [2, 3, 4, 1]), ([1, 2, 1, 2, 1], [3, 4, 2, 9]),
    ([0, 5, 0, 2, 4], [1, 4, 2, 3]),
]


def padded(items, fill=255):
    return list(items) + [fill] * (8-len(items))


def initial(algorithm, dataset):
    s = dict(algorithm=algorithm, room=algorithm+1, dataset=dataset,
             operations=0, comparisons=0, done=0, running=0, phase=0,
             ids=list(range(8)), result_len=0, result=[255]*8, result_mask=0)
    if algorithm < 2:
        s.update(values=SORT[dataset], swaps=0)
    elif algorithm == 2:
        values, target = BINARY[dataset]
        s.update(values=values, target=target, low=0, high=7, mid=65535)
    elif algorithm == 3:
        s.update(values=[0]+[255]*7, graph=GRAPHS[dataset], target=7,
                 parents=[0]+[255]*7, queue=[0]+[255]*7,
                 low=0, high=1, mask=1, swaps=1)
    elif algorithm == 4:
        bursts, priorities = PRIORITY[dataset]
        s.update(values=padded(bursts, 0), initial=padded(bursts, 0),
                 aux=padded(priorities, 0), elapsed=0, total_wait=0,
                 waits=[0]*4, turnaround=[0]*4, mid=65535, mask=0)
    elif algorithm == 5:
        blocks, requests = FIRST_FIT[dataset]
        s.update(values=padded(blocks, 0), aux=padded(requests, 0), low=0, mid=0, swaps=0)
    elif algorithm == 11:
        values, target = LINEAR[dataset]
        s.update(values=values, target=target, mid=65535, index=0)
    else:
        s.update(values=SORT[dataset], swaps=0)
        if algorithm == 6:
            s.update(outer=0, index=1, minimum=0)
        elif algorithm == 7:
            s.update(index=0, state=0)
        elif algorithm == 8:
            s.update(width=1, base=0, low=0, high=1, mid=1, end=2, write=0,
                     aux=[255]*8, initial=[255]*8)
        elif algorithm == 9:
            s.update(low=0, high=7, outer=0, index=0, pivot=SORT[dataset][7], stack_len=0)
        elif algorithm == 10:
            s.update(heap_size=8, outer=3, root=3, minimum=3, building=1)
    return deepcopy(s)


def sort_trace(values, algorithm):
    items = list(zip(values, range(8)))
    trace = []

    def compare(left, right):
        swap = items[left][0] > items[right][0]
        trace.append((left, right, items[left][0], items[right][0], int(swap)))
        if swap:
            items[left], items[right] = items[right], items[left]
        return swap

    if algorithm == 0:
        for end in range(7, 0, -1):
            changed = False
            for left in range(end):
                changed = compare(left, left+1) or changed
            if not changed:
                break
    else:
        for right in range(1, 8):
            while right and compare(right-1, right):
                right -= 1
    return trace, items


def operations(algorithm, dataset):
    """Return (pre-operation observation, committed state) pairs."""
    if algorithm >= 6:
        return expanded_operations(algorithm, dataset)
    result = []

    def emit(before, after):
        before = dict(before, operations=len(result)+1, phase=4)
        result.append((deepcopy(before), deepcopy(after)))

    if algorithm == 2:
        values, target = BINARY[dataset]
        low, high, found = 0, len(values)-1, None
        while low <= high:
            mid = (low+high)//2
            event = 0 if values[mid] < target else 1 if values[mid] == target else 2
            before = dict(low=low, high=high, mid=mid, left=mid, right=65535,
                          last_left=values[mid], last_right=target, event=event,
                          comparisons=len(result)+1, values=values)
            if event == 1:
                found = mid
            elif event == 0:
                low = mid+1
            else:
                high = mid-1
            emit(before, dict(low=low & 65535, high=high & 65535, mid=mid,
                              values=values, result=padded([] if found is None else [found]),
                              result_len=int(found is not None),
                              result_mask=0 if found is None else 1 << found,
                              done=int(found is not None or low > high)))
            if found is not None:
                break
    elif algorithm == 3:
        # Conventional FIFO traversal, mark on enqueue, neighbors by ID.
        graph = GRAPHS[dataset]
        queue, head, current = [0], 0, 65535
        distance, parents, path = [0]+[255]*7, [0]+[255]*7, []
        comparisons, seen, mask = 0, 1, 1

        def bfs_state(done=False):
            return dict(values=distance, parents=parents, queue=padded(queue),
                        low=head, high=len(queue), mid=current, comparisons=comparisons,
                        swaps=seen, mask=mask, result=padded(path), result_len=len(path),
                        result_mask=sum(1 << v for v in path), done=int(done))

        while head < len(queue):
            current = queue[head]
            head += 1
            emit(dict(event=0, pending=current, left=current, right=65535,
                      comparisons=comparisons), bfs_state())
            for neighbor in range(8):
                if not graph[current] & (1 << neighbor):
                    continue
                comparisons += 1
                fresh = distance[neighbor] == 255
                before = dict(event=2 if fresh else 1, pending=neighbor,
                              left=current, right=neighbor, comparisons=comparisons)
                if fresh:
                    distance[neighbor] = distance[current]+1
                    parents[neighbor] = current
                    seen += 1
                    mask |= 1 << neighbor
                    if neighbor == 7:
                        vertex = 7
                        while vertex:
                            path.append(vertex)
                            vertex = parents[vertex]
                        path.append(0)
                        path.reverse()
                    else:
                        queue.append(neighbor)
                after = bfs_state(bool(path))
                after['event'] = 3 if path else before['event']
                emit(before, after)
                if path:
                    break
            if path:
                break
        if not path:
            emit(dict(event=4, left=65535, right=65535, comparisons=comparisons), bfs_state(True))
    elif algorithm == 4:
        bursts, priorities = PRIORITY[dataset]
        remaining = bursts[:]
        order = sorted(range(4), key=lambda job: (priorities[job], bursts[job], job))
        waits, turnaround, finished = [0]*4, [0]*4, []
        elapsed = 0
        for job in order:
            for tick in range(bursts[job]):
                before = dict(event=int(tick == 0), pending=job, left=job, right=65535,
                              mid=65535 if tick == 0 else job, values=padded(remaining, 0),
                              elapsed=elapsed, comparisons=0)
                if tick == 0:
                    waits[job] = elapsed
                elapsed += 1
                remaining[job] -= 1
                if not remaining[job]:
                    finished.append(job)
                    turnaround[job] = elapsed
                mask = sum(1 << j for j in finished)
                emit(before, dict(elapsed=elapsed, waits=waits, total_wait=sum(waits),
                                  turnaround=turnaround, values=padded(remaining, 0),
                                  mid=job if remaining[job] else 65535,
                                  result=padded(finished), result_len=len(finished),
                                  mask=mask, result_mask=mask, done=int(len(finished) == 4)))
    elif algorithm == 5:
        blocks, requests = FIRST_FIT[dataset]
        free, assigned, placed, mask = blocks[:], [], 0, 0
        for request, need in enumerate(requests):
            for block in range(5):
                fits = free[block] >= need
                terminal = fits or block == 4
                before = dict(event=0 if fits else 2 if terminal else 1,
                              low=request, mid=block, left=block, right=65535,
                              last_left=free[block], last_right=need,
                              values=padded(free, 0), comparisons=len(result)+1)
                if fits:
                    free[block] -= need
                    assigned.append(block)
                    placed += 1
                    mask |= 1 << block
                elif terminal:
                    assigned.append(255)
                emit(before, dict(values=padded(free, 0), result=padded(assigned),
                                  result_len=len(assigned), swaps=placed, result_mask=mask,
                                  low=request+1 if terminal else request,
                                  mid=0 if terminal else block+1,
                                  done=int(request == 3 and terminal)))
                if terminal:
                    break
    else:
        raise ValueError('Use sort_trace for the animated sorts')
    return result


def expanded_operations(algorithm, dataset):
    """Instrument conventional loops/recursion, independently of the ROM FSM."""
    records = []
    items = list(zip(SORT[dataset], range(8)))
    comparisons = exchanges = 0

    def arrays():
        return dict(values=[v for v, _ in items], ids=[i for _, i in items])

    def sort_event(left, right, *, compare=False, swap=False, event=0,
                   tested=None, **extra):
        nonlocal comparisons, exchanges
        comparisons += int(compare)
        a, b = tested if tested is not None else (items[left][0], items[right][0])
        before = dict(arrays(), left=left, right=right, last_left=a, last_right=b,
                      comparisons=comparisons, swaps=exchanges, want_swap=int(swap),
                      operations=len(records)+1, phase=2, event=event, **extra)
        if swap:
            items[left], items[right] = items[right], items[left]
            exchanges += 1
        after = dict(arrays(), comparisons=comparisons, swaps=exchanges, done=0)
        records.append((before, after))

    if algorithm == 6:
        for front in range(7):
            minimum = front
            for scan in range(front+1, 8):
                smaller = items[scan][0] < items[minimum][0]
                sort_event(minimum, scan, compare=True, minimum=minimum,
                           outer=front, index=scan)
                if smaller:
                    minimum = scan
            if minimum != front:
                sort_event(front, minimum, swap=True, event=1)
    elif algorithm == 7:
        changed = True
        while changed:
            changed = False
            for parity in (0, 1):
                for left in range(parity, 7, 2):
                    swap = items[left][0] > items[left+1][0]
                    sort_event(left, left+1, compare=True, swap=swap, state=parity)
                    changed |= swap
    elif algorithm == 8:
        buffer = [(255, 255)]*8
        writes = 0
        for width in (1, 2, 4):
            for base in range(0, 8, width*2):
                middle, end = base+width, base+2*width
                left, right = base, middle
                for destination in range(base, end):
                    have_left, have_right = left < middle, right < end
                    a = items[left][0] if have_left else 65535
                    b = items[right][0] if have_right else 65535
                    comparisons += int(have_left and have_right)
                    from_left = have_left and (not have_right or a <= b)
                    source = left if from_left else right
                    event = (0 if from_left else 1) if have_left and have_right else (2 if from_left else 3)
                    before = dict(arrays(), phase=4, operations=len(records)+1,
                                  comparisons=comparisons, swaps=writes, width=width,
                                  base=base, low=left, high=right, mid=middle, end=end,
                                  write=destination, pending=source, event=event,
                                  left=left if have_left else 65535,
                                  right=right if have_right else 65535,
                                  last_left=a, last_right=b)
                    buffer[destination] = items[source]
                    writes += 1
                    if from_left:
                        left += 1
                    else:
                        right += 1
                    if destination == end-1:
                        items[base:end] = buffer[base:end]
                    after = dict(arrays(), comparisons=comparisons, swaps=writes,
                                 aux=[v for v, _ in buffer], initial=[i for _, i in buffer], done=0)
                    records.append((before, after))
    elif algorithm == 9:
        def quick(low, high):
            if low >= high:
                return
            pivot = items[high][0]
            boundary = low
            for scan in range(low, high):
                value = items[scan][0]
                qualifies = value <= pivot
                swap = qualifies and scan != boundary
                sort_event(boundary if swap else scan, scan if swap else high,
                           compare=True, swap=swap, event=int(qualifies),
                           tested=(value, pivot), low=low, high=high,
                           outer=boundary, index=scan, pivot=pivot)
                if qualifies:
                    boundary += 1
            sort_event(boundary, high, swap=boundary != high, event=2)
            # ROM pushes left then right; the right partition is visited first.
            quick(boundary+1, high)
            quick(low, boundary-1)
        quick(0, 7)
    elif algorithm == 10:
        def sift(root, size):
            while 2*root+1 < size:
                largest = root
                for child in range(2*root+1, min(2*root+3, size)):
                    greater = items[child][0] > items[largest][0]
                    sort_event(largest, child, compare=True, event=child-(2*root+1),
                               root=root, heap_size=size, child=child, minimum=largest)
                    if greater:
                        largest = child
                if largest == root:
                    return
                sort_event(root, largest, swap=True, event=2, root=root, heap_size=size)
                root = largest
        for root in range(3, -1, -1):
            sift(root, 8)
        for end in range(7, 0, -1):
            sort_event(0, end, swap=True, event=3, heap_size=end+1)
            sift(0, end)
    elif algorithm == 11:
        values, target = LINEAR[dataset]
        for index, value in enumerate(values):
            found = value == target
            before = dict(values=values, phase=4, operations=index+1, comparisons=index+1,
                          index=index, mid=index, left=index, right=65535, target=target,
                          last_left=value, last_right=target, event=int(found))
            after = dict(values=values, comparisons=index+1, mid=index,
                         index=index if found else index+1,
                         result=padded([index] if found else []), result_len=int(found),
                         result_mask=(1 << index) if found else 0, done=0)
            records.append((deepcopy(before), deepcopy(after)))
            if found:
                break
    else:
        raise ValueError(algorithm)
    records[-1][1]['done'] = 1
    if algorithm < 11:
        assert [v for v, _ in items] == sorted(SORT[dataset])
        assert sorted(items) == sorted(zip(SORT[dataset], range(8)))
        if algorithm in (7, 8):
            assert items == sorted(zip(SORT[dataset], range(8)), key=lambda pair: pair[0])
    return records


def final(algorithm, dataset):
    if algorithm < 2:
        trace, items = sort_trace(SORT[dataset], algorithm)
        return dict(done=1, phase=0, running=0, operations=len(trace),
                    comparisons=len(trace), swaps=sum(t[-1] for t in trace),
                    values=[v for v, _ in items], ids=[i for _, i in items])
    steps = operations(algorithm, dataset)
    return dict(steps[-1][1], phase=0, running=0, operations=len(steps),
                comparisons=steps[-1][0]['comparisons'])
