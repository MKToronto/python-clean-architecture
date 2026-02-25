# Pythonic Patterns Quick Reference

Classic design patterns reimagined for Python. This is a concise lookup table — for full progressions (OOP → functional) with explanations, see the individual files in `patterns/`.

## General Rules

- **Protocol over ABC** — unless shared state in the superclass is needed
- **`functools.partial`** — to configure generic functions rather than creating wrapper classes
- **Closures** — to separate configuration-time args from runtime args
- **`Callable` type aliases** — to replace single-method abstract classes
- **Don't go full functional** — readability is the ultimate arbiter; find the happy medium

---

## Strategy Pattern

**Recognize:** Long if/elif chain selecting different behavioral logic.

**Pythonic implementation:** Higher-order function accepting a `Callable`.

```python
from typing import Callable

DiscountFunction = Callable[[int], int]

@dataclass
class Order:
    price: int
    quantity: int
    discount: DiscountFunction

    def compute_total(self) -> int:
        return self.price * self.quantity - self.discount(self.price * self.quantity)
```

**With configuration via closure:**

```python
def percentage_discount(percentage: float) -> DiscountFunction:
    return lambda price: int(price * percentage)

order = Order(price=100, quantity=2, discount=percentage_discount(0.15))
```

**With `functools.partial`:**

```python
from functools import partial

def percentage_discount(price: int, percentage: float) -> int:
    return int(price * percentage)

order = Order(price=100, quantity=2, discount=partial(percentage_discount, percentage=0.15))
```

→ Full progression: `patterns/strategy.md`

---

## Abstract Factory Pattern

**Recognize:** Need to create families of related objects that vary together.

**Pythonic implementation:** Tuples of functions + `partial`.

```python
IncomeTaxFn = Callable[[int], int]
CapitalTaxFn = Callable[[int], int]
TaxFactory = tuple[IncomeTaxFn, CapitalTaxFn]

def calculate_tax_on_rate(base: int, tax_rate: float = 0.1) -> int:
    return int(base * tax_rate)

simple_tax: TaxFactory = (
    calculate_tax_on_rate,
    partial(calculate_tax_on_rate, tax_rate=0),
)

def compute_tax(income: int, capital: int, factory: TaxFactory) -> int:
    income_fn, capital_fn = factory
    return income_fn(income) + capital_fn(capital)
```

→ Full progression: `patterns/abstract-factory.md`

---

## Bridge Pattern

**Recognize:** Two independent hierarchies that need to vary independently.

**Pythonic implementation:** `Callable` type aliases replace abstract-level references.

```python
GetPricesFunction = Callable[[str], list[int]]

def should_buy_average(get_prices: GetPricesFunction, symbol: str) -> bool:
    prices = get_prices(symbol)
    return prices[-1] < statistics.mean(prices[-5:])
```

Pass a bound method as the callable: `should_buy_average(exchange.get_prices, "BTC")`.

→ Full progression: `patterns/bridge.md`

---

## Command Pattern

**Recognize:** Need to store, sequence, undo, or batch operations.

**Pythonic implementation:** Functions that return undo closures.

```python
UndoFunction = Callable[[], None]

def append_text(doc: Document, text: str) -> UndoFunction:
    doc.text += text
    def undo():
        doc.text = doc.text[:-len(text)]
    return undo
```

**Batch via list comprehension:**

```python
CommandFunction = Callable[[], UndoFunction]

def batch(commands: list[CommandFunction]) -> UndoFunction:
    undo_functions = [cmd() for cmd in commands]
    def undo():
        for fn in reversed(undo_functions):
            fn()
    return undo
```

→ Full progression: `patterns/command.md`

---

## Notification Patterns (Pub/Sub)

**Recognize:** Core actions trigger side effects (email, Slack, logging) that pollute business logic.

**Pythonic implementation:** Dict-based subscribe/post_event.

```python
EventHandler = Callable[[User], None]
subscribers: dict[str, list[EventHandler]] = {}

def subscribe(event_type: str, handler: EventHandler) -> None:
    subscribers.setdefault(event_type, []).append(handler)

def post_event(event_type: str, user: User) -> None:
    for handler in subscribers.get(event_type, []):
        handler(user)
```

**Gotcha:** String-based event types can silently fail on typos. Use an Enum.

→ Full progression: `patterns/notification.md`

---

## Registry Pattern

**Recognize:** Need to create objects dynamically from data files (JSON, config).

**Pythonic implementation:** Dict mapping strings → callables with `**kwargs` unpacking.

```python
task_functions: dict[str, Callable[..., None]] = {}

def register(task_type: str, task_fn: Callable[..., None]) -> None:
    task_functions[task_type] = task_fn

def run(args: dict[str, Any]) -> None:
    args_copy = args.copy()
    task_type = args_copy.pop("type")
    task_functions[task_type](**args_copy)
```

→ Full progression: `patterns/registry.md`

---

## Template Method Pattern

**Recognize:** Same algorithm duplicated across sibling classes, varying only in the primitive steps.

**Pythonic implementation:** Free function + Protocol parameters.

```python
class TradingEngine(Protocol):
    def get_price_data(self) -> list[int]: ...
    def get_amount(self) -> int: ...
    def buy(self, symbol: str, amount: int) -> None: ...
    def sell(self, symbol: str, amount: int) -> None: ...

class TradingStrategy(Protocol):
    def should_buy(self) -> bool: ...
    def should_sell(self) -> bool: ...

def trade(engine: TradingEngine, strategy: TradingStrategy) -> None:
    if strategy.should_buy():
        engine.buy(symbol, engine.get_amount())
    elif strategy.should_sell():
        engine.sell(symbol, engine.get_amount())
```

**Protocol Segregation** — split one large protocol into smaller focused ones. Pythonic alternative to mixins.

→ Full progression: `patterns/template-method.md`

---

## Pipeline Pattern

**Recognize:** Sequential transformations on data.

**Pythonic implementation:** Function composition with `functools.reduce`.

```python
from functools import reduce, partial

ComposableFunction = Callable[[float], float]

def compose(*functions: ComposableFunction) -> ComposableFunction:
    return reduce(lambda f, g: lambda x: g(f(x)), functions)

pipeline = compose(
    partial(add_n, n=3),
    multiply_by_two,
    partial(add_n, n=5),
)
result = pipeline(10)
```

For pandas: use `.pipe()`. For complex pipelines: use Luigi or Airflow.

→ Full progression: `patterns/pipeline.md`

---

## Functional Patterns

### Callback

A function passed as an argument, called when something happens:

```python
ClickHandler = Callable[[Button], None]

@dataclass
class Button:
    label: str
    click_handlers: list[ClickHandler] = field(default_factory=list)

    def click(self):
        for handler in self.click_handlers:
            handler(self)
```

### Function Wrapper

Wraps an existing function, translating its interface:

```python
def loyalty_discount(price: int, loyalty: LoyaltyProgram) -> int:
    percentage = {LoyaltyProgram.BRONZE: 10, LoyaltyProgram.GOLD: 20}[loyalty]
    return percentage_discount(price, percentage)
```

### Function Builder

Creates and returns a configured function:

```python
def create_email_sender(smtp_server: str, port: int, user: str, password: str) -> MessageSender:
    def send(customer: Customer, subject: str, body: str) -> None:
        send_email(smtp_server, port, user, password, customer.email, subject, body)
    return send
```

→ Full progression: `patterns/functional.md`

---

## Architectural & Domain Patterns

### Value Objects

**Recognize:** Bare primitives (float, str) representing domain concepts — prices, emails, percentages — with no validation.

**Pythonic implementation:** Subclass built-in types with validation in `__new__`, or use frozen dataclasses with `__post_init__`:

```python
class Price(float):
    def __new__(cls, value) -> Self:
        val = float(value)
        if val < 0:
            raise ValueError("Price must be non-negative")
        return super().__new__(cls, val)

@dataclass(frozen=True)
class EmailAddress:
    value: str
    def __post_init__(self) -> None:
        if not EMAIL_RE.match(self.value):
            raise ValueError(f"Invalid email: {self.value}")
```

→ Full reference: `patterns/value-objects.md`

### Event Sourcing

**Recognize:** Need audit trails, temporal queries, or multiple derived views of the same data.

**Pythonic implementation:** Immutable `Event[T]` (frozen dataclass), append-only `EventStore[T]`, pure projection functions:

```python
@dataclass(frozen=True)
class Event[T = str]:
    type: EventType
    data: T
    timestamp: datetime = datetime.now()

class EventStore[T]:
    def append(self, event: Event[T]) -> None: ...
    def get_all_events(self) -> list[Event[T]]: ...
```

→ Full reference: `patterns/event-sourcing.md`

### CQRS

**Recognize:** List endpoints compute derived fields on every read; read and write patterns differ significantly.

**Pythonic implementation:** Separate write model (source of truth) and read model (pre-computed projection). Commands modify; queries fetch:

```python
COMMANDS_COLL = "ticket_commands"   # write side
READS_COLL = "ticket_reads"        # read projection

async def project_ticket(db, ticket_id: str) -> None:
    doc = await db[COMMANDS_COLL].find_one({"_id": ticket_id})
    read_doc = {"preview": make_preview(doc["message"]), "has_note": bool(doc.get("agent_note"))}
    await db[READS_COLL].update_one({"_id": ticket_id}, {"$set": read_doc}, upsert=True)
```

→ Full reference: `patterns/cqrs.md`

### Builder

**Recognize:** Complex object construction with many optional parts; construction steps matter.

**Pythonic implementation:** Fluent API with `Self` return type; `.build()` returns frozen product:

```python
class HTMLBuilder:
    def set_title(self, title: str) -> Self:
        self._title = title
        return self

    def build(self) -> HTMLPage:
        return HTMLPage(self._title, self._metadata, self._body)

page = HTMLBuilder().set_title("Demo").add_header("Hello").build()
```

→ Full reference: `patterns/builder.md`

### Unit of Work

**Recognize:** Multiple database operations that must succeed or fail together.

**Pythonic implementation:** Context manager wrapping a transaction:

```python
class UnitOfWork:
    def __enter__(self) -> "UnitOfWork":
        self.connection = sqlite3.connect(self.db_name)
        self.connection.execute("BEGIN")
        self.repository = Repository(self.connection)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_val:
            self.connection.rollback()
        else:
            self.connection.commit()
        self.connection.close()
```

→ Full reference: `patterns/unit-of-work.md`

### Singleton

**Recognize:** Need exactly one instance of a resource (config, connection pool, model loader).

**Pythonic implementation (preferred):** Module-level instance — Python modules are natural singletons:

```python
# config.py
db_uri = "sqlite:///:memory:"
debug = True

# usage: import config; config.debug
```

When a class is needed, use a metaclass with `_instances` dict.

→ Full reference: `patterns/singleton.md`
