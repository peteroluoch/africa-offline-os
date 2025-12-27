# Transport Module Architectural Audit (Read-Only)

## 1️⃣ Domain Model Summary

### Core Entities

#### Route
**Fields:**
- `id`: Route identifier
- `name`: Route name
- `start_point`: Starting location
- `end_point`: Destination location
- `base_price`: Base fare for the route

**Responsibilities:**
- Represents a fixed transportation route between two points
- Stores pricing information

#### Vehicle
**Fields:**
- `plate_number`: Vehicle registration plate (primary identifier)
- `current_status`: Vehicle availability (`AVAILABLE`, `FULL`, `OFF_DUTY`)
- `current_route_id`: Currently assigned route (nullable)
- `last_seen`: Last status update timestamp

**Responsibilities:**
- Tracks real-time vehicle availability
- Associates vehicles with routes
- Records driver status updates

**Note:** No explicit DTO/model classes exist. Data is handled as raw dictionaries from SQL queries.

---

## 2️⃣ Public Module Interface

### `list_routes() -> list[dict]`
**Inputs:** None  
**Outputs:** List of route dictionaries with keys: `id`, `name`, `start`, `end`, `price`  
**Responsibility:** Retrieve all available routes from the database  
**Concern Mixing:** ❌ None - Pure data retrieval

### `update_vehicle_status(plate: str, status: str, route_id: str | None = None) -> bool`
**Inputs:**
- `plate`: Vehicle plate number
- `status`: New status (`AVAILABLE`, `FULL`, `OFF_DUTY`)
- `route_id`: Optional route assignment

**Outputs:** `True` if update succeeded, `False` if vehicle not found  
**Responsibility:** Update vehicle availability and route assignment  
**Concern Mixing:** ⚠️ **YES** - Contains commented-out event dispatch logic (line 61)

### `get_route_status(route_id: str) -> dict`
**Inputs:** `route_id`  
**Outputs:** Dictionary with keys: `route_id`, `route_name`, `vehicles` (list of vehicle status objects)  
**Responsibility:** Aggregate vehicle availability for a specific route  
**Concern Mixing:** ❌ None - Pure aggregation logic

---

## 3️⃣ Internal Logic Flow

### Data Flow

1. **Route Listing:**
   - Direct SQL query → Raw tuple conversion → Dictionary list
   - No intermediate processing or validation

2. **Vehicle Status Update:**
   - SQL UPDATE with plate number filter
   - Commit immediately
   - Check `rowcount` for success/failure
   - ⚠️ Commented event dispatch (not active)

3. **Route Status Aggregation:**
   - Query 1: Fetch vehicles on route (excluding `OFF_DUTY`)
   - Query 2: Fetch route name
   - Combine results into single dictionary

### Decision Points

- **Vehicle Update Success:** Based on SQL `rowcount > 0`
- **Route Name Fallback:** Returns `"Unknown"` if route not found
- **Vehicle Filtering:** Excludes `OFF_DUTY` vehicles from route status

### Coupling

**Database:**
- ✅ Direct SQL queries (acceptable for offline-first)
- ✅ No ORM dependency
- ⚠️ No repository abstraction (violates clean architecture)

**External Services:**
- ✅ None - Fully offline

**Event Bus:**
- ⚠️ Commented-out dispatcher call (incomplete integration)

**UI/Vehicles:**
- ✅ None in core module

---

## 4️⃣ Vehicle & Infra Touchpoints

### USSD Logic (`transport_ussd.py`)

**Violations:**
- ❌ **Business Logic in Adapter:** Status mapping (`1` → `AVAILABLE`) should be in domain
- ❌ **TODO Comment:** Line 60 - "Actually update DB" indicates incomplete implementation
- ❌ **Session State Management:** Menu navigation logic tightly coupled to USSD protocol

**Specific Issues:**
- Lines 25-30: Route listing logic duplicates domain responsibility
- Lines 56-61: Status translation should be a domain method
- Line 60: Direct comment indicates adapter is bypassing module

### SMS Logic (`transport_sms.py`)

**Status:** Not reviewed (file not inspected in this audit)

### Bot-Specific Logic

**Status:** No Telegram/WhatsApp handlers found in Transport module

### Database Assumptions

**Direct SQL Queries:**
- Line 44: `SELECT id, name, start_point, end_point, base_price FROM routes`
- Line 53-55: `UPDATE vehicles SET current_status = ?, current_route_id = ?, last_seen = CURRENT_TIMESTAMP WHERE plate_number = ?`
- Line 68-70: `SELECT plate_number, current_status FROM vehicles WHERE current_route_id = ? AND current_status != 'OFF_DUTY'`
- Line 74: `SELECT name FROM routes WHERE id = ?`

**Violations:**
- ⚠️ No repository pattern (direct SQL in module)
- ⚠️ Hardcoded table names
- ⚠️ No query parameterization abstraction

### Network Assumptions

- ✅ None - Fully offline

---

## 🚨 Architectural Violations Summary

### Critical

1. **No Repository Layer:** Direct SQL in domain module violates clean architecture
2. **USSD Adapter Contains Business Logic:** Status mapping and route formatting belong in domain
3. **Incomplete Event Integration:** Commented-out dispatcher (line 61)
4. **No DTOs:** Raw dictionaries instead of typed domain objects

### Moderate

1. **No Input Validation:** `update_vehicle_status` accepts any string for status
2. **Inconsistent Error Handling:** Silent failures (returns `False` without logging)
3. **USSD Handler Incomplete:** TODO comment indicates unfinished implementation

### Compliant

1. ✅ **Offline-First:** No external API calls
2. ✅ **Vehicle-Agnostic Core:** Module has no USSD/SMS dependencies
3. ✅ **SQLite-Based:** Uses local database

---

## ✅ AUDIT COMPLETE

**No code changes made.**  
**No refactoring performed.**  
**No optimization suggested.**

This is a read-only extraction for architectural review.
