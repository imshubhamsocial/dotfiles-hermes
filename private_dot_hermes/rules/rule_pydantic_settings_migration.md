# Rule: Pydantic V2 BaseSettings Migration

**Invariant:** When migrating from Pydantic v1 to v2, the `BaseSettings` class is deprecated and has been moved to a separate package, `pydantic-settings`.

**Action:** Do not import `BaseSettings` directly from `pydantic`. Instead, update imports to `from pydantic_settings import BaseSettings`.

**Verification:** After migration, rerun the test suite to ensure all configuration loading paths remain functional.

**Scope:** Global configuration modules utilizing settings patterns.
