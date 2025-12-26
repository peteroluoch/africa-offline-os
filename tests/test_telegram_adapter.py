"""
Tests for Telegram Adapter
Following TDD mandate from 01_roles.md
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from aos.adapters.telegram import TelegramAdapter
from aos.bus.dispatcher import EventDispatcher

@pytest.fixture
def event_bus():
    """Create mock event bus."""
    return Mock(spec=EventDispatcher)

@pytest.fixture
def telegram_adapter(event_bus):
    """Create TelegramAdapter instance."""
    return TelegramAdapter(event_bus)

class TestTelegramAdapter:
    """Test suite for TelegramAdapter."""
    
    def test_initialization(self, telegram_adapter, event_bus):
        """Test adapter initializes correctly."""
        assert telegram_adapter.event_bus == event_bus
        assert telegram_adapter.agri_module is None
        assert telegram_adapter.transport_module is None
    
    def test_get_bot_token_from_env(self, monkeypatch):
        """Test bot token retrieval from environment."""
        monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'test_token_123')
        token = TelegramAdapter.get_bot_token()
        assert token == 'test_token_123'
    
    def test_get_bot_token_missing(self, monkeypatch):
        """Test bot token when not set."""
        monkeypatch.delenv('TELEGRAM_BOT_TOKEN', raising=False)
        token = TelegramAdapter.get_bot_token()
        assert token == ''
    
    @patch('aos.adapters.telegram.requests.post')
    def test_send_message_success(self, mock_post, telegram_adapter, monkeypatch):
        """Test sending message successfully."""
        monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'test_token')
        mock_post.return_value.json.return_value = {'ok': True}
        
        result = telegram_adapter.send_message('123', 'Test message')
        
        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert 'chat_id' in call_args[1]['json']
        assert call_args[1]['json']['chat_id'] == '123'
        assert call_args[1]['json']['text'] == 'Test message'
    
    @patch('aos.adapters.telegram.requests.post')
    def test_send_message_with_keyboard(self, mock_post, telegram_adapter, monkeypatch):
        """Test sending message with inline keyboard."""
        monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'test_token')
        mock_post.return_value.json.return_value = {'ok': True}
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "Option 1", "callback_data": "opt1"}]
            ]
        }
        
        result = telegram_adapter.send_message('123', 'Choose:', reply_markup=keyboard)
        
        assert result is True
        call_args = mock_post.call_args
        assert 'reply_markup' in call_args[1]['json']
    
    @patch('aos.adapters.telegram.requests.post')
    def test_send_message_no_token(self, mock_post, telegram_adapter, monkeypatch):
        """Test sending message without bot token."""
        monkeypatch.delenv('TELEGRAM_BOT_TOKEN', raising=False)
        
        result = telegram_adapter.send_message('123', 'Test')
        
        assert result is False
        mock_post.assert_not_called()
    
    def test_handle_start_command(self, telegram_adapter):
        """Test /start command handler."""
        with patch.object(telegram_adapter, 'send_message') as mock_send:
            telegram_adapter.handle_command(123, 456, '/start')
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[0] == 456  # chat_id
            assert 'Welcome to Africa Offline OS' in call_args[1]
    
    def test_handle_help_command(self, telegram_adapter):
        """Test /help command handler."""
        with patch.object(telegram_adapter, 'send_message') as mock_send:
            telegram_adapter.handle_command(123, 456, '/help')
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert 'Welcome' in call_args[1]
    
    def test_handle_harvest_command(self, telegram_adapter):
        """Test /harvest command shows crop menu."""
        with patch.object(telegram_adapter, 'send_message') as mock_send:
            telegram_adapter.send_harvest_menu(456)
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert 'Record Harvest' in call_args[0][1]
            assert 'reply_markup' in call_args[1]
    
    def test_handle_routes_command(self, telegram_adapter):
        """Test /routes command lists routes."""
        with patch.object(telegram_adapter, 'send_message') as mock_send:
            telegram_adapter.send_routes_list(456)
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert 'Available Routes' in call_args[1]
    
    def test_handle_callback_harvest(self, telegram_adapter):
        """Test callback for harvest crop selection."""
        with patch.object(telegram_adapter, 'send_message') as mock_send:
            telegram_adapter.handle_callback(123, 456, 'harvest_maize')
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert 'Maize' in call_args[1]
    
    def test_handle_callback_booking(self, telegram_adapter):
        """Test callback for route booking."""
        with patch.object(telegram_adapter, 'send_message') as mock_send:
            telegram_adapter.handle_callback(123, 456, 'book_route_1')
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert 'Route selected' in call_args[1]
    
    def test_handle_unknown_command(self, telegram_adapter):
        """Test unknown command handling."""
        with patch.object(telegram_adapter, 'send_message') as mock_send:
            telegram_adapter.handle_command(123, 456, '/unknown')
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert 'Unknown command' in call_args[1]


class TestTelegramIntegration:
    """Integration tests for Telegram with modules."""
    
    def test_adapter_with_agri_module(self, event_bus):
        """Test adapter initialization with AgriModule."""
        mock_agri = Mock()
        adapter = TelegramAdapter(event_bus, agri_module=mock_agri)
        
        assert adapter.agri_module == mock_agri
    
    def test_adapter_with_transport_module(self, event_bus):
        """Test adapter initialization with TransportModule."""
        mock_transport = Mock()
        adapter = TelegramAdapter(event_bus, transport_module=mock_transport)
        
        assert adapter.transport_module == mock_transport
