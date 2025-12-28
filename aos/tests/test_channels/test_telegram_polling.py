"""
Tests for Telegram Polling Service
Following TDD mandate from 01_roles.md
"""
from __future__ import annotations

import asyncio
from unittest.mock import Mock, patch

import pytest

from aos.adapters.telegram import TelegramAdapter
from aos.adapters.telegram_polling import TelegramPollingService


@pytest.fixture
def telegram_adapter() -> Mock[TelegramAdapter]:
    """Create mock TelegramAdapter with Gateway."""
    adapter = Mock(spec=TelegramAdapter)
    adapter.gateway = Mock()
    return adapter


@pytest.fixture
def polling_service(
    telegram_adapter: Mock[TelegramAdapter],
) -> TelegramPollingService:
    """Create TelegramPollingService instance."""
    return TelegramPollingService(
        telegram_adapter,
        poll_interval=1,
        timeout=30,
    )


# ... (initialization tests stay same as they don't hit I/O)

class TestTelegramPollingService:
    """Test suite for TelegramPollingService."""

    def test_initialization(
        self,
        polling_service: TelegramPollingService,
        telegram_adapter: Mock[TelegramAdapter],
    ) -> None:
        """Test polling service initializes correctly."""
        assert polling_service.adapter == telegram_adapter
        assert polling_service.poll_interval == 1
        assert polling_service.timeout == 30
        assert polling_service.last_update_id == 0
        assert polling_service.running is False

    @pytest.mark.asyncio
    async def test_get_updates_success(
        self,
        polling_service: TelegramPollingService,
        telegram_adapter: Mock[TelegramAdapter],
    ) -> None:
        """Test getting updates from Gateway."""
        mock_updates = [
            {'update_id': 1, 'message': {'text': 'test'}},
            {'update_id': 2, 'message': {'text': 'test2'}},
        ]
        # Gateway.get_updates is async
        telegram_adapter.gateway.get_updates.return_value = asyncio.Future()
        telegram_adapter.gateway.get_updates.return_value.set_result(mock_updates)

        updates = await polling_service.get_updates()

        assert len(updates) == 2
        assert polling_service.last_update_id == 2

    @pytest.mark.asyncio
    async def test_get_updates_empty(
        self,
        polling_service: TelegramPollingService,
        telegram_adapter: Mock[TelegramAdapter],
    ) -> None:
        """Test getting empty updates."""
        telegram_adapter.gateway.get_updates.return_value = asyncio.Future()
        telegram_adapter.gateway.get_updates.return_value.set_result([])

        updates = await polling_service.get_updates()

        assert len(updates) == 0
        assert polling_service.last_update_id == 0

    @pytest.mark.asyncio
    async def test_get_updates_error(
        self,
        polling_service: TelegramPollingService,
        telegram_adapter: Mock[TelegramAdapter],
    ) -> None:
        """Test handling gateway error."""
        telegram_adapter.gateway.get_updates.side_effect = Exception("API Down")

        updates = await polling_service.get_updates()

        assert len(updates) == 0

    @pytest.mark.asyncio
    async def test_process_message_update(
        self,
        polling_service: TelegramPollingService,
        telegram_adapter: Mock[TelegramAdapter],
    ) -> None:
        """Test processing message update."""
        update = {
            'update_id': 1,
            'message': {
                'from': {'id': 123},
                'chat': {'id': 456},
                'text': '/start',
            },
        }
        telegram_adapter.handle_message.return_value = asyncio.Future()
        telegram_adapter.handle_message.return_value.set_result(None)

        await polling_service.process_update(update)

        telegram_adapter.handle_message.assert_called_once()
        assert polling_service.stats['messages_processed'] == 1

    @pytest.mark.asyncio
    async def test_process_callback_update(
        self,
        polling_service: TelegramPollingService,
        telegram_adapter: Mock[TelegramAdapter],
    ) -> None:
        """Test processing callback query update."""
        update = {
            'update_id': 1,
            'callback_query': {
                'from': {'id': 123},
                'message': {'chat': {'id': 456}},
                'data': 'harvest_maize',
            },
        }
        telegram_adapter.handle_callback.return_value = asyncio.Future()
        telegram_adapter.handle_callback.return_value.set_result(None)

        await polling_service.process_update(update)

        telegram_adapter.handle_callback.assert_called_once_with(
            123,
            456,
            'harvest_maize',
        )

    @pytest.mark.asyncio
    async def test_process_update_error_handling(
        self,
        polling_service: TelegramPollingService,
        telegram_adapter: Mock[TelegramAdapter],
    ) -> None:
        """Test error handling in update processing."""
        telegram_adapter.handle_message.side_effect = Exception('Test error')

        update = {
            'update_id': 1,
            'message': {
                'from': {'id': 123},
                'chat': {'id': 456},
                'text': '/start',
            },
        }

        # Should not raise exception
        await polling_service.process_update(update)
        assert polling_service.stats['errors'] == 1

    def test_stop_polling(
        self,
        polling_service: TelegramPollingService,
    ) -> None:
        """Test stopping polling service."""
        from datetime import datetime

        polling_service.stats['start_time'] = datetime.now()
        polling_service.running = True

        polling_service.stop_polling()

        assert polling_service.running is False

    def test_get_status(
        self,
        polling_service: TelegramPollingService,
    ) -> None:
        """Test getting service status."""
        status = polling_service.get_status()

        assert 'running' in status
        assert 'last_update_id' in status
        assert 'stats' in status
        assert status['running'] is False
        assert status['last_update_id'] == 0
