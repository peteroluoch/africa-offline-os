# Community Group Onboarding Playbook

**Version**: 1.0  
**Last Updated**: 2025-12-28  
**Target Audience**: Church/mosque administrators, SACCO leaders, community organizers

---

## Overview

This playbook guides community groups through the onboarding process for the Africa Offline OS (A-OS) Community Module. The system enables trusted local organizations to publish events and announcements to their members via USSD, SMS, Telegram, and WhatsApp.

**Core Principle**: Groups hold accounts, not individuals. Zero individual authentication required for members.

---

## Prerequisites

Before starting, ensure you have:

- ✅ **Organization Details**: Official name, location, type (church, mosque, SACCO, etc.)
- ✅ **Admin Contact**: Phone number and name of primary administrator
- ✅ **Member List**: Initial list of member phone numbers (optional, can add later)
- ✅ **Channel Preference**: Which channels to use (USSD, SMS, Telegram, WhatsApp)
- ✅ **Internet Access**: For initial web dashboard registration (one-time)

---

## Step 1: Register Your Group

### Via Web Dashboard (Recommended)

1. **Access the Dashboard**
   - Open browser and navigate to: `http://localhost:8000/community` (or your deployment URL)
   - If not logged in, you'll be redirected to login page

2. **Login as Operator** (First-time setup requires operator assistance)
   - Contact your local A-OS operator for credentials
   - Operators will create your group account

3. **Fill Registration Form**
   - **Group Name**: Official name (e.g., "St. Mary's Catholic Church")
   - **Description**: Brief description of your organization
   - **Group Type**: Select from dropdown (church, mosque, sacco, youth_group, etc.)
   - **Tags**: Add relevant tags (e.g., "catholic", "westlands", "sunday_service")
   - **Location**: Your area/neighborhood (e.g., "Westlands, Nairobi")
   - **Preferred Channels**: Select USSD, SMS, Telegram, or WhatsApp

4. **Submit and Wait for Approval**
   - Operator will review and approve within 24-48 hours
   - You'll receive confirmation via SMS or phone call

### Via Agent Assistance (Alternative)

If you don't have internet access:
1. Contact your local A-OS agent
2. Provide organization details verbally
3. Agent will register on your behalf
4. You'll receive confirmation via SMS

---

## Step 2: Add Members to Your Group

Once your group is approved, add members to receive announcements.

### Via Web Dashboard

1. **Navigate to Members Section**
   - Login to dashboard
   - Go to "Community" → "Your Group" → "Members"

2. **Add Individual Members**
   - Click "Add Member"
   - Enter phone number (format: 254712345678)
   - Select channel (SMS, Telegram, USSD, WhatsApp)
   - Click "Save"

3. **Bulk Upload** (Coming Soon)
   - Upload CSV file with columns: `phone_number`, `channel`
   - System will validate and add all members

### Via Agent Assistance

1. Provide member list to your agent (phone numbers + preferred channel)
2. Agent will add members on your behalf
3. Confirm member count via SMS

---

## Step 3: Publish Your First Announcement

### Via Web Dashboard

1. **Navigate to Announcements**
   - Login to dashboard
   - Go to "Community" → "Announcements" → "Create New"

2. **Fill Announcement Form**
   - **Message**: Your announcement text (keep under 160 characters for SMS)
   - **Urgency**: Normal or Urgent
   - **Target Audience**: Public (anyone can see) or Members (only your members)
   - **Expires At**: Optional expiry date/time

3. **Preview and Publish**
   - Review your message
   - Click "Publish"
   - Announcement is saved but NOT yet delivered

4. **Deliver to Members**
   - Go to "Announcements" → "Pending Delivery"
   - Click "Deliver" next to your announcement
   - System will send to all active members via their preferred channels

### Via Telegram Bot (Alternative)

If your group uses Telegram:
1. Add the A-OS bot to your admin Telegram account
2. Use `/announce` command
3. Follow prompts to compose and send

---

## Step 4: Manage Your Group

### View Group Statistics

- **Dashboard**: See member count, announcement count, delivery stats
- **Activity Log**: Track when announcements were sent and delivered

### Update Group Information

- **Edit Details**: Change name, description, tags, location
- **Change Admin**: Transfer admin rights to another member (requires operator approval)

### Remove Members

- **Individual Removal**: Go to "Members" → Select member → "Remove"
- **Bulk Removal**: Upload CSV with phone numbers to remove

---

## Best Practices

### Announcement Frequency

- ✅ **Recommended**: 1-3 announcements per week
- ⚠️ **Caution**: More than 5 per week may be considered spam
- ❌ **Avoid**: Daily announcements (unless urgent/time-sensitive)

### Message Content

- ✅ **Clear and Concise**: Keep messages under 160 characters for SMS compatibility
- ✅ **Relevant**: Only send information relevant to your community
- ✅ **Timely**: Send announcements at appropriate times (avoid late night)
- ❌ **Avoid**: Political content, commercial advertising, personal messages

### Urgency Levels

- **Normal**: Regular updates, event reminders, general announcements
- **Urgent**: Time-sensitive information, emergency alerts, critical updates

### Channel Selection

- **SMS**: Widest reach, works on all phones, costs per message
- **USSD**: Free, works on all phones, requires active session
- **Telegram**: Rich features, free, requires smartphone + internet
- **WhatsApp**: Popular, free, requires smartphone + internet

**Recommendation**: Start with one channel, expand based on member feedback.

---

## Common Issues and Solutions

### Issue: "Messages not delivering"

**Possible Causes**:
- No members added to group
- Members' phone numbers incorrect
- Channel not configured (e.g., Telegram bot not set up)

**Solutions**:
1. Check member list: Go to "Members" and verify count > 0
2. Verify phone numbers: Ensure format is correct (254XXXXXXXXX)
3. Test with your own number first
4. Contact operator if issue persists

---

### Issue: "Can't publish announcement"

**Possible Causes**:
- Not logged in as admin
- Group not approved yet
- Rate limit exceeded (too many announcements)

**Solutions**:
1. Verify you're logged in with correct credentials
2. Check group status: Should show "Active" in dashboard
3. Wait 24 hours if you've sent 5+ announcements today
4. Contact operator for rate limit increase

---

### Issue: "Members complaining about spam"

**Possible Causes**:
- Sending too frequently
- Content not relevant to all members
- Sending at inappropriate times

**Solutions**:
1. Reduce frequency to 1-3 per week
2. Use "Members" target audience instead of "Public"
3. Send during business hours (9 AM - 6 PM)
4. Ask for member feedback and adjust

---

## Getting Help

### Self-Service

1. **Troubleshooting Guide**: See `docs/playbooks/troubleshooting.md`
2. **FAQ**: Check dashboard "Help" section
3. **Telegram Support**: Join A-OS Community Support group

### Agent Assistance

1. Contact your local A-OS agent
2. Provide: Group name, issue description, error message (if any)
3. Agent will troubleshoot or escalate to operator

### Operator Support

1. Email: support@aos.local (or your deployment email)
2. Phone: Contact number provided during onboarding
3. Response time: 24-48 hours for non-urgent issues

---

## Next Steps

After successful onboarding:

1. ✅ **Test Delivery**: Send a test announcement to yourself first
2. ✅ **Gather Feedback**: Ask members if they received and understood the message
3. ✅ **Establish Rhythm**: Set a regular schedule (e.g., weekly updates)
4. ✅ **Train Backup Admin**: Ensure someone else can manage if you're unavailable
5. ✅ **Monitor Engagement**: Track delivery stats and adjust strategy

---

## Appendix: Phone Number Formats

### Correct Formats
- ✅ `254712345678` (Kenya, with country code)
- ✅ `254722345678` (Kenya, Safaricom)
- ✅ `254733345678` (Kenya, Airtel)

### Incorrect Formats
- ❌ `0712345678` (missing country code)
- ❌ `+254712345678` (remove + symbol)
- ❌ `254 712 345 678` (remove spaces)

---

## Appendix: Sample Announcements

### Church Service Reminder
```
St. Mary's: Sunday service at 9 AM. Theme: "Faith in Action". All welcome!
```

### SACCO Meeting Notice
```
Westlands SACCO: Monthly meeting this Saturday 2 PM at Community Hall. Agenda: Loan approvals.
```

### Youth Group Event
```
Youth Group: Football tournament this Sunday 3 PM at Uhuru Park. Register by Friday!
```

### Urgent Alert
```
URGENT: Church compound closed today due to maintenance. Service moved to Parish Hall.
```

---

**Questions?** Contact your local A-OS agent or operator.

**Version History**:
- v1.0 (2025-12-28): Initial release
