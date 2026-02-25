# Decorator Patterns Reference

Decorators wrap a function to add behavior before, after, or around it — without modifying the original function. They are Python's native implementation of the Function Wrapper pattern. Content inspired by Arjan Codes' Software Designer Mindset course.

## 1. Basic Decorator Structure

A decorator is a function that takes a function and returns a new function. Always use `functools.wraps` to preserve the original function's name, docstring, and signature.

```python
from functools import wraps
from typing import Callable, Any


def my_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # before
        result = func(*args, **kwargs)
        # after
        return result
    return wrapper


@my_decorator
def greet(name: str) -> str:
    return f"Hello, {name}"
```

Without `@wraps`, `greet.__name__` would be `"wrapper"` instead of `"greet"`, and the docstring would be lost. This breaks introspection, logging, and debugging.

---

## 2. Logging Decorator

Log function calls with arguments and return values. Useful for debugging and auditing.

```python
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)


def log_calls(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.info(f"Calling {func.__name__}({args}, {kwargs})")
        result = func(*args, **kwargs)
        logger.info(f"{func.__name__} returned {result}")
        return result
    return wrapper


@log_calls
def calculate_total(price: float, quantity: int) -> float:
    return price * quantity
```

---

## 3. Retry Decorator

Retry a function on failure with exponential backoff. Essential for network calls, database operations, and external API integrations.

```python
import time
from functools import wraps
from typing import Callable, Any


def retry(
    retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    wait = delay * (2 ** attempt)
                    time.sleep(wait)
            raise last_exception
        return wrapper
    return decorator


@retry(retries=3, delay=0.5, exceptions=(ConnectionError, TimeoutError))
def fetch_data(url: str) -> dict:
    ...
```

### Key design decisions

- **Catch specific exceptions** — pass a tuple of expected failure types; the default `(Exception,)` is intentionally broad as a safety net since retry re-raises after exhaustion, but narrowing to specific exceptions (e.g., `ConnectionError, TimeoutError`) is best practice
- **Exponential backoff** — `delay * (2 ** attempt)` prevents hammering a failing service
- **Re-raise the last exception** — if all retries fail, the caller sees the original error, not a generic one

### Async version

```python
import asyncio
from functools import wraps
from typing import Callable, Any


def async_retry(
    retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    wait = delay * (2 ** attempt)
                    await asyncio.sleep(wait)
            raise last_exception
        return wrapper
    return decorator
```

---

## 4. Timing Decorator

Measure function execution time.

```python
import time
from functools import wraps
from typing import Callable, Any


def timed(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper
```

---

## 5. Parameterized Decorators

When a decorator needs configuration, add an outer function that accepts parameters and returns the actual decorator. This creates three levels of nesting.

```python
# Without parameters: two levels
def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        ...
    return wrapper

# With parameters: three levels
def decorator(param):
    def actual_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ...
        return wrapper
    return actual_decorator
```

The retry decorator above is a parameterized decorator — `retry(retries=3)` returns the actual decorator, which is then applied to the function.

---

## 6. Stacking Decorators

Multiple decorators apply bottom-up (closest to the function runs first):

```python
@log_calls      # 3. logs the retry-wrapped, timed function
@timed          # 2. times the retry-wrapped function
@retry(retries=3)  # 1. adds retry behavior to the original function
def fetch_data(url: str) -> dict:
    ...
```

The execution order is: `log_calls(timed(retry(retries=3)(fetch_data)))`.

---

## 7. Class-Based Decorators

When a decorator needs to maintain state between calls, use a class with `__call__`:

```python
from functools import wraps
from typing import Callable, Any


class CallCounter:
    def __init__(self, func: Callable[..., Any]) -> None:
        wraps(func)(self)
        self.func = func
        self.count = 0

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.count += 1
        return self.func(*args, **kwargs)


@CallCounter
def process(data: str) -> str:
    return data.upper()

process("hello")
process("world")
print(process.count)  # 2
```

---

## 8. When to Use Decorators vs Other Patterns

| Situation | Use |
|---|---|
| Cross-cutting concern (logging, timing, retry, auth) | Decorator |
| Behavior varies per call (different algorithm) | Strategy (Callable) |
| Need to configure behavior at runtime | functools.partial or closure |
| Multiple cooperating behaviors | Composition with Protocol |

Decorators are best for concerns that apply uniformly across many functions. If the added behavior needs to vary per function or per call, use a Strategy or dependency injection instead.

---

## 9. Best Practices

### Do

- Always use `@functools.wraps(func)` on the wrapper function
- Catch specific exceptions in retry decorators — narrowing from the default `(Exception,)` is best practice (see `patterns/retry.md`)
- Keep decorators focused on one concern (logging OR retry, not both)
- Type hint decorator parameters and return types
- Use parameterized decorators when the decorator needs configuration

### Do Not

- Forget `@wraps` — it breaks `__name__`, `__doc__`, and introspection
- Stack more than 2-3 decorators — it becomes hard to reason about execution order
- Use decorators for complex business logic — they should add cross-cutting behavior, not core functionality
- Swallow exceptions inside decorators without re-raising
