---
name: suggest-patterns
description: Scan code and recommend Pythonic design patterns
argument-hint: [path]
---

Scan the code at `$ARGUMENTS` (or the current working directory if no path given) and recommend which of the 11 Pythonic design patterns would improve it.

## Process

1. **Read the code** — Find and read ALL Python files in the target path recursively.

2. **Match code smells to patterns** — Look for these specific smells:

   | Code Smell | Pattern | Pythonic Implementation |
   |---|---|---|
   | Long if/elif switching behavior | **Strategy** | `Callable` type alias, pass functions as args |
   | Need to create families of related objects | **Abstract Factory** | Tuples of functions + `functools.partial` |
   | Two independent hierarchies that vary | **Bridge** | `Callable` type alias replaces abstract reference |
   | Need undo/batch/queue operations | **Command** | Functions returning undo closures |
   | Side effects mixed with core logic | **Pub/Sub** | Dict-based `subscribe(event, handler)` / `post_event()` |
   | Object creation from config/JSON data | **Registry** | `dict[str, Callable]` mapping + `**kwargs` unpacking |
   | Same algorithm duplicated across classes | **Template Method** | Free function + Protocol parameter |
   | Sequential data transformations | **Pipeline** | `functools.reduce` for composition |
   | Need to react to events without coupling | **Callback** | Function passed as argument |
   | Reusing a function with a different interface | **Function Wrapper** | Wraps another function, translates args |
   | Separating configuration from usage | **Function Builder** | Higher-order function returns configured function |

3. **Report suggestions** — For each match, show:
   - **File and line** — where the smell is
   - **Code smell** — what makes this a candidate
   - **Pattern** — which pattern applies and why
   - **Before** — current code snippet
   - **After** — refactored code using the Pythonic implementation
   - **Trade-off** — is the refactoring worth it here? (sometimes the simple version is fine)

4. **Prioritize** — Order suggestions by impact. A pattern that simplifies 50 lines beats one that saves 3 lines. Note when the current code is simple enough that applying a pattern would be over-engineering.

For full pattern progressions (OOP → functional), consult `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/patterns/`.
