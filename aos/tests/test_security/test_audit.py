import json

import pytest

from aos.core.security.audit import AuditLogger


@pytest.fixture
def temp_audit_log(tmp_path):
    log_file = tmp_path / "audit.jsonl"
    return log_file

def test_audit_log_format(temp_audit_log):
    """Verify that audit logs are written in valid JSONLines format."""
    logger = AuditLogger(str(temp_audit_log))

    logger.log_event("SECURITY_BOOT", {"node_id": "test_node"}, severity="INFO")
    logger.log_event("ACCESS_DENIED", {"user": "admin"}, severity="WARNING")

    content = temp_audit_log.read_text().strip().split("\n")
    assert len(content) == 2

    first_event = json.loads(content[0])
    assert first_event["event_type"] == "SECURITY_BOOT"
    assert first_event["severity"] == "INFO"
    assert first_event["metadata"]["node_id"] == "test_node"
    assert "timestamp" in first_event
    assert "correlation_id" in first_event

def test_audit_correlation_id(temp_audit_log):
    """Verify that events can be linked via correlation IDs."""
    logger = AuditLogger(str(temp_audit_log))
    cid = "corr-123"

    logger.log_event("AUTH_START", {"step": 1}, correlation_id=cid)
    logger.log_event("AUTH_SUCCESS", {"step": 2}, correlation_id=cid)

    content = temp_audit_log.read_text().strip().split("\n")
    for line in content:
        event = json.loads(line)
        assert event["correlation_id"] == cid

def test_audit_file_persistence(temp_audit_log):
    """Verify that logger appends to existing log file."""
    logger = AuditLogger(str(temp_audit_log))
    logger.log_event("E1", {})

    # Re-instantiate logger
    logger2 = AuditLogger(str(temp_audit_log))
    logger2.log_event("E2", {})

    content = temp_audit_log.read_text().strip().split("\n")
    assert len(content) == 2
