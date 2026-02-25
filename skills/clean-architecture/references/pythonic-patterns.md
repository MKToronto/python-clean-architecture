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
    def get_price_data(self) -> list[float]: ...
    def get_amount(self) -> float: ...
    def buy(self, amount: float) -> None: ...
    def sell(self, amount: float) -> None: ...

class TradingStrategy(Protocol):
    def should_buy(self, prices: list[float]) -> bool: ...
    def should_sell(self, prices: list[float]) -> bool: ...

def trade(engine: TradingEngine, strategy: TradingStrategy) -> None:
    prices = engine.get_price_data()
    amount = engine.get_amount()
    if strategy.should_buy(prices):
        engine.buy(amount)
    elif strategy.should_sell(prices):
        engine.sell(amount)
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
    timestamp: datetime = field(default_factory=datetime.now)

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

### State

**Recognize:** Object behaves differently depending on its internal state; growing if/elif chains checking state before every action.

**Pythonic implementation:** Protocol-based state objects. The context delegates actions to the current state, and state objects trigger transitions:

```python
class DocumentState(Protocol):
    def edit(self, doc: "DocumentContext") -> None: ...
    def review(self, doc: "DocumentContext") -> None: ...
    def finalize(self, doc: "DocumentContext") -> None: ...

class DraftState:
    def edit(self, doc: "DocumentContext") -> None:
        doc.content.append("New content.")
    def review(self, doc: "DocumentContext") -> None:
        doc.state = ReviewedState()
    def finalize(self, doc: "DocumentContext") -> None:
        print("Cannot finalize — review first.")

class DocumentContext:
    def __init__(self) -> None:
        self.state: DocumentState = DraftState()
    def edit(self) -> None:
        self.state.edit(self)
```

→ Full reference: `patterns/state.md`

### Adapter

**Recognize:** External library's interface doesn't match what your code expects.

**Pythonic implementation (preferred):** Function + `functools.partial` for single-method adaptation. Protocol + composition class for multi-method adaptation:

```python
from typing import Any, Callable
from functools import partial

ConfigGetter = Callable[[str], Any]

def get_from_bs(soup: BeautifulSoup, key: str, default: Any = None) -> Any | None:
    value = soup.find(key)
    return value.get_text() if value else default

# Bind the external dependency — result matches ConfigGetter signature
bs_adapter = partial(get_from_bs, soup)
experiment = Experiment(bs_adapter)
```

Never use class-based (inheritance) adapters — they override the adaptee's methods with different semantics.

→ Full reference: `patterns/adapter.md`

### Facade

**Recognize:** Application code is coupled to a complex subsystem's internal details (connections, protocols, device management).

**Pythonic implementation:** A class that exposes a small number of high-level methods hiding subsystem complexity. Use `functools.partial` to bind the facade to controller functions:

```python
class IoTFacade:
    def __init__(self, service: IoTService) -> None:
        self.service = service
        self.speaker = SmartSpeaker(id="speaker_1")
        self.service.register_device(self.speaker)

    def power_speaker(self, on: bool) -> None:
        device = self.service.get_device(self.speaker.id)
        connection = Connection(device.ip, device.port)
        msg = Message(sender=self.speaker.id, content="switch_on" if on else "switch_off")
        connection.send(msg.to_b64())

# Composition root: bind facade to controller, pass to GUI
power_fn = partial(power_speaker, facade)  # Callable[[bool], None]
```

→ Full reference: `patterns/facade.md`

### Retry

**Recognize:** External API/database calls fail intermittently due to transient errors (timeouts, rate limits, temporary unavailability).

**Pythonic implementation:** `@retry` decorator with exponential backoff using `functools.wraps`:

```python
import functools
import time

def retry(retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return fn(*args, **kwargs)
                except exceptions:
                    if attempt == retries - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))
        return wrapper
    return decorator

@retry(retries=5, exceptions=(ConnectionError, TimeoutError))
def fetch_price(symbol: str) -> float:
    return requests.get(f"https://api.example.com/price/{symbol}").json()["price"]
```

→ Full reference: `patterns/retry.md`

### Lazy Loading

**Recognize:** Application startup is slow because it loads all data/models/resources upfront, even if many are never used.

**Pythonic implementation:** `functools.cache` for computed-once values, `cached_property` for class attributes, generators for streaming:

```python
from functools import cache, cached_property

@cache
def load_model(name: str) -> Model:
    return Model.from_pretrained(name)  # loaded once, cached forever

class DataPipeline:
    @cached_property
    def config(self) -> dict:
        with open(self.config_path) as f:
            return json.load(f)  # loaded on first access
```

→ Full reference: `patterns/lazy-loading.md`

### Plugin Architecture

**Recognize:** Adding new features requires modifying imports and core code. Need post-deployment extensibility.

**Pythonic implementation:** Registry + `importlib.import_module` + self-registering modules:

```python
# plugins/bard.py — self-registers when imported
from game.factory import register

@dataclass
class Bard:
    name: str
    def make_noise(self) -> None:
        print(f"{self.name} plays the flute")

class PluginInterface:
    @staticmethod
    def initialize() -> None:
        register("bard", Bard)
```

→ Full reference: `patterns/plugin-architecture.md`
