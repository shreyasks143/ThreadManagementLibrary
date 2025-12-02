# benchmark.py
"""
Benchmark Module for Scalable Thread Management Library
-------------------------------------------------------
This file measures:
 - CPU throughput
 - IO wait performance
 - Mixed workload behavior
 - Latency and total execution time
 - CPU% and RAM usage via monitoring.py
"""

import time
from core_engine import ThreadPool
from monitoring import Monitor   # << INTEGRATION

try:
    import psutil
except:
    psutil = None


# -----------------------------------------------------------
# TASK DEFINITIONS
# -----------------------------------------------------------
def cpu_task(n):
    """Heavy CPU computation used for benchmarking."""
    s = 0
    for i in range(n):
        s += i * i
    return s


def io_task(sleep_for):
    """Simulate IO-bound delay."""
    time.sleep(sleep_for)
    return sleep_for


# -----------------------------------------------------------
# CPU BENCHMARK (Integrated with Monitor)
# -----------------------------------------------------------
def run_cpu_benchmark(num_tasks=1000, work_per_task=3000, workers=16):
    print("\n=== CPU BENCHMARK ===")

    pool = ThreadPool(max_workers=workers, policy="fifo", name="BenchmarkPool")
    monitor = Monitor(pool)     # << INTEGRATION

    futures = []
    latencies = []
    t0 = time.time()

    for _ in range(num_tasks):
        t_submit = time.time()
        fut = pool.submit(cpu_task, work_per_task)
        futures.append((fut, t_submit))

    completed = 0
    for fut, t_submit in futures:
        fut.result()
        completed += 1
        latencies.append(time.time() - t_submit)

    total_time = time.time() - t0
    throughput = completed / total_time

    metrics = monitor.get_metrics()  # << FETCH LIVE METRICS

    print(f"Tasks completed: {completed}/{num_tasks}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Throughput: {throughput:.2f} tasks/sec")
    print(f"Avg latency: {sum(latencies)/len(latencies):.4f}s")

    print("--- System Metrics During CPU Benchmark ---")
    print(f"CPU Usage %: {metrics['cpu_percent']}")
    print(f"Memory Usage MB: {metrics['memory_usage_mb']}")
    print(f"Queue Length: {metrics['queue_length']}")
    print(f"Active Workers: {metrics['active_workers']}")

    pool.shutdown()


# -----------------------------------------------------------
# IO BENCHMARK (Integrated with Monitor)
# -----------------------------------------------------------
def run_io_benchmark(num_tasks=200, sleep=0.3, workers=40):
    print("\n=== IO BENCHMARK ===")

    pool = ThreadPool(max_workers=workers, policy="fifo", name="IOBenchmarkPool")
    monitor = Monitor(pool)

    futures = []
    t0 = time.time()

    for _ in range(num_tasks):
        futures.append(pool.submit(io_task, sleep))

    for f in futures:
        f.result()

    total_time = time.time() - t0

    metrics = monitor.get_metrics()

    print(f"Tasks completed: {num_tasks}")
    print(f"Total time: {total_time:.2f}s")
    print("--- System Metrics During IO Benchmark ---")
    print(f"CPU Usage %: {metrics['cpu_percent']}")
    print(f"Memory Usage MB: {metrics['memory_usage_mb']}")
    print(f"Queue Length: {metrics['queue_length']}")
    print(f"Active Workers: {metrics['active_workers']}")

    pool.shutdown()


# -----------------------------------------------------------
# MIXED BENCHMARK (Integrated with Monitor)
# -----------------------------------------------------------
def run_mixed_benchmark(num_tasks=300, workers=20):
    print("\n=== MIXED BENCHMARK ===")

    pool = ThreadPool(max_workers=workers)
    monitor = Monitor(pool)
    futures = []

    t0 = time.time()

    for i in range(num_tasks):
        if i % 3 == 0:
            futures.append(pool.submit(cpu_task, 2000))
        elif i % 3 == 1:
            futures.append(pool.submit(io_task, 0.2))
        else:
            futures.append(pool.submit(cpu_task, 1000))

    for f in futures:
        f.result()

    total_time = time.time() - t0
    metrics = monitor.get_metrics()

    print(f"Total time: {total_time:.2f}s")
    print("--- System Metrics During Mixed Benchmark ---")
    print(f"CPU Usage %: {metrics['cpu_percent']}")
    print(f"Memory Usage MB: {metrics['memory_usage_mb']}")
    print(f"Queue Length: {metrics['queue_length']}")
    print(f"Active Workers: {metrics['active_workers']}")

    pool.shutdown()


# -----------------------------------------------------------
# RUN BENCHMARK SUITE
# -----------------------------------------------------------
if __name__ == "__main__":
    run_cpu_benchmark(num_tasks=300, work_per_task=5000, workers=12)
    run_io_benchmark(num_tasks=150, sleep=0.2, workers=40)
    run_mixed_benchmark(num_tasks=300, workers=20)

