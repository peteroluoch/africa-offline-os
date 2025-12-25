import pytest
from aos.adapters.ussd import USSDAdapter
from aos.core.channels.ussd import USSDSessionManager
from aos.adapters.mocks.mock_ussd_gateway import MockUSSDGateway
from aos.modules.agri_ussd import AgriUSSDHandler


@pytest.fixture
def ussd_gateway():
    return MockUSSDGateway()


@pytest.fixture
def session_manager():
    return USSDSessionManager()


@pytest.fixture
def ussd_adapter(ussd_gateway, session_manager):
    adapter = USSDAdapter(ussd_gateway, session_manager)
    adapter.set_flow_handler(AgriUSSDHandler())
    return adapter


def test_ussd_main_menu_display(ussd_adapter, ussd_gateway):
    """Test that main menu is displayed on first request."""
    session_id = ussd_gateway.start_session("+254712345678")
    payload = ussd_gateway.send_input(session_id, "")
    
    request = ussd_adapter.parse_request(payload)
    response = ussd_adapter.handle_request(request)
    
    assert response.session_active is True
    assert "[A-OS Agri]" in response.content
    assert "1. Record Harvest" in response.content


def test_ussd_harvest_flow_complete(ussd_adapter, ussd_gateway):
    """Test complete harvest recording flow via USSD."""
    phone_number = "+254712345678"
    session_id = ussd_gateway.start_session(phone_number)
    
    # Step 1: Show main menu
    payload = ussd_gateway.send_input(session_id, "")
    request = ussd_adapter.parse_request(payload)
    response = ussd_adapter.handle_request(request)
    assert response.session_active is True
    
    # Step 2: Select "Record Harvest"
    payload = ussd_gateway.send_input(session_id, "1")
    request = ussd_adapter.parse_request(payload)
    response = ussd_adapter.handle_request(request)
    assert response.session_active is True
    assert "Select Crop" in response.content
    
    # Step 3: Select "Maize"
    payload = ussd_gateway.send_input(session_id, "1")
    request = ussd_adapter.parse_request(payload)
    response = ussd_adapter.handle_request(request)
    assert response.session_active is True
    assert "Maize qty" in response.content
    
    # Step 4: Enter quantity
    payload = ussd_gateway.send_input(session_id, "15")
    request = ussd_adapter.parse_request(payload)
    response = ussd_adapter.handle_request(request)
    assert response.session_active is True
    assert "Select Grade" in response.content
    
    # Step 5: Select quality grade
    payload = ussd_gateway.send_input(session_id, "1")
    request = ussd_adapter.parse_request(payload)
    response = ussd_adapter.handle_request(request)
    assert response.session_active is False
    assert "Recorded" in response.content
    assert "15" in response.content


def test_ussd_session_cleanup(session_manager):
    """Test automatic cleanup of old sessions."""
    from datetime import datetime, timezone, timedelta
    
    session = session_manager.get_or_create("old_session", "+254712345678")
    session.updated_at = datetime.now(timezone.utc) - timedelta(seconds=400)
    
    session_manager.cleanup(max_age_seconds=300)
    
    assert "old_session" not in session_manager._sessions


def test_ussd_response_formatting(ussd_adapter):
    """Test response formatting for Africa's Talking."""
    from aos.core.channels.base import ChannelResponse
    
    response = ChannelResponse(content="Select option:", session_active=True)
    formatted = ussd_adapter.format_response(response)
    assert formatted["text"].startswith("CON")
    
    response = ChannelResponse(content="Thank you!", session_active=False)
    formatted = ussd_adapter.format_response(response)
    assert formatted["text"].startswith("END")
