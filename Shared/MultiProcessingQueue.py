import multiprocessing.queues as queues
import multiprocessing as mp


class MultiProcessingQueue(queues.Queue):
    def __init__(self, maxsize=100):
        super().__init__(maxsize, ctx=mp.get_context())

    def is_empty(self) -> bool:
        return self.qsize() == 0

    def dequeue(self, name):
        print("{} size {}".format(name, self.qsize()))
        return self.get()

    def enqueue(self, obj, name):
        self.put_nowait(obj)
        print("{} size {}".format(name, self.qsize()))

    def mark_as_done(self):
        self.put_nowait(None)
