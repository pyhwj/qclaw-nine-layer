---
name: skill-api-fastapi
description: "REST API scaffolding with FastAPI patterns distilled from fastapi/fastapi (75k+ stars)."
---

# FastAPI Scaffold

Distilled from [tiangolo/fastapi](https://github.com/tiangolo/fastapi). Rapid REST API creation with auto-docs, validation, and async support.

## Quick Start Template

```python
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="MyAPI", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Item(BaseModel):
    name: str
    price: float
    tags: List[str] = []

# Dependency injection
def get_db():
    db = {"items": []}  # replace with real DB
    try:
        yield db
    finally:
        pass  # cleanup

@app.get("/items", response_model=List[Item])
async def list_items(db=Depends(get_db), limit: int = Query(10, le=100)):
    return db["items"][:limit]

@app.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item, db=Depends(get_db)):
    db["items"].append(item.model_dump())
    return item

@app.get("/items/{item_id}")
async def get_item(item_id: int, db=Depends(get_db)):
    if item_id >= len(db["items"]):
        raise HTTPException(status_code=404, detail="Not found")
    return db["items"][item_id]
```

## Pattern Catalog

| Pattern | Use Case |
|---------|----------|
| `Depends(get_db)` | DB/redis/auth injection |
| `response_model=...` | Auto-serialize + filter output |
| `Query(10, le=100)` | Input validation in params |
| `HTTPException(404)` | Standard error responses |
| `BackgroundTasks` | Fire-and-forget post-processing |
| `APIRouter(prefix="/v1")` | Modular route grouping |
| `@app.on_event("startup")` | Init connections/pools |

## Anti-patterns
- Don't put business logic in route handlers → separate service layer
- Don't skip response_model — it leaks DB fields
- Don't use `async def` with sync DB drivers (SQLite default)