import pytest
from unittest.mock import Mock, patch
from aos.core.resource.manager import ResourceManager
from aos.core.resource.monitor import ResourceSnapshot, BatteryInfo, BatteryStatus
from datetime import datetime, UTC
import json
import os

@pytest.fixture
def mock_snapshot_critical_disk():
    return ResourceSnapshot(
        timestamp=datetime.now(UTC),
        battery=BatteryInfo(percent=50, status=BatteryStatus.DISCHARGING, plugged=False),
        cpu_percent=10.0,
        memory_percent=50.0,
        memory_available_mb=1000,
        disk_free_mb=50,  # Below 100MB threshold
        disk_percent=95.0
    )

@pytest.mark.asyncio
async def test_forensic_alert_on_low_disk(mock_snapshot_critical_disk, tmp_path):
    # Set up a temporary audit log
    log_file = tmp_path / "test_audit.jsonl"
    
    with patch("aos.core.resource.monitor.ResourceMonitor.get_snapshot", return_value=mock_snapshot_critical_disk):
        # Initialize manager but don't start the background loop
        manager = ResourceManager()
        # Override the audit logger inside forensics with one pointing to our temp file
        manager.forensics.audit.log_path = log_file
        
        # Trigger a check manually
        await manager._check_resources()
        
        # Verify if CRITICAL event was logged
        assert log_file.exists()
        with open(log_file, "r") as f:
            lines = f.readlines()
            last_event = json.loads(lines[-1])
            assert last_event["event_type"] == "RESOURCE_CRITICAL"
            assert last_event["severity"] == "CRITICAL"
            assert last_event["metadata"]["type"] == "DISK_LOW"

def test_audit_log_rotation(tmp_path):
    from aos.core.security.audit import AuditLogger
    log_file = tmp_path / "rotate_test.jsonl"
    
    # 1KB max size for testing
    logger = AuditLogger(log_file=str(log_file), max_size_mb=0.001) 
    
    # Write enough events to trigger rotation
    large_data = "x" * 500
    for i in range(5):
        logger.log_event("TEST_EVENT", {"data": large_data})
        
    # Check if rotated file exists
    rotated_file = tmp_path / "rotate_test.jsonl.1"
    assert rotated_file.exists()
    assert log_file.exists()
