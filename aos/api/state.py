from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from aos.core.mesh.manager import MeshSyncManager
    from aos.modules.agri import AgriModule
    from aos.modules.transport import TransportModule

class MeshState:
    manager: Optional['MeshSyncManager'] = None

class AgriState:
    module: Optional['AgriModule'] = None

class TransportState:
    module: Optional['TransportModule'] = None

mesh_state = MeshState()
agri_state = AgriState()
transport_state = TransportState()
