"""External adapters."""
from __future__ import annotations

from aos.adapters.telegram import TelegramAdapter
from aos.adapters.telegram_polling import TelegramPollingService

__all__ = ["TelegramAdapter", "TelegramPollingService"]
