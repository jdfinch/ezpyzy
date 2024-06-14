
import threading as th
import multiprocessing as mp
import queue as q
import functools as ft
import atexit as ae
import time


def printing(queue: q.Queue):
    while True:
        s = queue.get()
        if s is None:
            break
        for ch in s:
            print(ch, end='', flush=True)
            time.sleep(0.2)

queue = mp.Queue()
worker = mp.Process(target=printing, args=(queue,), daemon=True)
worker.start()

def cleanup():
    queue.put(None)
    worker.join()

ae.register(cleanup)


def output(s):
    queue.put(s)


if __name__ == '__main__':
    import random as rng
    from ezpyzy.timer import Timer

    workload = 10**6

    with Timer('Without output'):
        for i in range(5):
            print('Hello, World!')
            l = []
            for _ in range(workload):
                l.append(rng.randint(0, 99))

    with Timer('With output'):
        for i in range (5):
            output('Hello, World!\n')
            l = []
            for _ in range(workload):
                l.append(rng.randint(0, 99))
    output('\n\nMain thread done!')