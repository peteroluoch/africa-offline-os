# Changelog
All notable changes to this project are documented here.

This project follows a **phased infrastructure roadmap**.  
Each phase is intentional and auditable.

---

## [Unreleased]

### Planned
- Phase 9: Regional Aggregation (Sync-Nodes)
- Phase 10: Governance & Quality Hardening

---

## [0.8.0] — Phase 8: Power & Resource Awareness (2025-12-26)

### Added
- **Resource Monitoring**: Battery, CPU, memory, disk tracking via psutil
- **Power Profiles**: 4-tier system (FULL_POWER → BALANCED → POWER_SAVER → CRITICAL)
- **Resource-Aware Scheduler**: Priority-based task queue with power-aware deferral
- **ResourceManager**: Background monitoring loop with event bus integration
- **Dashboard Widget**: Real-time resource status in sidebar with SSE updates
- **Power-Aware Modules**: AgriModule and TransportModule now defer tasks when battery low
- **API Endpoints**: `/sys/resource/*` for status, profile control, and deferred tasks

### Impact
- Edge survival on solar/battery power
- Automatic task deferral when battery <50%
- Graceful degradation (user ops always work)
- Real-world tested: Battery 14-23%, auto-switching verified

---

## [0.7.0] — Phase 7: Transport & Mobility (2025-12-25)

### Added
- **TransportModule**: Route management, vehicle tracking, booking system
- **Transport UI**: Dashboard with route cards, vehicle status, booking forms
- **Transport USSD**: Driver and passenger flows for feature phones
- **Vehicle Management**: Registration, status updates, route assignment
- **Add Vehicle Feature**: Modal form with HTMX integration

### Fixed
- All dashboard navigation links functional
- Template syntax errors resolved
- Button functionality verified

---

## [0.6.0] — Phase 6: Agri-Module (Lighthouse) (2025-12-24)

### Added
- **AgriModule**: Farmer registration, harvest recording, inventory tracking
- **Agri UI**: Dashboard with farmer list, harvest forms, inventory cards
- **Agri USSD**: Complete farmer onboarding flow for feature phones
- **Universal USSD/SMS Adapters**: Channel abstraction for Africa's Talking/Twilio
- **Harvest Recording**: Mobile-optimized forms with HTMX submission

### Infrastructure
- Event-driven harvest recording
- SQLite repositories for farmers, crops, harvests
- Mock gateways for USSD/SMS testing

---

## [0.5.0] — Phase 5: Vehicle Implementations (2025-12-23)

### Added
- **FAANG Design System**: Atomic design components (atoms, molecules)
- **Premium UI**: Glassmorphism, dynamic backgrounds, smooth animations
- **IAM System**: Argon2id password hashing, Ed25519 JWT tokens
- **Authentication**: Login/logout with cookie-based sessions
- **Dashboard**: Real-time event monitor with HTMX/SSE
- **UI Gallery**: Component showcase at `/sys/gallery`
- **Mesh Sync**: Peer-to-peer discovery, store-and-forward, delta sync
- **RemoteNode Adapter**: Signed payload exchange between nodes

### Design System
- `tokens.json` v1.1.0 with breakpoints, grid, transitions
- Atomic components: Badge, Button, Card, Input, Preloader, Pagination
- Molecular components: DataCard, NodeStatus, SidebarItem, ResourceWidget
- Zero emoji policy enforced
- Mobile-first responsive utilities

---

## [0.2.0] — Event Bus & Scheduler (2025-12-24)

### Added
- **Durable Event Bus**: SQLite-backed journaling with crash recovery
- **Event Scheduler**: Persistent time-based task engine (one-off and recurring)
- **Base Contracts**: Abstract base classes for `Adapter` and `Module` extension points
- **Improved Testing**: Reached 80+ tests and 85%+ code coverage

---

## [0.1.0] — Kernel Bootstrap (2025-12-23)

### Added
- Core configuration system
- SQLite engine with WAL mode
- FastAPI kernel
- Health endpoint
- Lifecycle management
- Test harness

### Notes
- No modules or vehicles included
- Offline-first guarantees established
- Mobile-compatible paths enforced

---

## Versioning Policy

- Major versions indicate architectural milestones
- Minor versions indicate feature additions
- Patch versions indicate bug fixes or internal improvements

---

## Guiding Principle

> Stability before scale.  
> Infrastructure before interfaces.
