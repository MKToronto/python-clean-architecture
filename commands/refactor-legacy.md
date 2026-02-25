---
name: refactor-legacy
description: Plan a safe refactoring path for untested legacy code
argument-hint: [path]
---

Analyze the code at `$ARGUMENTS` (or the current working directory if no path given) and produce a step-by-step refactoring plan with testability as the first goal.

## Process

1. **Read the code** — Find and read ALL Python files in the target path recursively.

2. **Identify testability blockers** — Look for:
   - Global state and module-level side effects
   - Hardcoded dependencies (`self.x = ConcreteClass()`)
   - Mixed I/O and business logic (print/input in logic classes)
   - Missing abstractions (no Protocol interfaces)
   - Complex `__init__` methods with setup logic
   - Functions with inconsistent return types

3. **Identify code smells** — Scan for recurring refactoring opportunities:
   - Deep nesting (→ guard clauses)
   - Magic numbers (→ named constants)
   - String comparisons (→ Enums)
   - Scattered if/elif chains (→ data-driven rules)
   - Raw data structures (→ domain classes)
   - Catch-all exception handling (→ specific catches)

4. **Produce a phased plan:**

   **Phase 1: Add characterization tests**
   - Capture current behavior with pinning tests
   - Don't fix anything yet — just lock down what exists

   **Phase 2: Extract pure logic from side effects**
   - Separate UI/IO from business logic
   - Move print/input into dedicated classes
   - Extract named helper functions from complex conditions

   **Phase 3: Introduce Protocol interfaces**
   - Define Protocol for external dependencies
   - Apply dependency injection at the composition root
   - Create stubs for testing

   **Phase 4: Add proper unit tests**
   - Test extracted pure logic with stubs
   - Verify business rules independently of I/O

5. **For each phase**, show specific before/after code snippets from the actual codebase.

References:
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/refactoring-case-studies.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/testing-legacy-code.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/code-smells.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/dependency-injection.md`
