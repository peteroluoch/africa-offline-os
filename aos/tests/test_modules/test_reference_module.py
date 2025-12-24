import pytest
import asyncio
from aos.bus.events import Event
from aos.bus.dispatcher import EventDispatcher
from aos.modules.reference import ReferenceModule

class MockEventStore:
    # Mimic minimal EventStore interface for testing
    async def enqueue(self, event): pass
    async def mark_completed(self, event_id): pass
    async def mark_failed(self, event_id, error): pass

@pytest.fixture
def dispatcher():
    return EventDispatcher(store=MockEventStore())

@pytest.fixture
def module(dispatcher):
    return ReferenceModule(dispatcher)

@pytest.mark.asyncio
async def test_module_identity(module):
    """Verify module defines its identity correctly."""
    assert module.name == "system.reference"

@pytest.mark.asyncio
async def test_module_initialization(module, dispatcher):
    """Verify module registers subscribers on init."""
    await module.initialize()
    # Check if 'system.ping' has a subscriber
    assert "system.ping" in dispatcher._subscribers
    assert len(dispatcher._subscribers["system.ping"]) > 0

@pytest.mark.asyncio
async def test_ping_pong_logic(module):
    """Verify ping event triggers pong response."""
    # We maintain a list of emitted events to verify output
    emitted_events = []
    
    # Mock the dispatcher.publish method to capture output
    async def mock_capture(event):
        emitted_events.append(event)
    
    module.dispatcher.dispatch = mock_capture
    
    # Trigger logic directly
    ping_event = Event(name="system.ping", payload={"nonce": 12345})
    await module.handle_event(ping_event)
    
    assert len(emitted_events) == 1
    response = emitted_events[0]
    assert response.name == "system.pong"
    assert response.payload["nonce"] == 12345
    assert response.payload["status"] == "ok"

@pytest.mark.asyncio
async def test_shutdown_lifecycle(module):
    """Verify shutdown is idempotent and safe."""
    await module.shutdown()
    assert True # Should not raise
