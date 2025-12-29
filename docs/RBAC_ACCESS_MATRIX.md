# RBAC Access Control Matrix
**Version**: 1.0  
**Last Updated**: 2025-12-30  
**Status**: AUTHORITATIVE SOURCE OF TRUTH

## Role Hierarchy

```
Level 5: SUPER_ADMIN (super_admin in DB)
Level 4: SYSTEM_ADMIN (admin in DB)
Level 3: COMMUNITY_ADMIN (community_admin in DB)
Level 2: OPERATOR (operator in DB)
Level 1: VIEWER (viewer in DB)
```

## Access Matrix

### 1. SUPER_ADMIN (Level 5)
**Scope**: Global system access

| Resource | Access | Notes |
|----------|--------|-------|
| Dashboard (/) | ✅ READ | Kernel event monitor |
| Security Policy (/security) | ✅ READ | View security config |
| Operators (/operators) | ✅ READ/WRITE | Manage all operators |
| Agri-Pulse (/agri) | ✅ READ/WRITE | Full agricultural module access |
| Fleet Link (/transport) | ✅ READ/WRITE | Full transport module access |
| Community-Pulse (/) | ✅ READ/WRITE | View all communities |
| Community Detail | ✅ READ/WRITE | Access any community |
| Community Registration | ✅ CREATE | Register new communities |
| Member Management | ✅ READ/WRITE | Manage members in any community |
| Broadcast | ✅ SEND | Send to any community |
| Mesh Network (/sys/mesh) | ✅ READ/WRITE | Manage mesh peers |
| UI Gallery (/sys/gallery) | ✅ READ | View design system |
| Telegram Users (/dashboard/users) | ✅ READ/WRITE | Manage Telegram users |
| Regional Dashboard (/regional) | ✅ READ | View regional stats |

### 2. SYSTEM_ADMIN (Level 4)
**Scope**: Regional/organizational management

| Resource | Access | Notes |
|----------|--------|-------|
| Dashboard (/) | ✅ READ | Kernel event monitor |
| Security Policy (/security) | ✅ READ | View security config |
| Operators (/operators) | ✅ READ/WRITE | Manage operators (except SUPER_ADMIN) |
| Agri-Pulse (/agri) | ✅ READ/WRITE | Full agricultural module access |
| Fleet Link (/transport) | ✅ READ/WRITE | Full transport module access |
| Community-Pulse (/) | ✅ READ/WRITE | View all communities |
| Community Detail | ✅ READ/WRITE | Access any community |
| Community Registration | ✅ CREATE | Register new communities |
| Member Management | ✅ READ/WRITE | Manage members in any community |
| Broadcast | ✅ SEND | Send to any community |
| Mesh Network (/sys/mesh) | ❌ DENY | System-level only |
| UI Gallery (/sys/gallery) | ✅ READ | View design system |
| Telegram Users (/dashboard/users) | ✅ READ/WRITE | Manage Telegram users |
| Regional Dashboard (/regional) | ✅ READ | View regional stats |

### 3. COMMUNITY_ADMIN (Level 3)
**Scope**: Single community management (isolated)

| Resource | Access | Notes |
|----------|--------|-------|
| Dashboard (/) | 🔀 REDIRECT | Auto-redirect to assigned community |
| Security Policy (/security) | ❌ DENY | Admin-only |
| Operators (/operators) | ❌ DENY | Admin-only |
| Agri-Pulse (/agri) | ❌ DENY | Module-specific access only |
| Fleet Link (/transport) | ❌ DENY | Module-specific access only |
| Community-Pulse (/) | 🔀 REDIRECT | Auto-redirect to assigned community |
| Community Detail (own) | ✅ READ/WRITE | Only their assigned community |
| Community Detail (other) | ❌ DENY | Isolated to own community |
| Community Registration | ❌ DENY | Admin-only |
| Member Management (own) | ✅ READ/WRITE | Only their community members |
| Member Management (other) | ❌ DENY | Isolated to own community |
| Broadcast (own) | ✅ SEND | Only to their community |
| Broadcast (other) | ❌ DENY | Isolated to own community |
| Mesh Network (/sys/mesh) | ❌ DENY | System-level only |
| UI Gallery (/sys/gallery) | ❌ DENY | Admin-only |
| Telegram Users (/dashboard/users) | ❌ DENY | Admin-only |
| Regional Dashboard (/regional) | ❌ DENY | Admin-only |

### 4. OPERATOR (Level 2)
**Scope**: Read-only access to assigned community

| Resource | Access | Notes |
|----------|--------|-------|
| Dashboard (/) | 🔀 REDIRECT | Auto-redirect to assigned community |
| Security Policy (/security) | ❌ DENY | Admin-only |
| Operators (/operators) | ❌ DENY | Admin-only |
| Agri-Pulse (/agri) | ❌ DENY | No module access |
| Fleet Link (/transport) | ❌ DENY | No module access |
| Community-Pulse (/) | 🔀 REDIRECT | Auto-redirect to assigned community |
| Community Detail (own) | ✅ READ | View only their assigned community |
| Community Detail (other) | ❌ DENY | Isolated to own community |
| Community Registration | ❌ DENY | Admin-only |
| Member Management (own) | ✅ READ | View only their community members |
| Member Management (other) | ❌ DENY | Isolated to own community |
| Broadcast (own) | ❌ DENY | Read-only role |
| Broadcast (other) | ❌ DENY | Read-only role |
| Mesh Network (/sys/mesh) | ❌ DENY | System-level only |
| UI Gallery (/sys/gallery) | ❌ DENY | Admin-only |
| Telegram Users (/dashboard/users) | ❌ DENY | Admin-only |
| Regional Dashboard (/regional) | ❌ DENY | Admin-only |

### 5. VIEWER (Level 1)
**Scope**: Minimal read-only access

| Resource | Access | Notes |
|----------|--------|-------|
| Dashboard (/) | ✅ READ | View kernel events only |
| All other routes | ❌ DENY | Minimal access role |

## Navigation Visibility Rules

### Sidebar Menu Items by Role

#### SUPER_ADMIN & SYSTEM_ADMIN
- ✅ Monitoring → Real-time Stream
- ✅ Security & Access → Operators
- ✅ Security & Access → Security Policy
- ✅ Domain Modules → Agri-Pulse
- ✅ Domain Modules → Fleet Link
- ✅ Domain Modules → Community-Pulse
- ✅ Administration → Telegram Users
- ✅ Administration → Regional Dashboard
- ✅ Administration → Mesh Nodes
- ✅ Administration → UI Gallery

#### COMMUNITY_ADMIN
- ❌ All sidebar items hidden (auto-redirected to community page)

#### OPERATOR
- ❌ All sidebar items hidden (auto-redirected to community page)

#### VIEWER
- ✅ Monitoring → Real-time Stream
- ❌ All other items hidden

## Enforcement Layers

### Layer 1: Route Guards (app.py)
- Middleware checks role before routing
- Returns 403 for unauthorized access
- Redirects isolated roles to their scope

### Layer 2: Dependency Injection (auth.py)
- `requires_role(minimum_role)` - Hierarchical check
- `requires_community_access()` - Community isolation check

### Layer 3: Template Guards (Jinja2)
- `{% if user.role in ['super_admin', 'admin'] %}`
- Hide UI elements based on role

### Layer 4: Navigation Filtering (dashboard.html)
- Sidebar dynamically rendered based on role
- Links only shown if user has access

## Special Cases

### Unassigned Users
- COMMUNITY_ADMIN or OPERATOR without `community_id`
- Redirected to `/unassigned` page
- Cannot access any community resources

### Self-Service Signup
- New users default to OPERATOR role
- Must be assigned to community by SYSTEM_ADMIN
- Cannot access system until assigned

## Audit Requirements

All access denials must be logged with:
- Timestamp
- Username
- Attempted resource
- User role
- Denial reason

## Testing Checklist

- [ ] SUPER_ADMIN can access all routes
- [ ] SYSTEM_ADMIN blocked from /sys/mesh
- [ ] COMMUNITY_ADMIN isolated to own community
- [ ] COMMUNITY_ADMIN cannot access /security
- [ ] OPERATOR has read-only access to own community
- [ ] OPERATOR cannot send broadcasts
- [ ] OPERATOR cannot access /operators
- [ ] Direct URL access blocked for unauthorized roles
- [ ] Sidebar filtered correctly for each role
- [ ] Unassigned users see pending page
