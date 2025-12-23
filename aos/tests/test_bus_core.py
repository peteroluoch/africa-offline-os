import asyncio
import pytest
from datetime import datetime, timezone
from aos.bus.events import Event
from aos.bus.dispatcher import EventDispatcher

@pytest.mark.asyncio
async def test_event_dispatch_to_single_subscriber():
    """Verify an event reaches a registered subscriber."""
    dispatcher = EventDispatcher()
    received_events = []

    async def handler(event: Event):
        received_events.append(event)

    dispatcher.subscribe("test.event", handler)
    
    event = Event(name="test.event", payload={"key": "value"})
    await dispatcher.dispatch(event)
    
    # Wait a tiny bit for the async task to process
    await asyncio.sleep(0.01)
    
    assert len(received_events) == 1
    assert received_events[0].name == "test.event"
    assert received_events[0].payload["key"] == "value"
    assert received_events[0].id is not None
    assert isinstance(received_events[0].timestamp, datetime)

@pytest.mark.asyncio
async def test_event_dispatch_to_multiple_subscribers():
    """Verify an event reaches all registered subscribers."""
    dispatcher = EventDispatcher()
    calls = {"h1": 0, "h2": 0}

    async def h1(event: Event): calls["h1"] += 1
    async def h2(event: Event): calls["h2"] += 1

    dispatcher.subscribe("multi.event", h1)
    dispatcher.subscribe("multi.event", h2)
    
    await dispatcher.dispatch(Event(name="multi.event", payload={}))
    await asyncio.sleep(0.01)
    
    assert calls["h1"] == 1
    assert calls["h2"] == 1

@pytest.mark.asyncio
async def test_error_isolation():
    """Verify a failing subscriber doesn't prevent others from receiving the event."""
    dispatcher = EventDispatcher()
    received = []

    async def failing_handler(event: Event):
        raise ValueError("Simulated failure")

    async def succeeding_handler(event: Event):
        received.append(event)

    dispatcher.subscribe("isolate.event", failing_handler)
    dispatcher.subscribe("isolate.event", succeeding_handler)
    
    await dispatcher.dispatch(Event(name="isolate.event", payload={}))
    await asyncio.sleep(0.01)
    
    assert len(received) == 1

@pytest.mark.asyncio
async def test_wildcard_subscription():
    """Verify subscribers can listen to event patterns (Future proofing)."""
    # This might be an enhancement, but let's start with exact matches for Batch 1
    # unless requirements specify globbing.
    pass

@pytest.mark.asyncio
async def test_high_concurrency_dispatch():
    """Test the bus under high load (1000 events)."""
    dispatcher = EventDispatcher()
    count = 0
    total_events = 1000

    async def handler(event: Event):
        nonlocal count
        count += 1

    dispatcher.subscribe("load.test", handler)
    
    tasks = [
        dispatcher.dispatch(Event(name="load.test", payload={"i": i}))
        for i in range(total_events)
    ]
    await asyncio.gather(*tasks)
    
    # Wait for queue depletion
    for _ in range(10):
        if count == total_events:
            break
        await asyncio.sleep(0.05)
        
    assert count == total_events
