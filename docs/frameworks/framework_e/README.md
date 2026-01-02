# Framework E (Monitoring & Observability) — A-OS Implementation

**Canonical source**: `docs/01_roles.md` (FAANG 5-Framework System — A-OS Edition)

### [Framework E: Monitoring & Observability](file:///C:/Users/LENOVO/Documents/africa-offline-os/docs/frameworks/framework_e/README.md) ✅ COMPLETE

- **Goal**: Black-box visibility on disconnected edge nodes.
- **Key Item**: `/health` endpoint and structured JSON telemetry.

Framework E provides visibility into the "black box" of offline edge nodes, enabling proactive maintenance and resource management.

**Status**: ✅ 100% COMPLETE (January 2026)

## 2. Objectives
- Implement structured JSON logging system.
- Establish performance telemetry for edge nodes.
- Create local alerting system (Health Endpoint).
- Enable proactive issue detection in "black box" offline environments.
- **Monitor self-hosted dependencies** for updates.

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
- **Phase 6: SSE Stream Fixes (January 2026)**
  - Connected `event_dispatcher` to broadcast all events to SSE.
  - Made Live Kernel Log collapsible (default: collapsed).
  - Fixed SSE stream to show real-time events.
- **Phase 7: Dependency Update Checker (January 2026)**
  - FAANG-grade alert system for self-hosted dependencies (HTMX, fonts).
  - Daily GitHub API checks with breaking change detection.
  - Admin-only dashboard alerts (non-intrusive, dismissible).

## 4. Observability Standards
- **Correlation IDs**: Mandatory for any event crossing a module boundary.
- **Health-First**: Every node must report status even in low-power mode.
- **Disk Resilience**: Monitoring available storage to prevent SQLite corruption.
- **Dependency Awareness**: Proactive alerts for outdated self-hosted libraries.

## 5. Key Deliverables
- ✅ `/health` Endpoint: The heartbeat of the system.
- ✅ `aos.core.resource`: Proactive resource monitoring.
- ✅ `Event Stream UI`: Real-time kernel event visualization.
- ✅ `Dependency Checker`: FAANG-grade update alerts.

## 6. How to Verify
- `curl localhost:8000/health`
- `pytest aos/tests/test_health_enhanced.py`
- Open Dashboard → View "Kernel Health" widget.
- **SSE Test**: Open Dashboard → Expand "Live Kernel Log" → Generate events.
- **Dependency Alerts**: Check dashboard for update notifications (admin only).
