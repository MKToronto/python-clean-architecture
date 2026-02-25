# CQRS (Command Query Responsibility Segregation)

Separate the write model (source of truth) from the read model (optimized for queries). Commands modify state; queries fetch pre-computed views. Eliminates the problem of list endpoints that compute derived fields on every request.

> **Note:** CQRS is an advanced pattern. Our three-layer architecture (Routers → Operations → Database) is the default for most projects. Use CQRS when read and write patterns diverge significantly.

---

## The Problem

A typical list endpoint fetches raw data and computes derived fields on every request:

```python
@app.get("/tickets", response_model=list[TicketListItem])
async def list_tickets(status: Status | None = None, limit: int = 20, skip: int = 0):
    db = get_db()
    # Must fetch message + agent_note just to compute preview and has_note
    cursor = db["tickets"].find(query, projection={
        "subject": 1, "status": 1, "updated_at": 1,
        "message": 1,      # only needed for preview computation
        "agent_note": 1,    # only needed for has_note computation
    })

    out = []
    for doc in cursor:
        note = (doc.get("agent_note") or "").strip()
        out.append(TicketListItem(
            id=str(doc["_id"]),
            subject=doc["subject"],
            status=doc["status"],
            updated_at=doc["updated_at"],
            preview=make_preview(doc.get("message", "")),  # computed every time
            has_note=bool(note),                            # computed every time
        ))
    return out
```

**Problems:**
- Fetches more data than the view needs (message, agent_note)
- Computes derived fields (preview, has_note) on every read
- Can't index or filter on computed fields
- Gets worse as more derived fields are added (scores, analytics)

---

## The Solution: Separate Write and Read Models

### Two Collections (or Tables)

```python
COMMANDS_COLL = "ticket_commands"   # source of truth (write side)
READS_COLL = "ticket_reads"        # optimized projection (read side)
```

### Separate DTOs

Commands describe intent. Queries describe what the view needs:

```python
# Commands (write DTOs)
class CreateTicket(BaseModel):
    customer_id: str
    subject: str
    message: str

class UpdateStatus(BaseModel):
    new_status: Status

class AddAgentNote(BaseModel):
    note: str

# Queries (read DTOs)
class TicketListItem(BaseModel):
    id: str
    subject: str
    status: Status
    updated_at: datetime
    preview: str       # pre-computed
    has_note: bool     # pre-computed

class TicketDetails(BaseModel):
    id: str
    customer_id: str
    subject: str
    message: str
    status: Status
    agent_note: str | None = None
    created_at: datetime
    updated_at: datetime
```

### Command Handlers (Write Side)

Standalone functions that modify the source of truth. Business rules live here:

```python
async def cmd_create_ticket(db: Database, cmd: CreateTicket) -> str:
    now = utcnow()
    doc = {
        "customer_id": cmd.customer_id,
        "subject": cmd.subject,
        "message": cmd.message,
        "status": "open",
        "agent_note": None,
        "created_at": now,
        "updated_at": now,
    }
    res = await db[COMMANDS_COLL].insert_one(doc)
    return str(res.inserted_id)


async def cmd_update_status(db: Database, ticket_id: str, cmd: UpdateStatus) -> None:
    existing = await db[COMMANDS_COLL].find_one({"_id": parse_id(ticket_id)})
    if existing is None:
        raise ValueError("Ticket not found")

    # Business rule: closed tickets cannot be reopened
    if existing["status"] == "closed" and cmd.new_status != "closed":
        raise ValueError("Closed tickets cannot be reopened")

    await db[COMMANDS_COLL].update_one(
        {"_id": parse_id(ticket_id)},
        {"$set": {"status": cmd.new_status, "updated_at": utcnow()}},
    )
```

### The Projector (Builds Read Model)

After each command, compute and store the derived fields once:

```python
async def project_ticket(db: Database, ticket_id: str) -> None:
    """Build read model from write model. Derived fields computed once here."""
    doc = await db[COMMANDS_COLL].find_one({"_id": parse_id(ticket_id)})
    if doc is None:
        return

    note = (doc.get("agent_note") or "").strip()

    read_doc = {
        "_id": doc["_id"],
        "subject": doc["subject"],
        "status": doc["status"],
        "updated_at": doc["updated_at"],
        "preview": make_preview(doc.get("message", "")),  # computed once
        "has_note": bool(note),                            # computed once
    }

    await db[READS_COLL].update_one(
        {"_id": doc["_id"]},
        {"$set": read_doc},
        upsert=True,
    )
```

### Command Endpoints (Write API)

Each write triggers the projector:

```python
@app.post("/tickets")
async def create_ticket(cmd: CreateTicket) -> dict[str, str]:
    db = get_db()
    ticket_id = await cmd_create_ticket(db, cmd)
    await project_ticket(db, ticket_id)
    return {"id": ticket_id}

@app.post("/tickets/{ticket_id}/status")
async def update_status(ticket_id: str, cmd: UpdateStatus) -> dict[str, str]:
    db = get_db()
    try:
        await cmd_update_status(db, ticket_id, cmd)
        await project_ticket(db, ticket_id)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Query Endpoints (Read API)

Reads are now simple lookups on pre-computed data:

```python
@app.get("/tickets", response_model=list[TicketListItem])
async def list_tickets(
    status: Status | None = None,
    has_note: bool | None = None,  # can now filter on derived field!
    limit: int = 20,
    skip: int = 0,
):
    db = get_db()
    query = {}
    if status is not None:
        query["status"] = status
    if has_note is not None:
        query["has_note"] = has_note  # indexed, pre-computed

    cursor = (
        db[READS_COLL]
        .find(query, projection={
            "subject": 1, "status": 1, "updated_at": 1,
            "preview": 1, "has_note": 1,
        })
        .sort("updated_at", -1)
        .skip(skip)
        .limit(limit)
    )
    # No computation needed — just map to response model
    return [TicketListItem(id=str(doc["_id"]), **doc) async for doc in cursor]
```

For detail views, read from the source of truth:

```python
@app.get("/tickets/{ticket_id}", response_model=TicketDetails)
async def get_ticket(ticket_id: str) -> TicketDetails:
    """Detail view reads from source of truth (write model)."""
    db = get_db()
    doc = await db[COMMANDS_COLL].find_one({"_id": parse_id(ticket_id)})
    if doc is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketDetails(id=ticket_id, **doc)
```

---

## When to Use CQRS

| Use CQRS when... | Stick with three-layer architecture when... |
|---|---|
| List views need derived/computed fields | Read and write shapes are similar |
| Dashboard/analytics endpoints are slow | Simple CRUD operations |
| You need to filter on computed values | One canonical view is sufficient |
| Read and write loads scale differently | Team is small, domain is straightforward |
| Event sourcing drives the write side | Projection maintenance adds no value |

---

## Relationship to Other Patterns

- **Event Sourcing** (event-sourcing.md) — Natural companion. Events are the write model; projections are the read model.
- **Pub/Sub** (notification.md) — Projectors can be event subscribers, updating read models asynchronously.
- **Three-layer architecture** (layered-architecture.md) — CQRS extends it. Commands go through operations layer; queries go through a separate read path.

---

## Trade-offs

| Advantage | Cost |
|---|---|
| Read endpoints are fast (pre-computed) | Data duplication (write + read models) |
| Can index and filter on derived fields | Projector must be called after every write |
| Read/write can scale independently | Eventual consistency if projection is async |
| Clear separation of intent (commands vs queries) | More code to maintain |
