# Functional Design Patterns

> Content inspired by Arjan Codes' Pythonic Patterns course.

Three functional patterns for structuring higher-order functions: Callback, Function Wrapper, and Function Builder. Each uses functions as first-class values but serves a distinct purpose.

---

## 1. Callback -- Function Passed as Argument, Called on Events

A callback is a function passed to another function or class, called when a specific event occurs. The caller does not know what the callback does -- it simply invokes it at the right time.

### Single Callback

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Button:
    label: str
    on_click: Callable[[Button], None] = field(
        default_factory=lambda: lambda _: None
    )

    def click(self) -> None:
        print(f"Clicked on {self.label}")
        self.on_click(self)


def click_handler(button: Button) -> None:
    print(f"Handling click for {button.label}")


def main() -> None:
    # Pass a named function as callback
    btn = Button(label="Submit", on_click=click_handler)
    btn.click()
    # Output:
    #   Clicked on Submit
    #   Handling click for Submit

    # Or use a lambda for simple inline behavior
    btn2 = Button(label="Cancel", on_click=lambda _: print("Cancelled"))
    btn2.click()

    # Default callback does nothing -- safe to omit
    btn3 = Button(label="Idle")
    btn3.click()
```

The default callback is a no-op lambda. This avoids `None` checks when no handler is provided.

### Multiple Handlers

When multiple functions should respond to the same event, store a list of callbacks. This is the functional equivalent of the Observer pattern.

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

ClickHandler = Callable[["Button"], None]


@dataclass
class Button:
    label: str
    _click_handlers: list[ClickHandler] = field(default_factory=list)

    def add_click_handler(self, handler: ClickHandler) -> None:
        self._click_handlers.append(handler)

    def click(self) -> None:
        print(f"Clicked on {self.label}")
        for handler in self._click_handlers:
            handler(self)


def log_click(button: Button) -> None:
    print(f"[LOG] {button.label} clicked")


def track_analytics(button: Button) -> None:
    print(f"[ANALYTICS] Tracking click on {button.label}")


def main() -> None:
    btn = Button(label="Purchase")
    btn.add_click_handler(log_click)
    btn.add_click_handler(track_analytics)
    btn.click()
    # Output:
    #   Clicked on Purchase
    #   [LOG] Purchase clicked
    #   [ANALYTICS] Tracking click on Purchase
```

Relationship to Observer: the list of click handlers functions as the observer list. `add_click_handler` is `subscribe`. `click()` is `notify`. The functional approach avoids the Observer base class and subscription machinery.

---

## 2. Function Wrapper -- Calls Another Function, Translates Interface

A function wrapper calls an existing function internally but presents a different interface to the caller. It translates arguments, adapts return values, or both. A wrapper is **not** a decorator -- it does not modify the original function in place or use `@` syntax.

### Example: Loyalty Discount Wrapping Percentage Discount

```python
from enum import Enum
from functools import partial
from dataclasses import dataclass
from typing import Callable

DiscountFunction = Callable[[int], int]


def percentage_discount(price: int, percentage: float) -> int:
    return int(price * percentage)


def fixed_discount(price: int, amount: int) -> int:
    return min(price, amount)


class LoyaltyProgram(Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


LOYALTY_PERCENTAGES: dict[LoyaltyProgram, float] = {
    LoyaltyProgram.BRONZE: 0.10,
    LoyaltyProgram.SILVER: 0.15,
    LoyaltyProgram.GOLD: 0.20,
}


def loyalty_program_discount(price: int, loyalty: LoyaltyProgram) -> int:
    """Wrapper: translates loyalty program into a percentage,
    then delegates to percentage_discount."""
    return percentage_discount(price, LOYALTY_PERCENTAGES[loyalty])


@dataclass
class Order:
    price: int
    quantity: int
    discount: DiscountFunction

    @property
    def total(self) -> int:
        return self.price * self.quantity - self.discount(self.price * self.quantity)


def main() -> None:
    loyalty = LoyaltyProgram.SILVER
    loyalty_discount = partial(loyalty_program_discount, loyalty=loyalty)
    order = Order(price=100, quantity=2, discount=loyalty_discount)
    print(f"Total: ${order.total}")  # Total: $170
```

What the wrapper does:
- `loyalty_program_discount` accepts `(price, LoyaltyProgram)` -- a different interface than `percentage_discount(price, percentage)`.
- It looks up the percentage from the loyalty level, then calls `percentage_discount` with the translated arguments.
- `partial` is used at the call site to fix the `loyalty` argument so the result matches the `DiscountFunction` signature `(int) -> int`.

A wrapper does not create a new function object to return. It calls the inner function immediately and returns the result.

---

## 3. Function Builder -- Higher-Order Function That Creates Configured Functions

A function builder is a higher-order function that accepts configuration arguments and **returns a new function**. The returned function captures the configuration in a closure, separating config-time arguments from runtime arguments.

### Example: Loyalty Discount Builder

```python
from functools import partial

DiscountFunction = Callable[[int], int]


def loyalty_program_converter(loyalty: LoyaltyProgram) -> DiscountFunction:
    """Builder: returns a discount function configured for the given loyalty level."""
    return partial(percentage_discount, percentage=LOYALTY_PERCENTAGES[loyalty])


def main() -> None:
    loyalty = LoyaltyProgram.GOLD
    loyalty_discount = loyalty_program_converter(loyalty)
    order = Order(price=100, quantity=2, discount=loyalty_discount)
    print(f"Total: ${order.total}")  # Total: $160
```

The builder eliminates the `partial` at the call site. `loyalty_program_converter(LoyaltyProgram.GOLD)` returns a ready-to-use `DiscountFunction` that fits directly into `Order`.

### Example: Email Sender Builder with Closures

When a function needs configuration data (SMTP settings) that the caller should not have to pass every time, use a builder to separate config-time from runtime arguments.

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class Customer:
    name: str
    email: str


MessageSender = Callable[[Customer, str, str], None]


def send_email(
    smtp_server: str,
    port: int,
    username: str,
    password: str,
    to_address: str,
    subject: str,
    body: str,
) -> None:
    """Low-level email sending (simplified)."""
    print(f"Connecting to {smtp_server}:{port}")
    print(f"Sending email to {to_address}: {subject}")
    print(f"Body: {body}")


def create_email_sender(
    smtp_server: str,
    port: int,
    username: str,
    password: str,
) -> MessageSender:
    """Builder: captures SMTP config in a closure, returns a
    MessageSender that only needs customer, subject, and body."""

    def send_email_to_customer(
        customer: Customer, subject: str, body: str
    ) -> None:
        send_email(
            smtp_server=smtp_server,
            port=port,
            username=username,
            password=password,
            to_address=customer.email,
            subject=subject,
            body=body,
        )

    return send_email_to_customer


def send_welcome_message(customer: Customer, sender: MessageSender) -> None:
    """Business logic: composes the message. Does not know about SMTP."""
    sender(customer, "Welcome!", f"Hello {customer.name}, welcome aboard!")


def main() -> None:
    # Config-time: set up the sender once with SMTP settings
    email_sender = create_email_sender(
        smtp_server="smtp.gmail.com",
        port=587,
        username="noreply@example.com",
        password="secret",
    )

    # Runtime: use the sender without knowing SMTP details
    customer = Customer(name="Alice", email="alice@example.com")
    send_welcome_message(customer, email_sender)
```

Advantages of the builder over wrapper + partial:
- The builder encapsulates the `partial` / closure creation. The caller receives a clean function that matches the expected signature.
- `send_welcome_message` never sees SMTP configuration -- it only receives a `MessageSender`. This separates configuration concerns from business logic.
- The built function can be reused across any function that needs to send messages, without re-specifying config.

---

## Summary Table

| Aspect | Callback | Function Wrapper | Function Builder |
|---|---|---|---|
| **What it does** | Passed as argument, called when an event occurs | Calls another function, translates arguments or return value | Creates and returns a new configured function |
| **Direction** | Inward (caller passes it in) | Through (delegates to inner function) | Outward (returns a new function) |
| **When called** | Called by the receiver at event time | Called by the caller immediately -- delegates internally | Called once at config time; the returned function is called later at runtime |
| **Returns** | Whatever the callback contract specifies (often None) | The result of the inner function (possibly translated) | A new function (higher-order) |
| **Relationship** | Similar to Observer pattern | Similar to Adapter (for function interfaces) | Similar to Factory (for functions, not objects) |
| **Use partial?** | Rarely needed | Often needed at the call site to fix extra args | Encapsulates partial/closure internally -- caller does not use partial |
| **Example** | `on_click`, `on_error`, `on_complete` handlers | `loyalty_program_discount` wrapping `percentage_discount` | `create_email_sender` returning a `MessageSender` |

### Decision Guide

- **Use a callback** when the caller needs to inject behavior that runs at a future event (click, completion, error). Multiple callbacks act as lightweight observers.
- **Use a function wrapper** when an existing function has the right logic but the wrong interface. The wrapper translates arguments without creating a new function.
- **Use a function builder** when you need to separate configuration-time arguments from runtime arguments. The builder returns a function that integrates cleanly with the rest of the system without requiring `partial` at every call site.
