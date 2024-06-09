
from __future__ import annotations
import typing as T
import itertools as it
import functools as ft
from ezpyzy.timer import Timer
from ezpyzy.globalize import globalize


J = T.TypeVar('J', bound=T.Iterable)
R = T.TypeVar('R')

def multiprocess(
    fn:T.Callable[[J], T.Sequence[R]],
    data:J=None,
    n_processes=None,
    batch_size=None,
    batch_count=None,
    batches_per_chunk=None,
    display=False
) -> tuple[R]:
    parameters = tuple(ins.signature(fn).parameters.values())
    data = parameters[0].default if data is None else data
    if (n_processes, batch_size, batch_count) == (None, None, None):
        n_processes = mp.cpu_count()
        n_processes_reason = 'cpus'
    elif isinstance(n_processes, int) and n_processes <= 0:
        n_processes_reason = f'cpus-{abs(n_processes)}'
        n_processes = max(mp.cpu_count() + n_processes, 1)
    elif isinstance(n_processes, float):
        n_processes_reason = f'cpus*{n_processes}'
        n_processes = max(int(mp.cpu_count() * n_processes), 1)
    elif n_processes is not None:
        n_processes_reason = 'given'
    if (batch_size, batch_count) == (None, None):
        batch_count_reason = 'n'
        batch_count = n_processes
        batch_size_reason = 'data/n'
        batch_size = len(data) // batch_count + int(bool(len(data) % batch_count))
    elif batch_size is not None:
        batch_count_reason = 'data/batchsize'
        batch_size_reason = 'given'
        batch_count = len(data) // batch_size + int(bool(len(data) % batch_size))
    else:
        batch_size_reason = 'data/batches'
        batch_count_reason = 'given'
        batch_size = len(data) // batch_count + int(bool(len(data) % batch_count))
    if n_processes is None:
        n_processes = mp.cpu_count()
        n_processes_reason = 'cpus'
        if n_processes > batch_count:
            n_processes = batch_count
            n_processes_reason = 'batches'
    batching_timer = Timer()
    if n_processes == 1:
        if display:
            print(f'{fn.__name__}:  n_processes={n_processes} ({n_processes_reason}),  batch_count={batch_count} ({batch_size_reason}),  batch_size={batch_size} ({batch_count_reason})') # noqa
            print('    batching', end='.. ' )
        if hasattr(data, '__getitem__') and hasattr(data, '__len__'):
            batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]
        else:
            iterator = iter(data)
            batches = list(it.takewhile(bool, (tuple(it.islice(iterator, batch_size)) for _ in it.count())))
        if display:
            print(batching_timer.str.stop(), end=', ')
        processing_timer = Timer()
        results = [fn(batch) for batch in batches]
    else:
        global_fn = globalize(fn)
        if batches_per_chunk is None:
            batches_per_chunk = batch_count // n_processes + int(bool(batch_count % n_processes))
            batches_per_chunk_reason = 'batches/procs'
        else:
            batches_per_chunk_reason = 'given'
        if display:
            print(f'{fn.__name__}:  n_processes={n_processes} ({n_processes_reason}),  batch_count={batch_count} ({batch_count_reason}),  batch_size={batch_size} ({batch_size_reason})' + (f',  batches_per_chunk={batches_per_chunk} ({batches_per_chunk_reason})' if batches_per_chunk != 1 or batches_per_chunk_reason == "given" else '')) # noqa
            print('    batching', end='.. ' )
        if hasattr(data, '__getitem__') and hasattr(data, '__len__'):
            batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]
        else:
            iterator = iter(data)
            batches = list(it.takewhile(bool, (tuple(it.islice(iterator, batch_size)) for _ in it.count())))
        if display:
            print(batching_timer.str.stop(), end=', ')
        processing_timer = Timer()
        print('processing', end='.. ')
        with mp.Pool(processes=n_processes) as pool:
            iterator = pool.imap(global_fn, batches, chunksize=batches_per_chunk)
            results = list(iterator)
    if display:
        print(processing_timer.str.stop(), end=', ')
    compiling_timer = Timer()
    print('compiling', end='.. ' )
    results = tuple(it.chain(*results))
    if display:
        print(compiling_timer.str.stop())
        print('    total:', (batching_timer.delta + processing_timer.delta + compiling_timer.delta).display())
    return results # noqa


F = T.TypeVar('F', bound=T.Callable)

def multiprocessed(
    n_processes=None,
    batch_size=None,
    batch_count=None,
    batches_per_chunk=None,
    display=False
) -> T.Callable[[F], F]:
    bound_multiprocess = ft.partial(multiprocess,
        n_processes=n_processes,
        batch_size=batch_size,
        batch_count=batch_count,
        batches_per_chunk=batches_per_chunk,
        progress_bar=display)
    return ft.partial(ft.partial, bound_multiprocess)


if __name__ == '__main__':

    from ezpyzy import Timer
    import multiprocessing as mp
    import inspect as ins

    def main():

        with Timer('Create data'):
            data = [[*range(10**1)] for n in range(10**7)]

        print()
        def batch_sum(batch=data):
            return [int(', '.join([str(x) for x in item]).replace(', ', '')[:100]) for item in batch]
        results = multiprocess(batch_sum, n_processes=2.0, display=True)

        print()
        with Timer('Single process'):
            results = batch_sum(data)

    main()