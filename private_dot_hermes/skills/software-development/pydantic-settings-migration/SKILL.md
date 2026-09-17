---
name: pydantic-settings-migration
description: Migrate BaseSettings to pydantic-settings.
version: 1.0.0
author: Hermes Agent (Nous Research)
---

## Overview
This skill encapsulates the common pattern for migrating Pydantic v1 applications to Pydantic v2 regarding configuration management.

## Core Problem
`BaseSettings` from `pydantic` is deprecated and removed in Pydantic v2.

## Solution
1. **Update Imports:** Replace `from pydantic import BaseSettings` with `from pydantic_settings import BaseSettings`.
2. **Dependency:** Ensure `pydantic-settings` is installed as a dependency.
3. **Verification:** After applying the change, run the full test suite to confirm configuration loading integrity.

## Usage
This skill should be loaded when encountering Pydantic v1 settings errors.
