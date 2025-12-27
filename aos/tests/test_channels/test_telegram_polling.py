"""
Tests for Telegram Polling Service
Following TDD mandate from 01_roles.md
"""
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from aos.adapters.telegram import TelegramAdapter
from aos.adapters.telegram_polling import TelegramPollingService


@pytest.fixture
def telegram_adapter() -> Mock[TelegramAdapter]:
    """Create mock TelegramAdapter."""
    adapter = Mock(spec=TelegramAdapter)
    adapter.get_bot_token.return_value = 'test_token_123'
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

    def test_stats_initialization(
        self,
        polling_service: TelegramPollingService,
    ) -> None:
        """Test statistics are initialized."""
        assert polling_service.stats['updates_received'] == 0
        assert polling_service.stats['messages_processed'] == 0
        assert polling_service.stats['errors'] == 0
        assert polling_service.stats['start_time'] is None

    @patch('aos.adapters.telegram_polling.requests.post')
    def test_get_updates_success(
        self,
        mock_post: Mock,
        polling_service: TelegramPollingService,
    ) -> None:
        """Test getting updates from Telegram API."""
        mock_response = {
            'ok': True,
            'result': [
                {'update_id': 1, 'message': {'text': 'test'}},
                {'update_id': 2, 'message': {'text': 'test2'}},
            ],
        }
        mock_post.return_value.json.return_value = mock_response

        updates = polling_service.get_updates()

        assert len(updates) == 2
        assert polling_service.last_update_id == 2

    @patch('aos.adapters.telegram_polling.requests.post')
    def test_get_updates_empty(
        self,
        mock_post: Mock,
        polling_service: TelegramPollingService,
    ) -> None:
        """Test getting empty updates."""
        mock_response = {'ok': True, 'result': []}
        mock_post.return_value.json.return_value = mock_response

        updates = polling_service.get_updates()

        assert len(updates) == 0
        assert polling_service.last_update_id == 0

    @patch('aos.adapters.telegram_polling.requests.post')
    def test_get_updates_api_error(
        self,
        mock_post: Mock,
        polling_service: TelegramPollingService,
    ) -> None:
        """Test handling Telegram API error."""
        mock_response = {'ok': False, 'description': 'Invalid token'}
        mock_post.return_value.json.return_value = mock_response

        updates = polling_service.get_updates()

        assert len(updates) == 0

    @patch('aos.adapters.telegram_polling.requests.post')
    def test_get_updates_timeout(
        self,
        mock_post: Mock,
        polling_service: TelegramPollingService,
    ) -> None:
        """Test handling request timeout."""
        import requests

        mock_post.side_effect = requests.exceptions.Timeout()

        updates = polling_service.get_updates()

        assert len(updates) == 0

    def test_process_message_update(
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

        polling_service.process_update(update)

        telegram_adapter.send_typing_action.assert_called_once_with('456')
        telegram_adapter.handle_message.assert_called_once()
        assert polling_service.stats['messages_processed'] == 1

    def test_process_callback_update(
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

        polling_service.process_update(update)

        telegram_adapter.handle_callback.assert_called_once_with(
            123,
            456,
            'harvest_maize',
        )

    def test_process_update_error_handling(
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
        polling_service.process_update(update)
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
