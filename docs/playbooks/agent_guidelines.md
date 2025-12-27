# Agent Assistance Guidelines

**Version**: 1.0  
**Last Updated**: 2025-12-28  
**Target Audience**: Field agents, community liaisons

---

## Overview

As an A-OS agent, you are a **light-touch facilitator**, not a system operator. Your role is to help community groups onboard and troubleshoot basic issues, while escalating complex problems to operators.

**Core Principle**: Empower groups to self-serve. Assist, don't operate.

---

## Your Role

### What You DO

✅ **Onboarding Assistance**
- Help groups register via web dashboard
- Explain system features and benefits
- Add initial members on behalf of groups (if requested)

✅ **Basic Troubleshooting**
- Help groups log in to dashboard
- Verify phone number formats
- Test message delivery

✅ **Training and Education**
- Show groups how to publish announcements
- Explain best practices (frequency, content, timing)
- Demonstrate channel selection

✅ **Feedback Collection**
- Gather user feedback and suggestions
- Report common issues to operators
- Track adoption metrics in your area

### What You DON'T DO

❌ **System Administration**
- Don't create operator accounts
- Don't modify system settings
- Don't access database directly

❌ **Content Moderation**
- Don't approve/reject announcements
- Don't enforce spam policies (operators do this)
- Don't remove groups (escalate to operators)

❌ **Technical Support**
- Don't debug code or fix bugs
- Don't restart servers or services
- Don't modify infrastructure

---

## Onboarding Process

### Step 1: Initial Contact

1. **Identify Potential Groups**
   - Churches, mosques, SACCOs, youth groups, community committees
   - Focus on trusted, established organizations
   - Prioritize groups with 20+ members

2. **Explain the System**
   - "A-OS helps you send announcements to your members via SMS, USSD, or Telegram"
   - "No cost for members to receive messages"
   - "You control what gets sent and when"

3. **Assess Readiness**
   - Do they have a member list?
   - Do they have internet access for initial setup?
   - Do they have a designated admin?

### Step 2: Registration

1. **Collect Information**
   - Group name, location, type
   - Admin name and phone number
   - Preferred channels (SMS, USSD, Telegram)
   - Initial member list (optional)

2. **Register via Dashboard** (if you have agent access)
   - Login to dashboard with your agent credentials
   - Go to "Community" → "Register New Group"
   - Fill in group details
   - Submit for operator approval

3. **Alternative: Contact Operator**
   - If you don't have dashboard access, send details to operator via SMS/email
   - Operator will register and notify you

### Step 3: Add Members

1. **Get Member List**
   - Ask for phone numbers in correct format (254XXXXXXXXX)
   - Ask for preferred channel per member (SMS, Telegram, etc.)

2. **Add via Dashboard**
   - Go to group's member section
   - Add members one by one or via bulk upload (if available)

3. **Verify Addition**
   - Check member count matches list
   - Send test announcement to verify delivery

### Step 4: First Announcement

1. **Guide Admin Through Process**
   - Show how to log in to dashboard
   - Walk through announcement creation
   - Explain urgency levels and target audience

2. **Send Test Message**
   - Have admin send test to their own number first
   - Verify delivery and format
   - Adjust if needed

3. **Handoff**
   - Ensure admin can publish independently
   - Provide contact info for future support
   - Schedule follow-up check-in (1 week later)

---

## Troubleshooting Guide

### Issue: Group Can't Log In

**Diagnosis**:
- Verify username/password correct
- Check if group is approved (status = "Active")
- Verify internet connection

**Solution**:
1. Reset password via dashboard (if you have access)
2. Contact operator to verify group status
3. Help group access dashboard from different device/location

**Escalate If**: Password reset doesn't work, group status unclear

---

### Issue: Messages Not Delivering

**Diagnosis**:
- Check if members added to group
- Verify phone numbers in correct format
- Check channel configuration (e.g., Telegram bot running)

**Solution**:
1. Verify member count > 0 in dashboard
2. Test with your own number
3. Check phone number format (254XXXXXXXXX, no spaces/+)
4. Verify channel is configured (ask operator)

**Escalate If**: Phone numbers correct but still not delivering

---

### Issue: "Rate Limit Exceeded" Error

**Diagnosis**:
- Group sent too many announcements (>5 per day)

**Solution**:
1. Explain rate limiting policy to admin
2. Advise to wait 24 hours before next announcement
3. Suggest batching multiple updates into one message

**Escalate If**: Group has legitimate need for higher limit (e.g., emergency alerts)

---

### Issue: Members Complaining About Spam

**Diagnosis**:
- Group sending too frequently
- Content not relevant to all members

**Solution**:
1. Review announcement history with admin
2. Suggest reducing frequency to 1-3 per week
3. Recommend using "Members" target instead of "Public"
4. Advise sending during business hours only

**Escalate If**: Complaints continue despite adjustments

---

## Best Practices

### Communication

- ✅ **Be Patient**: Many admins are not tech-savvy
- ✅ **Use Simple Language**: Avoid technical jargon
- ✅ **Show, Don't Tell**: Demonstrate on their device when possible
- ✅ **Follow Up**: Check in 1 week after onboarding

### Documentation

- ✅ **Track Onboardings**: Keep list of groups you've helped
- ✅ **Note Issues**: Document common problems for reporting
- ✅ **Record Feedback**: Share user suggestions with operators

### Boundaries

- ✅ **Know Your Limits**: Escalate when unsure
- ✅ **Don't Overpromise**: Be honest about what system can/can't do
- ✅ **Respect Privacy**: Don't share group data with others

---

## Escalation Path

### When to Escalate

Escalate to operators when:
- ❌ Technical issue you can't solve (e.g., server down, bug)
- ❌ Policy question (e.g., spam enforcement, rate limit increase)
- ❌ Security concern (e.g., suspected abuse, unauthorized access)
- ❌ Feature request (e.g., new channel, bulk upload)

### How to Escalate

1. **Gather Information**
   - Group name and ID
   - Issue description
   - Steps already taken
   - Error messages (if any)

2. **Contact Operator**
   - Email: operator@aos.local (or your deployment email)
   - SMS: Operator phone number
   - Telegram: Operator support group

3. **Provide Context**
   - "Group: St. Mary's Church (GRP-ABC123)"
   - "Issue: Messages not delivering to Telegram users"
   - "Tried: Verified phone numbers, tested with my number, still failing"
   - "Error: None visible in dashboard"

4. **Follow Up**
   - Check back with operator within 24 hours
   - Update group on status
   - Close loop once resolved

---

## Reporting

### Weekly Report (Submit to Operator)

**Template**:
```
Week of: [Date]
Agent: [Your Name]

Onboardings:
- [Group Name 1] - [Location] - [# Members] - [Status: Complete/Pending]
- [Group Name 2] - [Location] - [# Members] - [Status: Complete/Pending]

Issues Resolved:
- [Issue 1] - [Group Name] - [Resolution]
- [Issue 2] - [Group Name] - [Resolution]

Issues Escalated:
- [Issue 1] - [Group Name] - [Status: Pending/Resolved]

Feedback:
- [User feedback or suggestions]

Metrics:
- Total groups assisted: [#]
- Total members added: [#]
- Total announcements sent: [#]
```

---

## Compensation and Incentives

(To be defined by deployment operator)

Typical models:
- **Per Onboarding**: Fixed fee per group successfully onboarded
- **Monthly Retainer**: Fixed monthly payment for ongoing support
- **Performance Bonus**: Bonus for high satisfaction ratings

---

## Training and Support

### Initial Training

- 1-day workshop covering:
  - System overview and features
  - Onboarding process walkthrough
  - Troubleshooting common issues
  - Escalation procedures

### Ongoing Support

- **Monthly Check-ins**: Group call with all agents and operators
- **Telegram Group**: Agent support group for quick questions
- **Knowledge Base**: Access to all playbooks and guides

---

## Do's and Don'ts

### DO

✅ Help groups understand the system  
✅ Test features yourself before explaining to others  
✅ Document issues and feedback  
✅ Escalate when unsure  
✅ Follow up with groups after onboarding  
✅ Respect user privacy and data  

### DON'T

❌ Make promises about features not yet available  
❌ Access groups' data without permission  
❌ Modify system settings or configuration  
❌ Share operator credentials with anyone  
❌ Charge groups for onboarding (unless authorized)  
❌ Ignore escalated issues  

---

## Contact Information

**Your Operator**: [Name, Phone, Email]  
**Technical Support**: [Email/Telegram]  
**Emergency Contact**: [Phone for critical issues]

---

**Version History**:
- v1.0 (2025-12-28): Initial release
