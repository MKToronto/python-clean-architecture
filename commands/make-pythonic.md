---
name: make-pythonic
description: Refactor code to use Pythonic patterns
argument-hint: [path]
---

Analyze the code at `$ARGUMENTS` (or the current working directory if no path given) and apply Pythonic pattern replacements.

## Process

1. **Read the code** — Find and read ALL Python files in the target path recursively. Read every `.py` file.

2. **Identify non-Pythonic patterns** — Look for these specific code smells:

   | Code Smell | Replace With |
   |---|---|
   | ABC/abstract base class hierarchy | Protocol (structural typing) |
   | Single-method abstract class | `Callable` type alias |
   | Deep class inheritance / mixins | Composition with Protocol interface |
   | Wrapper classes for configuration | `functools.partial` |
   | Factory class hierarchies | Closures or tuples of functions + `partial` |
   | Long if/elif switching behavior | Strategy pattern — pass functions as args |
   | if/elif for object creation | Registry pattern — `dict[str, Callable]` mapping |
   | Inline notification side effects | Pub/Sub — `subscribe(event, handler)` / `post_event()` |
   | Duplicated algorithm across classes | Template Method — free function + Protocol parameter |
   | try/finally for resource cleanup | Context managers |
   | Manual `__init__` for data holders | `@dataclass` |
   | Bare string constants for options | `Enum` or `StrEnum` |

3. **Propose changes** — For each finding, show:
   - **File and line**
   - **Current pattern** — what it does now
   - **Pythonic replacement** — what it should become
   - **Before/after code** — complete snippets ready to apply

4. **Ask before applying** — Use AskUserQuestion to confirm: "Apply these changes?" Let the user review before any edits.

5. **Apply changes** — Edit the files with the approved refactorings.

For detailed pattern guidance, consult:
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/pythonic-patterns.md` (quick lookup table for all 25 patterns)
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/classes-and-dataclasses.md` (for class → dataclass conversions)
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/decorators.md` (for decorator patterns)
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/context-managers.md` (for try/finally → context manager conversions)
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/patterns/` (full OOP → functional progressions per pattern)
