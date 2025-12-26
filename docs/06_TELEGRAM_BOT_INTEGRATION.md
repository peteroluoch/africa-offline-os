# Telegram Bot Integration for A-OS

**Document Number**: 06  
**Status**: Implementation Complete  
**Phase**: 5.9 (Vehicle Implementations - Telegram Adapter)  
**Date**: 2025-12-26

---

## Executive Summary

A-OS now supports Telegram as a communication channel, enabling farmers and drivers to interact with the system via Telegram bots. This implementation uses **polling mode** (no webhook required) for local development, adapted from Tenda's proven architecture.

### Key Benefits
- ✅ **100% Free** - No API subscription required
- ✅ **Instant Testing** - Test with @BotFather immediately
- ✅ **No Infrastructure** - No ngrok/webhook needed for development
- ✅ **Rich UI** - Inline keyboards, formatting, emojis
- ✅ **Proven Architecture** - Adapted from Tenda's production bot

---

## Architecture

### Component Structure

```
Telegram User
    ↓ Commands (/start, /register, /harvest)
Telegram Bot API (polling)
    ↓
TelegramPollingService
    ↓
TelegramAdapter
    ↓ Routes to handlers
AgriModule / TransportModule
```

### Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `aos/adapters/telegram.py` | Core adapter with command handlers | ~230 |
| `aos/adapters/telegram_polling.py` | Polling service (adapted from Tenda) | ~180 |
| `telegram_polling_start.py` | Standalone startup script | ~60 |
| `aos/adapters/__init__.py` | Package exports | ~7 |

---

## Features Implemented

### Command Handlers

#### General Commands
- `/start` - Welcome message with menu
- `/help` - Show available commands

#### Agri Commands
- `/register` - Register as farmer
- `/harvest` - Record harvest with inline keyboard

#### Transport Commands
- `/routes` - List available routes
- `/book` - Book a seat with inline keyboard

### Inline Keyboards

Telegram inline keyboards provide button-based menus:

```python
# Example: Crop selection keyboard
{
    "inline_keyboard": [
        [
            {"text": "🌽 Maize", "callback_data": "harvest_maize"},
            {"text": "🫘 Beans", "callback_data": "harvest_beans"}
        ],
        [
            {"text": "☕ Coffee", "callback_data": "harvest_coffee"}
        ]
    ]
}
```

### Message Formatting

- **HTML Formatting**: Bold, italic, code blocks
- **Emojis**: Visual indicators (✅, ❌, 🌾, 🚌)
- **Typing Indicators**: Shows "typing..." while processing

---

## Polling vs Webhook

### Polling Mode (Current Implementation)

**Advantages**:
- No public URL required
- No ngrok needed
- Works on localhost
- Perfect for development
- No webhook configuration

**How It Works**:
1. Service polls Telegram API every 1 second
2. Receives updates (messages, button clicks)
3. Processes updates sequentially
4. Sends responses back to Telegram

### Webhook Mode (Production)

**When to Use**:
- Production deployment
- Public domain available
- Need instant delivery

**Migration Path**:
1. Deploy A-OS to public server
2. Configure webhook URL
3. Set webhook via Telegram API
4. Disable polling service

---

## Setup Instructions

### 1. Create Telegram Bot

```
1. Open Telegram app
2. Search for @BotFather
3. Send /newbot
4. Choose bot name (e.g., "A-OS Agri Bot")
5. Choose username (e.g., "aos_agri_bot")
6. Copy bot token (format: 123456:ABC-DEF1234...)
```

### 2. Configure A-OS

```bash
# Add to .env file
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 3. Start Polling Service

```bash
# From project root
python telegram_polling_start.py
```

### 4. Test Bot

```
1. Search for your bot in Telegram
2. Send /start
3. Try commands: /register, /harvest, /routes, /book
```

---

## Design Decisions

### Why Polling for Development?

1. **No Infrastructure** - Works without public URL
2. **Windows Compatible** - No ngrok/tunnel issues
3. **Proven Pattern** - Tenda uses this successfully
4. **Easy Testing** - Start/stop anytime

### Why Simplified vs Tenda?

| Feature | Tenda | A-OS |
|---------|-------|------|
| Lines of Code | 3,381 | ~230 |
| Mini Web App | ✅ | ❌ |
| AI Integration | ✅ | ❌ (future) |
| State Management | Database | In-memory |
| Caching | Redis-like | Simple dict |

**Rationale**: Start simple, add complexity only when needed

### Message Format Standards

Following A-OS design principles:
- **Clarity**: Clear, concise messages
- **Consistency**: Uniform emoji usage
- **Accessibility**: HTML formatting for emphasis
- **Mobile-First**: Short messages, button-based navigation

---

## Integration with Existing Modules

### AgriModule Integration (Future)

```python
# In telegram.py
def handle_harvest_recording(self, chat_id, crop, quantity):
    if self.agri_module:
        harvest = await self.agri_module.record_harvest(
            farmer_id=get_farmer_by_telegram(chat_id),
            crop_type=crop,
            quantity=quantity
        )
        self.send_message(chat_id, f"✅ Harvest recorded! ID: {harvest.id}")
```

### TransportModule Integration (Future)

```python
# In telegram.py
def handle_booking(self, chat_id, route_id, passengers):
    if self.transport_module:
        booking = await self.transport_module.create_booking(
            route_id=route_id,
            passengers=passengers
        )
        self.send_message(chat_id, f"✅ Booking confirmed! ID: {booking.id}")
```

---

## Testing Strategy

### Manual Testing Checklist

- [ ] Bot responds to `/start`
- [ ] Bot responds to `/help`
- [ ] `/register` shows registration flow
- [ ] `/harvest` shows crop selection keyboard
- [ ] Clicking crop button triggers callback
- [ ] `/routes` lists available routes
- [ ] `/book` shows route selection keyboard
- [ ] Typing indicator appears before responses

### Automated Testing (TODO)

```python
# tests/test_telegram_adapter.py
def test_start_command():
    adapter = TelegramAdapter(event_bus)
    # Mock send_message
    adapter.handle_command(123, 456, "/start")
    # Assert welcome message sent

def test_harvest_keyboard():
    adapter = TelegramAdapter(event_bus)
    adapter.send_harvest_menu(123)
    # Assert inline keyboard sent with crop options
```

---

## Known Limitations

1. **No State Persistence** - User state stored in memory (lost on restart)
2. **No Module Integration** - Handlers not yet connected to AgriModule/TransportModule
3. **No Tests** - Automated tests not yet implemented
4. **Basic Error Handling** - Needs more robust error messages

---

## Next Steps

### Phase 5.9 Completion

1. **Add Tests** - Unit tests for adapter and polling service
2. **Module Integration** - Connect to AgriModule and TransportModule
3. **State Persistence** - Store user state in SQLite
4. **Error Handling** - Improve error messages and recovery

### Future Enhancements

1. **Media Support** - Images, documents, location sharing
2. **Group Support** - Cooperative/group messaging
3. **Webhook Mode** - Production deployment support
4. **AI Integration** - Natural language processing (like Tenda)

---

## Compliance Checklist

### FAANG Standards (from 01_roles.md)

- ❌ **TDD Mandate**: Tests not yet written (TODO)
- ✅ **Type Hints**: All functions have type annotations
- ✅ **Documentation**: This document + inline docstrings
- ❌ **Zero-Bug Policy**: Needs testing to verify
- ✅ **Single Source of Truth**: No duplication with existing code
- ✅ **Audit Before Action**: Checked Tenda implementation before building

### Design System Compliance

- ✅ **Clarity**: Clear command structure
- ✅ **Consistency**: Uniform emoji usage
- ✅ **Mobile-First**: Button-based navigation
- ⚠️ **Accessibility**: Text-based, inherently accessible

---

## References

- **Tenda Implementation**: `tenda-now-api/telegram_polling_service.py`
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **@BotFather**: https://t.me/botfather

---

**Status**: ✅ Implementation Complete, ❌ Tests Pending  
**Next Action**: Write automated tests (Phase 5.9 completion)
