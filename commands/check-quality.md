---
name: check-quality
description: Quick code quality check against the 22 design rules
argument-hint: [path]
---

Run a focused code quality check on `$ARGUMENTS` (or the current working directory if no path given) against the 22 design rules. This is a lighter, faster check than `/review-architecture`.

## Process

1. **Read the code** — Find and read ALL Python files in the target path recursively.

2. **Check the 22 rules** — For each file, check:

   **Naming & Structure:**
   1. No type abuse (don't embed type in name: `user_list` → `users`)
   2. No vague identifiers (`data`, `info`, `temp`, `result`, `handle`)
   3. No single-letter variables outside comprehensions and lambdas
   4. No abbreviations (`cfg` → `config`, `mgr` → `manager`)

   **Functions:**
   5. No flag parameters (boolean args that switch behavior → split into two functions)
   6. No deep nesting (3+ levels → early returns or extract function)
   7. Tell don't ask (don't query state then act on it — tell the object to act)
   8. Functions do one thing (extract if doing two things)

   **Classes:**
   9. No god classes (too many responsibilities → extract classes)
   10. No parallel data structures (two lists tracking same entities → single dataclass)
   11. Information Expert (methods should live on the class that owns the data)

   **Types & Safety:**
   12. Type hints on all function signatures
   13. Enums for fixed option sets (not bare strings)
   14. No mutable default arguments (`def f(items=[])` → `def f(items=None)`)
   15. No wildcard imports (`from x import *`)

   **Error Handling:**
   16. No broad exception catching (`except Exception` → catch specific exceptions)
   17. Context managers for resources (`with open()` not manual try/finally)

   **Advanced Design:**
   18. No isinstance checks for dispatch (move behavior into the class hierarchy or use a strategy dict)
   19. No overloaded classes (too many instance variables → extract cohesive groups)
   20. No asymmetric naming (consistent method names across similar classes, use dunder methods)
   21. No misleading method names (`create_X` should create and return, `add_X` should add to collection)
   22. No hardwired initialization sequences (factory method or `__init__` guarantees complete setup)

3. **Report findings** — For each violation:
   - **Rule number and name**
   - **File and line**
   - **Fix** — short code snippet showing the correction

   Group by file for easy navigation. Show a summary count at the top:
   ```
   Quality Check: 14 files scanned, 8 issues found
   ─────────────────────────────────────────────────
   Rule 6  (deep nesting):     3 instances
   Rule 12 (missing types):    2 instances
   Rule 16 (broad except):     2 instances
   Rule 5  (flag parameter):   1 instance
   ```

For detailed rule explanations and examples, consult:
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/code-quality.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/types-and-type-hints.md` (for rules 12–13)
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/error-handling.md` (for rules 16–17)
