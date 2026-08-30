---
name: polars-data-analysis
category: software-development
description: Execute multi-threaded, high-speed DataFrame analytics using Polars lazy execution.
---

# Polars High-Performance Data Engineering Standard

Always prefer `polars` over `pandas` for all tabular data manipulation, feature extraction, and dataset transformation in Hermes Agent OS.

## Core Invariants
1. **Lazy Execution First**:
   - Always initialize pipelines via `pl.scan_csv()`, `pl.scan_parquet()`, or `df.lazy()`.
   - Apply filters and projections *before* calling `.collect()` to allow Polars query optimizer to push predicates down.
2. **Native Expression Chains**:
   - Avoid Python `.map_elements()` or `.apply()` row-by-row loops whenever a native Polars expression (`pl.when().then()`, `pl.col().str.*`, `pl.col().dt.*`) exists.
3. **Multi-Threaded Aggregations**:
   - Polars uses Rust Rayon under the hood; let it scale across all available CPU cores.
4. **Memory Guard**:
   - For multi-gigabyte files, use `.collect(streaming=True)` to process batches out-of-core without exceeding host RAM boundaries.
