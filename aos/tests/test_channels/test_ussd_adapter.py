import pytest
from aos.adapters.ussd import USSDAdapter, USSDSessionManager, USSDSessionState
from aos.adapters.mocks.mock_ussd_gateway import MockUSSDGateway


@pytest.fixture
def ussd_gateway():
    return MockUSSDGateway()


@pytest.fixture
def session_manager():
    return USSDSessionManager()


@pytest.fixture
def ussd_adapter(ussd_gateway, session_manager):
    return USSDAdapter(ussd_gateway, session_manager)


def test_ussd_main_menu_display(ussd_adapter, ussd_gateway):
    """Test that main menu is displayed on first request."""
    # Start session
    session_id = ussd_gateway.start_session("+254712345678")
    
    # Send empty input (initial request)
    payload = ussd_gateway.send_input(session_id, "")
    
    # Parse and handle
    request = ussd_adapter.parse_request(payload)
    response = ussd_adapter.handle_request(request)
    
    # Verify main menu is shown
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
    assert "Record Harvest" in response.content
    
    # Step 2: Select "Record Harvest"
    payload = ussd_gateway.send_input(session_id, "1")
    request = ussd_adapter.parse_request(payload)
    response = ussd_adapter.handle_request(request)
    assert response.session_active is True
    assert "Select Crop" in response.content
    assert "Maize" in response.content
    
    # Step 3: Select "Maize"
    payload = ussd_gateway.send_input(session_id, "1")
    request = ussd_adapter.parse_request(payload)
    response = ussd_adapter.handle_request(request)
    assert response.session_active is True
    assert "quantity" in response.content.lower()
    
    # Step 4: Enter quantity
    payload = ussd_gateway.send_input(session_id, "15")
    request = ussd_adapter.parse_request(payload)
    response = ussd_adapter.handle_request(request)
    assert response.session_active is True
    assert "Quality Grade" in response.content
    
    # Step 5: Select quality grade
    payload = ussd_gateway.send_input(session_id, "1")
    request = ussd_adapter.parse_request(payload)
    response = ussd_adapter.handle_request(request)
    assert response.session_active is False  # Session ends
    assert "Harvest recorded" in response.content
    assert "15" in response.content
    assert "Grade A" in response.content


def test_ussd_invalid_crop_selection(ussd_adapter, ussd_gateway):
    """Test handling of invalid crop selection."""
    session_id = ussd_gateway.start_session("+254712345678")
    
    # Navigate to crop selection
    ussd_gateway.send_input(session_id, "")
    request = ussd_adapter.parse_request(ussd_gateway.send_input(session_id, "1"))
    ussd_adapter.handle_request(request)
    
    # Select invalid crop (9)
    payload = ussd_gateway.send_input(session_id, "9")
    request = ussd_adapter.parse_request(payload)
    response = ussd_adapter.handle_request(request)
    
    assert response.session_active is False
    assert "Invalid" in response.content


def test_ussd_invalid_quantity(ussd_adapter, ussd_gateway):
    """Test handling of invalid quantity input."""
    session_id = ussd_gateway.start_session("+254712345678")
    
    # Navigate to quantity input
    ussd_gateway.send_input(session_id, "")
    ussd_adapter.handle_request(ussd_adapter.parse_request(ussd_gateway.send_input(session_id, "1")))
    ussd_adapter.handle_request(ussd_adapter.parse_request(ussd_gateway.send_input(session_id, "1")))
    
    # Enter invalid quantity
    payload = ussd_gateway.send_input(session_id, "abc")
    request = ussd_adapter.parse_request(payload)
    response = ussd_adapter.handle_request(request)
    
    assert response.session_active is False
    assert "Invalid" in response.content


def test_ussd_session_state_tracking(session_manager):
    """Test session state management."""
    session = session_manager.get_or_create_session("test_session", "+254712345678")
    
    assert session.state == USSDSessionState.MAIN_MENU
    assert session.phone_number == "+254712345678"
    
    # Update state
    session.update_state(USSDSessionState.SELECT_CROP, "1")
    assert session.state == USSDSessionState.SELECT_CROP
    assert session.data[USSDSessionState.SELECT_CROP.value] == "1"
    
    # End session
    session_manager.end_session("test_session")
    assert session_manager.get_session("test_session") is None


def test_ussd_session_cleanup(session_manager):
    """Test automatic cleanup of old sessions."""
    import time
    from datetime import datetime, timezone, timedelta
    
    # Create session
    session = session_manager.get_or_create_session("old_session", "+254712345678")
    
    # Manually set old timestamp
    session.updated_at = datetime.now(timezone.utc) - timedelta(seconds=400)
    
    # Cleanup sessions older than 300 seconds
    session_manager.cleanup_old_sessions(max_age_seconds=300)
    
    # Session should be removed
    assert session_manager.get_session("old_session") is None


def test_ussd_response_formatting(ussd_adapter):
    """Test response formatting for Africa's Talking."""
    from aos.adapters.channel import ChannelResponse
    
    # Test CON response
    response = ChannelResponse(content="Select option:", session_active=True)
    formatted = ussd_adapter.format_response(response)
    assert formatted["text"].startswith("CON")
    assert "Select option:" in formatted["text"]
    
    # Test END response
    response = ChannelResponse(content="Thank you!", session_active=False)
    formatted = ussd_adapter.format_response(response)
    assert formatted["text"].startswith("END")
    assert "Thank you!" in formatted["text"]
