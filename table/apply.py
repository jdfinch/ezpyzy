
from __future__ import annotations
import typing as T
import itertools as it
from ezpyzy.batch import batched


globalized_fn_tag = '__globalized_multiprocessed_function_'


class progress:
    def __init__(self, iterable=None, label=''):
        self.iterable = iterable
        self.label = label
        
        
def globalize(fn: callable):
    globalized_fn_name = ''.join((
        globalized_fn_tag, 
        '_'.join(c if c.isalnum() else '_' for c in fn.__qualname__), 
        str(id(fn))))
    def global_fn(*args, **kwargs):
        return fn(*args, **kwargs)
    fn_module = sys.modules[global_fn.__module__]
    if not hasattr(fn_module, globalized_fn_name):
        global_fn.__name__ = global_fn.__qualname__ = globalized_fn_name
        setattr(fn_module, global_fn.__name__, global_fn)
    else:
        global_fn = getattr(fn_module, globalized_fn_name)
    return global_fn


J = T.TypeVar('J', bound=T.Iterable)
R = T.TypeVar('R')

def multiprocess(
    fn:T.Callable[[J], R],
    data:J=None,
    n_processes=None,
    batch_size=None,
    batch_count=None,
    batches_per_chunk=None,
    progress_bar=None
) -> R:
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
    elif batch_count is None and batch_size is not None:
        batch_count_reason = 'data/b.size'
        batch_size_reason = 'given'
    elif batch_count is not None and batch_size is None:
        batch_size_reason = 'data/batches'
        batch_count_reason = 'given'
    batches = batched(data, size=batch_size, number=batch_count)
    batch_count = len(batches)
    if n_processes is None:
        n_processes = mp.cpu_count()
        n_processes_reason = 'cpus'
        if n_processes > batch_count:
            n_processes = batch_count
            n_processes_reason = 'batches'
    if n_processes == 1:
        if progress_bar:
            print(f'Single process ({n_processes_reason}) batch_count={batch_count} ({batch_size_reason}) batch_size={len(batches[0]) if batches else 0} ({batch_count_reason})') # noqa
        results = [fn(batch) for batch in batches]
    else:
        global_fn = globalize(fn)
        if batches_per_chunk is None:
            batches_per_chunk = batch_count // n_processes + int(bool(batch_count % n_processes))
            batches_per_chunk_reason = 'batches/procs'
        else:
            batches_per_chunk_reason = 'given'
        if progress_bar:
            print(f'n_processes={n_processes} ({n_processes_reason}) batch_count={batch_count} ({batch_count_reason}) batch_size={len(batches[0]) if batches else 0} ({batch_size_reason})' + (f' batches_per_chunk={batches_per_chunk} ({batches_per_chunk_reason})' if batches_per_chunk != 1 or batches_per_chunk_reason == "given" else '')) # noqa
        with mp.Pool(processes=n_processes) as pool:
            results = list(pool.imap(global_fn, batches, chunksize=batches_per_chunk))
    results = tuple(it.chain(*results))
    return results



if __name__ == '__main__':

    from ezpyzy import Timer
    import multiprocessing as mp
    from ezpyzy.cat import cat
    import inspect as ins
    import sys

    def main():

        with Timer('Create data'):
            
            data = [[*range(10**5)] for n in range(10**3)]
            

        with Timer('Batch multiprocessing'):
            print()
            def batch_sum(batch=data):
                return [int(', '.join([str(x) for x in item]).replace(', ', '')[:100]) for item in batch]
            results = multiprocess(batch_sum, batch_size=2, n_processes=20, progress_bar=True)

            print(sum(results))


        with Timer('Single process'):

            results = batch_sum(data)
            print(sum(results))

    main()