---
name: skill-system-design
description: "Architecture patterns and system design templates distilled from donnemartin/system-design-primer (280k+ stars)."
---

# System Design Templates

Distilled from [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer). Design scalable systems with battle-tested patterns.

## Core Concepts

### CAP Theorem Trade-offs
```
CP (Consistency + Partition Tolerance): Banking, payments → sacrifice Availability
AP (Availability + Partition Tolerance): Social feeds, CDN → sacrifice Consistency
CA: Doesn't exist in distributed systems (partition tolerance is mandatory)
```

### Scaling Patterns

| Pattern | When | How |
|---------|------|-----|
| Vertical Scaling | <10k users | Bigger CPU/RAM |
| Horizontal Scaling | >10k users | Add more servers |
| Load Balancer | >1 server | Nginx, HAProxy, AWS ALB |
| CDN | Static assets | CloudFlare, CloudFront |
| Caching | Hot data/reads | Redis, Memcached |
| Database Replication | Read-heavy | Master-Slave, Multi-Master |
| Sharding | Huge datasets | Partition by user_id/region |
| Message Queue | Async ops | Kafka, RabbitMQ, SQS |

### Common Architectures

**URL Shortener (tinyurl)**
```
Client → Load Balancer → App Server → DB (key-value: short_url → long_url)
                                    → Cache (Redis: hot URLs)
Key generation: base62(md5(url))[:7], collision check with retry
```

**Chat System (WhatsApp)**
```
Client ↔ WebSocket Server ↔ Message Queue ↔ Chat Service → DB
                             ↔ Presence Service (heartbeat every 5s)
Storage: Messages in time-series DB, Media in S3/CDN
```

**News Feed (Twitter)**
```
Write: Post → Fanout Service → Timeline Cache (Redis List per user)
Read:  User → Timeline Cache (first 200) → Merge + Rank
Celebrity posts: pull-on-read (not fanout) to avoid thundering herd
```

## Design Template

```python
# Quick capacity estimate
def estimate(users: int, req_per_user_per_day: int, storage_per_req_kb: float):
    rps = users * req_per_user_per_day / 86400
    bandwidth_mbps = rps * storage_per_req_kb * 8 / 1000
    storage_tb_per_year = rps * 86400 * 365 * storage_per_req_kb / 1e9
    return {"rps": round(rps), "bandwidth_mbps": round(bandwidth_mbps, 1), "storage_tb_year": round(storage_tb_per_year, 1)}
```

## Interview Framework (RADIO)
1. **R**equirements: functional + non-functional (latency, consistency, availability)
2. **A**rchitecture: high-level diagram, data flow
3. **D**eep-dive: data model, API design, scaling bottlenecks
4. **I**mprovements: monitoring, alerting, failover, disaster recovery
5. **O**utlook: future scaling, tech debt, migration path