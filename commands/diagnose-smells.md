---
name: diagnose-smells
description: Detect code smells and anti-patterns with fix suggestions
argument-hint: [path]
---

Scan the code at `$ARGUMENTS` (or the current working directory if no path given) for code smells and anti-patterns from the full smell catalog.

## Process

1. **Read the code** — Find and read ALL Python files in the target path recursively.

2. **Check for all smells** — Scan each file against the smell categories:

   **Naming & Identity:** Type abuse, vague identifiers, built-in shadowing, asymmetric naming
   **Structural:** Too many arguments, too many instance vars, redundant variables, parallel data structures, wrong data structure
   **Behavioral:** Boolean flags, deep nesting, tell-don't-ask violations, no-self methods, redefining concepts, missing composition
   **Import & Module:** Wildcard imports, hardwired dependencies, hardwired init sequences

3. **Report each smell found:**
   - **Smell name and category**
   - **File and line**
   - **Severity:** Critical (design flaw) / Important (should fix) / Suggestion (consider fixing)
   - **Before** — the offending code snippet
   - **After** — the suggested fix

4. **Summary** — Show a table at the top:
   ```
   Smell Diagnosis: 12 files scanned, 6 smells found
   ─────────────────────────────────────────────────
   Structural:  Too Many Instance Vars    2 instances  (Important)
   Behavioral:  Boolean Flags             2 instances  (Important)
   Naming:      Vague Identifiers         1 instance   (Suggestion)
   Import:      Hardwired Dependencies    1 instance   (Critical)
   ```

5. **Priority ordering** — Report critical smells first, then important, then suggestions.

For detailed smell explanations and examples, consult:
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/code-smells.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/code-quality.md`
