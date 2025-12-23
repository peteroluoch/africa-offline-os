from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdapterInfo:
    name: str
    version: str
