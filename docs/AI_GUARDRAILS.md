# 🔒 A-OS AI Guardrails & System Invariants

**CRITICAL: These rules apply to ALL AI-assisted development across A-OS modules.**  
**AI must respect invariants, not "improve" them.**

---

## 1. Core Identity Invariants

### Person vs Membership Separation
- **A Person** represents a real human (anchored by phone number)
- **A Membership** represents a Person's relationship to a Group
- **A Person** may belong to multiple Groups via separate Memberships

### Forbidden Actions
❌ **NEVER** merge or overwrite Persons automatically without an explicit identity match rule  
❌ **NEVER** treat "member" as a global entity  
❌ **NEVER** edit a Person when only a Membership change is intended

---

## 2. Group Isolation Rule

### Operational Isolation
- **Groups are operationally isolated**
- Actions in one group **MUST NOT** affect another unless explicitly designed

### Forbidden Actions
❌ **NEVER** cascade updates across groups  
❌ **NEVER** assume shared state between group memberships  
❌ **NEVER** create cross-group side effects without explicit design

---

## 3. Join & Registration Constraints

### Registration Authority
- **Admin/field-agent registration is authoritative**
- **Self-registration** (SMS/USSD/WhatsApp/Telegram) creates **PENDING** memberships by default
- **Activation requires explicit approval** unless group policy allows auto-approve

### Forbidden Actions
❌ **NEVER** auto-enroll users silently  
❌ **NEVER** bypass approval logic  
❌ **NEVER** assume self-registration = active membership

---

## 4. Capability-Based Behavior (No Hardcoding)

### Feature Control
- **Group-specific features** are controlled via **capabilities**, not conditionals
- **Core logic must remain generic**

### Required Actions
✅ **ALWAYS** add new behavior behind capability flags  
✅ **ALWAYS** avoid branching core flows by group type  
✅ **ALWAYS** use capability checks, not `if group_type == "church"`

---

## 5. Broadcasting & Bulk Actions

### Controlled Backend Flows
- **All bulk actions** must go through controlled backend flows
- **Direct "send immediately" paths are disallowed**
- **Cost, scope, and recipient count must be explicit**

### Forbidden Actions
❌ **NEVER** introduce background side effects without logging  
❌ **NEVER** add new broadcast channels without isolation  
❌ **NEVER** bypass the queue-based broadcast system

---

## 6. UI & Kernel Constraints

### Technology Stack
- **Kernel UI** uses server-rendered HTML + HTMX only
- **No heavy frontend frameworks** in core modules
- **Modals are preferred** for quick actions

### Forbidden Actions
❌ **NEVER** introduce React/Vue/SPA logic into kernel pages  
❌ **NEVER** add real-time sync unless explicitly approved  
❌ **NEVER** use client-side state management in kernel UI

---

## 7. AI Assistance Boundaries

### AI Role Definition
- **AI may fill gaps, refactor, or extend** only within declared invariants
- **AI must prefer explicitness over automation**
- **When uncertain, AI should defer, not invent**

### Forbidden Actions
❌ **NEVER** "optimize" by removing guardrails  
❌ **NEVER** assume future intent without instruction  
❌ **NEVER** introduce breaking changes without approval

---

## 8. Forward-Compatibility Rule

### New Module Requirements
New modules (Health, Education, AI Coaching, etc.) **MUST**:
- ✅ Plug in via capabilities
- ✅ Respect identity and membership boundaries
- ✅ Avoid kernel mutations

### Rejection Criteria
**If a suggestion violates any rule above, it must be rejected — even if it appears helpful.**

---

## 🛑 When AI Should Stop

AI must **STOP and ASK** when encountering:
1. **Identity Merge Requests** - Requires explicit user confirmation
2. **Cross-Group Data Sharing** - Requires architectural approval
3. **Capability Bypass Attempts** - Requires security review
4. **Kernel Architecture Changes** - Requires PM approval
5. **New External Dependencies** - Requires dependency audit

---

## ✅ AI Compliance Checklist

Before completing any task, verify:
- [ ] No Person/Membership confusion
- [ ] No cross-group side effects
- [ ] No approval logic bypassed
- [ ] No hardcoded group-type conditionals
- [ ] No direct broadcast paths (queue-based only)
- [ ] No heavy frontend frameworks in kernel
- [ ] No guardrail removal
- [ ] No kernel mutations from new modules

---

**This document is machine-readable and enforced via code review and CI gates.**

**Last Updated**: 2025-12-29  
**Status**: ACTIVE - MANDATORY FOR ALL AI AGENTS
