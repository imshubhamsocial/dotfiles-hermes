"""Unit test suite for Polyglot Authentication."""

import pytest
from auth_engine import MultiTenantJwtAuthenticator


def test_legacy_token_auth():
    auth = MultiTenantJwtAuthenticator(issuer="hermes.internal")
    payload = {
        "iss": "hermes.internal",
        "exp": 2000000000,
        "tenant": "tenant_alpha"
    }
    assert auth.validate_claim_signature(payload, "tenant_alpha") is True


def test_modern_v2_token_auth():
    auth = MultiTenantJwtAuthenticator(issuer="hermes.internal")
    # Modern token with tenant_id key
    payload = {
        "iss": "hermes.internal",
        "exp": 2000000000,
        "tenant_id": "tenant_alpha"
    }
    # This assertion currently FAILS because auth_engine only checks 'tenant'
    assert auth.validate_claim_signature(payload, "tenant_alpha") is True


def test_tid_fallback_token_auth():
    auth = MultiTenantJwtAuthenticator(issuer="hermes.internal")
    # Modern compact token with tid key
    payload = {
        "iss": "hermes.internal",
        "exp": 2000000000,
        "tid": "tenant_beta"
    }
    assert auth.validate_claim_signature(payload, "tenant_beta") is True
