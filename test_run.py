# test_run.py
"""
Clean & Simple ThreadPool Test Script
-------------------------------------
Tests:
1. Basic sample task execution
2. CPU / IO / Mixed workloads
3. Exception handling
4. Priority scheduling
5. Final pool metrics
"""

import time
import threading
from core_engine import ThreadPool


# ----------------------------
# TASK DEFINITIONS
# ----------------------------

def sample_task(x):
    """Simple task to demonstrate basic execution."""
    print(f"Task {x} running on:", threading.current_thread().name)
    time.sleep(0.3)
    return x * x


def cpu_task(x):
    """Simulated CPU-heavy task."""
    _ = sum(i * i for i in range(20000))
    return f"CPU-{x}", x * x


def io_task(x):
    """Simulated IO-bound task."""
    time.sleep(0.5)
    return f"IO-{x}", x + 10


def mixed_task(x):
    """Mixed CPU + IO task."""
    _ = sum(i * i for i in range(10000))
    time.sleep(0.2)
    return f"MIX-{x}", x * 2


def error_task(x):
    """Task that raises an error for testing exception handling."""
    if x == 2:
        raise ValueError("Intentional error triggered!")
    return f"OK-{x}", x


# ----------------------------
# PRINT HELPERS
# ----------------------------

def print_line():
    print("-" * 55)


def print_header(text):
    print_line()
    print(text)
    print_line()


# ----------------------------
# MAIN TEST SCRIPT
# ----------------------------

def main():
    print_header("Creating ThreadPool with 6 Workers")
    pool = ThreadPool(max_workers=6, policy="fifo", name="TestRunPool")

    # ---------------------------------------------------
    # TEST 1: Basic Task Execution
    # ---------------------------------------------------
    print_header("TEST 1: Basic Squaring Test")

    futures = [pool.submit(sample_task, i) for i in range(10)]

    for i, f in enumerate(futures):
        print(f"task {i} ->", f.result())

    # ---------------------------------------------------
    # TEST 2: CPU / IO / Mixed Tasks
    # ---------------------------------------------------
    print_header("TEST 2: CPU / IO / Mixed Workload Test")

    futures = []
    start = time.time()

    for i in range(3):
        futures.append(pool.submit(cpu_task, i))
        futures.append(pool.submit(io_task, i))
        futures.append(pool.submit(mixed_task, i))

    for f in futures:
        print("Result:", f.result())

    print(f"Workload Execution Time: {time.time() - start:.2f}s")

    # ---------------------------------------------------
    # TEST 3: Exception Handling
    # ---------------------------------------------------
    print_header("TEST 3: Exception Handling Test")

    futures = [pool.submit(error_task, i) for i in range(4)]

    for i, f in enumerate(futures):
        try:
            print(f"task {i} ->", f.result())
        except Exception as e:
            print(f"task {i} error:", e)

    # ---------------------------------------------------
    # TEST 4: Priority Scheduling
    # ---------------------------------------------------
    print_header("TEST 4: Priority Scheduling Test")

    print("Submitting tasks with different priorities...")

    def simple_priority_task(x):
        print(f"Running priority task: {x}")
        time.sleep(0.3)
        return x

    # HIGH priority should finish first
    f_low = pool.submit(simple_priority_task, 1, priority=1)
    f_med = pool.submit(simple_priority_task, 2, priority=3)
    f_high = pool.submit(simple_priority_task, 3, priority=5)

    print("\nGetting results based on priority (not execution order):")
    print("High priority result  ->", f_high.result())
    print("Medium priority result->", f_med.result())
    print("Low priority result   ->", f_low.result())

    # ---------------------------------------------------
    # FINAL METRICS
    # ---------------------------------------------------
    print_header("FINAL THREADPOOL METRICS")

    metrics = pool.get_metrics_snapshot()
    for k, v in metrics.items():
        print(f"{k:20} : {v}")

    print_line()
    print("Shutting down ThreadPool...")
    pool.shutdown()
    print("DONE ✔")


# ----------------------------
# RUN MAIN
# ----------------------------
if __name__ == "__main__":
    main()
