import pytest
from unittest.mock import AsyncMock

from aos.adapters.mocks.mock_sms_gateway import MockSMSGateway
from aos.adapters.africas_talking.sms_adapter import SMSAdapter
from aos.modules.agri_sms import AgriSMSHandler


@pytest.fixture
def sms_gateway():
    return MockSMSGateway()


@pytest.fixture
def sms_adapter(sms_gateway):
    adapter = SMSAdapter(sms_gateway)
    adapter.set_command_handler(AgriSMSHandler())
    return adapter


def test_sms_adapter_request_parsing(sms_adapter, sms_gateway):
    """Test SMS webhook payload parsing."""
    payload = {
        "from": "+254712345678",
        "to": "21525",
        "text": "HARVEST MAIZE 15 A",
        "id": "msg_123",
        "date": "2025-12-25 12:00:00"
    }

    request = sms_adapter.parse_request(payload)
    assert request.sender == "+254712345678"
    assert request.content == "HARVEST MAIZE 15 A"
    assert request.channel_type == "sms"


@pytest.mark.asyncio
async def test_sms_adapter_harvest_handling(sms_adapter, sms_gateway):
    """Test SMS harvest command handling."""
    payload = sms_gateway.receive_message("+254712345678", "HARVEST MAIZE 15 A")
    request = sms_adapter.parse_request(payload)
    # handle_request is now async
    response = await sms_adapter.handle_request(request)

    # Without AgriModule, it returns "SMS Harvest parsed"
    assert "SMS Harvest parsed" in response.content
    assert response.session_active is False


@pytest.mark.asyncio
async def test_sms_adapter_send_message(sms_adapter, sms_gateway):
    """Test sending SMS via adapter."""
    # Mock gateway send method to avoid actual calls (although MockSMSGateway is already a mock)
    sms_gateway.send = AsyncMock(return_value={"status": "success"})
    
    success = await sms_adapter.send_message("+254712345678", "Test message")
    assert success is True

    # Verify gateway was called
    sms_gateway.send.assert_called_with("+254712345678", "Test message")
