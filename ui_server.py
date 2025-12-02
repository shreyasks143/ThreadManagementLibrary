# ui_server.py
"""
Flask Web Dashboard for ThreadPool Monitoring
---------------------------------------------
Integrates:
 - ThreadPool from core_engine.py
 - Monitor from monitoring.py

Provides:
 - /metrics JSON endpoint
 - Live real-time Chart.js dashboard
 - Background load generator (optional)
"""

from flask import Flask, jsonify, render_template_string
from monitoring import Monitor
from core_engine import ThreadPool
import threading
import time

app = Flask(__name__)

# Create ThreadPool + Monitor
pool = ThreadPool(max_workers=6, policy="fifo")
monitor = Monitor(pool)


# -------------------------------
# /metrics endpoint
# -------------------------------
@app.route("/metrics")
def metrics():
    """Return JSON metrics from monitoring.py."""
    return jsonify(monitor.get_metrics())


# -------------------------------
# HTML DASHBOARD PAGE
# -------------------------------
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>ThreadPool Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>

<body style="font-family: Arial; margin: 40px;">
    <h2>📊 ThreadPool Real-Time Monitoring Dashboard</h2>
    <p>Auto-refreshing every 1 second...</p>

    <h3>CPU Usage (%)</h3>
    <canvas id="cpuChart" width="650" height="200"></canvas>

    <h3>Memory Usage (MB)</h3>
    <canvas id="memChart" width="650" height="200"></canvas>

    <h3>Queue Length</h3>
    <canvas id="queueChart" width="650" height="200"></canvas>

    <script>
    async function fetchMetrics() {
        const res = await fetch('/metrics');
        return await res.json();
    }

    const timestamps = [];
    const cpuData = [];
    const memData = [];
    const queueData = [];

    const cpuChart = new Chart(document.getElementById("cpuChart"), {
        type: "line",
        data: {
            labels: timestamps,
            datasets: [{ label: "CPU %", data: cpuData, borderColor: "red" }]
        }
    });

    const memChart = new Chart(document.getElementById("memChart"), {
        type: "line",
        data: {
            labels: timestamps,
            datasets: [{ label: "Memory (MB)", data: memData, borderColor: "blue" }]
        }
    });

    const queueChart = new Chart(document.getElementById("queueChart"), {
        type: "line",
        data: {
            labels: timestamps,
            datasets: [{ label: "Queue Length", data: queueData, borderColor: "green" }]
        }
    });

    async function updateCharts() {
        const data = await fetchMetrics();
        const timeLabel = new Date().toLocaleTimeString();

        timestamps.push(timeLabel);
        cpuData.push(data.cpu_percent || 0);
        memData.push(data.memory_usage_mb || 0);
        queueData.push(data.queue_length || 0);

        cpuChart.update();
        memChart.update();
        queueChart.update();
    }

    setInterval(updateCharts, 1000);
    </script>

</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(dashboard_html)


# -------------------------------
# SIMULATED TASK LOAD (Optional)
# -------------------------------
def generate_background_load():
    """Submit tasks continuously to make dashboard graphs active."""
    while True:
        pool.submit(time.sleep, 0.5)
        time.sleep(0.3)


# Start background load thread (optional but useful)
load_thread = threading.Thread(target=generate_background_load, daemon=True)
load_thread.start()


# -------------------------------
# RUN SERVER
# -------------------------------
if __name__ == "__main__":
    print("🚀 Monitoring Dashboard running at http://127.0.0.1:5000")
    app.run(debug=True)
