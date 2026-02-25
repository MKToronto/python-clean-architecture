# Retry Pattern

**Recognize:** Code that calls external services (APIs, databases, message queues) fails intermittently due to transient errors — network timeouts, rate limits, temporary unavailability.

**Problem:** Without retry logic, a single transient failure causes the entire operation to fail. Naive retry (immediate, unlimited) can overwhelm the service. Retry logic mixed into business code clutters operations functions.

---

## Simple Retry Function

The most basic approach — retry a fixed number of times with a delay:

```python
import time
from typing import Callable, TypeVar

T = TypeVar("T")

def retry(fn: Callable[..., T], retries: int = 3, delay: float = 1.0, **kwargs) -> T:
    for attempt in range(retries):
        try:
            return fn(**kwargs)
        except Exception as e:
            if attempt == retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError("Unreachable")  # satisfies type checker
```

**Usage:**

```python
result = retry(fetch_user_data, retries=3, delay=2.0, user_id="abc123")
```

---

## Exponential Backoff

Each retry waits longer than the last — prevents overwhelming the service and avoids thundering herd problems:

```python
import time
from typing import Callable, TypeVar

T = TypeVar("T")

def retry_with_backoff(
    fn: Callable[..., T],
    retries: int = 5,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    **kwargs,
) -> T:
    for attempt in range(retries):
        try:
            return fn(**kwargs)
        except Exception as e:
            if attempt == retries - 1:
                raise
            delay = base_delay * (backoff_factor ** attempt)
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
            time.sleep(delay)
    raise RuntimeError("Unreachable")
```

**Backoff schedule** (base_delay=1, factor=2): 1s → 2s → 4s → 8s → 16s

---

## `@retry` Decorator

Separates retry logic from business logic using `functools.wraps`:

```python
import time
import functools
from typing import Callable, TypeVar

T = TypeVar("T")

def retry(
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
) -> Callable:
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            for attempt in range(1, retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    if attempt == retries:
                        raise
                    time.sleep(delay * (backoff ** (attempt - 1)))
            raise RuntimeError("All retries failed")
        return wrapper
    return decorator
```

**Usage:**

```python
@retry(retries=5, delay=0.5)
def fetch_price(symbol: str) -> float:
    response = requests.get(f"https://api.example.com/price/{symbol}")
    response.raise_for_status()
    return response.json()["price"]
```

The decorator catches `Exception` broadly — this is one of the rare cases where that is acceptable, because it always re-raises the original error after all retries are exhausted. The re-raise is the safety mechanism. For production code where you need finer exception control, use the `tenacity` library (see below) rather than hand-rolling exception filtering.

---

## Fallback Strategies

When all retries are exhausted, choose a fallback instead of crashing:

### Return a Default Value

```python
def retry_with_fallback(
    fn: Callable[..., T],
    fallback: T,
    retries: int = 3,
    **kwargs,
) -> T:
    for attempt in range(retries):
        try:
            return fn(**kwargs)
        except Exception:
            if attempt == retries - 1:
                return fallback
            time.sleep(1.0 * (2 ** attempt))
    return fallback
```

### Try Alternative Operations

```python
def retry_with_alternatives(
    operations: list[Callable[[], T]],
) -> T:
    for i, operation in enumerate(operations):
        try:
            return operation()
        except Exception as e:
            if i == len(operations) - 1:
                raise
            print(f"Operation {i + 1} failed: {e}. Trying next...")
    raise RuntimeError("All operations failed")
```

**Usage:**

```python
result = retry_with_alternatives([
    lambda: fetch_from_primary_api(symbol),
    lambda: fetch_from_backup_api(symbol),
    lambda: fetch_from_cache(symbol),
])
```

---

## The `tenacity` Library

For production code, use the [`tenacity`](https://github.com/jd/tenacity) library instead of hand-rolling retry logic:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)
def fetch_price(symbol: str) -> float:
    response = requests.get(f"https://api.example.com/price/{symbol}")
    response.raise_for_status()
    return response.json()["price"]
```

Tenacity handles edge cases (logging, callbacks, async support) that hand-rolled solutions miss. For production code, prefer `tenacity` over a custom decorator. If you need to filter by exception type, tenacity offers `retry_if_exception_type((ConnectionError, TimeoutError))` via the `retry` parameter.

---

## When to Use

- **Network calls** — HTTP requests, database connections, message queue operations
- **Rate-limited APIs** — wait and retry when the API returns 429 Too Many Requests
- **Cloud services** — AWS, GCP, and Azure SDKs often recommend exponential backoff
- **Distributed systems** — inter-service communication in microservice architectures

## When NOT to Use

- **Deterministic errors** — `ValueError`, `TypeError`, bad input validation will always fail
- **Authentication errors** — 401/403 responses won't succeed on retry
- **Business logic failures** — "insufficient funds" or "item out of stock" aren't transient
- **Infinite retries** — always set a maximum; use circuit breaker pattern for persistent failures

## Idempotency Requirement

Retried operations **must be idempotent** — executing them multiple times should produce the same result as executing them once. If an operation partially succeeds before a timeout, retrying it must not cause duplicates or corruption.

```python
# BAD: not idempotent — retrying creates duplicate charges
def charge_customer(customer_id: str, amount: int) -> None:
    db.insert({"customer_id": customer_id, "amount": amount})

# GOOD: idempotent — uses idempotency key to prevent duplicates
def charge_customer(customer_id: str, amount: int, idempotency_key: str) -> None:
    if db.exists(idempotency_key):
        return  # already processed
    db.insert({"key": idempotency_key, "customer_id": customer_id, "amount": amount})
```

For HTTP APIs, use idempotency keys (Stripe uses `Idempotency-Key` header). For database operations, use upserts or check-before-write patterns.

---

## LLM API Retry Use Case

LLM APIs (OpenAI, Anthropic) are a common retry target — they may return malformed JSON, hit rate limits, or time out on long generations:

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import json

class MalformedResponseError(Exception):
    """LLM returned invalid JSON or unexpected structure."""

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((MalformedResponseError, TimeoutError)),
)
def get_structured_response(prompt: str) -> dict:
    response = call_llm(prompt)
    try:
        result = json.loads(response)
    except json.JSONDecodeError:
        raise MalformedResponseError(f"Invalid JSON: {response[:100]}")
    if "answer" not in result:
        raise MalformedResponseError("Missing 'answer' field")
    return result
```

Use list multiplication to build operation sequences with retries:

```python
# Retry the same operation 3 times, then fall back to a different model
operations = [lambda: call_model("gpt-4")] * 3 + [lambda: call_model("gpt-3.5-turbo")]
result = retry_with_alternatives(operations)
```

---

## Circuit Breaker Relationship

When retries keep failing, a **circuit breaker** stops retrying and fails fast. This prevents wasting time and resources on a service that is clearly down.

```
Closed (normal)  →  Open (failing fast)  →  Half-Open (testing recovery)
     ↑                                              │
     └──────────── success ◄─────────────────────────┘
```

The retry pattern handles **transient** failures (a few retries fix the problem). The circuit breaker handles **persistent** failures (the service is down, stop trying). In practice, combine both: retry a few times within a circuit breaker. When the retry budget is exhausted, the circuit breaker opens and all subsequent calls fail immediately until a cooldown period expires.

---

## Relationship to Other Patterns

- **Decorator** (`references/decorators.md`) — the `@retry` decorator uses `functools.wraps` and parameterized decorator pattern
- **Error Handling** (`references/error-handling.md`) — retry is a complement to exception handling, not a replacement; catch specific exceptions
- **Strategy** (`strategy.md`) — fallback alternatives use the same pattern of passing functions as arguments
