---
name: extract-god-class
description: Find and split god classes into focused collaborators
argument-hint: [path]
---

Analyze the code at `$ARGUMENTS` (or the current working directory if no path given) for god classes and generate the split.

## Process

1. **Read the code** — Find and read ALL Python files in the target path recursively. Read every `.py` file.

2. **Identify god classes** — A class is a god class if it has any of:
   - Too many distinct responsibilities (doing more than one thing)
   - Methods that cluster into unrelated groups
   - Too many instance variables
   - Methods that don't use most of the class's state

3. **Analyze responsibilities** — For each god class:
   - Group methods by the data they access and the responsibility they serve
   - Identify natural boundaries between responsibilities
   - Determine which methods belong together
   - Name each responsibility group

4. **Propose extraction** — Show:
   - **Original class** — file, line count, responsibilities found
   - **Proposed split** — one new class per responsibility group with:
     - Class name
     - Methods it takes
     - Its `__init__` parameters
     - Complete code for the new class
   - **Updated original** — the slimmed-down class that composes the extracted ones
   - **Updated callers** — any files that need import changes

5. **Ask before applying** — Use AskUserQuestion to confirm the split. The user may want to adjust which methods go where.

6. **Apply changes** — Create the new files and update the original class and its callers.

Principles: P1 High Cohesion, P4 Composition over Inheritance. Consult `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/design-principles.md` for refactoring recipes.
