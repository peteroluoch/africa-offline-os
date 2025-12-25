from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from aos.core.mesh.manager import MeshSyncManager

class MeshState:
    manager: Optional['MeshSyncManager'] = None

mesh_state = MeshState()
