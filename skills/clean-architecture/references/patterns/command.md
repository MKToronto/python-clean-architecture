# Command Pattern Reference

Encapsulate operations as objects (or functions) to gain control over execution: store them, sequence them, undo them, or batch them.

> Content inspired by Arjan Codes' Pythonic Patterns course.

---

## 1. Problem

Direct method calls on domain objects give no control over execution timing, ordering, or reversal. Consider a text processor where the main function directly mutates documents:

```python
from dataclasses import dataclass


@dataclass
class Document:
    title: str
    text: str = ""

    def clear(self) -> None:
        self.text = ""

    def append(self, text: str) -> None:
        self.text += text

    def set_title(self, title: str) -> None:
        self.title = title


def main() -> None:
    doc1 = Document(title="ArjanCodes")
    doc2 = Document(title="Meeting Notes")

    doc1.append("Hello World!")
    doc2.append("The meeting started at 9:00.")
    doc1.set_title("Important Meeting")

    print(doc1)
    print(doc2)
```

This works, but there is no way to:

- **Undo** the title change or the appended text.
- **Batch** several operations into one atomic unit.
- **Sequence** or **delay** operations for later execution.
- **Log** what was done in a replayable history.

The Command pattern solves all of these by turning each operation into a first-class object.

---

## 2. Classic OOP Solution

Define a `Command` Protocol with `execute` and `undo` methods. Implement each operation as a dataclass command. Wire them through a controller that maintains an undo stack.

### Command Protocol and Concrete Commands

```python
from dataclasses import dataclass, field
from typing import Protocol


class Command(Protocol):
    def execute(self) -> None:
        """Execute the command."""

    def undo(self) -> None:
        """Undo the command."""


@dataclass
class AppendText:
    doc: Document
    text: str

    def execute(self) -> None:
        self.doc.append(self.text)

    def undo(self) -> None:
        self.doc.text = self.doc.text[: -len(self.text)]


@dataclass
class Clear:
    doc: Document
    _old_text: str = ""

    def execute(self) -> None:
        self._old_text = self.doc.text
        self.doc.clear()

    def undo(self) -> None:
        self.doc.append(self._old_text)


@dataclass
class ChangeTitle:
    doc: Document
    title: str
    _old_title: str = ""

    def execute(self) -> None:
        self._old_title = self.doc.title
        self.doc.set_title(self.title)

    def undo(self) -> None:
        self.doc.set_title(self._old_title)
```

Each command stores the receiver (`doc`) and any arguments needed for execution. For undo support, commands that destroy information (like `Clear` and `ChangeTitle`) capture the old state in `execute` before mutating.

### Controller with Undo Stack

```python
@dataclass
class TextController:
    undo_stack: list[Command] = field(default_factory=list)

    def execute(self, command: Command) -> None:
        command.execute()
        self.undo_stack.append(command)

    def undo(self) -> None:
        if not self.undo_stack:
            return
        command = self.undo_stack.pop()
        command.undo()

    def undo_all(self) -> None:
        while self.undo_stack:
            self.undo()
```

The controller knows nothing about concrete commands. It works exclusively through the `Command` Protocol, so any new command integrates without changes to the controller.

### Usage

```python
def main() -> None:
    controller = TextController()

    doc1 = Document(title="ArjanCodes")
    doc2 = Document(title="Meeting Notes")

    controller.execute(AppendText(doc1, "Hello World!"))
    controller.execute(AppendText(doc2, "The meeting started at 9:00."))
    controller.execute(ChangeTitle(doc1, "Important Meeting"))

    print(doc1)  # Document(title='Important Meeting', text='Hello World!')
    print(doc2)  # Document(title='Meeting Notes', text='The meeting started at 9:00.')

    controller.undo()  # undoes ChangeTitle
    print(doc1)  # Document(title='ArjanCodes', text='Hello World!')

    controller.undo_all()  # undoes remaining commands
    print(doc1)  # Document(title='ArjanCodes', text='')
    print(doc2)  # Document(title='Meeting Notes', text='')
```

---

## 3. Batch / Composite

Treat a batch of commands as a single command. Execute runs every command in order. Undo reverses them in the opposite order, so the most recently applied change unwinds first.

```python
@dataclass
class Batch:
    commands: list[Command] = field(default_factory=list)

    def execute(self) -> None:
        for command in self.commands:
            command.execute()

    def undo(self) -> None:
        for command in reversed(self.commands):
            command.undo()
```

Because `Batch` satisfies the `Command` Protocol, the controller can execute it (and undo it) as a single unit:

```python
def main() -> None:
    controller = TextController()

    doc1 = Document(title="ArjanCodes")
    doc2 = Document(title="Meeting Notes")

    controller.execute(
        Batch(
            commands=[
                AppendText(doc1, "Hi there!"),
                ChangeTitle(doc1, "Important Meeting"),
                Clear(doc2),
            ]
        )
    )

    print(doc1)  # Document(title='Important Meeting', text='Hi there!')
    print(doc2)  # Document(title='Meeting Notes', text='')

    controller.undo()  # undoes the entire batch in reverse order
    print(doc1)  # Document(title='ArjanCodes', text='')
    print(doc2)  # Document(title='Meeting Notes', text='')
```

Batches can nest inside other batches, forming a composite tree. The controller still sees a single command.

---

## 4. Pythonic Progression

Replace command classes with functions that return undo closures. Each function performs its action immediately and returns a callable that reverses it. The closure captures all state it needs from the enclosing scope.

### Type Aliases

```python
from typing import Callable

UndoFunction = Callable[[], None]
CommandFunction = Callable[[], UndoFunction]
```

`UndoFunction` is a zero-argument callable that reverses one operation. `CommandFunction` is a zero-argument callable that performs an operation and returns its undo.

### Command Functions

```python
def append_text(doc: Document, text: str) -> UndoFunction:
    doc.append(text)

    def undo() -> None:
        doc.text = doc.text[: -len(text)]

    return undo


def clear_text(doc: Document) -> UndoFunction:
    old_text = doc.text
    doc.clear()

    def undo() -> None:
        doc.append(old_text)

    return undo


def change_title(doc: Document, title: str) -> UndoFunction:
    old_title = doc.title
    doc.set_title(title)

    def undo() -> None:
        doc.set_title(old_title)

    return undo
```

Each function performs the action, then defines and returns an inner `undo` closure. The closure has access to the enclosing scope -- `old_text`, `old_title`, `text`, `doc` -- so it carries all the context it needs without a class.

### Direct Usage

Call a command function. Store the returned undo. Call the undo whenever reversal is needed:

```python
def main() -> None:
    doc1 = Document(title="ArjanCodes")
    doc2 = Document(title="Meeting Notes")

    undo_append1 = append_text(doc1, "Hello World!")
    undo_append2 = append_text(doc2, "The meeting started at 9:00.")
    undo_change_title = change_title(doc1, "Important Meeting")

    print(doc1)  # Document(title='Important Meeting', text='Hello World!')

    undo_change_title()
    print(doc1)  # Document(title='ArjanCodes', text='Hello World!')
```

No controller needed. The undo function itself is the only artifact.

### Batch via List Comprehension

Use `functools.partial` to pre-bind arguments, producing zero-argument `CommandFunction` callables. Pass them to a `batch` function that executes all commands and returns a single undo:

```python
from functools import partial


def batch(commands: list[CommandFunction]) -> UndoFunction:
    undo_fns = [cmd() for cmd in commands]

    def undo() -> None:
        for undo_fn in reversed(undo_fns):
            undo_fn()

    return undo
```

The list comprehension `[cmd() for cmd in commands]` executes every command and collects the undo functions. The returned `undo` closure calls them in reverse order.

### Batch Usage with `functools.partial`

```python
def main() -> None:
    doc1 = Document(title="ArjanCodes")
    doc2 = Document(title="Meeting Notes")

    undo_append1 = append_text(doc1, "Hello World!")
    undo_append2 = append_text(doc2, "The meeting started at 9:00.")
    undo_change_title = change_title(doc1, "Important Meeting")

    # execute a batch of commands
    undo_batch = batch([
        partial(append_text, doc=doc1, text="Hi there!"),
        partial(clear_text, doc=doc2),
    ])

    print(doc1)  # text is now 'Hello World!Hi there!'
    print(doc2)  # text is now ''

    undo_batch()  # undoes the entire batch in reverse order
    print(doc1)  # text is back to 'Hello World!'
    print(doc2)  # text is back to 'The meeting started at 9:00.'
```

`partial(append_text, doc=doc1, text="Hi there!")` creates a zero-argument callable. When `batch` calls `cmd()`, it calls `append_text(doc=doc1, text="Hi there!")` and receives the undo function back.

---

## 5. When to Use

Reach for the Command pattern when you see these signals:

- **Undo/redo is required.** Users need to reverse operations (text editors, drawing apps, form wizards).
- **Operations must be queued or scheduled.** Commands execute later, not at the call site (task queues, job runners).
- **Audit trail or logging of actions.** Each command object/function call can be serialized or logged.
- **Batch or transactional execution.** Multiple operations must succeed or roll back together.
- **Macro recording.** Users record a sequence of actions for replay.
- **Decoupling invoker from receiver.** The controller/UI does not know what concrete operation it triggers.

---

## 6. Trade-offs

### OOP Version (Protocol + Dataclass Commands)

**Better when:**
- Commands carry complex state that evolves over their lifetime (multiple internal fields for undo).
- You need to serialize commands (dataclass fields map cleanly to JSON/database rows).
- The command lifecycle matters: you inspect, modify, or extend commands after creation.
- Team members are more comfortable with class-based patterns.

**Costs:**
- One class per operation. Boilerplate grows linearly with the number of commands.
- The Protocol, controller, and each command class must stay in sync.

### Functional Version (Functions Returning Undo Closures)

**Better when:**
- Commands are simple (one action, one undo).
- You want to add new commands quickly -- each is a standalone function.
- `functools.partial` naturally fits how you configure arguments.
- You prefer less code and no class hierarchy.

**Costs:**
- Closures are opaque. You cannot inspect internal state after creation (no `command._old_title`).
- Debugging is harder when the undo function is an anonymous closure deep in a call stack.
- Serialization requires extra work (closures are not directly picklable).

### Rule of Thumb

Start with the functional version. Promote to the OOP version when you need inspectable state, serialization, or the command lifecycle grows beyond "execute and undo."
