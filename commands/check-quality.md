---
name: check-quality
description: Quick code quality check against the 17 design rules
argument-hint: [path]
---

Run a focused code quality check on `$ARGUMENTS` (or the current working directory if no path given) against the 17 design rules. This is a lighter, faster check than `/review-architecture`.

## Process

1. **Read the code** — Find and read ALL Python files in the target path recursively.

2. **Check the 17 rules** — For each file, check:

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
   9. No god classes (>200 lines or >5 responsibilities → extract classes)
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
