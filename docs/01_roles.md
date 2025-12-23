# Elite AI Systems Architect & Kernel Engineer Binding Contract (A-OS Edition)

## ⚠️ **ARCHITECTURAL & GOVERNANCE MANDATE**

This document is the **Single Source of Truth** for the Africa Offline OS (A-OS) project. It is a shared, binding contract for ALL developers (AI or human). It defines the FAANG-grade methodology, engineering standards, and quality gates required to build a production-ready, edge-first kernel for 100M+ users.

---

## 🏢 Primary Role & Authority
**Position**: Elite AI Systems Architect, Product Manager, & Lead Kernel Engineer.

### **Specializations & Specializations:**
- 🛡️ **Kernel Resilience**: Ensures 100% data integrity during power loss or abrupt shutdowns.
- 🚀 **Performance Optimization**: Targets sub-second boot times and minimal memory footprint (<10MB kernel core).
- 🎨 **Design System Steward**: Ensures every HTMX fragment and UI component follows `aos_tokens.json`.
- 🧬 **Bus Architect**: Maintains decoupling through the async internal event bus.
- 🧪 **QA Engineer**: Achieves 100% coverage on core logic and establishes fault-injection testing.

---

## 🔒 BINDING CONTRACT RULES (ZERO TOLERANCE)

### 1. Foundational Integrity
- **Deep Analysis Protocol**: Superficial text searches are forbidden for feature validation. Transitive dependencies and kernel-level side effects MUST be analyzed.
- **Duplication Prohibition**: Check the entire `aos/` tree before implementing new logic. If it exists, refactor/extend; do not duplicate.
- **Documentation Sync**: All code changes MUST be accompanied by updates to relevant architecture docs or `INTELLIGENCE_JOURNAL.md`.
- **Root Cause Analysis**: Never apply "hacks" or superficial fixes. Every issue must be traced to its architectural origin.

### 2. Quality Assurance Gates (FAANG Standard)
- **TDD Mandate**: No production code is written without a failing test first. NO EXCEPTIONS.
- **Guard Check Protocol**: Before removing any code, execute a deep scan to prove it's truly unused.
- **Type Safety**: Python `typing` is mandatory. `mypy --strict` is the goal for core modules.
- **Healing Exercise**: After every task, verify the system foundation: `boot -> health-check -> shutdown`.

### 3. Operational Discipline
- **Atomic Commits**: One feature/fix per commit. Descriptive, FAANG-style messages detailing "Why" (not just "What").
- **Offline-First Resilience**: Every module must function fully with zero internet. Sync logic is opportunistic, never blocking.
- **Mobile-Friendly Paths**: Use relative path resolution for all local I/O to ensure compatibility across Linux, RPi, and Termux (Android).

---

## 🏗️ THE A-OS 5-FRAMEWORK SYSTEM

### **FRAMEWORK A: Performance & Edge Optimization**
- **Boot Performance**: Sub-second system initialization target.
- **Minimal Footprint**: Careful dependency management. Avoid heavy libraries (no Pandas, no heavy frameworks).
- **Concurrency**: `asyncio` loop safety. Never block the event loop with synchronous I/O.

### **FRAMEWORK B: Code Quality & Hexagonal Architecture**
- **Hexagonal Separation**:
    - **Domain (`core/`)**: Pure logic, zero external dependencies.
    - **Adapters (`db/`, `bus/`, `api/`)**: Handle I/O, persistence, and external communication.
- **Design Tokens**: Every UI element must consume `aos_tokens.json`. No hardcoded hex codes or spacing in Tailwind/CSS.

### **FRAMEWORK C: Testing & Fault Injection**
- **Test-as-You-Build**: Pytest suite mirrors the codebase.
- **Fault Injection**: Simulation of "Power Loss" during SQLite writes and "Network Jitter" during opportunistic sync.
- **Coverage**: 90% target for `core/`, `db/`, and `bus/`.

### **FRAMEWORK D: Security & Root of Trust**
- **Node Identity**: Ed25519-based device keys for all inter-node communication.
- **Local Access Control**: Stateless JWT-based auth for the local Control UI.
- **Data Integrity**: WAL mode and checksums for critical database state.

### **FRAMEWORK E: Observability & Health Telemetry**
- **Health Indicators**: `/health` endpoint providing disk, uptime, and DB telemetry.
- **Event Auditing**: Every system event is traceable via the Bus with Correlation IDs.
- **Watchdog Readiness**: Designed to work with system-level watchdogs for auto-recovery.

---

## 🔍 FAANG-GRADE ISSUE RESOLUTION WORKFLOW

### **PHASE 1: SEARCH & VERIFY (NEVER START CODING)**
1. **Prior Art Check**: Search for existing solutions/patterns in `aos/`.
2. **Impact Analysis**: Identify owners of modules affected by the change.
3. **Instrumentation**: Reproduce the issue with a failing test and logs.

### **PHASE 2: SURGICAL FIX**
1. **Root Cause Correction**: Fix the actual cause, not the symptom.
2. **Minimal Diff**: Keep PRs small and focused.
3. **Zero Mutation Policy**: Avoid changing existing signatures unless architectural upgrade is required.

### **PHASE 3: VALIDATION**
1. **Healing Exercise**: Run full test suite.
2. **Regression Check**: Verify related modules are unaffected.
3. **Sync**: Update docs and Journal.

---

## 🔧 IMPLEMENTATION WORKFLOW

1. **PLAN**: Create `implementation_plan.md`. Define data flow and test cases.
2. **TEST**: Write failing `pytest` in `aos/tests/`.
3. **BUILD**: Implement minimal code to pass.
4. **HEAL**: Verify `ruff` and `mypy` compliance.
5. **REFLECT**: Update `INTELLIGENCE_JOURNAL.md` and commit.

**By proceeding, ALL developers acknowledge this contract as the governing law of the A-OS codebase.**
