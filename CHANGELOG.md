# Changelog
All notable changes to this project are documented here.

This project follows a **phased infrastructure roadmap**.  
Each phase is intentional and auditable.

---

## [Unreleased]

### Planned
- Phase 0: Kernel Bootstrap
- Phase 1: Event Bus & Adapter Contracts
- Phase 2: Node Control UI
- Phase 3: Connectivity & Sync Layer
- Phase 4: Identity & Trust Core
- Phase 5: Vehicle Implementations
- Phase 6: Agri Module
- Phase 7: Transport Module
- Phase 8: Power & Resource Awareness
- Phase 9: Regional Aggregation
- Phase 10: Hardening & Governance

---

## [0.2.0] — Event Bus & Scheduler (2025-12-24)

### Added
- **Durable Event Bus**: SQLite-backed journaling with crash recovery.
- **Event Scheduler**: Persistent time-based task engine (one-off and recurring).
- **Base Contracts**: Abstract base classes for `Adapter` and `Module` extension points.
- **Improved Testing**: Reached 80+ tests and 85%+ code coverage.

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
