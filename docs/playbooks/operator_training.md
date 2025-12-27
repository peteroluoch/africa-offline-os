# Operator Training Guide

**Version**: 1.0  
**Last Updated**: 2025-12-28  
**Target Audience**: System operators, administrators

---

## Overview

This guide provides comprehensive training for A-OS operators responsible for managing the Community Module deployment. Operators are the backbone of the system, handling user management, group approvals, monitoring, and incident response.

**Core Responsibility**: Ensure system reliability, security, and user satisfaction.

---

## System Architecture Overview

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                     A-OS Community Module                    │
├─────────────────────────────────────────────────────────────┤
│  Web Dashboard  │  Telegram Bot  │  USSD Gateway  │  SMS   │
├─────────────────────────────────────────────────────────────┤
│              Community Module (Kernel)                       │
│  - Group Management                                          │
│  - Member Management (Security-Critical)                     │
│  - Announcement Delivery                                     │
│  - Message Isolation Enforcement                             │
├─────────────────────────────────────────────────────────────┤
│                    SQLite Database                           │
│  - community_groups                                          │
│  - community_members                                         │
│  - community_announcements                                   │
└─────────────────────────────────────────────────────────────┘
```

### Key Security Invariants

1. **Mandatory Community Scoping**: All messages require valid `community_id`
2. **Admin→Community Binding**: Admins can only message their own community
3. **Recipient Resolution Firewall**: `WHERE community_id = ?` enforced at kernel
4. **Fail Closed**: Invalid requests rejected (no partial send)
5. **Adapter Ignorance**: No routing logic in adapters

---

## Dashboard Walkthrough

### Logging In

1. Navigate to: `http://localhost:8000/auth/login` (or your deployment URL)
2. Enter operator credentials
3. You'll be redirected to dashboard

### Dashboard Sections

#### 1. Overview
- System health metrics
- Active groups count
- Total members count
- Announcements sent (last 30 days)

#### 2. Community Management
- **Groups**: View, approve, suspend, or ban groups
- **Members**: View member lists per group
- **Announcements**: View announcement history

#### 3. User Management
- **Operators**: Create, edit, or delete operator accounts
- **Roles**: Assign roles (ADMIN, OPERATOR, VIEWER)

#### 4. Monitoring
- **System Health**: CPU, memory, disk usage
- **Delivery Stats**: Success/failure rates per channel
- **Error Logs**: Recent errors and warnings

---

## User Management

### Creating Operator Accounts

1. **Navigate to**: Dashboard → Users → Create Operator
2. **Fill Form**:
   - Username (unique)
   - Password (strong, 12+ characters)
   - Role (ADMIN, OPERATOR, VIEWER)
3. **Click**: "Create"
4. **Share Credentials**: Securely share with new operator

### Assigning Roles

- **ADMIN**: Full access (create operators, modify system settings)
- **OPERATOR**: Manage groups, view logs, handle reports
- **VIEWER**: Read-only access (monitoring, reports)

### Resetting Passwords

1. **Navigate to**: Dashboard → Users → [Username] → Reset Password
2. **Generate New Password**: System generates secure password
3. **Share**: Securely share with user

---

## Group Management

### Approving Group Registrations

1. **Navigate to**: Dashboard → Community → Pending Approvals
2. **Review Group Details**:
   - Name, location, type
   - Admin contact
   - Preferred channels
3. **Decision**:
   - **Approve**: Group can start using system
   - **Reject**: Group cannot use system (provide reason)
4. **Notify**: System sends SMS/email to admin

### Suspending Groups

**When to Suspend**:
- Spam violations (>5 announcements/day)
- Content guideline violations
- User complaints

**Process**:
1. **Navigate to**: Dashboard → Community → Groups → [Group Name]
2. **Click**: "Suspend"
3. **Provide Reason**: Explain violation
4. **Duration**: 7 days (default) or custom
5. **Notify**: System sends notification to admin

### Banning Groups

**When to Ban**:
- Severe violations (hate speech, fraud, harassment)
- Repeated violations after suspension
- Deliberate system abuse

**Process**:
1. **Navigate to**: Dashboard → Community → Groups → [Group Name]
2. **Click**: "Ban"
3. **Provide Reason**: Explain violation
4. **Confirm**: Permanent action, cannot be undone (except via appeal)
5. **Notify**: System sends notification to admin

---

## Monitoring

### System Health Checks

**Daily**:
- ✅ Check dashboard "System Health" widget
- ✅ Verify all channels operational (SMS, USSD, Telegram)
- ✅ Review error logs for critical issues

**Weekly**:
- ✅ Review delivery success rates (should be >90%)
- ✅ Check disk space (should have >20% free)
- ✅ Review user reports and complaints

**Monthly**:
- ✅ Generate usage report (groups, members, announcements)
- ✅ Review spam/abuse incidents
- ✅ Update playbooks based on learnings

### Key Metrics to Monitor

- **Delivery Success Rate**: % of announcements successfully delivered
  - Target: >90%
  - Alert if: <80%

- **System Uptime**: % of time system is operational
  - Target: >99%
  - Alert if: <95%

- **Active Groups**: Groups sending announcements in last 30 days
  - Target: >50% of registered groups
  - Alert if: <30%

- **User Reports**: Spam/abuse reports per month
  - Target: <5% of groups
  - Alert if: >10%

---

## Incident Response

### Critical Incidents

**Definition**: System down, data breach, widespread delivery failure

**Response**:
1. **Assess**: Determine scope and impact
2. **Notify**: Alert technical team immediately
3. **Communicate**: Inform affected users (if possible)
4. **Mitigate**: Take immediate action (e.g., restart service)
5. **Document**: Log incident details
6. **Post-Mortem**: Analyze root cause, prevent recurrence

### Non-Critical Incidents

**Definition**: Individual group issues, minor bugs, user complaints

**Response**:
1. **Assess**: Verify issue and impact
2. **Troubleshoot**: Use troubleshooting guide
3. **Escalate**: If unable to resolve, contact technical team
4. **Communicate**: Update user on status
5. **Document**: Log issue and resolution

---

## Backup and Recovery

### Database Backups

**Frequency**: Daily (automated)

**Location**: `backups/aos_db_YYYY-MM-DD.db`

**Retention**: 30 days

**Verification**: Weekly test restore to verify backup integrity

### Manual Backup

```bash
# Stop services
systemctl stop aos-web aos-telegram

# Backup database
cp aos.db backups/aos_db_manual_$(date +%Y%m%d_%H%M%S).db

# Restart services
systemctl start aos-web aos-telegram
```

### Recovery Procedure

**If database corrupted**:
1. Stop all services
2. Restore from latest backup
3. Verify data integrity
4. Restart services
5. Test functionality

**If system unresponsive**:
1. Check logs: `journalctl -u aos-web -n 100`
2. Restart services: `systemctl restart aos-web aos-telegram`
3. If still unresponsive, escalate to technical team

---

## Common Tasks

### Task 1: Increase Rate Limit for Group

**Scenario**: Group requests higher announcement limit for emergency

**Steps**:
1. Verify legitimacy (emergency, time-sensitive event)
2. Navigate to: Dashboard → Community → Groups → [Group Name] → Settings
3. Update "Daily Announcement Limit" (e.g., 5 → 10)
4. Set expiry date (e.g., 7 days)
5. Notify group admin

### Task 2: Handle Spam Report

**Scenario**: User reports group for spam

**Steps**:
1. Navigate to: Dashboard → Reports → [Report ID]
2. Review announcement history for group
3. Verify violation (>5/day, irrelevant content, etc.)
4. Take action: Warn, Suspend, or Ban
5. Notify reporter and group admin

### Task 3: Add Bulk Members

**Scenario**: Group wants to add 100+ members at once

**Steps**:
1. Request CSV file from group (columns: phone_number, channel)
2. Validate format (254XXXXXXXXX, no spaces)
3. Navigate to: Dashboard → Community → Groups → [Group Name] → Members → Bulk Upload
4. Upload CSV
5. System validates and adds members
6. Notify group admin of success/failures

---

## Security Best Practices

### Password Management

- ✅ Use strong passwords (12+ characters, mixed case, numbers, symbols)
- ✅ Change passwords every 90 days
- ✅ Never share passwords via email or SMS
- ✅ Use password manager

### Access Control

- ✅ Grant minimum necessary permissions
- ✅ Review operator accounts quarterly
- ✅ Revoke access immediately when operator leaves

### Data Privacy

- ✅ Never share user data with third parties
- ✅ Access user data only when necessary (troubleshooting, support)
- ✅ Log all data access for audit trail

---

## Escalation

### When to Escalate

Escalate to technical team when:
- ❌ System down or unresponsive
- ❌ Database corruption or data loss
- ❌ Security breach or unauthorized access
- ❌ Bug causing widespread issues
- ❌ Performance degradation (slow dashboard, failed deliveries)

### How to Escalate

1. **Gather Information**:
   - Issue description
   - Steps to reproduce
   - Error messages
   - Affected users/groups
   - Impact assessment

2. **Contact Technical Team**:
   - Email: tech@aos.local
   - Phone: [Emergency number]
   - Telegram: Technical support group

3. **Provide Context**:
   - "Issue: Dashboard unresponsive"
   - "Affected: All operators"
   - "Started: 2025-12-28 10:00 AM"
   - "Error: 500 Internal Server Error"
   - "Impact: Cannot approve groups or view logs"

---

## Training Checklist

Before going live, ensure you can:

- [ ] Log in to dashboard
- [ ] Create operator account
- [ ] Approve group registration
- [ ] Suspend/ban group
- [ ] View announcement history
- [ ] Handle spam report
- [ ] Check system health metrics
- [ ] Perform manual database backup
- [ ] Escalate critical incident

---

## Contact Information

**Technical Support**: [Email, Phone, Telegram]  
**Project Manager**: [Email, Phone]  
**Emergency Contact**: [Phone for critical issues]

---

**Version History**:
- v1.0 (2025-12-28): Initial release
