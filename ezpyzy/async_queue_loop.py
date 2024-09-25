
import asyncio


class QueueLoop:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.results = asyncio.Queue()
        self.active_jobs = 0

    def __call__(self, jobs):
        for job in jobs:
            if asyncio.iscoroutine(job):
                async def run_job_and_put_result():
                    result = await job
                    self.results.put_nowait(result)
                    self.active_jobs -= 1
                self.active_jobs += 1
                self.loop.create_task(run_job_and_put_result())
            else:
                self.results.put_nowait(job)
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if not self.results.empty():
            return self.results.get_nowait()
        elif self.active_jobs:
            return self.loop.run_until_complete(self.results.get())
        else:
            raise StopIteration


if __name__ == '__main__':

    import random
    import time

    def api(s):
        time.sleep(1)
        first_half = s[:len(s) // 2]
        second_half = s[len(s) // 2:]
        waiting_time = random.randint(1, 10)
        print(f'   API call with {s}...')
        # await asyncio.sleep(waiting_time)
        time.sleep(waiting_time)
        result = [x for x in [first_half, second_half] if len(x) > 1]
        print(f'   API call with {s} got reply {result} in {waiting_time}s')
        return result


    class MyWaitPolicy:
        def __init__(self, time):
            self.time = time
        async def wait(self):
            await asyncio.sleep(self.time)
        async def __call__(self):
            await self.wait()


    def main():
        loop = QueueLoop()
        ti = time.perf_counter()
        for i, result in enumerate(loop([api('abcdefghijklmnop')])):
            for subseq in result:
                loop([api(subseq)])
        tf = time.perf_counter()
        print(f'batch done in {tf - ti:.2f} seconds')


    # asyncio.run(amain())
    main()













