---
name: skill-workflow-patterns
description: "Workflow orchestration patterns distilled from PrefectHQ/prefect (16k+ stars) — retry, pipeline DAG, error handling."
---

# Workflow Orchestration

Distilled from [PrefectHQ/prefect](https://github.com/PrefectHQ/prefect). Build resilient multi-step workflows with retry, caching, and observability.

## Core Patterns

### Task + Flow (DAG)

```python
from prefect import task, flow
import httpx
from time import sleep

@task(retries=3, retry_delay_seconds=[1, 5, 30])
def fetch_data(url: str) -> dict:
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

@task(cache_key_fn=lambda **kw: f"transform:{kw['data']['id']}", cache_expiration=3600)
def transform(data: dict) -> dict:
    return {"id": data["id"], "summary": data["title"][:100]}

@task
def save(result: dict, db_path: str):
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO results VALUES (?, ?)", (result["id"], result["summary"]))
    conn.commit()

@flow(name="ETL Pipeline", log_prints=True)
def etl_pipeline(urls: list[str], db_path: str = "output.db"):
    for url in urls:
        raw = fetch_data(url)
        result = transform(raw)
        save(result, db_path)
```

### Conditional Branching

```python
@flow
def process_order(order: dict):
    if order["amount"] > 1000:
        fraud_result = fraud_check(order)  # @task
        if not fraud_result["approved"]:
            return reject(order, fraud_result["reason"])
    charge_result = charge(order)
    return notify(order, charge_result["id"])
```

### Map (Fan-out)

```python
@flow
def batch_process(user_ids: list[int]):
    # Runs process_one for each user_id in parallel
    results = process_one.map(user_ids)
    return aggregate(results)

@task
def process_one(user_id: int) -> dict:
    return {"user_id": user_id, "status": "done"}
```

## Error Handling Strategies

| Strategy | When | How |
|----------|------|-----|
| Retry | Transient failures (network, rate limit) | `retries=3, retry_delay_seconds=[1,5,30]` |
| Fallback | Degraded mode acceptable | `except → return cached/default` |
| Dead Letter | Unrecoverable, needs human | `except → save to DLQ, alert` |
| Circuit Breaker | Downstream is down | `fail fast after N failures in window` |
| Timeout | Slow external calls | `httpx.get(url, timeout=10)` |

## Anti-patterns
- No retry without backoff (exponential/jitter) — avoid thundering herd
- Don't cache user-specific data globally
- Don't swallow exceptions silently — always log + alert