# core_engine.py
"""
Core ThreadPool + synchronization helpers.
Designed to be robust, simple, and extensible for high-concurrency workloads.
"""

from threading import Thread, Lock, Event, Semaphore, Condition, current_thread
from queue import PriorityQueue, Empty
import itertools
import time
from typing import Callable, Any, Optional, Tuple

class Future:
    def __init__(self):
        self._done = Event()
        self._result = None
        self._exc = None

    def set_result(self, result):
        self._result = result
        self._done.set()

    def set_exception(self, exc):
        self._exc = exc
        self._done.set()

    def result(self, timeout: Optional[float] = None):
        finished = self._done.wait(timeout)
        if not finished:
            raise TimeoutError("Future.result() timeout")
        if self._exc:
            raise self._exc
        return self._result

    def done(self):
        return self._done.is_set()


class ThreadPool:
    """
    A flexible thread pool with FIFO or priority scheduling.
    - Uses a PriorityQueue to allow FIFO or priority semantics.
    - Keeps worker threads alive; supports adding workers (resize up).
    - Basic metrics available via get_metrics_snapshot().
    """

    def __init__(self, max_workers: int = 8, policy: str = "fifo", name: str = "ThreadPool"):
        self.name = name
        self.max_workers = max_workers
        self.policy = policy  # "fifo" or "priority"
        self._queue = PriorityQueue()
        self._seq = itertools.count()
        self._shutdown = False
        self._workers = []
        self._workers_lock = Lock()

        # Metrics
        self._metrics_lock = Lock()
        self._metrics = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "queue_max_len": 0,
        }

        # Start workers
        self._start_workers(self.max_workers)

    # -------------------------
    # Public API
    # -------------------------
    def submit(self, fn: Callable, *args, priority: int = 0, **kwargs) -> Future:
        if self._shutdown:
            raise RuntimeError("ThreadPool has been shutdown")
        seq = next(self._seq)
        # Compose priority key:
        # For FIFO: use seq (lower seq -> earlier)
        # For priority: use (-priority, seq) so higher priority numbers run first
        if self.policy == "priority":
            key = (-priority, seq)
        else:
            key = (seq, )

        future = Future()
        submitted_at = time.time()
        self._queue.put((key, fn, args, kwargs, future, submitted_at))
        with self._metrics_lock:
            self._metrics["tasks_submitted"] += 1
            ql = self._queue.qsize()
            if ql > self._metrics["queue_max_len"]:
                self._metrics["queue_max_len"] = ql
        return future

    def resize(self, new_size: int):
        """Increase pool size. Decreasing workers requires graceful retire (not implemented)."""
        with self._workers_lock:
            if new_size <= self.max_workers:
                # shrinking is a noop for now (complex: need per-worker terminate flags)
                self.max_workers = new_size
                return
            add = new_size - self.max_workers
            self._start_workers(add)
            self.max_workers = new_size

    def shutdown(self, wait: bool = True, drain: bool = True):
        """
        Shutdown pool. If drain==True, let the queue drain (workers finish).
        If drain==False, workers will stop quickly (they check shutdown flag between tasks).
        """
        self._shutdown = True
        if not drain:
            # clear queue quickly
            try:
                while True:
                    self._queue.get_nowait()
                    self._queue.task_done()
            except Empty:
                pass
        if wait:
            with self._workers_lock:
                for w in list(self._workers):
                    w.join(timeout=3.0)

    def get_metrics_snapshot(self) -> dict:
        with self._metrics_lock:
            m = dict(self._metrics)
        m.update({
            "queue_len": self._queue.qsize(),
            "active_workers": len(self._workers),
        })
        return m

    # -------------------------
    # Internal
    # -------------------------
    def _start_workers(self, count: int):
        with self._workers_lock:
            base = len(self._workers)
            for i in range(count):
                idx = base + i
                t = Thread(target=self._worker_loop, name=f"{self.name}-worker-{idx}", daemon=True)
                t.start()
                self._workers.append(t)

    def _worker_loop(self):
        while not self._shutdown:
            try:
                item = self._queue.get(timeout=0.5)
            except Empty:
                continue
            try:
                (key, fn, args, kwargs, future, submitted_at) = item
            except Exception:
                self._queue.task_done()
                continue

            try:
                result = fn(*args, **kwargs)
                future.set_result(result)
                with self._metrics_lock:
                    self._metrics["tasks_completed"] += 1
            except Exception as e:
                future.set_exception(e)
                with self._metrics_lock:
                    self._metrics["tasks_failed"] += 1
            finally:
                try:
                    self._queue.task_done()
                except Exception:
                    pass
        # worker exiting

# -------------------------
# Lightweight synchronization helpers (wrappers)
# -------------------------
class Mutex:
    def __init__(self):
        self._lock = Lock()

    def acquire(self, blocking: bool = True, timeout: Optional[float] = -1) -> bool:
        if timeout and timeout >= 0:
            return self._lock.acquire(timeout=timeout)
        return self._lock.acquire(blocking)

    def release(self):
        self._lock.release()

class RWLock:
    """
    Simple read-write lock (not reentrant). Many variations exist; this one is fair-ish.
    """
    def __init__(self):
        self._readers = 0
        self._read_lock = Lock()
        self._write_lock = Lock()

    def acquire_read(self):
        with self._read_lock:
            self._readers += 1
            if self._readers == 1:
                self._write_lock.acquire()

    def release_read(self):
        with self._read_lock:
            self._readers -= 1
            if self._readers == 0:
                self._write_lock.release()

    def acquire_write(self):
        self._write_lock.acquire()

    def release_write(self):
        self._write_lock.release()

