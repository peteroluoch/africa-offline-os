# Framework D (Security & Compliance) — A-OS Implementation

**Canonical source**: `docs/01_roles.md` (FAANG 5-Framework System — A-OS Edition)

## 1. What Framework D is in A-OS

Framework D provides a multi-layered "Defense in Depth" strategy to protect the A-OS Kernel and sensitive agricultural/personal data in offline-first environments.

**Status**: ✅ 100% COMPLETE (December 27, 2025)

## 2. Objectives
- Implement enterprise-grade edge node identity (Ed25519).
- Ensure data privacy at rest (ChaCha20-Poly1305 / AES-GCM).
- Establish strictly enforced hierarchical Role-Based Access Control (RBAC).
- Maintain immutable security audit logs for offline nodes.

## 3. Implementation Details

- **Phase 1: Node Identity**
  - Ed25519 keypair generation for every node, tied to hardware/seed.
- **Phase 2: Transparent Encryption**
  - Implemented `SecureRepositoryMixin` in `repository.py`.
  - Automatic encryption of PII (Farmer location, contact) using keys derived from the node unique ID.
- **Phase 3: Hierarchical RBAC**
  - Defined `AosRole` Enum: `ROOT`, `ADMIN`, `OPERATOR`, `VIEWER`.
  - Implemented `requires_role` FastAPI dependency to block unauthorized access at the route level.
- **Phase 4: Security Auditing**
  - Structured JSON audit logging in `data/logs/audit.jsonl`.
  - Logging of `UNAUTHORIZED_ACCESS` and `SECURITY_BREACH` events with severity markers.
- **Phase 5: Secure Session Persistence**
  - Secure Logout functionality with `HttpOnly` and `SameSite` cookie purging.

## 4. Security Standards
- **Zero Secrets in Code**: All master secrets derived from environment or node ID.
- **Defense in Depth**: Authenticated routing + Encrypted storage + Signed logs.
- **PII Protection**: Mandate encryption for any field identifying specific individuals.
- **Audit Integrity**: Cryptographic signing of audit log lines (in-progress hardening).

## 5. Key Deliverables
- ✅ `aos.core.security.encryption`: AEAD encryption engine.
- ✅ `aos.core.security.auth`: RBAC and JWT management.
- ✅ `FarmerRepository`: The first hardened repository with transparent encryption.
- ✅ `audit.jsonl`: Traceable security history.

## 6. How to Verify
- `pytest aos/tests/test_farmer_encryption.py` (Encryption check)
- `pytest aos/tests/test_security_rbac.py` (Authorization check)
- `pytest aos/tests/test_auth_logout.py` (Session check)
