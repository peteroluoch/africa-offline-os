# Troubleshooting Guide

**Version**: 1.0  
**Last Updated**: 2025-12-28  
**Target Audience**: Operators, agents, advanced users

---

## Overview

This guide provides solutions to common issues encountered in the A-OS Community Module. Issues are organized by category with step-by-step troubleshooting steps.

**Troubleshooting Principle**: Check simple things first, escalate complex issues.

---

## Authentication Issues

### Issue: "I can't log in"

**Symptoms**:
- Login page shows "Incorrect username or password"
- Redirected back to login after entering credentials

**Possible Causes**:
- Wrong username or password
- Account not created yet
- Account suspended or banned
- Session expired

**Troubleshooting Steps**:
1. **Verify Credentials**: Double-check username and password (case-sensitive)
2. **Check Account Status**: Contact operator to verify account exists and is active
3. **Reset Password**: Request password reset from operator
4. **Clear Browser Cache**: Clear cookies and try again
5. **Try Different Browser**: Test with Chrome, Firefox, or Edge

**Escalate If**: Still can't log in after password reset

---

### Issue: "Session timeout" or "Logged out automatically"

**Symptoms**:
- Logged out after period of inactivity
- Have to log in again frequently

**Possible Causes**:
- Session expired (default: 24 hours)
- Browser cleared cookies
- Server restarted

**Troubleshooting Steps**:
1. **Log In Again**: This is expected behavior
2. **Check "Remember Me"**: If available, check box to stay logged in longer
3. **Don't Clear Cookies**: Avoid clearing browser cookies

**Escalate If**: Logged out within minutes (not expected)

---

## Message Delivery Issues

### Issue: "Messages not delivering"

**Symptoms**:
- Announcement published but members not receiving
- Delivery status shows "Failed" or "Pending"

**Possible Causes**:
- No members added to group
- Incorrect phone numbers
- Channel not configured (e.g., Telegram bot down)
- Network issues

**Troubleshooting Steps**:
1. **Check Member List**:
   - Dashboard → Community → Groups → [Group Name] → Members
   - Verify member count > 0

2. **Verify Phone Numbers**:
   - Check format: 254XXXXXXXXX (no spaces, no +)
   - Test with your own number first

3. **Check Channel Status**:
   - SMS: Verify SMS gateway configured
   - Telegram: Verify bot is running (`systemctl status aos-telegram`)
   - USSD: Verify USSD gateway configured

4. **Test Delivery**:
   - Send test announcement to yourself
   - Check if you receive it

5. **Check Logs**:
   - Dashboard → Monitoring → Error Logs
   - Look for delivery errors

**Escalate If**: Phone numbers correct, channel configured, still not delivering

---

### Issue: "Some members receiving, others not"

**Symptoms**:
- Partial delivery (e.g., 50 out of 100 members receive)

**Possible Causes**:
- Some phone numbers incorrect
- Some members' phones off or out of coverage
- Channel-specific issues (e.g., Telegram users blocked bot)

**Troubleshooting Steps**:
1. **Check Delivery Report**:
   - Dashboard → Community → Announcements → [Announcement] → Delivery Report
   - See which members failed

2. **Verify Failed Numbers**:
   - Check if failed numbers are in correct format
   - Test failed numbers individually

3. **Check Channel**:
   - If Telegram failures, verify users haven't blocked bot
   - If SMS failures, verify numbers are active

**Escalate If**: Consistent pattern of failures (e.g., all Telegram users failing)

---

## Group Management Issues

### Issue: "Can't publish announcement"

**Symptoms**:
- "Publish" button disabled or grayed out
- Error message when trying to publish

**Possible Causes**:
- Not logged in as admin
- Group not approved yet
- Rate limit exceeded (>5 announcements/day)
- Group suspended or banned

**Troubleshooting Steps**:
1. **Verify Login**: Ensure you're logged in with correct admin credentials
2. **Check Group Status**: Dashboard → Community → Groups → [Group Name]
   - Status should be "Active"
3. **Check Rate Limit**: See announcement history
   - If >5 today, wait until tomorrow
4. **Contact Operator**: If group suspended, request reinstatement

**Escalate If**: Group active, within rate limit, still can't publish

---

### Issue: "Group registration pending for days"

**Symptoms**:
- Submitted registration but no approval/rejection
- Status shows "Pending"

**Possible Causes**:
- Operator hasn't reviewed yet
- Registration incomplete or missing information

**Troubleshooting Steps**:
1. **Wait 24-48 Hours**: Normal approval time
2. **Contact Operator**: If >48 hours, follow up via email/SMS
3. **Verify Information**: Ensure all required fields filled correctly

**Escalate If**: >7 days with no response

---

## Member Management Issues

### Issue: "Can't add members"

**Symptoms**:
- Error when trying to add member
- Member added but not showing in list

**Possible Causes**:
- Phone number format incorrect
- Member already exists
- Rate limit exceeded (>100 members/day)

**Troubleshooting Steps**:
1. **Check Phone Format**: Must be 254XXXXXXXXX (no spaces, no +)
2. **Check Existing Members**: Member might already be in list
3. **Check Rate Limit**: If adding >100/day, wait until tomorrow
4. **Try Different Channel**: If Telegram failing, try SMS

**Escalate If**: Phone format correct, member not existing, still failing

---

### Issue: "Members complaining about spam"

**Symptoms**:
- Members asking to be removed
- Complaints about too many messages

**Possible Causes**:
- Sending too frequently (>3/week)
- Content not relevant to all members
- Sending at inappropriate times (late night)

**Troubleshooting Steps**:
1. **Review Frequency**: Check announcement history
   - Reduce to 1-3/week if sending daily
2. **Review Content**: Ensure messages relevant to community
3. **Review Timing**: Send during business hours (9 AM - 6 PM)
4. **Ask for Feedback**: Survey members on preferred frequency

**Escalate If**: Complaints continue despite adjustments

---

## Technical Issues

### Issue: "Dashboard slow or unresponsive"

**Symptoms**:
- Pages take >10 seconds to load
- Buttons don't respond to clicks
- Browser shows "Loading..." indefinitely

**Possible Causes**:
- Server overloaded
- Network issues
- Browser cache full
- Too many users logged in simultaneously

**Troubleshooting Steps**:
1. **Check Internet**: Verify your internet connection working
2. **Clear Browser Cache**: Clear cookies and cache, reload page
3. **Try Different Browser**: Test with Chrome, Firefox, or Edge
4. **Wait and Retry**: If server overloaded, try again in 5-10 minutes

**Escalate If**: Dashboard consistently slow for >1 hour

---

### Issue: "Error 500 - Internal Server Error"

**Symptoms**:
- Page shows "500 Internal Server Error"
- Cannot access dashboard or specific pages

**Possible Causes**:
- Server bug or crash
- Database issue
- Configuration error

**Troubleshooting Steps**:
1. **Refresh Page**: Try reloading (Ctrl+R or Cmd+R)
2. **Try Different Page**: See if other pages work
3. **Wait and Retry**: Server might be restarting

**Escalate Immediately**: This is a critical issue, contact operator

---

### Issue: "Error 403 - Forbidden"

**Symptoms**:
- Page shows "403 Forbidden"
- "You don't have permission to access this page"

**Possible Causes**:
- Insufficient permissions (wrong role)
- Account suspended
- Trying to access another group's data

**Troubleshooting Steps**:
1. **Check Role**: Verify you have correct role (ADMIN, OPERATOR, VIEWER)
2. **Check Account Status**: Contact operator to verify account active
3. **Verify Group**: Ensure you're accessing your own group's data

**Escalate If**: Role correct, account active, still getting 403

---

## Channel-Specific Issues

### Telegram Bot Not Responding

**Symptoms**:
- Bot doesn't reply to commands
- Messages sent but no response

**Possible Causes**:
- Bot offline or crashed
- Telegram API issues
- User blocked bot

**Troubleshooting Steps**:
1. **Check Bot Status**: Ask operator to verify bot running
2. **Restart Conversation**: Send `/start` command
3. **Unblock Bot**: If you blocked bot, unblock in Telegram settings
4. **Try Web Dashboard**: Use web interface instead

**Escalate If**: Bot not responding for >1 hour

---

### SMS Not Delivering

**Symptoms**:
- SMS announcements not received
- Other channels (Telegram) working fine

**Possible Causes**:
- SMS gateway down
- Phone number incorrect
- Phone off or out of coverage
- SMS credits exhausted

**Troubleshooting Steps**:
1. **Verify Phone Number**: Check format 254XXXXXXXXX
2. **Check Phone Status**: Ensure phone on and has signal
3. **Try Different Number**: Test with another phone
4. **Contact Operator**: Verify SMS gateway configured and has credits

**Escalate If**: Multiple users not receiving SMS

---

### USSD Session Timeout

**Symptoms**:
- USSD session ends before completing action
- "Session expired" message

**Possible Causes**:
- Took too long to respond (>30 seconds)
- Network dropped session
- USSD gateway issue

**Troubleshooting Steps**:
1. **Retry**: Dial USSD code again and complete faster
2. **Check Network**: Ensure good mobile signal
3. **Use Alternative**: Try web dashboard or Telegram instead

**Escalate If**: Session always timing out immediately

---

## Error Messages Decoded

| Error Message | Meaning | Solution |
|---------------|---------|----------|
| "Rate limit exceeded" | Too many announcements (>5/day) | Wait 24 hours |
| "Invalid community_id" | Group doesn't exist | Contact operator |
| "Not authorized" | Admin trying to message another group | Use correct admin account |
| "Phone number format invalid" | Wrong phone format | Use 254XXXXXXXXX |
| "Member already exists" | Duplicate member | Check existing members |
| "Group not approved" | Registration pending | Wait for operator approval |
| "Session expired" | Logged out due to inactivity | Log in again |

---

## Diagnostic Commands (For Operators)

### Check System Health
```bash
# Check service status
systemctl status aos-web aos-telegram

# Check logs
journalctl -u aos-web -n 100
journalctl -u aos-telegram -n 100

# Check disk space
df -h

# Check database size
ls -lh aos.db
```

### Test Delivery
```bash
# Send test SMS (if configured)
curl -X POST http://localhost:8000/api/test/sms \
  -H "Content-Type: application/json" \
  -d '{"phone": "254712345678", "message": "Test"}'

# Check Telegram bot
curl http://localhost:8000/api/test/telegram
```

---

## When to Escalate

Escalate to operator/technical team when:

- ❌ Issue persists after trying all troubleshooting steps
- ❌ Error 500 (Internal Server Error)
- ❌ System-wide delivery failures
- ❌ Security concerns (unauthorized access, data breach)
- ❌ Database corruption or data loss

---

## Contact Information

**Operator Support**: [Email, Phone, Telegram]  
**Technical Support**: [Email, Phone]  
**Emergency**: [Phone for critical issues]

---

**Version History**:
- v1.0 (2025-12-28): Initial release
