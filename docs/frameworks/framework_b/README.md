# Framework B (Code Quality & Design System) — A-OS Implementation

**Canonical source**: `docs/01_roles.md` (FAANG 5-Framework System — A-OS Edition)

## 1. What Framework B is in A-OS

Framework B ensures the A-OS codebase remains maintainable, consistent, and visually premium through strict design tokens and atomic principles.

**Status**: ✅ 100% COMPLETE (December 25, 2025)

## 2. Objectives
- Eliminate ALL hardcoded CSS values (colors, spacing, typography).
- Establish single source of truth via `aos/ui/tokens.json`.
- Implement Atomic Design Registry (Atoms & Molecules) via Jinja2 macros.
- Mandatory verification via `/sys/gallery`.

## 3. Implementation Details

- **Phase 1: Tokenization Foundation**
  - Created `tokens.json` and `bridge.py` for Python/CSS interop.
- **Phase 2: Atomic Registry**
  - Implemented `EliteButton`, `Badge`, `Card`, `SearchBar` in `aos/api/templates/components/atoms/`.
- **Phase 3: Molecular Composition**
  - Built `DataCard`, `NodeStatus`, `ResourceWidget` in `aos/api/templates/components/molecules/`.
- **Phase 4: Verification Suite**
  - Deployed `/sys/gallery` for real-time visualization of all components.
- **Phase 5: Unified Template Overhaul**
  - Refactored `login.html` and `dashboard.html` to be 100% token-compliant.

## 4. Design Standards
- **Zero Hardcoded Values**: Mandatory use of `var(--aos-*)`.
- **Atomic Hierarchy**: Strict Atoms → Molecules → Organisms flow.
- **Rugged Aesthetic**: High-contrast, accessibility-first design.
- **Visual Performance**: Hardware-accelerated transitions and glassmorphism.

## 5. Key Deliverables
- ✅ `aos/ui/tokens.json`: The source of truth for design.
- ✅ `aos/ui/bridge.py`: Dynamic CSS generation.
- ✅ `/sys/gallery`: Operational design system playground.

## 6. How to Verify
- Visit `/sys/gallery` in the Admin Console.
- Run token compliance scan (planned automate script).
- Inspect CSS in browser to ensure `var(--aos-*)` usage.
