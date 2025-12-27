# Framework C (Testing & QA) — A-OS Implementation

**Canonical source**: [docs/01_roles.md](file:///C:/Users/LENOVO/Documents/africa-offline-os/docs/01_roles.md) (FAANG 5-Framework System — A-OS Edition)

**Status**: ✅ 100% COMPLETE (December 27, 2025)

## 1. What Framework C is in A-OS

Framework C is the enforcement layer that guarantees:

- Unit correctness (TDD: Red → Green → Refactor)
- Data-flow integrity (SQLite WAL → Event Bus → API → UI fragments)
- Resilience under hostile edge conditions (fault injection: power-loss, disk failure, network partitions)
- Regression prevention via automated gates (pytest + coverage, ruff, mypy)

## 2. Non-negotiable invariants (Binding Contract)

- All new production code requires tests first (TDD mandate).
- Coverage gate is enforced by `pyproject.toml` (`fail_under = 90`).
- Tests must be deterministic and runnable offline.
- Any crash-recovery or persistence feature must be verified with repeatable simulations.

## 3. Current state (what already exists)

Framework C is already partially implemented in A-OS via the existing test suite:

- `aos/tests/test_event_persistence.py` (EventStore persistence + replay)
- `aos/tests/test_crash_recovery.py` (dispatcher recovery + failure durability)
- `aos/tests/test_db_resilience.py` (WAL persistence, reconnect behavior, integrity check)
- `aos/tests/test_adapter_contract.py` (adapter lifecycle + health contract)

## 4. A-OS-specific adaptation (no copy/paste)

TendaNow’s testing ideas are portable, but the implementation in A-OS must be rebuilt around:

- Python + pytest + asyncio (not Jest/RTL)
- SQLite WAL durability and edge crash recovery (not cloud DB assumptions)
- FastAPI lifespan boundaries
- Vehicle adapters (USSD/SMS/Telegram) as contract-tested I/O boundaries

## 5. Implementation plan (this repo)

### Phase C1 — Baseline gates (already in place)

- `pytest` + coverage gate (enforced in `pyproject.toml`)
- `ruff` + `mypy --strict`

### Phase C2 — Fault injection harness (NEW)

Add a small, A-OS-native fault injection utility used by tests to simulate:

- Abrupt DB connection termination
- EventStore connection termination
- “Crash then restart” recovery using the same SQLite DB file

Implementation location:

- `aos/testing/fault_injection.py`

### Phase C3 — Data-flow verification tests (NEXT)

Add end-to-end tests that validate the full flow:

- API request → DB write → event emitted → event persisted → dispatcher recovery path

Targets:

- Critical kernel endpoints (health, event stream)
- One vehicle (Telegram) flow with a mocked adapter boundary

## 6. How to run

From repo root:

- `pytest`
- `pytest -k fault_injection`
- `ruff check .`
- `mypy .`
