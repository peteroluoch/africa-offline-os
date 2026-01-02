# Dependency Update Checker - Documentation

## Purpose
Alert admins about available updates for self-hosted dependencies (HTMX, fonts) without auto-updating.

## Dependencies to Monitor
1. **HTMX** - Current: v1.9.10
2. **Inter Font** - Current: v3
3. **Outfit Font** - Current: latest

## Update Check Frequency
- **Automatic check**: Once per day (background)
- **Manual check**: Admin can trigger anytime
- **Alert display**: Dashboard (admin only)

## Update Process
1. System checks GitHub releases/font repos
2. Compares current vs latest versions
3. Shows alert if updates available
4. Admin reviews changelog
5. Admin decides: Update now or Dismiss
6. If update: Download → Test → Deploy

## Safety Guidelines
- ✅ Never auto-update
- ✅ Show breaking changes warning
- ✅ Provide changelog links
- ✅ Admin approval required
- ✅ Test before production

## Implementation
- Backend: `aos/core/monitoring/dependency_checker.py`
- Frontend: Dashboard alert widget
- Storage: Track dismissed alerts (don't re-show)
- Frequency: Daily check (configurable)

## FAANG Compliance
This follows industry best practices:
- GitHub Dependabot
- npm outdated warnings
- VS Code extension updates
- Chrome update notifications
