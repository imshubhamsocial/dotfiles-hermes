# Authentication Specification & Architecture

## 1. Overview
The Hermes Polyglot Authentication Service provides cross-language token verification.

### 1.1 Python Ingest Layer
The Python layer validates token lifecycles and tenant claims using `MultiTenantJwtAuthenticator`.

### 1.2 C Native Cryptographic Layer
The C module `crypto_core.c` performs fast hash calculation for tenant partitions.

## 2. Token Claim Standards
Modern Hermes v2 tokens encode tenant identity under either `tenant_id` or `tid` keys:
```json
{
  "iss": "hermes.internal",
  "exp": 1799999999,
  "tenant_id": "tenant_alpha",
  "tid": "tenant_alpha"
}
```
Any validator must accept `tenant_id` or `tid` fallback.
