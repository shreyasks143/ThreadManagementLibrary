# # monitoring.py
# """
# Simple Monitor that can sample a ThreadPool's internal metrics and provide
# system resource usage (optional psutil).
# """
#
# main code
# import threading
# import time
# from typing import Dict, Optional
#
# try:
#     import psutil
# except Exception:
#     psutil = None  # optional dependency
#
# class Monitor:
#     def __init__(self, pool=None, sample_interval: float = 1.0):
#         self.pool = pool
#         self.sample_interval = sample_interval
#         self._metrics_lock = threading.Lock()
#         self.metrics = {
#             "tasks_submitted": 0,
#             "tasks_completed": 0,
#             "tasks_failed": 0,
#             "queue_len": 0,
#             "queue_max_len": 0,
#             "active_workers": 0,
#         }
#         self._running = False
#         self._thread: Optional[threading.Thread] = None
#
#     def start(self):
#         if self._running:
#             return
#         self._running = True
#         self._thread = threading.Thread(target=self._loop, daemon=True)
#         self._thread.start()
#
#     def stop(self):
#         self._running = False
#         if self._thread:
#             self._thread.join(timeout=1.0)
#
#     def _loop(self):
#         while self._running:
#             self.sample_once()
#             time.sleep(self.sample_interval)
#
#     def sample_once(self):
#         if self.pool:
#             snap = self.pool.get_metrics_snapshot()
#             with self._metrics_lock:
#                 for k in ("tasks_submitted", "tasks_completed", "tasks_failed",
#                           "queue_len", "active_workers", "queue_max_len"):
#                     if k in snap:
#                         self.metrics[k] = snap[k]
#
#         # Add system-level metrics if psutil exists
#         if psutil:
#             try:
#                 with self._metrics_lock:
#                     self.metrics["system_cpu_percent"] = psutil.cpu_percent(interval=0.0)
#                     self.metrics["process_rss_mb"] = psutil.Process().memory_info().rss / (1024 * 1024)
#             except Exception:
#                 pass
#
#     def snapshot(self) -> Dict:
#         with self._metrics_lock:
#             s = dict(self.metrics)
#             s["ts"] = time.time()
#         return s
# monitoring.py
"""
Monitoring Module for the Thread Management Library
---------------------------------------------------
Provides real-time system metrics:
 - CPU usage
 - Memory usage
 - ThreadPool stats
 - Timestamped JSON snapshot
"""

import time
import json
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None


class Monitor:
    def __init__(self, pool):
        """
        pool: instance of ThreadPool (from core_engine.py)
        """
        self.pool = pool

    def get_system_stats(self):
        """Return CPU and memory usage."""
        if psutil:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.Process().memory_info().rss / (1024 * 1024)
        else:
            cpu = None
            mem = None

        return {
            "cpu_percent": cpu,
            "memory_usage_mb": mem
        }

    def get_pool_stats(self):
        """Fetch metrics from ThreadPool core."""
        if hasattr(self.pool, "get_metrics_snapshot"):
            return self.pool.get_metrics_snapshot()
        return {}

    def get_metrics(self):
        """Combine all monitoring info into a JSON-ready dict."""
        sys_stats = self.get_system_stats()
        pool_stats = self.get_pool_stats()

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tasks_submitted": pool_stats.get("tasks_submitted", 0),
            "tasks_completed": pool_stats.get("tasks_completed", 0),
            "tasks_failed": pool_stats.get("tasks_failed", 0),
            "queue_length": pool_stats.get("queue_len", 0),
            "active_workers": pool_stats.get("active_workers", 0),
            "cpu_percent": sys_stats["cpu_percent"],
            "memory_usage_mb": sys_stats["memory_usage_mb"]
        }

    def print_snapshot(self):
        """Pretty print monitoring output (for CLI testing)."""
        metrics = self.get_metrics()
        print(json.dumps(metrics, indent=4))


# Demo run (you can remove this if integrating with your UI)
if __name__ == "__main__":
    from core_engine import ThreadPool

    pool = ThreadPool(max_workers=4)
    mon = Monitor(pool)

    # Submit sample tasks for testing
    for i in range(5):
        pool.submit(time.sleep, 0.5)

    print("Collecting 5 monitoring snapshots...\n")
    for _ in range(5):
        mon.print_snapshot()
        time.sleep(1)

