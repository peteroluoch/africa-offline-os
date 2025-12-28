# Transport Module Adoption Playbook

**Phase**: 11 (Transport Rollout)
**Version**: 1.0
**Target**: City Managers, Agents, Marshals

---

## 1. City Rollout Strategy

**Core Principle**: Seed the "Skeleton", Crowd-source the "Flesh".

Do NOT try to map every road yourself. Seed the major arteries, let users report the state.

### Step 1: The "Skeleton" Seeding (Day 1)
Before announcing to users, the Operator must seed the **Major Arteries** and **Hubs**.

*   **Roads**: The 3-5 main highways entering the city (e.g., Waiyaki Way, Thika Road, Mombasa Road).
*   **Hubs**: The 2-3 central bus stations (e.g., Railways, Odeon, Country Bus).
*   **Scope**: Use "Town" scope (e.g., "Nairobi").

**Command**:
```python
# Operator Console
module.register_zone("Waiyaki Way", "road", "Nairobi")
module.register_zone("Thika Road", "road", "Nairobi")
module.register_zone("Railways Station", "stage", "Nairobi/CBD")
```

### Step 2: Marshal Recruitment (Day 1-7)
Recruit **Stage Marshals** at the 3 Hubs.
*   **Role**: Report "Availability" (Are matatus filling up? Is there a shortage?).
*   **Incentive**: Free airtime or small stipend per week for consistent reporting.
*   **Action**: Marshal sends SMS every 30 mins during peak hours.

### Step 3: Commuter Launch (Day 8+)
Announce to commuters via SMS/WhatsApp.
*   **Value Prop**: "Check traffic before you leave work. Dial *384*...#"

---

## 2. Reporter Onboarding Guide

### Who Reports What?

| Persona | Reports | Channel | Frequency | Example |
| :--- | :--- | :--- | :--- | :--- |
| **Commuter** | **Traffic Signals** | SMS/Telegram | Ad-hoc (when stuck) | "Avoid Waiyaki, blocked at ABC" |
| **Marshal** | **Availability** | USSD/SMS | Scheduled (every 30m) | "Railways full, long queues for Rongai" |
| **Driver** | **Traffic Signals** | WhatsApp | Ad-hoc (on route) | "Accident at Nyayo Stadium" |
| **Agent** | **Both** | Web Dashboard | Monitoring | Verifies conflicting reports |

### Training a Marshal (5 Minutes)
1.  **Show Value**: "Help passengers know if they should come to your stage or wait."
2.  **The Code**: "Dial *384*2*1# to report 'Available'."
3.  **The Rule**: "Only report truth. If you lie, the system ignores you."

---

## 3. Trust & Abuse Handling

**The "Noise" Problem**: Users will report false info, or competing SACCOs may spam.

### Handling Strategy

1.  **Confidence Scoring (Kernel-Level)**
    *   One report = Low Confidence (Warning).
    *   Two reports = Medium Confidence (Confirmed).
    *   Agent/Authority report = High Confidence (Override).

2.  **Conflict Resolution**
    *   User A says "Flowing". User B says "Blocked".
    *   System waits for Tie-Breaker (User C).
    *   Until then, status is "Uncertain".

3.  **Spammer Ban**
    *   If a phone number sends >10 false reports (contradicted by consensus), Blacklist them.
    *   *Action*: Operator sets their confidence weight to 0.0.

---

## 4. Operational Constraints (The "Real World")

### Power Loss / Network Outage
*   **Scenario**: The server goes offline for 2 hours.
*   **Impact**: All signals expire (30 min TTL).
*   **Recovery**: When back online, system shows "Unknown" until new reports come in.
*   **Playbook**: Do NOT restore old backup data. Traffic changes fast. Start fresh.

### Partial Data
*   **Scenario**: Only Thika Road has reports. Waiyaki Way is silent.
*   **User View**: "Waiyaki Way: Unknown".
*   **Advisory**: "No news is NOT good news. It just means no news."

### SMS Latency
*   **Scenario**: SMS takes 10 mins to deliver.
*   **Mitigation**: Kernel uses `receive_time` for expiry, but reports are effectively valid for less time.
*   **Advisory**: Tell users "Updates are ~15 mins fresh".

---

## 5. What NOT To Promise

To manage expectations, **NEVER** market the system as:
1.  ❌ **GPS Navigation**: We don't do turn-by-turn.
2.  ❌ **Exact Arrival Times**: We deal in "Flowing" or "Blocked", not "14 minutes".
3.  ❌ **Seat Booking**: We show *availability*, we don't sell tickets.

**Promise**: "Know before you go."
