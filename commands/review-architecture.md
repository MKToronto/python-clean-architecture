---
name: review-architecture
description: Review code against Python Clean Architecture principles
argument-hint: [path]
---

Review the code at `$ARGUMENTS` (or the current working directory if no path given) against Python Clean Architecture principles.

## Review Process

1. **Read the code** — Find and read ALL Python files in the target path recursively. Read every `.py` file — do not skip any. Understand the project structure, imports, and relationships between files.

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
   - Pub/Sub for notification side effects, not inline calls
   - Registry for data-driven object creation, not if/elif
   - Context managers for resource management, not try/finally
   - Custom exception classes, not broad except catching
   - Dataclasses for value objects and DTOs, not manual __init__
   - Pure functions where possible, side effects pushed to boundaries

6. **Check code cleanup opportunities** — Look for concrete refactoring targets:
   - Extract class when a class does two things
   - Extract function when a function does two things
   - Replace mutable globals with injected dataclass context
   - Replace boolean flag parameters with separate functions
   - Replace string constants with Enums
   - Replace deep nesting (3+ levels) with early returns or extraction
   - Replace god classes (>200 lines, >5 responsibilities) with collaborators
   - Move methods to the class that owns the data (Information Expert)
   - Replace parallel data structures with a single data class
   - Replace if/elif chains with dict mapping

7. **Report findings** — Structure the output in this order:

   ### Architecture Summary Diagram
   Open with an ASCII diagram showing the actual dependency flow discovered in the project. Map real file/module names onto the three-layer model. Show which modules depend on which, and flag any arrows that violate the layer rules. Example format:

   ```
   Routers (API)          Operations (logic)      Database (persistence)
   ─────────────          ──────────────────      ─────────────────────
   routers/booking.py  →  operations/booking.py →  db/db_interface.py
   routers/customer.py →  operations/customer.py    db/models.py
                                                     db/database.py

   ⚠ routers/admin.py → db/models.py  (layer skip — should go through operations)
   ```

   Adapt the diagram to the actual project structure. If the project does not follow the three-layer model, show the dependency flow as-is and note what a target architecture would look like.

   ### What Works Well
   Call out specific things the code does right. Reference files and patterns. Examples:
   - Clean layer separation with no direct DB imports in routers
   - Good use of Protocol-based DataInterface for dependency injection
   - Consistent Pydantic model separation (Create vs Read)
   - Effective use of dataclasses for value objects
   - Pure functions in operations with side effects at boundaries
   - Meaningful naming, good type hint coverage

   This section builds trust and avoids a purely negative tone. Be specific — cite actual files and lines, not generic praise.

   ### Findings by Severity
   Present issues organized by severity:
   - **Critical** — Layer violations, missing abstractions, tight coupling to concrete DB
   - **Important** — Cohesion issues, Law of Demeter violations, missing type hints
   - **Suggestions** — Pattern improvements, naming, simplification opportunities, cleanup refactorings

   For each finding, reference the specific file and line, explain the principle violated, and show the recommended fix with a code snippet. Prioritize actionable cleanup suggestions over architectural observations.

Load `references/design-principles.md`, `references/code-quality.md`, `references/error-handling.md`, and `references/pythonic-patterns.md` from the clean-architecture skill for review checklists. For detailed pattern guidance (when explaining HOW to fix), consult the relevant files in `references/patterns/`.
