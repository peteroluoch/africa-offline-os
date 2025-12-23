from __future__ import annotations

from collections import deque
from typing import Deque, Optional

from aos.bus.events import Event


class InMemoryEventQueue:
    def __init__(self) -> None:
        self._q: Deque[Event] = deque()

    def put(self, event: Event) -> None:
        self._q.append(event)

    def get_nowait(self) -> Optional[Event]:
        return self._q.popleft() if self._q else None
