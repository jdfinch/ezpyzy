
import asyncio


class JobQueue:
    def __init__(self, jobs=()):
        self.loop = asyncio.get_event_loop()
        self.results = asyncio.Queue()
        self.active_jobs = 0
        self.extend(jobs)

    async def run_job_and_put_result(self, job):
        result = await job
        self.results.put_nowait(result)
        self.active_jobs -= 1

    def extend(self, jobs):
        for job in jobs:
            if asyncio.iscoroutine(job):
                self.active_jobs += 1
                self.loop.create_task(self.run_job_and_put_result(job))
            else:
                self.results.put_nowait(job)
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if not self.results.empty():
            return self.results.get_nowait()
        elif self.active_jobs:
            item = self.loop.run_until_complete(self.results.get())
            return item
        else:
            raise StopIteration


if __name__ == '__main__':

    import random
    import time


    async def api(s):
        time.sleep(1)
        first_half = s[:len(s) // 2]
        second_half = s[len(s) // 2:]
        waiting_time = random.randint(1, 10)
        print(f'   API call with {s}...')
        request = asyncio.sleep(waiting_time)
        await request
        # time.sleep(waiting_time)
        result = [x for x in [first_half, second_half] if len(x) > 1]
        print(f'   API call with {s} got reply {result} in {waiting_time}s')
        return result


    def main():
        queue = JobQueue()
        ti = time.perf_counter()
        for i, result in enumerate(queue.extend([api('abcdefghijklmnop')])):
            for subseq in result:
                queue.extend([api(subseq)])
        tf = time.perf_counter()
        print(f'batch done in {tf - ti:.2f} seconds')


    main()













