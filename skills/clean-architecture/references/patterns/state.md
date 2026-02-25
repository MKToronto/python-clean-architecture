# State Pattern

**Recognize:** An object behaves differently depending on its internal state, and you have growing if/elif chains checking the current state before every action.

**Problem:** All state-specific behavior lives in one class, leading to low cohesion and complex conditionals. Adding a new state means modifying every method that checks state.

---

## Pythonic Implementation: Protocol-Based State Objects

Define a Protocol for the state interface. Each concrete state is a separate class that implements the Protocol and encapsulates the behavior for that state. The context object delegates to its current state.

### Step 1: Define the State Protocol

```python
from typing import Protocol

class DocumentState(Protocol):
    def edit(self, doc: "DocumentContext") -> None: ...
    def review(self, doc: "DocumentContext") -> None: ...
    def finalize(self, doc: "DocumentContext") -> None: ...
```

The state methods receive the context object so they can trigger state transitions.

### Step 2: Implement Concrete States

```python
class DraftState:
    def edit(self, doc: "DocumentContext") -> None:
        doc.content.append("New content added.")
        print("Editing document.")

    def review(self, doc: "DocumentContext") -> None:
        doc.state = ReviewedState()
        print("Document submitted for review.")

    def finalize(self, doc: "DocumentContext") -> None:
        print("Cannot finalize — document must be reviewed first.")


class ReviewedState:
    def edit(self, doc: "DocumentContext") -> None:
        print("Cannot edit — document is under review.")

    def review(self, doc: "DocumentContext") -> None:
        print("Document is already under review.")

    def finalize(self, doc: "DocumentContext") -> None:
        doc.state = FinalizedState()
        print("Document finalized.")


class FinalizedState:
    def edit(self, doc: "DocumentContext") -> None:
        print("Cannot edit — document is finalized.")

    def review(self, doc: "DocumentContext") -> None:
        print("Cannot review — document is finalized.")

    def finalize(self, doc: "DocumentContext") -> None:
        print("Document is already finalized.")
```

Each state class has a single responsibility: the behavior for that state. No class needs to know about the others' logic.

### Step 3: The Context Object

```python
class DocumentContext:
    def __init__(self) -> None:
        self.state: DocumentState = DraftState()
        self.content: list[str] = []

    def edit(self) -> None:
        self.state.edit(self)

    def review(self) -> None:
        self.state.review(self)

    def finalize(self) -> None:
        self.state.finalize(self)
```

The context delegates every action to its current state. State transitions happen inside the state objects themselves by assigning a new state to `doc.state`.

### Usage

```python
doc = DocumentContext()
doc.edit()       # "Editing document."
doc.finalize()   # "Cannot finalize — document must be reviewed first."
doc.review()     # "Document submitted for review."
doc.edit()       # "Cannot edit — document is under review."
doc.finalize()   # "Document finalized."
doc.edit()       # "Cannot edit — document is finalized."
```

---

## Simpler Version: Light Bulb Toggle

For trivial two-state systems, the same pattern applies at smaller scale:

```python
class LightState(Protocol):
    def switch(self, bulb: "LightBulb") -> None: ...

class OnState:
    def switch(self, bulb: "LightBulb") -> None:
        bulb.state = OffState()
        print("Light turned off.")

class OffState:
    def switch(self, bulb: "LightBulb") -> None:
        bulb.state = OnState()
        print("Light turned on.")

class LightBulb:
    def __init__(self) -> None:
        self.state: LightState = OnState()

    def switch(self) -> None:
        self.state.switch(self)
```

---

## Module-Based Alternative

Since you often need only one instance of each state, you can use modules with functions instead of classes:

```python
# states/draft.py
def edit(doc: "DocumentContext") -> None:
    doc.content.append("New content.")

def review(doc: "DocumentContext") -> None:
    from states import reviewed
    doc.state = reviewed

def finalize(doc: "DocumentContext") -> None:
    print("Cannot finalize — review first.")
```

Each module acts as a singleton state. The context stores a module reference instead of a class instance. This is more Pythonic for simple cases but loses the Protocol-based type checking.

---

## When to Use

- **Object has distinct behavioral modes** — editing vs. reviewing vs. finalized; playing vs. paused vs. game-over
- **State-specific logic is growing** — each state has many actions, and putting everything in one class creates a god class
- **State transitions follow rules** — not every transition is valid (can't finalize without reviewing first)
- **Game development** — game screens (title, playing, paused, game-over) are classic State pattern territory

## When NOT to Use

- **Only two states with trivial behavior** — a simple boolean flag is enough
- **Framework handles state** — many GUI and game frameworks have built-in state machines
- **No behavioral differences between states** — if the object always does the same thing regardless of state, you don't need this pattern

## Relationship to Other Patterns

- **Strategy** selects an algorithm; **State** selects behavior based on internal state that changes over time. Both use Protocol-based delegation, but State objects trigger their own transitions.
- **Separate Creation from Use** — the initial state is wired in the context constructor (composition root).
