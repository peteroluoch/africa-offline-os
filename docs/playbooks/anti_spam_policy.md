# Anti-Spam and Anti-Misuse Policy

**Version**: 1.0  
**Last Updated**: 2025-12-28  
**Target Audience**: Operators, community moderators, group admins

---

## Overview

This policy defines what constitutes spam and misuse in the A-OS Community Module, and outlines enforcement mechanisms to maintain system integrity and user trust.

**Core Principle**: Trust-based system with clear boundaries. Light enforcement, heavy consequences for violations.

---

## Definitions

### Spam

**Spam** is defined as:
- ✅ Sending announcements **more than 5 times per day** without legitimate reason
- ✅ Sending **irrelevant content** to members (e.g., commercial ads in church group)
- ✅ Sending **duplicate messages** within short time periods (<1 hour)
- ✅ Sending messages **late at night** (10 PM - 7 AM) without urgency
- ✅ **Unsolicited commercial messages** (unless group is explicitly commercial)

### Misuse

**Misuse** is defined as:
- ✅ **Impersonation**: Registering as a group you don't represent
- ✅ **Harassment**: Sending threatening, abusive, or hateful messages
- ✅ **Fraud**: Using system for scams or fraudulent activities
- ✅ **Political campaigning**: Using system for political purposes (unless group is political)
- ✅ **Unauthorized access**: Accessing another group's account or data

---

## Rate Limiting

### Default Limits

- **Announcements**: 5 per day per group
- **Member additions**: 100 per day per group
- **Member removals**: 50 per day per group

### Exceptions

Rate limits may be increased for:
- **Emergency alerts**: Natural disasters, security threats
- **Time-sensitive events**: Elections, urgent meetings
- **Large organizations**: Groups with 500+ members

**Process**: Contact operator with justification, operator approves/rejects

---

## Content Guidelines

### Acceptable Content

✅ **Community announcements**: Events, meetings, services  
✅ **Educational content**: Health tips, safety information  
✅ **Emergency alerts**: Security threats, natural disasters  
✅ **Organizational updates**: Leadership changes, policy updates  

### Prohibited Content

❌ **Hate speech**: Content targeting race, religion, gender, etc.  
❌ **Violence**: Threats, incitement to violence  
❌ **Pornography**: Explicit sexual content  
❌ **Fraud**: Scams, pyramid schemes, fake products  
❌ **Spam**: Unsolicited commercial messages  
❌ **Misinformation**: Deliberately false health/safety information  

---

## Reporting Mechanism

### How Users Report Spam

1. **Via Telegram**: Reply to bot with `/report [group_name] [reason]`
2. **Via SMS**: Send "REPORT [group_name] [reason]" to operator number
3. **Via Web**: Fill report form on dashboard (if logged in)
4. **Via Agent**: Contact local agent who escalates to operator

### What Happens After Report

1. **Operator Review**: Operator reviews report within 24-48 hours
2. **Investigation**: Operator checks announcement history, delivery logs
3. **Decision**: Operator decides: dismiss, warn, suspend, or ban
4. **Notification**: Group admin notified of decision and reason

---

## Enforcement Actions

### Warning (First Offense)

**Triggers**:
- Exceeding rate limit by 1-2 announcements
- Sending late-night messages without urgency
- Minor content guideline violations

**Actions**:
- Email/SMS warning to group admin
- Explanation of violation
- Reminder of policies
- No service interruption

**Duration**: Warning on record for 30 days

---

### Suspension (Second Offense or Moderate Violation)

**Triggers**:
- Exceeding rate limit by 3+ announcements
- Repeated late-night messages
- Moderate content violations (e.g., commercial spam)
- Ignoring previous warning

**Actions**:
- Account suspended for 7 days
- Cannot publish announcements during suspension
- Email/SMS notification with reason
- Opportunity to appeal

**Duration**: 7 days, then automatic reinstatement (if no further violations)

---

### Ban (Third Offense or Severe Violation)

**Triggers**:
- Repeated violations after suspension
- Severe content violations (hate speech, fraud, harassment)
- Impersonation or unauthorized access
- Deliberate system abuse

**Actions**:
- Account permanently banned
- All announcements deleted
- Members notified of ban
- No reinstatement (unless successful appeal)

**Duration**: Permanent

---

## Appeals Process

### How to Appeal

1. **Submit Appeal**: Email operator with:
   - Group name and ID
   - Enforcement action being appealed
   - Reason for appeal
   - Evidence (if any)

2. **Operator Review**: Operator reviews appeal within 7 days

3. **Decision**: Operator decides:
   - **Uphold**: Enforcement action stands
   - **Reduce**: Reduce penalty (e.g., ban → suspension)
   - **Overturn**: Remove enforcement action entirely

4. **Notification**: Group admin notified of decision

### Appeal Criteria

Appeals are more likely to succeed if:
- ✅ First-time offense
- ✅ Violation was unintentional
- ✅ Group has good track record
- ✅ Evidence supports appeal

Appeals are unlikely to succeed if:
- ❌ Repeated violations
- ❌ Severe content violations
- ❌ No evidence provided
- ❌ Deliberate abuse

---

## Technical Controls

### Automated Rate Limiting

- System automatically blocks announcements exceeding 5/day
- Error message: "Rate limit exceeded. Try again tomorrow."
- No manual intervention required

### Manual Review Queue

- All groups in pilot phase subject to manual approval
- Operator reviews each announcement before delivery
- Reduces spam risk during early adoption

### Content Filtering (Future)

- Keyword-based filters for prohibited content
- Automatic flagging for operator review
- Not implemented in v1.0

---

## Monitoring and Metrics

### Operator Dashboard

Operators can monitor:
- **Announcement frequency**: Groups sending >3/day flagged
- **User reports**: All reports visible in dashboard
- **Delivery failures**: High failure rates may indicate spam
- **Member churn**: High removal rates may indicate spam

### Monthly Reports

Operators generate monthly reports showing:
- Total announcements sent
- Spam reports received
- Enforcement actions taken
- Appeals processed

---

## Group Admin Responsibilities

As a group admin, you are responsible for:

✅ **Compliance**: Follow rate limits and content guidelines  
✅ **Relevance**: Only send content relevant to your members  
✅ **Timing**: Respect members' time (avoid late-night messages)  
✅ **Accuracy**: Verify information before sending  
✅ **Respect**: Treat members with respect and dignity  

**Failure to meet these responsibilities may result in enforcement action.**

---

## Examples

### Example 1: Acceptable Use

**Scenario**: Church sends 2 announcements per week (Sunday service reminder, midweek Bible study)

**Assessment**: ✅ Acceptable
- Within rate limit (5/day)
- Relevant to members
- Appropriate timing

---

### Example 2: Spam

**Scenario**: SACCO sends 10 announcements in one day promoting loan products

**Assessment**: ❌ Spam
- Exceeds rate limit (5/day)
- Commercial content
- Likely irrelevant to some members

**Action**: Warning (first offense) or Suspension (repeat offense)

---

### Example 3: Misuse

**Scenario**: Group sends message: "Vote for [Candidate] in upcoming election"

**Assessment**: ❌ Misuse (political campaigning)
- Violates content guidelines
- Not appropriate for community group (unless explicitly political)

**Action**: Suspension or Ban (depending on severity)

---

### Example 4: Emergency Exception

**Scenario**: Church sends 8 announcements in one day due to security threat in neighborhood

**Assessment**: ✅ Acceptable (emergency exception)
- Legitimate emergency
- Time-sensitive information
- Benefits members

**Action**: None (may require post-hoc approval from operator)

---

## Policy Updates

This policy may be updated based on:
- User feedback
- Regulatory changes
- System evolution
- Lessons learned from enforcement

**Process**: Operator proposes update → Review with stakeholders → Announce changes → 30-day notice before enforcement

---

## Contact

**Report Spam**: [Email/SMS/Telegram]  
**Appeal Enforcement**: [Email]  
**Policy Questions**: [Email]

---

**Version History**:
- v1.0 (2025-12-28): Initial release
