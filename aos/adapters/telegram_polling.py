#!/usr/bin/env python3
"""
Telegram Polling Service for A-OS
Polls Telegram API for updates instead of using webhooks.
Perfect for local development without ngrok.

Adapted from Tenda's proven polling implementation.
"""
import logging
import time
from datetime import datetime

import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class TelegramPollingService:
    """
    Telegram Bot Polling Service
    Continuously polls Telegram API for new messages.
    """

    def __init__(self, telegram_adapter, poll_interval=1, timeout=30):
        """
        Initialize polling service.
        
        Args:
            telegram_adapter: TelegramAdapter instance
            poll_interval: Seconds between polls (default: 1)
            timeout: Telegram API timeout (default: 30)
        """
        self.adapter = telegram_adapter
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.last_update_id = 0
        self.running = False
        self.stats = {
            'updates_received': 0,
            'messages_processed': 0,
            'errors': 0,
            'start_time': None
        }

    def start_polling(self):
        """Start polling for Telegram updates."""
        self.running = True
        self.stats['start_time'] = datetime.now()

        logger.info("="*60)
        logger.info("A-OS Telegram Polling Service Started")
        logger.info("="*60)
        logger.info(f"Poll Interval: {self.poll_interval}s")
        logger.info(f"Timeout: {self.timeout}s")
        logger.info("Listening for messages...")
        logger.info("")

        try:
            while self.running:
                try:
                    updates = self.get_updates()

                    if updates:
                        self.stats['updates_received'] += len(updates)
                        logger.info(f"Received {len(updates)} update(s)")

                        for update in updates:
                            self.process_update(update)

                    time.sleep(self.poll_interval)

                except Exception as e:
                    self.stats['errors'] += 1
                    logger.error(f"Polling error: {e}")
                    time.sleep(5)  # Back off on error

        except KeyboardInterrupt:
            self.stop_polling()

    def get_updates(self):
        """
        Get updates from Telegram API.
        
        Returns:
            List of update objects
        """
        try:
            token = self.adapter.bot_token
            if not token:
                logger.error("Bot token not configured")
                return []

            url = f"https://api.telegram.org/bot{token}/getUpdates"

            payload = {
                'offset': self.last_update_id + 1,
                'timeout': self.timeout,
                'allowed_updates': ['message', 'callback_query']
            }

            response = requests.post(url, json=payload, timeout=self.timeout + 5)
            result = response.json()

            if result.get('ok'):
                updates = result.get('result', [])

                if updates:
                    # Update offset for next poll
                    self.last_update_id = updates[-1]['update_id']

                return updates
            else:
                error = result.get('description', 'Unknown error')
                logger.error(f"Telegram API error: {error}")
                return []

        except requests.exceptions.Timeout:
            # Expected for long polling
            return []
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []

    def process_update(self, update):
        """
        Process single Telegram update.
        """
        try:
            # Handle message updates
            if 'message' in update:
                message = update['message']
                user_id = message['from']['id']
                chat_id = message['chat']['id']
                text = message.get('text', '')

                if text:
                    logger.info(f"Message from {user_id}: {text[:50]}...")
                    self.stats['messages_processed'] += 1

                    # Handle message using the new unified signature
                    self.adapter.handle_message(message)

            # Handle callback queries (button clicks)
            elif 'callback_query' in update:
                callback = update['callback_query']
                user_id = callback['from']['id']
                chat_id = callback['message']['chat']['id']
                callback_data = callback.get('data', '')

                logger.info(f"Callback from {user_id}: {callback_data}")
                self.adapter.handle_callback(user_id, chat_id, callback_data)

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error processing update: {e}")

    def stop_polling(self):
        """Stop polling and display statistics."""
        self.running = False

        # Calculate uptime
        if self.stats['start_time']:
            uptime = datetime.now() - self.stats['start_time']
            uptime_str = str(uptime).split('.')[0]
        else:
            uptime_str = "N/A"

        logger.info("")
        logger.info("="*60)
        logger.info("Telegram Polling Service Stopped")
        logger.info("="*60)
        logger.info(f"Uptime: {uptime_str}")
        logger.info(f"Updates Received: {self.stats['updates_received']}")
        logger.info(f"Messages Processed: {self.stats['messages_processed']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("="*60)


def main():
    """Main entry point for standalone polling service."""
    # This will be called from a separate script
    # For now, just a placeholder
    logger.info("Use telegram_polling_start.py to start the polling service")


if __name__ == "__main__":
    main()
