# Intelligence Journal - Africa Offline OS

## 🧠 System Memory & Evolution Log

This document serves as the persistent memory for the AI Architect. It records lessons learned, anti-patterns detected, and strategic improvements for the A-OS project.

---

## 📅 Initial Reconnaissance (Dec 23, 2025)

### Lessons Learned
1. **Python Package Structure**:
   - **Observation**: Tests failed initially because directories were missing `__init__.py`.
   - **Lesson**: Python explicitly requires `__init__.py` to treat directories as importable packages. This is critical for test discovery.
   - **Action**: Always ensure new modules include `__init__.py`. Use `aos.core` style imports.

2. **Project Structure**:
   - **Observation**: The rigorous directory structure (`core`, `db`, `bus`) works well for separation of concerns.
   - **Lesson**: Maintaining this separation prevents circular dependencies.
   - **Protocol**: Domain logic goes in `core`. I/O goes in `adapters`. Wiring goes in `main`/`api`.

3. **Lifecycle Management**:
   - **Observation**: `FastAPI` lifespan events are the correct place for DB connection management.
   - **Lesson**: Global variables for DB connections are acceptable IF managed strictly within the lifespan context manager.
   - **Protocol**: Use `asynccontextmanager` in `aos.api.app` to bind resources.

### Anti-Patterns to Avoid
- **Implicit Dependencies**: Do not use libraries not listed in `requirements.txt`.
- **Blocking I/O in Async**: Do not run `time.sleep` or heavy calculations in async routes. Use `asyncio.sleep` or thread pools.
- **Hardcoded Paths**: Always use `aos.core.config.Settings` for paths (e.g., DB file location).

### Strategic Improvements (Backlog)
- [ ] **Automated Linting**: Integrate `ruff` into a pre-commit check or CI script.
- [ ] **Type Checking**: Add `mypy` configuration and enforce strict typing.
- [ ] **Watchdog**: Implement a system watchdog for the main process.

---
*End of Entry - Initial Setup*
