from aos.bus.events import Event
from aos.bus.queue import InMemoryEventQueue


def test_event_queue_round_trip() -> None:
    q = InMemoryEventQueue()
    event = Event(name="kernel.boot", payload={"v": 1})

    q.put(event)
    assert q.get_nowait() == event
    assert q.get_nowait() is None
