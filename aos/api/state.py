from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aos.core.mesh.manager import MeshSyncManager
    from aos.core.resource.manager import ResourceManager
    from aos.modules.agri import AgriModule
    from aos.modules.transport import TransportModule
    from aos.modules.community import CommunityModule

class MeshState:
    manager: MeshSyncManager | None = None

class AgriState:
    module: AgriModule | None = None

class TransportState:
    module: TransportModule | None = None

class ResourceState:
    manager: ResourceManager | None = None

class CommunityState:
    module: CommunityModule | None = None

mesh_state = MeshState()
agri_state = AgriState()
transport_state = TransportState()
resource_state = ResourceState()
community_state = CommunityState()
