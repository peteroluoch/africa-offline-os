#!/usr/bin/env python3
"""
Start Telegram Polling Service for A-OS
Run this script to start the Telegram bot in polling mode (no webhook needed).
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


from aos.adapters import TelegramAdapter, TelegramPollingService
from aos.bus.dispatcher import EventDispatcher


def main():
    """Start Telegram polling service."""
    print("\n" + "="*60)
    print("A-OS Telegram Bot - Polling Mode")
    print("="*60)
    print("\n✅ Advantages:")
    print("   - No ngrok needed")
    print("   - No webhook configuration")
    print("   - Works on localhost")
    print("   - Perfect for development\n")

    # Check for bot token
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN not set")
        print("\n📝 To fix:")
        print("   1. Create a bot with @BotFather on Telegram")
        print("   2. Copy the bot token")
        print("   3. Set TELEGRAM_BOT_TOKEN in your .env file")
        print("   4. Restart this script\n")
        sys.exit(1)

    print("✅ Bot token configured")
    print("🤖 Starting polling service...\n")

    # Initialize components (simplified for standalone polling)
    event_bus = EventDispatcher()

    # Create adapter (without modules for now - will add later)
    adapter = TelegramAdapter(event_bus)

    # Create and start polling service
    service = TelegramPollingService(adapter, poll_interval=1)

    try:
        service.start_polling()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        service.stop_polling()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        service.stop_polling()
        sys.exit(1)


if __name__ == "__main__":
    main()
