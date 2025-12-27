# Framework E (Monitoring & Observability) — A-OS Implementation

**Canonical source**: `docs/01_roles.md` (FAANG 5-Framework System — A-OS Edition)

## 1. What Framework E is in A-OS

Framework E provides visibility into the "black box" of offline edge nodes, enabling proactive maintenance and resource management.

**Status**: ✅ ACTIVE / 90% COMPLETE (December 2025)

## 2. Objectives
- Implement structured JSON logging system.
- Establish performance telemetry for edge nodes.
- Create local alerting system (Health Endpoint).
- Enable proactive issue detection in "black box" offline environments.

## 3. Implementation Details

- **Phase 1: Structured Logging**
  - Integrated `aos.core.logging` for consistent JSON-line logs.
- **Phase 2: Health Monitoring**
  - `/health` endpoint providing real-time Disk, RAM, Uptime, and DB status.
- **Phase 3: Resource Management**
  - Implemented `ResourceManager` to track hardware constraints and signal modules to conserve power.
- **Phase 4: Correlation Tracking**
  - Added unique IDs to every event in the bus for trace-friendly debugging.
- **Phase 5: Visual Cockpit**
  - Admin Dashboard health widgets and "Live Kernel Log" SSE stream.

## 4. Observability Standards
- **Correlation IDs**: Mandatory for any event crossing a module boundary.
- **Health-First**: Every node must report status even in low-power mode.
- **Disk Resilience**: Monitoring available storage to prevent SQLite corruption.

## 5. Key Deliverables
- ✅ `/health` Endpoint: The heartbeat of the system.
- ✅ `aos.core.resource`: Proactive resource monitoring.
- ✅ `Event Stream UI`: Real-time kernel event visualization.

## 6. How to Verify
- `curl localhost:8000/health`
- `pytest aos/tests/test_health_enhanced.py`
- Open Dashboard → View "Kernel Health" widget.
