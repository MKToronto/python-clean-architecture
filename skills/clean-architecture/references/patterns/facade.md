# Facade Pattern

**Recognize:** Your application code (GUI, controllers, API endpoints) is tightly coupled to a complex subsystem — creating connections, constructing messages, managing devices, handling low-level protocols. Changes in the subsystem force changes throughout the application.

**Problem:** The client code needs to know implementation details of the subsystem (network connections, message formats, device registration). This creates high coupling, low cohesion, and makes the code hard to extend.

---

## Pythonic Implementation: Simplified Interface Class

A Facade is a class that sits between your application and a complex subsystem, exposing a small number of high-level methods that hide the subsystem's complexity.

### Before: Client Coupled to Subsystem

```python
class SmartApp:
    def __init__(self) -> None:
        self.service = IoTService()
        self.speaker = SmartSpeaker(id="speaker_1")
        self.service.register_device(self.speaker)

    def toggle_speaker(self, on: bool) -> None:
        device = self.service.get_device(self.speaker.id)
        connection = Connection(device.ip, device.port)
        message = Message(sender=self.speaker.id, content="switch_on" if on else "switch_off")
        connection.send(message.to_b64())
        logging.info("Message sent")

    def get_status(self) -> str:
        status = ""
        for device in self.service.devices:
            status += f"{device.id}: active\n"
        return status
```

The GUI knows about `IoTService`, `SmartSpeaker`, `Connection`, `Message`, `to_b64()` — all low-level details it shouldn't care about.

### After: Facade Hides Subsystem

```python
class IoTFacade:
    def __init__(self, service: IoTService) -> None:
        self.service = service
        self.speaker = SmartSpeaker(id="speaker_1")
        self.service.register_device(self.speaker)

    def power_speaker(self, on: bool) -> None:
        message = "switch_on" if on else "switch_off"
        device = self.service.get_device(self.speaker.id)
        connection = Connection(device.ip, device.port)
        msg = Message(sender=self.speaker.id, content=message)
        connection.send(msg.to_b64())

    def get_status(self) -> str:
        status = ""
        for device in self.service.devices:
            status += f"{device.id}: active\n"
        return status
```

All subsystem complexity is centralized in the Facade. The rest of the application only interacts with `power_speaker()` and `get_status()`.

---

## Connecting Facade to Controllers with `functools.partial`

The controller functions need the facade, but the GUI only wants simple callbacks. Use `functools.partial` to bind the facade argument:

**Controller functions (business logic + logging):**

```python
import logging

def power_speaker(iot: IoTFacade, on: bool) -> None:
    logging.info(f"Powering speaker {'on' if on else 'off'}")
    iot.power_speaker(on)
    logging.info("Message sent to speaker")

def get_status(iot: IoTFacade) -> str:
    logging.info("Retrieving status")
    return iot.get_status()
```

**Composition root (main function):**

```python
from functools import partial

def main() -> None:
    service = IoTService()
    facade = IoTFacade(service)

    # Bind facade to controller functions — GUI gets simple signatures
    power_fn = partial(power_speaker, facade)    # Callable[[bool], None]
    status_fn = partial(get_status, facade)      # Callable[[], str]

    app = SmartApp(
        power_speaker_function=power_fn,
        get_status_function=status_fn,
    )
    app.mainloop()
```

**GUI only knows about callbacks:**

```python
from typing import Callable

class SmartApp:
    def __init__(
        self,
        power_speaker_function: Callable[[bool], None],
        get_status_function: Callable[[], str],
    ) -> None:
        self.power_speaker_fn = power_speaker_function
        self.get_status_fn = get_status_function

    def toggle(self) -> None:
        self.speaker_on = not self.speaker_on
        self.power_speaker_fn(self.speaker_on)

    def display_status(self) -> None:
        status = self.get_status_fn()
        self.status_label.config(text=status)
```

The GUI is fully decoupled from the IoT subsystem. It has no imports from `iot/`, `network/`, or `message/`.

---

## Architecture: Facade + MVC

The Facade works naturally with MVC (or our Routers → Operations → Database architecture):

```
GUI (View)  →  Controller Functions  →  Facade  →  Subsystem
```

- **GUI** handles display and user input only
- **Controllers** handle logging, orchestration, cross-cutting concerns
- **Facade** provides a simplified interface to the complex subsystem
- **Subsystem** contains the actual implementation details

This maps to our three-layer architecture: the Facade sits at the Database layer boundary, providing a clean interface that Operations can use.

---

## When to Use

- **Complex subsystem** with many classes, connections, and protocols that the application shouldn't know about
- **Multiple clients** need the same simplified access to a subsystem
- **Decoupling application from infrastructure** — database systems, external APIs, IoT services, messaging systems
- **Reducing import dependencies** — after introducing a Facade, client modules only import the Facade

## When NOT to Use

- **Subsystem is already simple** — adding a Facade over a single class adds indirection without value
- **Client genuinely needs fine-grained control** — the Facade's simplification would be limiting
- **Rapidly changing subsystem API** — the Facade must be updated for every change, negating the benefit

## Trade-offs

- **Pro:** Centralizes subsystem interaction — changes to the subsystem only require updating the Facade
- **Pro:** Client code becomes cleaner with fewer imports and simpler function signatures
- **Con:** Adding new subsystem features requires extending the Facade
- **Con:** Can become a god class if too many subsystem operations are exposed — keep the interface focused

## Relationship to Other Patterns

- **Adapter** translates one interface to another. **Facade** simplifies a complex interface into a smaller one.
- **Separate Creation from Use** — the Facade is created in the composition root (main function) and injected into controllers via `partial`.
- **Low Coupling principle** — Facade is a concrete technique for reducing coupling between application layers and complex subsystems.
