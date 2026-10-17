# layered-service

Token cost levels are relative estimates within this step, not measurements.

Summary: A backend in three layers with one-way dependencies: Router (HTTP only) → Service (business rules) → Repository (queries only). Services receive repositories, never a database session. Schema changes ship as backward-compatible expand-contract migrations.

```
HTTP ─▶ Router ─────────▶ Service ─────────▶ Repository ─▶ DB
        auth, parse,       rules, validation,  select / insert /
        call service,      combine repos,      update / delete
        format response    raise domain errors
```

Typical stack: Python FastAPI + SQLAlchemy + Alembic. The same shape fits Express/NestJS, Spring, Go HTTP services.

Fits:
- Web APIs with business rules beyond plain CRUD.
- Services that deploy with rolling or overlapping versions (old code still running while migrations apply).
- Codebases where routers have started to hold queries and rules.

Does not fit:
- Thin CRUD APIs where a service would only forward to a repository. Let the router call the repository's caller directly only if this document says so; otherwise the empty layer is noise.
- Event-driven or batch systems whose main unit is a job, not a request.

## Example (Python, FastAPI)

```python
# repositories/order_repository.py
class OrderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def open_for_cart(self, cart_id: int) -> Order | None:
        return self._session.scalar(
            select(Order).where(Order.cart_id == cart_id, Order.status == "open")
        )

    def add(self, order: Order) -> Order:
        self._session.add(order)
        self._session.flush()
        return order


# services/order_service.py
class OrderAlreadyOpenError(Exception): ...

class OrderService:
    def __init__(self, orders: OrderRepository, clock: Clock) -> None:
        self._orders = orders
        self._clock = clock

    def place(self, cart_id: int, user_id: int) -> Order:
        if self._orders.open_for_cart(cart_id):
            raise OrderAlreadyOpenError(cart_id)
        return self._orders.add(
            Order(cart_id=cart_id, user_id=user_id, placed_at=self._clock.now(), status="open")
        )


# routers/orders.py
def get_order_service(session: Session = Depends(get_session)) -> OrderService:
    return OrderService(OrderRepository(session), SystemClock())

@router.post("/carts/{cart_id}/orders", status_code=201)
def place_order(
    cart_id: int,
    user: User = Depends(current_user),
    service: OrderService = Depends(get_order_service),
) -> OrderOut:
    try:
        return OrderOut.model_validate(service.place(cart_id, user.id))
    except OrderAlreadyOpenError:
        raise HTTPException(status_code=409, detail="Cart already has an open order")
```

Service tests pass fake repositories and a fixed clock. Repository tests run against a throwaway test database.

Pros:
- Business rules are testable without HTTP or a database.
- Queries live in one place per entity, so performance fixes (N+1, indexes) have one home.
- Routers stay short and uniform; auth and status codes are easy to audit.
- Expand-contract keeps old and new versions working during deploys.

Cons:
- Simple endpoints pass through three files.
- The service/repository line needs judgment ("is this filter a rule or a query?").
- Expand-contract turns one schema change into several PRs over several deploys.
- Migrating an existing codebase is gradual; old and new styles coexist for a while.

Token cost: Medium — a new endpoint touches router, service, repository, and their tests; schema changes add expand-contract PRs.

Recommended when: the project is an HTTP backend with business rules and deploys with old and new versions overlapping.

## Failure modes to avoid

- **Queries in routers.** Even one "quick" query in a router bypasses the rules in the service.
- **Services holding a session.** A service that takes a session starts writing queries itself, and its tests need a database.
- **Reverse dependencies.** Repositories do not call services; services do not import router or HTTP types (no HTTP exceptions in services).
- **Generic repositories.** A `BaseRepository[T]` with every possible method hides which queries are actually used. Write the queries callers need.
- **One-shot destructive migrations.** Dropping, renaming, or making a column `NOT NULL` in the same deploy as the code change breaks the version still running.

## Expand-contract migrations

Migrations run before new code starts, and old instances (including background schedulers) can keep running on the old revision for a while. So every schema change must work with both the old and the new code.

1. **Expand**: add the new column or table, nullable or with a default. Do not remove or rename anything.
2. **Compatible code**: deploy code that writes both shapes (or the new shape in a way the old code tolerates) and reads either.
3. **Backfill**: fill the new shape from the old data, in a migration or a one-off job, idempotently.
4. **Contract**: in a later PR, after no old version runs, remove the old column, add `NOT NULL`, or drop the table.

Each phase is its own PR. Migration defaults must make sense for rows the old code keeps writing.

## Contract to write

````markdown
## Backend layers

The backend has three layers. Dependencies point one way only.

```
Router ─▶ Service ─▶ Repository ─▶ database
```

- **Router**: HTTP only. Authentication and authorization checks, input parsing, calling a service, formatting the response, mapping domain errors to status codes.
- **Service**: business rules. Validates, combines repositories to carry out a use case, raises domain errors. Receives repositories (and other I/O such as a clock) through its constructor. Never receives a database session. Never imports HTTP types.
- **Repository**: queries only. Encapsulates select / insert / update / delete for one entity or aggregate. No business rules.

### Rules

- No database queries in routers. Go through a service.
- Services take repositories, not a session.
- No reverse dependencies: repositories never call services; services never call routers.
- No generic base repository. Each repository has the queries its callers use.
- When editing existing code in a domain that does not follow these layers yet, separate that domain's layers in the same change, without touching unrelated domains.

### Schema changes

Migrations run before new code starts, and old code can keep running for a while. Every schema change is backward compatible and ships as expand-contract:

1. Expand migration (add nullable columns or new tables; remove nothing).
2. Code that works with both old and new schema.
3. Backfill, idempotent.
4. Contract migration in a later PR, once no old version runs.

Never drop, rename, or make a column `NOT NULL` in the same deploy as the code that stops using it.

### Tests

- Service tests use fake repositories and a fixed clock. No database.
- Repository tests run against an isolated test database.
- Router tests cover auth, status codes, and response shape through the framework's test client.
````

## Review checklist

- No ORM or SQL usage in router files.
- Services do not accept a session or connection; they receive repositories.
- No service imports HTTP types; no repository calls a service.
- New repository methods are used by a caller; no generic base repository added.
- Each migration is backward compatible with the code currently deployed: no drop, rename, or immediate `NOT NULL` alongside the code change; defaults fit rows old code writes; backfill is idempotent.
- A destructive schema change has a separate, later cleanup phase.
- When a touched domain still mixes layers, the change separates it (or the PR says why not).
- Structural changes are reflected in this document.
