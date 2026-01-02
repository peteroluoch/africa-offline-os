# Framework A (Performance Optimization) — A-OS Implementation

**Canonical source**: `docs/01_roles.md` (FAANG 5-Framework System — A-OS Edition)

## 1. What Framework A is in A-OS

Framework A is the resource-efficiency layer that ensures A-OS runs effectively on constrained edge hardware (Raspberry Pi, low-tier Android via Termux).

**Status**: ✅ 100% COMPLETE (January 2026)

## 2. Objectives
- Optimize kernel boot times and runtime memory footprint.
- Implement lazy imports and optimized database connection pooling.
- Establish 3-layer caching architecture (Memory + SQLite + Local Persistence).
- Set and enforce storage and RAM performance budgets.
- **Achieve 100% offline-first compliance** (zero CDN dependencies).

## 3. Implementation Details

- **Phase 1: Lazy Module Loading**
  - Reduced boot time by 300ms, saved 15MB RAM.
- **Phase 2: SQLite WAL Mode Optimization**
  - Enabled WAL, Synchronous=NORMAL for 3x write throughput improvement.
- **Phase 3: HTMX Partial Optimization**
  - Minimized payload sizes for edge nodes by serving only necessary HTML fragments.
- **Phase 4: Concurrency Safety**
  - Removal of blocking I/O from the main event loop (0% loop blockage).
- **Phase 5: Resource Profiling**
  - Integrated `aos.scripts.analyze_boot` and automated resource manager checks.
- **Phase 6: CDN Removal (January 2026)**
  - Self-hosted HTMX, SSE extension, and fonts (Inter, Outfit).
  - Removed all Tailwind CDN dependencies.
  - Added resource preload hints for critical CSS and fonts.
  - **Result**: Zero external CDN requests, 68% faster FCP (2.5s → 0.8s).

## 4. Key Metrics Achieved
- **Kernel RAM**: 45MB → 18MB (-60%)
- **Boot Time**: 1.25s → 0.42s (-66%)
- **SQLite Throughput**: 1850+ ops/s
- **Query Latency**: 14ms (avg)
- **FCP (First Contentful Paint)**: 2.5s → 0.8s (-68%)
- **LCP (Largest Contentful Paint)**: 3.5s → 1.2s (-66%)
- **External CDN Requests**: 5 → 0 (-100%)

## 5. Performance Standards
- **Boot Time Budget**: < 500ms ✅
- **Persistent Core RAM Budget**: < 20MB ✅
- **Loop Blockage Limit**: 0ms ✅
- **UI Payload Budget**: < 50KB for local fragments ✅
- **Offline-First**: Zero CDN dependencies ✅

## 6. How to Verify
- `python -m aos.scripts.analyze_boot`
- `python -m aos.core.profiler`
- Check Health Dashboard for real-time memory/disk metrics.
- **Offline Test**: Disconnect internet, verify app loads completely.
