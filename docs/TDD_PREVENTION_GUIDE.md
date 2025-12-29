# TDD Breakdown Prevention Guide

## What Went Wrong

### Root Causes of This Pain
1. **Singleton Pattern Without Tests** - `EventStream` was created in `app.py` without testing its isolation
2. **Global State Proliferation** - Multiple modules importing globals differently created "ghost" instances
3. **Deferred Testing** - Features were built first, tests added later (backwards!)
4. **No Fixture Validation** - Test fixtures weren't verified to properly initialize/teardown state

## Prevention Rules (MANDATORY)

### Rule 1: Red-Green-Refactor (NO EXCEPTIONS)
```
❌ WRONG: Write feature → Write tests later
✅ RIGHT: Write failing test → Make it pass → Refactor
```

**Enforcement**: Every PR must show the failing test commit BEFORE the implementation commit.

### Rule 2: Test Fixtures First
Before writing ANY test that needs app state:
1. Write a fixture test that verifies setup/teardown
2. Run it 10 times in a row - if it fails once, fix it
3. Only then write feature tests

**Example**:
```python
def test_fixture_isolation():
    """Verify reset_globals actually resets everything."""
    app1 = create_app()
    # ... use app1 ...
    reset_globals()
    app2 = create_app()
    # Verify app2 has fresh state, not app1's leftovers
    assert core_state.event_dispatcher is None  # Before lifespan
```

### Rule 3: Singleton Checklist
Before creating ANY singleton:
- [ ] Is it truly needed? (Can it be dependency-injected instead?)
- [ ] Is it in a dedicated `state.py` or `singletons.py` file?
- [ ] Does it have a `clear()` or `reset()` method for tests?
- [ ] Is there a test proving it's the SAME instance across imports?

### Rule 4: Daily Test Health Check
Run this EVERY morning:
```bash
# Full suite must pass
pytest

# Must complete in <2 minutes (if slower, investigate)
time pytest

# No hanging tests (add --timeout=30)
pytest --timeout=30
```

### Rule 5: Pre-Commit Gate
```bash
# In .git/hooks/pre-commit
pytest --maxfail=1 -x
if [ $? -ne 0 ]; then
    echo "❌ Tests failing - commit blocked"
    exit 1
fi
```

## Warning Signs (Stop Immediately If You See These)

🚨 **"I'll add tests after this works"** → STOP. Write test first.

🚨 **Test hangs for >5 seconds** → STOP. Debug immediately, don't accumulate.

🚨 **"Just one more feature..."** → STOP. Fix failing tests first.

🚨 **Global variable added** → STOP. Prove it's testable first.

🚨 **Import works differently in test vs prod** → STOP. Fix import structure.

## Recovery Protocol (When Tests Break)

### Step 1: Isolate (30 min max)
```bash
# Find the exact failing test
pytest -x  # Stop at first failure

# Run just that test
pytest path/to/test.py::test_name -v
```

### Step 2: Bisect (If unclear when it broke)
```bash
git bisect start
git bisect bad HEAD
git bisect good <last-known-good-commit>
# Git will checkout commits - run pytest at each
```

### Step 3: Fix or Skip (Don't let it linger)
```python
@pytest.mark.skip(reason="Issue #123 - SSE cleanup")
def test_stream_hangs():
    ...
```
Create a GitHub issue immediately, link it, fix within 24 hours.

## Metrics to Track

### Green Metrics (Good Health)
- **Pass Rate**: >95% at all times
- **Test Duration**: <2 minutes for full suite
- **Coverage**: >80% for core modules
- **Flakiness**: 0 tests fail randomly

### Red Metrics (Immediate Action Required)
- Pass rate <90%
- Any test takes >30 seconds
- Same test fails 2+ times in a row

## Tools to Add

### 1. Pytest Plugins
```bash
pip install pytest-timeout pytest-xdist pytest-randomly
```

### 2. Pre-commit Hooks
```bash
pip install pre-commit
# Add .pre-commit-config.yaml with pytest
```

### 3. CI/CD Gate
```yaml
# .github/workflows/tests.yml
- name: Run tests
  run: pytest --timeout=30 --maxfail=5
  # Fail the build if tests fail
```

## The Golden Rule

**If a test is hard to write, the code is badly designed.**

Don't fight the test - refactor the code to be testable. That's the whole point of TDD.

---

## Action Items for A-OS

- [ ] Add `pytest-timeout` to prevent future hangs
- [ ] Create fixture validation tests
- [ ] Document singleton pattern in `01_roles.md`
- [ ] Set up pre-commit hooks
- [ ] Add test duration monitoring
- [/] Fix remaining 5 test failures within 48 hours (see plan below)

---

## Recovery Plan: 5 Remaining Test Failures

### Strategy: One-at-a-Time Investigation
**Rule**: Fix ONE test at a time. Commit after each fix. Never batch.

### Workflow for Each Test:
1. **Isolate**: Run only that test with `-v -s --tb=short`
2. **Instrument**: Add minimal logging to understand the failure
3. **Fix**: Apply the smallest possible fix
4. **Verify**: Run the test 10 times to ensure it's stable
5. **Commit**: `git commit -m "fix: [test_name] - [one-line description]"`
6. **Update Docs**: Update `02_ROADMAP.md` Phase 12 progress
7. **Push**: `git push`
8. **Move to Next**: Repeat for next failing test

### Test 1: [To be identified]
- **Status**: Not started
- **Command**: `pytest path/to/test.py::test_name -v -s --tb=short`
- **Hypothesis**: [Fill after investigation]
- **Fix**: [Fill after fix]
- **Commit**: [Link to commit]

### Test 2: [To be identified]
- **Status**: Not started
- **Command**: `pytest path/to/test.py::test_name -v -s --tb=short`
- **Hypothesis**: [Fill after investigation]
- **Fix**: [Fill after fix]
- **Commit**: [Link to commit]

### Test 3: [To be identified]
- **Status**: Not started
- **Command**: `pytest path/to/test.py::test_name -v -s --tb=short`
- **Hypothesis**: [Fill after investigation]
- **Fix**: [Fill after fix]
- **Commit**: [Link to commit]

### Test 4: [To be identified]
- **Status**: Not started
- **Command**: `pytest path/to/test.py::test_name -v -s --tb=short`
- **Hypothesis**: [Fill after investigation]
- **Fix**: [Fill after fix]
- **Commit**: [Link to commit]

### Test 5: [To be identified]
- **Status**: Not started
- **Command**: `pytest path/to/test.py::test_name -v -s --tb=short`
- **Hypothesis**: [Fill after investigation]
- **Fix**: [Fill after fix]
- **Commit**: [Link to commit]

### Completion Criteria
- [ ] All 5 tests passing
- [ ] Each test runs 10 times without failure
- [ ] Full suite completes in <2 minutes
- [ ] Zero hangs with `--timeout=30`
- [ ] Documentation updated
- [ ] Changes committed and pushed
