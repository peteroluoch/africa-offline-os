import pytest
from aos.adapters.sms import SMSAdapter, SMSCommandParser
from aos.adapters.mocks.mock_sms_gateway import MockSMSGateway


@pytest.fixture
def sms_gateway():
    gateway = MockSMSGateway()
    return gateway


@pytest.fixture
def sms_adapter(sms_gateway):
    return SMSAdapter(sms_gateway)


@pytest.fixture
def command_parser():
    return SMSCommandParser()


def test_sms_harvest_command_parsing(command_parser):
    """Test parsing of harvest SMS commands."""
    # Standard format
    command = command_parser.parse("HARVEST MAIZE 15 A")
    assert command.command == "HARVEST"
    assert command.crop == "maize-01"
    assert command.quantity == 15.0
    assert command.quality == "A"
    
    # Lowercase
    command = command_parser.parse("harvest maize 15 a")
    assert command.crop == "maize-01"
    assert command.quality == "A"
    
    # With "bags" keyword
    command = command_parser.parse("HARVEST 20 bags of beans grade B")
    assert command.crop == "beans-01"
    assert command.quantity == 20.0
    assert command.quality == "B"


def test_sms_command_validation(command_parser):
    """Test command validation."""
    # Valid command
    command = command_parser.parse("HARVEST MAIZE 15 A")
    is_valid, error = command_parser.validate(command)
    assert is_valid is True
    assert error == ""
    
    # Missing crop
    command = command_parser.parse("HARVEST 15 A")
    is_valid, error = command_parser.validate(command)
    assert is_valid is False
    assert "Crop" in error
    
    # Missing quantity
    command = command_parser.parse("HARVEST MAIZE A")
    is_valid, error = command_parser.validate(command)
    assert is_valid is False
    assert "Quantity" in error
    
    # Missing quality
    command = command_parser.parse("HARVEST MAIZE 15")
    is_valid, error = command_parser.validate(command)
    assert is_valid is False
    assert "Quality" in error


def test_sms_adapter_request_parsing(sms_adapter, sms_gateway):
    """Test SMS webhook payload parsing."""
    # Africa's Talking format
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


def test_sms_adapter_harvest_handling(sms_adapter, sms_gateway):
    """Test SMS harvest command handling."""
    # Simulate incoming SMS
    payload = sms_gateway.receive_message("+254712345678", "HARVEST MAIZE 15 A")
    
    # Process with adapter
    request = sms_adapter.parse_request(payload)
    response = sms_adapter.handle_request(request)
    
    # Verify response
    assert "Harvest recorded" in response.content
    assert "15" in response.content
    assert "Grade A" in response.content
    assert response.session_active is False


@pytest.mark.asyncio
async def test_sms_adapter_send_message(sms_adapter, sms_gateway):
    """Test sending SMS via adapter."""
    success = await sms_adapter.send_message(
        to="+254712345678",
        message="Test message"
    )
    
    assert success is True
    
    # Verify message in outbox
    outbox = sms_gateway.get_outbox()
    assert len(outbox) == 1
    assert outbox[0].recipient == "+254712345678"
    assert outbox[0].content == "Test message"
    assert outbox[0].status == "delivered"


def test_sms_invalid_command(sms_adapter, sms_gateway):
    """Test handling of invalid SMS commands."""
    payload = sms_gateway.receive_message("+254712345678", "INVALID COMMAND")
    
    request = sms_adapter.parse_request(payload)
    response = sms_adapter.handle_request(request)
    
    assert "Unknown command" in response.content or "HELP" in response.content


def test_sms_incomplete_harvest_command(sms_adapter, sms_gateway):
    """Test handling of incomplete harvest commands."""
    # Missing quality
    payload = sms_gateway.receive_message("+254712345678", "HARVEST MAIZE 15")
    
    request = sms_adapter.parse_request(payload)
    response = sms_adapter.handle_request(request)
    
    assert "Error" in response.content
    assert "Quality" in response.content


def test_sms_natural_language_parsing(command_parser):
    """Test parsing of natural language SMS."""
    # Natural language format
    command = command_parser.parse("I harvested 25 bags of sorghum, grade B")
    assert command.command == "HARVEST"
    assert command.crop == "sorghum-01"
    assert command.quantity == 25.0
    assert command.quality == "B"


def test_sms_crop_name_variations(command_parser):
    """Test different crop name variations."""
    # Maize variations
    command = command_parser.parse("HARVEST CORN 10 A")
    assert command.crop == "maize-01"
    
    # Sorghum variations
    command = command_parser.parse("HARVEST MILLET 20 B")
    assert command.crop == "sorghum-01"


def test_sms_decimal_quantities(command_parser):
    """Test parsing of decimal quantities."""
    command = command_parser.parse("HARVEST MAIZE 15.5 A")
    assert command.quantity == 15.5
    
    command = command_parser.parse("HARVEST BEANS 10.25 B")
    assert command.quantity == 10.25


def test_sms_response_formatting(sms_adapter):
    """Test SMS response formatting."""
    from aos.adapters.channel import ChannelResponse
    
    response = ChannelResponse(content="Test message", session_active=False)
    formatted = sms_adapter.format_response(response)
    
    assert "message" in formatted
    assert formatted["message"] == "Test message"
