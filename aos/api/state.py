from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from aos.core.mesh.manager import MeshSyncManager
    from aos.modules.agri import AgriModule
    from aos.modules.transport import TransportModule
    from aos.core.resource.manager import ResourceManager

class MeshState:
    manager: Optional['MeshSyncManager'] = None

class AgriState:
    module: Optional['AgriModule'] = None

class TransportState:
    module: Optional['TransportModule'] = None

class ResourceState:
    manager: Optional['ResourceManager'] = None

mesh_state = MeshState()
agri_state = AgriState()
transport_state = TransportState()
resource_state = ResourceState()
