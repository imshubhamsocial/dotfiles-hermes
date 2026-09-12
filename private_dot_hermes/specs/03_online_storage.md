---
id: online_storage
title: "Habitat High-Throughput SQLite WAL Storage Specification"
version: 1
prerequisites: ["core_architecture"]
target_artifact: "generated/online_storage.py"
---

# Online WAL Storage Specification

## Overview
Durable specification for SQLite WAL connection pooling, sub-millisecond trajectory streaming, and lock contention avoidance.

### Worked Example: Connection Pool Lease
- Active connection pool: max_connections = 10
- Transaction concurrency: 8 concurrent readers, 1 dedicated WAL writer
- Write lock wait duration: 0.0ms (non-blocking snapshot isolation)
- State persistence throughput: > 500 records/sec

### Reconciliation Anchors
ANCHOR: expr="1.0 / ((1.0 - p) + (p / s))" vars={"p": 0.9, "s": 10.0} expected=5.263157894736842
ANCHOR: expr="read_latency + write_latency" vars={"read_latency": 1.2, "write_latency": 2.8} expected=4.0
