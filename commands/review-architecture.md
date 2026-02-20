---
name: review-architecture
description: Review code against Python Clean Architecture principles
argument-hint: [path]
---

Review the code at `$ARGUMENTS` (or the current working directory if no path given) against Python Clean Architecture principles.

## Review Process

1. **Read the code** — Scan all Python files in the target path. Understand the project structure, imports, and relationships.

2. **Check architecture layers** — Verify the three-layer separation:
   - Routers (API) → Operations (business logic) → Database (persistence)
   - No layer skipping (routers should not import DB modules directly)
   - Operations accept `DataInterface` Protocol, not concrete DB classes
   - Router acts as composition root (wires concrete implementations)

3. **Check the 7 design principles** — For each file/class/function, evaluate:
   - **High Cohesion** — Does each unit have a single responsibility?
   - **Low Coupling** — Are dependencies minimized? Any Law of Demeter violations?
   - **Depend on Abstractions** — Protocol/Callable used for DI? Or concrete imports?
   - **Composition over Inheritance** — Any deep hierarchies or mixins?
   - **Separate Creation from Use** — One composition root? Dict mapping over if/elif?
   - **Start with the Data** — Prefixed fields? Parallel lists? Methods far from data?
   - **Keep Things Simple** — Over-engineered? Speculative features? Unnecessary abstractions?

4. **Check code quality** — Apply the 17 design rules:
   - No type abuse, vague identifiers, flag parameters, deep nesting
   - Tell don't ask, no parallel data structures, no god classes
   - No broad exception catching, no mutable defaults, no wildcard imports
   - Type hints on all functions, enums for fixed options, context managers for resources

5. **Check Pythonic patterns** — Are patterns implemented the Pythonic way?
   - Strategy as Callable, not ABC hierarchy
   - Factory as dict mapping, not if/elif
   - Protocol over ABC (unless shared state needed)
   - functools.partial for configuration, closures for builders

6. **Report findings** — Present results organized by severity:
   - **Critical** — Layer violations, missing abstractions, tight coupling to concrete DB
   - **Important** — Cohesion issues, Law of Demeter violations, missing type hints
   - **Suggestions** — Pattern improvements, naming, simplification opportunities

For each finding, reference the specific file and line, explain the principle violated, and show the recommended fix with a code snippet.

Load `references/design-principles.md`, `references/code-quality.md`, `references/error-handling.md`, and the relevant pattern files from `references/patterns/` for detailed guidance.
