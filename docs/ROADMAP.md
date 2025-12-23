# A-OS — MASTER DEVELOPMENT ROADMAP

**Vision**: The foundational operating layer for the next 100M+ edge-connected users in Africa.  
**Standard**: FAANG-grade Production (TDD, Zero-Bug, Offline-First, Power-Safe).  
**Philosophy**: Thick Infrastructure, Thin Vehicles. Build once, adapt everywhere.

---

## 🚦 Executive Status: Phase 0 HARDENED
| Phase | Title | Focus | Progress | Status |
| :--- | :--- | :--- | :--- | :--- |
| **0** | **Kernel Bootstrap** | Foundation & Resilience | 100% | 🔒 **PROD-READY** |
| **1** | **Event Bus & Adapters** | Extension & Contracts | 15% | 🔜 **IN PROGRESS** |
| **2** | **A-OS Node UI** | Observability (HTMX) | 5% | ⏳ PLANNED |
| **3** | **Sync & Connectivity** | Intermittent Intelligence | 0% | ⏳ PLANNED |
| **4** | **Identity & Trust Core** | Decentralized ID | 0% | ⏳ PLANNED |
| **5** | **Vehicle Implementations** | Human Interaction | 0% | ⏳ PLANNED |

---

## 🧩 Phase 0: Kernel Bootstrap (The Foundation)
**Goal**: Establish a power-safe, high-concurrency runtime that survives anything.  
**Status**: 🔒 **SECURED (TDD Hardened)**

### 🛠️ What Exists
- **FastAPI Core**: Lifespan managed, async-first.
- **SQLite Engine**: WAL-mode enabled, power-loss resilience validated.
- **Config System**: Environment-driven, mobile-path aware (`AOS_` prefix).
- **Health System**: Real-time disk/uptime/DB telemetry.
- **Quality Gates**: 90% coverage mandate, strict linting/typing (Ruff/MyPy).

### 📦 Artifacts
- [x] `aos.api.app` (Kernel entry)
- [x] `aos.db.engine` (Persistence)
- [x] `docs/01_roles.md` (Shared Blueprint)
- [x] `aos/tests/` (28+ Production-grade tests)

---

## ⚡ Phase 1: Event Bus & Adapter Contracts
**Goal**: Decouple business logic from human/external interfaces.  
**Status**: 🔜 **NEXT PRIORITY**

### 🎯 Scope
- **Domain Event Bus**: In-process, thread-safe message passing.
- **Persistence Hooks**: Event-sourcing readiness (local replay).
- **The Adapter Contract**: Abstract base for USSD, SMS, WhatsApp, Hub.
- **The Module Contract**: Abstract base for Agri, Finance, Identity logic.

### 🔑 Unlocks
- Dev teams can build **Modules** (Calculations/Logic) without knowing about **Vehicles** (SMS/Web).
- **Vehicles** (Adapters) can be hot-swapped or multiplexed.

---

## 🖥️ Phase 2: Node Control UI (OS UI)
**Goal**: Operational visibility for hub managers and field agents.  
**Status**: ⏳ PLANNED (H1 2026)

### 🎯 Scope
- **Tech Stack**: HTMX + Alpine.js (Zero heavy JS bundles).
- **Features**: 
    - Real-time Node telemetry (Disk, RAM, Battery).
    - Module status dashboard.
    - Local sync queue inspection (How much data is waiting for signal?).
    - Power-loss event logging.

---

## 📡 Phase 3: Connectivity & Sync Layer
**Goal**: Smart data movement over "broken" networks.  
**Status**: ⏳ PLANNED

### 🎯 Scope
- **Connectivity Detection**: Heartbeat logic for signal drift.
- **Signed Payloads**: Ensuring data remains tamper-proof during ferry/sync.
- **Delta Sync**: Sending only bits that changed (bandwidth optimization).
- **Conflict Resolution**: "Last-signed wins" vs "Merge-safe" strategies.

---

## 🆔 Phase 4: Identity & Trust Core
**Goal**: Reliable ID in contexts where "Google Login" is impossible.  
**Status**: ⏳ PLANNED

### 🎯 Scope
- **Local Registry**: Encrypted local ID tables (Ed25519 signatures).
- **Biometric Hooks**: Standardized interfaces for external scanners.
- **Trust Chaining**: Verifying ID `A` was vouched for by Agent `B` offline.

---

## 🚜 Phase 5: Vehicle Implementations
**Goal**: Multiplexing the A-OS kernel to every African interface.  
**Status**: ⏳ PLANNED

### 🎯 Scope
- **USSD Adapter**: For low-end feature phones.
- **SMS Adapter**: For asynchronous field reporting.
- **WhatsApp/Telegram Adapters**: For smartphone-connected agents.
- **Agent PWA**: For high-trust field hubs.

---

## 🛡️ Strategic Guardrails (Standard for All Phases)
1. **No Docker Requirement**: Must run native on Linux/Android/RPi.
2. **Zero Global Variables**: Everything bound to `App` lifecycle.
3. **TDD Mandatory**: No code pushes without `pytest` coverage.
4. **Mobile-First Paths**: Default to user-writable directories (no root required).
5. **Shared Blueprint Compliance**: Every commit must adhere to `docs/01_roles.md`.

---
*Created by A-OS Architecture Team | Dec 2025*
