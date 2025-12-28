"""
Tests for Telegram Adapter
Following TDD mandate from 01_roles.md
"""
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from aos.adapters.telegram import TelegramAdapter
from aos.bus.dispatcher import EventDispatcher


@pytest.fixture
def event_bus() -> Mock[EventDispatcher]:
    """Create mock event bus."""
    return Mock(spec=EventDispatcher)


@pytest.fixture
def telegram_adapter(event_bus: Mock[EventDispatcher]) -> TelegramAdapter:
    """Create TelegramAdapter instance with mock gateway."""
    mock_gateway = Mock()
    mock_gateway.bot_token = "test_token"
    mock_gateway.send.return_value = asyncio.Future()
    mock_gateway.send.return_value.set_result({"ok": True})
    return TelegramAdapter(event_bus, gateway=mock_gateway)

class TestTelegramAdapter:
    """Test suite for TelegramAdapter."""

    def test_initialization(
        self,
        telegram_adapter: TelegramAdapter,
        event_bus: Mock[EventDispatcher],
    ) -> None:
        """Test adapter initializes correctly."""
        assert telegram_adapter.event_bus == event_bus
        assert telegram_adapter.agri_module is None
        assert telegram_adapter.transport_module is None
        assert telegram_adapter.gateway is not None

    @pytest.mark.asyncio
    async def test_send_message_success(
        self,
        telegram_adapter: TelegramAdapter,
    ) -> None:
        """Test sending message successfully via gateway."""
        result = await telegram_adapter.send_message('123', 'Test message')

        assert result is True
        telegram_adapter.gateway.send.assert_called_once()
        args = telegram_adapter.gateway.send.call_args[0]
        assert args[0] == '123'
        assert args[1] == 'Test message'

    @pytest.mark.asyncio
    async def test_handle_start_command(
        self,
        telegram_adapter: TelegramAdapter,
    ) -> None:
        """Test /start command handler."""
        with patch.object(telegram_adapter, 'send_welcome', return_value=asyncio.Future()) as mock_welcome:
            mock_welcome.return_value.set_result(None)
            message = {'chat': {'id': 456}, 'from': {'id': 123}, 'text': '/start'}
            await telegram_adapter.handle_message(message)
            mock_welcome.assert_called_once_with(456)

    @pytest.mark.asyncio
    async def test_handle_help_command(
        self,
        telegram_adapter: TelegramAdapter,
    ) -> None:
        """Test /help command handler."""
        with patch.object(telegram_adapter, 'send_help', return_value=asyncio.Future()) as mock_help:
             mock_help.return_value.set_result(None)
             message = {'chat': {'id': 456}, 'from': {'id': 123}, 'text': '/help'}
             await telegram_adapter.handle_message(message)
             mock_help.assert_called_once_with(456)

    @pytest.mark.asyncio
    async def test_handle_unknown_command(
        self,
        telegram_adapter: TelegramAdapter,
    ) -> None:
        """Test unknown command handling."""
        from unittest.mock import AsyncMock
        
        # Mock send_chat_action to avoid gateway calls
        telegram_adapter.send_chat_action = Mock(return_value=True)
        
        with patch.object(telegram_adapter, 'send_message', new=AsyncMock(return_value=True)) as mock_send:
            # Mock the router to return False (unhandled) using AsyncMock
            with patch.object(telegram_adapter.router, 'route_command', new=AsyncMock(return_value=False)) as mock_route:
                message = {'chat': {'id': 456}, 'from': {'id': 123}, 'text': '/unknown'}
                await telegram_adapter.handle_message(message)

                # Verify send_message was called
                assert mock_send.called
                
                # Verify the call contains the unknown command message
                call_args = mock_send.call_args
                assert call_args is not None
                assert len(call_args[0]) >= 2
                assert 'Unknown command' in call_args[0][1]

import asyncio
