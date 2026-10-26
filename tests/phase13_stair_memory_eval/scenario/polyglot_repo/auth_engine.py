"""Polyglot Auth Engine: Multi-tenant JWT and token validation."""

import time
from typing import Dict, Any, Optional, List


class BaseAuthenticator:
    """Base class for authentication providers."""
    def __init__(self, issuer: str = "hermes.internal"):
        self.issuer = issuer

    def is_issuer_valid(self, payload: Dict[str, Any]) -> bool:
        return payload.get("iss") == self.issuer


class TokenAuthenticator(BaseAuthenticator):
    """Token-based authenticator with expiration checks."""
    def __init__(self, issuer: str = "hermes.internal", clock_skew_sec: int = 30):
        super().__init__(issuer=issuer)
        self.clock_skew_sec = clock_skew_sec

    def is_expired(self, payload: Dict[str, Any], current_time: Optional[float] = None) -> bool:
        now = current_time or time.time()
        exp = payload.get("exp", 0)
        return now > (exp + self.clock_skew_sec)


class MultiTenantJwtAuthenticator(TokenAuthenticator):
    """Enterprise multi-tenant JWT validator with tenant partition isolation."""
    def __init__(self, issuer: str = "hermes.internal", allowed_tenants: Optional[List[str]] = None):
        super().__init__(issuer=issuer)
        self.allowed_tenants = set(allowed_tenants or ["tenant_alpha", "tenant_beta", "tenant_gamma"])

    def verify_tenant_membership(self, tenant_id: str) -> bool:
        return tenant_id in self.allowed_tenants

    def validate_claim_signature(self, token_payload: Dict[str, Any], tenant_id: str, current_time: Optional[float] = None) -> bool:
        """STAIR TARGET METHOD: Validates tenant signature and payload claims.
        
        Requires:
        1. Valid issuer.
        2. Valid unexpired token.
        3. Tenant membership.
        4. Matching tenant claim in payload.
        """
        if not self.is_issuer_valid(token_payload):
            return False

        if self.is_expired(token_payload, current_time=current_time):
            return False

        if not self.verify_tenant_membership(tenant_id):
            return False

        claimed_tenant = (
            token_payload.get("tenant")
            or token_payload.get("tenant_id")
            or token_payload.get("tid")
        )
        return claimed_tenant == tenant_id
