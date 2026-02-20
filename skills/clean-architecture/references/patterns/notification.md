# Notification Patterns Reference

Separate side effects (email, Slack, logging) from business logic using Observer, Mediator, or Pub/Sub. Pub/Sub is the preferred Pythonic approach.

> Content inspired by Arjan Codes' Pythonic Patterns course.

---

## Problem: Side Effects Mixed with Business Logic

API functions that perform a core action (register a user, upgrade a plan) also directly call email, Slack, and logging services. Every function imports and invokes these side-effect systems inline.

```python
import logging
from lib.db import create_user, find_user
from lib.email import send_email
from lib.slack import post_slack_message


def register_new_user(name: str, password: str, email: str) -> None:
    # create an entry in the database
    user = create_user(name, password, email)

    # post a Slack message to sales department
    post_slack_message(
        "sales",
        f"{user.name} has registered with email address {user.email}. Please add them.",
    )

    # send a welcome email
    send_email(
        user.name,
        user.email,
        "Welcome",
        f"Thanks for registering, {user.name}!",
    )

    # write server log
    logging.debug(f"User registered with email address {user.email}")


def upgrade_plan(email: str) -> None:
    user = find_user(email)
    user.plan = "paid"

    post_slack_message("sales", f"{user.name} has upgraded their plan.")
    send_email(
        user.name,
        user.email,
        "Thank you",
        f"Thanks for upgrading, {user.name}! You're gonna love it.",
    )
    logging.debug(f"User with email address {user.email} has upgraded their plan.")


def password_forgotten(email: str) -> None:
    user = find_user(email)
    reset_code = user.init_reset_password()

    send_email(
        user.name,
        user.email,
        "Reset your password",
        f"To reset your password, use this very secure code: {reset_code}.",
    )
    logging.debug(f"User with email address {user.email} requested a password reset.")
```

**What is wrong here:**

- Every function imports `send_email`, `post_slack_message`, and `logging` directly.
- Adding a new notification channel (e.g., SMS) means editing every function.
- The core action (`create_user`, `user.plan = "paid"`) is buried under side-effect code.
- `register_new_user` is really just one line of business logic: `user = create_user(name, password, email)`. Everything else is notification plumbing.

---

## Observer Pattern

The classic Gang of Four approach. A Subject maintains a list of Observers and notifies them when something happens.

```
Subject                          <<abstract>> Observer
  observers: list[Observer]          notify()
  register_observer(observer)            |
  unregister_observer(observer)    ConcreteObserver1
  notify_observers()               ConcreteObserver2
```

### Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class Observer(ABC):
    @abstractmethod
    def notify(self) -> None:
        """Notify the observer."""


class ConcreteObserver(Observer):
    def notify(self) -> None:
        print("Observer was notified.")


@dataclass
class Subject:
    observers: list[Observer] = field(default_factory=list)

    def register_observer(self, observer: Observer) -> None:
        self.observers.append(observer)

    def unregister_observer(self, observer: Observer) -> None:
        self.observers.remove(observer)

    def notify_observers(self) -> None:
        for obs in self.observers:
            obs.notify()

    def do_something(self) -> None:
        print("Subject did something.")
        self.notify_observers()


def main() -> None:
    subject = Subject()
    observer = ConcreteObserver()
    subject.register_observer(observer)
    subject.do_something()
    # Output:
    #   Subject did something.
    #   Observer was notified.
```

### Limitations

- **Couples one subject to a list of observers.** Each subsystem (user registration, plan upgrade, password reset) needs its own Subject, or everything ends up in one bloated class.
- **Scales poorly.** As the API grows, creating subjects for every action becomes impractical.
- **The subject already has its own responsibilities.** Adding observer management to it reduces cohesion.

---

## Mediator Pattern

Centralizes notification logic inside a Mediator class. Components tell the mediator that something happened; the mediator decides what to do.

```
<<abstract>> Mediator               Component
  notify(sender, event)               mediator: Mediator
        |                                  |
  ConcreteMediator               ConcreteComponent1
    notify(sender, event)        ConcreteComponent2
    do_something()
```

### Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class Mediator(ABC):
    @abstractmethod
    def notify(self, sender: "Component", event: str) -> None: ...


@dataclass
class Component:
    mediator: Mediator | None = field(default=None, init=False)


class Button(Component):
    def click(self) -> None:
        if self.mediator:
            self.mediator.notify(self, "click")


@dataclass
class TextField(Component):
    value: str = ""
    enabled: bool = True


class LoginPage(Mediator):
    def __init__(self) -> None:
        self.text_field = TextField()
        self.button = Button()
        self.text_field.mediator = self
        self.button.mediator = self

    def notify(self, sender: Component, event: str) -> None:
        if sender is self.button and event == "click":
            self.start_login()

    def start_login(self) -> None:
        self.text_field.enabled = False
        print(f"Starting login with email: {self.text_field.value}")


def main() -> None:
    page = LoginPage()
    page.text_field.value = "hi@arjancodes.com"
    page.button.click()
    print(f"Text field disabled: {not page.text_field.enabled}")
    # Output:
    #   Starting login with email: hi@arjancodes.com
    #   Text field disabled: True
```

### Limitations

- **All logic lives in the mediator class.** As component types grow, the mediator accumulates methods and conditional branches, decreasing cohesion.
- **The mediator can become a God Object.** In UI frameworks, putting all handling code in UI classes leads to a mess (which is why patterns like MVC exist).
- **Not standardized.** Each mediator has its own bespoke `notify` logic, making the system harder to extend.

---

## Pub/Sub Pattern (Preferred)

Also called the Event Aggregator (term introduced by Martin Fowler). Combine the centralized aspect of the mediator with the standardized notification mechanism of the observer. The subject does not know anything about its observers. Events are posted to a central system, and handler functions are dynamically attached to event types.

**Key insight:** Pub/Sub is centralized like Mediator, but standardized like Observer. Best of both worlds.

### Core Event System

Create an `event/` package with a `core.py` module containing the entire Pub/Sub engine.

```python
# event/core.py
from typing import Callable

from lib.db import User

EventHandler = Callable[[User], None]

subscribers: dict[str, list[EventHandler]] = {}


def subscribe(event_type: str, handler: EventHandler) -> None:
    if event_type not in subscribers:
        subscribers[event_type] = []
    subscribers[event_type].append(handler)


def post_event(event_type: str, user: User) -> None:
    if event_type not in subscribers:
        return
    for handler in subscribers[event_type]:
        handler(user)
```

That is the entire engine. Two functions and a dictionary.

**Shorter alternative** using `dict.get` and `dict.setdefault`:

```python
def subscribe(event_type: str, handler: EventHandler) -> None:
    subscribers.setdefault(event_type, []).append(handler)


def post_event(event_type: str, user: User) -> None:
    for handler in subscribers.get(event_type, []):
        handler(user)
```

### Handler Modules with Self-Registration

Create separate handler modules for each notification channel. Each module defines handler functions and a `setup_*_event_handlers()` function that subscribes them.

**Email handlers:**

```python
# event/email.py
from lib.db import User
from lib.email import send_email
from event.core import subscribe


def handle_user_registered_event(user: User) -> None:
    send_email(
        user.name,
        user.email,
        "Welcome",
        f"Thanks for registering, {user.name}!",
    )


def handle_user_password_forgotten_event(user: User) -> None:
    send_email(
        user.name,
        user.email,
        "Reset your password",
        f"To reset your password, use this very secure code: {user.reset_code}.",
    )


def handle_user_upgrade_plan_event(user: User) -> None:
    send_email(
        user.name,
        user.email,
        "Thank you",
        f"Thanks for upgrading, {user.name}! You're gonna love it.",
    )


def setup_email_event_handlers() -> None:
    subscribe("user_registered", handle_user_registered_event)
    subscribe("user_password_forgotten", handle_user_password_forgotten_event)
    subscribe("user_upgrade_plan", handle_user_upgrade_plan_event)
```

**Slack handlers:**

```python
# event/slack.py
from lib.slack import post_slack_message
from lib.db import User
from event.core import subscribe


def handle_user_registered_event(user: User) -> None:
    post_slack_message(
        "sales",
        f"{user.name} has registered with email address {user.email}",
    )


def handle_user_upgrade_plan_event(user: User) -> None:
    post_slack_message("sales", f"{user.name} has upgraded their plan.")


def setup_slack_event_handlers() -> None:
    subscribe("user_registered", handle_user_registered_event)
    subscribe("user_upgrade_plan", handle_user_upgrade_plan_event)
```

**Log handlers:**

```python
# event/log.py
import logging

from lib.db import User
from event.core import subscribe


def handle_user_registered_event(user: User) -> None:
    logging.debug(f"User registered with email address {user.email}")


def handle_user_password_forgotten_event(user: User) -> None:
    logging.debug(f"User with email address {user.email} requested a password reset.")


def handle_user_upgrade_plan_event(user: User) -> None:
    logging.debug(f"User with email address {user.email} has upgraded their plan.")


def setup_log_event_handlers() -> None:
    subscribe("user_registered", handle_user_registered_event)
    subscribe("user_password_forgotten", handle_user_password_forgotten_event)
    subscribe("user_upgrade_plan", handle_user_upgrade_plan_event)
```

### Refactored API Functions

After introducing Pub/Sub, the API functions become clean. They perform only business logic and post a single event. No imports of email, Slack, or logging.

```python
# api/user.py
from event.core import post_event
from lib.db import create_user, find_user


def register_new_user(name: str, password: str, email: str) -> None:
    # create an entry in the database
    user = create_user(name, password, email)

    # post an event
    post_event("user_registered", user)


def password_forgotten(email: str) -> None:
    # retrieve the user
    user = find_user(email)

    # generate a password reset code
    user.init_reset_password()

    # post an event
    post_event("user_password_forgotten", user)
```

```python
# api/plan.py
from event.core import post_event
from lib.db import find_user


def upgrade_plan(email: str) -> None:
    # find the user
    user = find_user(email)

    # upgrade the plan
    user.plan = "paid"

    # post an event
    post_event("user_upgrade_plan", user)
```

### Wiring It Up in Main

Call each setup function before performing any actions. This is where the event system is initialized.

```python
# main.py
from api.plan import upgrade_plan
from api.user import password_forgotten, register_new_user
from event.email import setup_email_event_handlers
from event.log import setup_log_event_handlers
from event.slack import setup_slack_event_handlers


def main() -> None:
    # initialize the event handling structure
    setup_slack_event_handlers()
    setup_log_event_handlers()
    setup_email_event_handlers()

    # register a new user
    register_new_user("Arjan", "BestPasswordEva", "hi@arjancodes.com")

    # send a password reset message
    password_forgotten("hi@arjancodes.com")

    # upgrade the plan
    upgrade_plan("hi@arjancodes.com")


if __name__ == "__main__":
    main()
```

### Flexibility Advantage

Want to temporarily disable Slack notifications? Comment out one line:

```python
def main() -> None:
    # setup_slack_event_handlers()  # Slack disabled
    setup_log_event_handlers()
    setup_email_event_handlers()
    ...
```

Store handler activation in a database or config file to toggle notification channels at runtime without redeploying.

---

## Gotchas

### String-Based Event Types Cause Silent Failures

Using raw strings as event types makes typos invisible. A misspelled event type posts to nobody and raises no error:

```python
# Typo: "user_pasword_forgotten" instead of "user_password_forgotten"
post_event("user_pasword_forgotten", user)  # silently does nothing
```

**Fix: Use an Enum for event types.**

```python
from enum import Enum, auto


class EventType(Enum):
    USER_REGISTERED = auto()
    USER_PASSWORD_FORGOTTEN = auto()
    USER_UPGRADE_PLAN = auto()


subscribers: dict[EventType, list[EventHandler]] = {}


def subscribe(event_type: EventType, handler: EventHandler) -> None:
    subscribers.setdefault(event_type, []).append(handler)


def post_event(event_type: EventType, user: User) -> None:
    for handler in subscribers.get(event_type, []):
        handler(user)
```

Now a typo like `EventType.USER_PASWORD_FORGOTTEN` raises an `AttributeError` immediately.

### Implement Unsubscribe

The basic implementation shown above does not include `unsubscribe`. Add it for completeness:

```python
def unsubscribe(event_type: str, handler: EventHandler) -> None:
    if event_type in subscribers:
        subscribers[event_type].remove(handler)
```

### Duplicate Registration

Calling a setup function twice registers every handler twice, causing duplicate notifications. Guard against this at the setup level or use a set instead of a list (requires hashable handlers):

```python
subscribers: dict[str, set[EventHandler]] = {}

def subscribe(event_type: str, handler: EventHandler) -> None:
    subscribers.setdefault(event_type, set()).add(handler)
```

---

## When to Use Notification Patterns

### Recognition Signals

- A function performs its core job and then calls two or more unrelated side-effect systems.
- Multiple functions share the same side-effect calls (all of them send email + log + Slack).
- Adding a new notification channel requires editing every function that triggers notifications.
- The imports at the top of a module include `send_email`, `post_slack_message`, and `logging` alongside domain-specific imports.

### Scaling to Cloud Architecture

Pub/Sub is not just a code pattern -- it is an architectural pattern. Cloud platforms provide managed Pub/Sub services:

- **Google Cloud Pub/Sub** -- managed message queuing with exactly-once delivery
- **AWS SNS/SQS** -- Simple Notification Service paired with message queues
- **Azure Service Bus** -- enterprise message broker with topics and subscriptions

The in-process `dict`-based Pub/Sub shown above translates directly to these cloud services. Replace `post_event()` with a call to publish a message to a cloud topic, and replace `subscribe()` with a cloud subscription that triggers a serverless function.

---

## Trade-offs: Observer vs Mediator vs Pub/Sub

| Aspect | Observer | Mediator | Pub/Sub |
|---|---|---|---|
| **Coupling** | Subject knows about the abstract Observer interface | Components know about the Mediator interface | Publisher knows nothing about subscribers |
| **Where logic lives** | Distributed across each Observer's `notify()` | Centralized in the Mediator class | Distributed across handler functions |
| **Registration** | Subject maintains observer list | Mediator holds references to components | Central dictionary maps event types to handlers |
| **Scalability** | One Subject per subsystem, or one bloated Subject | Mediator becomes a God Object as components grow | Flat: add new handler modules without touching existing code |
| **Standardization** | Standardized `notify()` interface | Bespoke `notify(sender, event)` per mediator | Standardized `subscribe()` / `post_event()` |
| **Best for** | Small, isolated subsystems with few observers | UI component coordination (with frameworks) | Application-wide side-effect decoupling |
| **Origin** | Gang of Four (GoF) | Gang of Four (GoF) | Martin Fowler (Event Aggregator) |

**Use Observer** when the observing relationship is small, local, and self-contained -- one subject, a handful of observers.

**Use Mediator** when components need coordinated interaction (e.g., a dialog box where button state depends on text field content). Accept that the mediator class will absorb complexity.

**Use Pub/Sub** for everything else. It is the most flexible, the most decoupled, and the easiest to extend. Start with the in-process `dict`-based implementation and graduate to a cloud Pub/Sub service when the system grows beyond a single process.
