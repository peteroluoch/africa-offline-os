import pytest
import asyncio
import sqlite3
from aos.adapters.mocks.mock_ussd_gateway import MockUSSDGateway
from aos.adapters.mocks.mock_sms_gateway import MockSMSGateway
from aos.adapters.ussd import USSDAdapter
from aos.adapters.sms import SMSAdapter
from aos.modules.agri import AgriModule
from aos.modules.agri_ussd import AgriUSSDHandler
from aos.modules.agri_sms import AgriSMSHandler
from aos.bus.dispatcher import EventDispatcher
from aos.core.security.rate_limiter import TokenBucketLimiter

@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    # Create tables
    conn.execute("""
        CREATE TABLE harvests (
            id TEXT PRIMARY KEY, 
            farmer_id TEXT, 
            crop_id TEXT, 
            quantity REAL, 
            unit TEXT, 
            quality_grade TEXT, 
            harvest_date TEXT,
            status TEXT,
            created_at TEXT
        )
    """)
    return conn

@pytest.fixture
def agri_module(db_conn):
    dispatcher = EventDispatcher()
    return AgriModule(dispatcher, db_conn)

@pytest.fixture
def ussd_adapter(agri_module):
    gateway = MockUSSDGateway()
    adapter = USSDAdapter(gateway)
    adapter.set_flow_handler(AgriUSSDHandler(agri_module))
    return adapter, gateway

@pytest.fixture
def sms_adapter():
    gateway = MockSMSGateway()
    # Very tight rate limit for testing: 2 capacity, 0.1 fill rate
    limiter = TokenBucketLimiter(capacity=2, fill_rate=0.1)
    adapter = SMSAdapter(gateway, rate_limiter=limiter)
    adapter.set_command_handler(AgriSMSHandler())
    return adapter, gateway

@pytest.mark.asyncio
async def test_ussd_persistence(ussd_adapter, agri_module, db_conn):
    """Test that USSD flow actually saves a record to the DB."""
    adapter, gateway = ussd_adapter
    phone = "+254712345678"
    session_id = gateway.start_session(phone)

    # Walk through the flow
    inputs = ["", "1", "1", "15", "1"]
    for inp in inputs:
        payload = gateway.send_input(session_id, inp)
        request = adapter.parse_request(payload)
        response = await adapter.handle_request(request)
        gateway.receive_response(session_id, response.content)

    # Check database
    cursor = db_conn.execute("SELECT COUNT(*) FROM harvests")
    count = cursor.fetchone()[0]
    assert count == 1
    
    cursor = db_conn.execute("SELECT crop_id, quantity, quality_grade FROM harvests")
    row = cursor.fetchone()
    assert row[0] == "Maize"
    assert row[1] == 15.0
    assert row[2] == "A"

@pytest.mark.asyncio
async def test_sms_rate_limiting(sms_adapter):
    """Test that SMS rate limiting rejects excessive messages."""
    adapter, gateway = sms_adapter
    phone = "+254700000000"

    # First 2 should be allowed (capacity 2)
    for _ in range(2):
        payload = gateway.receive_message(phone, "HARVEST MAIZE 10 A")
        request = adapter.parse_request(payload)
        response = await adapter.handle_request(request)
        assert "Error: Rate limit exceeded" not in response.content

    # Third should be rejected
    payload = gateway.receive_message(phone, "HARVEST MAIZE 10 A")
    request = adapter.parse_request(payload)
    response = await adapter.handle_request(request)
    assert "Error: Rate limit exceeded" in response.content
