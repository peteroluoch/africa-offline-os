from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Event:
    name: str
    payload: Mapping[str, Any]
