from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from aos.core.mesh.manager import MeshSyncManager
    from aos.modules.agri import AgriModule

class MeshState:
    manager: Optional['MeshSyncManager'] = None

class AgriState:
    module: Optional['AgriModule'] = None

mesh_state = MeshState()
agri_state = AgriState()
