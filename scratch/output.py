
import threading as th
import multiprocessing as mp
import queue as q
import functools as ft
import atexit as ae
import time


buffer = ['x'] * 100


def printing():
    for ch in buffer:
        print(ch, end='', flush=True)
        time.sleep(0.2)

queue = mp.Queue()
worker = th.Thread(target=printing, args=(), daemon=True)
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

    workload = 10**6 * 5

    with Timer('Without output'):
        for i in range(5):
            print('.', end='', flush=True)
            l = []
            for _ in range(workload):
                x = rng.randint(0, 99)
                l.append(x)


    with Timer('With output'):
        for i in range(5):
            print('.', end='', flush=True)
            l = []
            for _ in range(workload):
                x = rng.randint(0, 99)
                l.append(x)
            buffer[x % 100] = chr(32 + x % 10)
    output('\n\nMain thread done!')