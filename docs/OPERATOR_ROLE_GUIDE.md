# OPERATOR Role - Quick Reference Guide

**Role Level**: 2 (Community-scoped CRUD access)  
**Real-world examples**: Church secretary, field agent, community organizer  
**Database role name**: `operator`

## ✅ What OPERATOR CAN Do

### Community Management (Own Community Only)
- ✅ **View community dashboard** - See stats, metrics, member count
- ✅ **Send broadcasts** - Create and send messages to community members
- ✅ **View broadcast history** - See past broadcasts and delivery status

### Member Management (Own Community Only)
- ✅ **View member list** - See all members in their community
- ✅ **Add new members** - Register new community members
- ✅ **Edit member details** - Update member information
- ✅ **Delete members** - Remove members from community
- ✅ **Export member data** - Download CSV of community members
- ✅ **Search members** - Filter and search member list

### Self-Service
- ✅ **Sign up** - Can self-register via `/signup` page
- ✅ **Login/Logout** - Standard authentication

## ❌ What OPERATOR CANNOT Do

### System Access
- ❌ **Access other communities** - Strictly isolated to assigned community
- ❌ **View global community list** - Auto-redirected to own community
- ❌ **Access system settings** - No `/security` access
- ❌ **Manage operators** - No `/operators` access
- ❌ **View system dashboard** - No kernel event monitor access

### Module Access
- ❌ **Agri-Pulse** - No `/agri` access
- ❌ **Fleet Link** - No `/transport` access
- ❌ **Mesh Network** - No `/sys/mesh` access
- ❌ **Regional Dashboard** - No `/regional` access
- ❌ **Telegram Users** - No `/dashboard/users` access

### Administrative Functions
- ❌ **Register new communities** - Only SYSTEM_ADMIN and above
- ❌ **Promote/demote users** - Cannot change operator roles
- ❌ **Access audit logs** - Admin-only feature

## 🔄 User Journey

### 1. Self-Registration
```
User visits /signup
→ Selects community from dropdown
→ Creates account (defaults to OPERATOR role)
→ Redirected to /login
```

### 2. First Login (Unassigned)
```
User logs in
→ No community_id assigned yet
→ Redirected to /unassigned page
→ Waits for SYSTEM_ADMIN to assign community
```

### 3. After Assignment
```
User logs in
→ community_id is set
→ Auto-redirected to /community/{community_id}
→ Sees community dashboard with full CRUD access
```

### 4. Daily Operations
```
OPERATOR can:
1. Send broadcast to members
2. Add new member who joined
3. Update member phone number
4. Export member list for offline use
5. View broadcast delivery status
```

## 🛡️ Security Boundaries

### Isolation Enforcement
- **Route-level**: Middleware blocks unauthorized URLs
- **Dependency-level**: `requires_community_access()` checks community_id
- **Template-level**: UI elements hidden based on role
- **Navigation**: Sidebar completely hidden (auto-redirect)

### What Happens if OPERATOR Tries to Access Forbidden Resource?

#### Scenario 1: Manual URL Entry
```
OPERATOR types: http://localhost:8000/security
→ Middleware intercepts request
→ Returns 403 Forbidden
→ Logs unauthorized access attempt
```

#### Scenario 2: Different Community Access
```
OPERATOR (assigned to GRP-123) tries: /community/GRP-456
→ requires_community_access() dependency checks
→ community_id mismatch detected
→ Returns 403 Forbidden
→ Error: "You do not have access to this community"
```

#### Scenario 3: Sidebar Navigation
```
OPERATOR logs in
→ Dashboard template checks role
→ Sidebar sections wrapped in {% if user.role in ['super_admin', 'admin'] %}
→ OPERATOR sees NO sidebar
→ Cannot click on forbidden links
```

## 📊 Comparison with Other Roles

| Feature | VIEWER | OPERATOR | COMMUNITY_ADMIN | SYSTEM_ADMIN |
|---------|--------|----------|-----------------|--------------|
| View own community | ✅ | ✅ | ✅ | ✅ |
| Send broadcasts | ❌ | ✅ | ✅ | ✅ |
| Manage members | ❌ | ✅ | ✅ | ✅ |
| Access other communities | ❌ | ❌ | ❌ | ✅ |
| Manage operators | ❌ | ❌ | ❌ | ✅ |
| System settings | ❌ | ❌ | ❌ | ✅ |
| Module access (Agri/Transport) | ❌ | ❌ | ❌ | ✅ |

## 🧪 Testing OPERATOR Access

### Test Case 1: Verify Broadcast Access
```
1. Login as OPERATOR
2. Navigate to community page
3. Verify "Send Broadcast" form is visible
4. Fill in message
5. Click "Send Broadcast"
6. Verify broadcast is queued
```

### Test Case 2: Verify Member Management
```
1. Login as OPERATOR
2. Click "Member Directory" (if visible) or navigate to /community/{id}/members
3. Click "Add Member"
4. Fill in member details
5. Save
6. Verify member appears in list
```

### Test Case 3: Verify Isolation
```
1. Login as OPERATOR (assigned to GRP-123)
2. Manually type: /community/GRP-456
3. Verify: 403 Forbidden error
4. Manually type: /security
5. Verify: 403 Forbidden error
6. Manually type: /operators
7. Verify: 403 Forbidden error
```

### Test Case 4: Verify Sidebar Hiding
```
1. Login as OPERATOR
2. Check page source
3. Verify: No sidebar navigation elements rendered
4. Verify: Auto-redirected to community page
```

## 🔧 Troubleshooting

### OPERATOR Cannot Send Broadcast
**Symptom**: Broadcast form not visible  
**Check**:
1. Verify role in database: `SELECT role_id FROM operators WHERE username='...'`
2. Verify role name: `SELECT name FROM roles WHERE id='...'`
3. Should be `operator`, not `viewer`

### OPERATOR Sees "Unassigned" Page
**Symptom**: Redirected to /unassigned after login  
**Fix**:
1. SYSTEM_ADMIN needs to assign community_id
2. Go to `/operators`
3. Click "Manage" on the operator
4. Select community from dropdown
5. Save

### OPERATOR Can Access Other Communities
**Symptom**: Can view /community/GRP-OTHER  
**Issue**: Middleware not loaded or community_id not in JWT  
**Fix**:
1. Restart server to load middleware
2. Logout and login again to refresh JWT token
3. Verify token includes community_id

## 📝 Summary

**OPERATOR is a POWERFUL but ISOLATED role.**

They have full CRUD capabilities within their assigned community, making them effective field agents who can:
- Communicate with members (broadcasts)
- Manage membership (add/edit/delete)
- Export data for offline use

But they are strictly confined to their community and cannot access system-level features or other communities.

This design follows the **Principle of Least Privilege** while still enabling field operations.
