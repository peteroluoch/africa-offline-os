"""
Dashboard Metrics Calculator
Provides real-time system metrics for monitoring dashboard.
"""
import time
from typing import Dict, Any


def calculate_dashboard_metrics(conn) -> Dict[str, Any]:
    """
    Calculate real-time dashboard metrics from system state.
    
    Returns:
        dict: Metrics for heartbeat, throughput, mesh_peers, queue_depth
    """
    
    # 1. Heartbeat - Database latency
    start = time.time()
    try:
        conn.execute("SELECT 1")
        latency_ms = round((time.time() - start) * 1000, 2)
        heartbeat_status = "NOMINAL" if latency_ms < 10 else "DEGRADED"
    except Exception:
        latency_ms = 999.99
        heartbeat_status = "ERROR"
    
    # 2. Throughput - Events per second
    try:
        cursor = conn.execute("""
            SELECT COUNT(*) FROM event_log 
            WHERE timestamp > datetime('now', '-1 minute')
        """)
        events_per_min = cursor.fetchone()[0] or 0
        throughput = int(events_per_min / 60) if events_per_min > 0 else 0
    except Exception:
        throughput = 0
    
    # 3. Queue Depth - Pending events
    try:
        cursor = conn.execute("""
            SELECT COUNT(*) FROM event_log 
            WHERE processed = 0
        """)
        queue_count = cursor.fetchone()[0] or 0
        queue_status = "ZERO" if queue_count == 0 else str(queue_count)
    except Exception:
        queue_count = 0
        queue_status = "ZERO"
    
    # 4. Mesh Peers - Offline-first mode
    mesh_peers = 0  # Sovereign mode (no mesh networking yet)
    
    return {
        "heartbeat": {
            "value": heartbeat_status,
            "latency_ms": latency_ms,
            "status": "success" if heartbeat_status == "NOMINAL" else "error"
        },
        "throughput": {
            "value": throughput,
            "unit": "ev/s",
            "status": "info"
        },
        "mesh_peers": {
            "value": mesh_peers,
            "unit": "Nodes",
            "status": "warning"
        },
        "queue_depth": {
            "value": queue_status,
            "count": queue_count,
            "status": "success" if queue_count == 0 else "warning"
        }
    }
