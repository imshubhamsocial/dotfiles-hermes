---
name: parse-text-comment-fix
description: "Strip trailing comments from config value strings."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [parsing, config, text-processing]
    related_skills: [test-driven-development]
---

# Fix: parse() - Comments appearing after value

## Overview

The parse() function reads 'key = value' lines into a dict. Comments may appear after values in the input text (e.g., key=value # comment). The function should strip trailing comments before storing the value.

## When to Use

- When implementing parse() that reads config files
- When config files may contain comments after values
- When values may have trailing # comment syntax

## Prerequisites

- config.py with parse() function implemented
- Input text may contain lines like key=value # comment

## Procedure

1. Write test cases showing expected behavior (comments after values should be stripped)
2. Run tests to verify they fail (RED phase)
3. In parse(), after splitting on =, strip trailing # ... from the value
4. Run tests to verify pass

## Pitfalls

- Comments after values should be stripped but not comments on lines before =
- Empty string values with comments: key= # comment → {'key': ''}
- Multiple = in value: key=a=b # comment → {'key': 'a=b'}

## Verification

- parse("key=value") returns {'key': 'value'}
- parse("# comment only") returns {}
- parse("key=value # trailing comment") returns {'key': 'value'}
- parse("key=value\n# comment line") returns {'key': 'value'}
