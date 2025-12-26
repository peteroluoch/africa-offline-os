from __future__ import annotations

import os
from typing import Any
from unittest.mock import Mock, patch

import pytest

from aos.adapters.telegram import TelegramAdapter
from aos.bus.dispatcher import EventDispatcher


@pytest.fixture
def event_bus() -> EventDispatcher:
    return EventDispatcher()


def test_send_message_returns_false_when_token_missing(
    event_bus: EventDispatcher,
) -> None:
    with patch.dict(
        os.environ,
        {"TELEGRAM_BOT_TOKEN": ""},
        clear=False,
    ):
        adapter = TelegramAdapter(event_bus)

    assert adapter.send_message(chat_id="123", text="hello") is False


def test_send_message_posts_to_telegram_api_when_token_set(
    event_bus: EventDispatcher,
) -> None:
    with patch.dict(
        os.environ,
        {"TELEGRAM_BOT_TOKEN": "test-token"},
        clear=False,
    ):
        adapter = TelegramAdapter(event_bus)

    mock_response: Mock = Mock()
    mock_response.json.return_value = {"ok": True}

    with patch(
        "aos.adapters.telegram.requests.post",
        return_value=mock_response,
    ) as post:
        ok = adapter.send_message(
            chat_id="123",
            text="hello",
            reply_markup={"k": "v"},
        )

    assert ok is True

    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    args, kwargs = post.call_args

    expected_url = "https://api.telegram.org/bottest-token/sendMessage"
    assert args[0] == expected_url
    assert kwargs["json"]["chat_id"] == "123"
    assert kwargs["json"]["text"] == "hello"
    assert kwargs["json"]["parse_mode"] == "HTML"
    assert kwargs["json"]["reply_markup"] == {"k": "v"}


def test_send_message_returns_false_on_telegram_api_error(
    event_bus: EventDispatcher,
) -> None:
    with patch.dict(
        os.environ,
        {"TELEGRAM_BOT_TOKEN": "test-token"},
        clear=False,
    ):
        adapter = TelegramAdapter(event_bus)

    mock_response: Mock = Mock()
    mock_response.json.return_value = {"ok": False, "description": "bad"}

    with patch(
        "aos.adapters.telegram.requests.post",
        return_value=mock_response,
    ):
        ok = adapter.send_message(chat_id="123", text="hello")

    assert ok is False


def test_send_typing_action_returns_false_when_token_missing() -> None:
    with patch.dict(
        os.environ,
        {"TELEGRAM_BOT_TOKEN": ""},
        clear=False,
    ):
        assert TelegramAdapter.send_typing_action(chat_id="123") is False


def test_send_typing_action_posts_to_telegram_api_when_token_set() -> None:
    with patch.dict(
        os.environ,
        {"TELEGRAM_BOT_TOKEN": "test-token"},
        clear=False,
    ):
        mock_response: Mock = Mock()
        mock_response.json.return_value = {"ok": True}

        with patch(
            "aos.adapters.telegram.requests.post",
            return_value=mock_response,
        ) as post:
            ok = TelegramAdapter.send_typing_action(chat_id="123")

    assert ok is True

    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    args, kwargs = post.call_args

    expected_url = "https://api.telegram.org/bottest-token/sendChatAction"
    assert args[0] == expected_url
    assert kwargs["json"]["chat_id"] == "123"
    assert kwargs["json"]["action"] == "typing"
