
import sys
import time


class progress:
    def __init__(self, iterable=None, label='', total=None, length=40, fill='█', print_end="\r"):
        self.iterable = iterable
        self.label = label
        self.total = total if total is not None else len(iterable) if iterable is not None else 0
        self.length = length
        self.fill = fill
        self.print_end = print_end

    def __iter__(self):
        self.start_time = time.time()
        self.iteration = 0
        return self

    def __next__(self):
        if self.iterable is not None and self.iteration < self.total:
            item = next(self.iterable)
            self.iteration += 1
            self.print_progress()
            return item
        else:
            self.finish()
            raise StopIteration

    def print_progress(self):
        percent = "{0:.1f}".format(100 * (self.iteration / float(self.total)))
        filled_length = int(self.length * self.iteration // self.total)
        bar = self.fill * filled_length + '-' * (self.length - filled_length)
        elapsed_time = time.time() - self.start_time
        estimated_total_time = elapsed_time / self.iteration * self.total if self.iteration > 0 else 0
        remaining_time = estimated_total_time - elapsed_time
        sys.stdout.write(f'\r{self.label} |{bar}| {percent}% Complete | {elapsed_time:.2f}s')
        sys.stdout.flush()

    def finish(self):
        print()