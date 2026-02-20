# python-clean-architecture

A Claude Code plugin that provides Clean Architecture guidance for Python/FastAPI projects.

## Attribution

The principles, patterns, and architectural approach in this plugin are inspired by and synthesized from [Arjan Codes](https://www.arjancodes.com/)' courses:

- **The Software Designer Mindset** — Seven core design principles (cohesion, coupling, abstractions, composition, creation/use separation, data-first design, simplicity)
- **Pythonic Patterns** — Classic GoF patterns reimagined for Python using Protocol, Callable, functools.partial, and closures
- **Complete Extension** — Three-layer FastAPI architecture (Routers → Operations → Database) with Protocol-based dependency injection

This plugin distills those principles into actionable guidance for Claude Code. It is not a reproduction of course content. If you find this useful, consider supporting Arjan's work at [arjancodes.com](https://www.arjancodes.com/).

## Installation

```
/plugin marketplace add MKToronto/python-clean-architecture
/plugin install python-clean-architecture@python-clean-architecture
```

Or test locally:

```bash
claude --plugin-dir /path/to/python-clean-architecture
```

## Usage

### Automatic (Skill)

The skill triggers automatically when you ask Claude Code to:

- "Scaffold a new FastAPI project"
- "Set up clean architecture"
- "Refactor to clean architecture"
- "Add a new endpoint / router / use case / repository"
- "Review my code structure"
- "Apply design patterns in Python"
- "Decouple my code"
- "Make my code testable"

Or mention: layered architecture, dependency injection, Protocol-based design, Pythonic design patterns.

### Explicit (Slash Command)

```
/review-architecture              Review current directory
/review-architecture src/         Review a specific directory
/review-architecture app/main.py  Review a specific file
```

The review checks:
- **Architecture layers** — Three-layer separation, no layer skipping, router as composition root
- **7 design principles** — Cohesion, coupling, abstractions, composition, creation/use, data-first, simplicity
- **17 code quality rules** — Naming, nesting, types, error handling, imports, structure
- **Pythonic patterns** — Strategy as Callable, Factory as dict mapping, Protocol over ABC

Findings are reported by severity (Critical / Important / Suggestions) with file/line references and fix snippets.

## What's Inside

```
python-clean-architecture/
├── .claude-plugin/plugin.json          Plugin manifest
├── README.md                           This file
├── commands/
│   └── review-architecture.md          /review-architecture slash command
└── skills/
    └── clean-architecture/
        ├── SKILL.md                    Core skill (loaded when triggered)
        ├── references/
        │   ├── design-principles.md    7 principles with refactoring recipes
        │   ├── pythonic-patterns.md    10 pattern recipes (OOP → functional)
        │   ├── layered-architecture.md 3-layer FastAPI guide with full code
        │   ├── testable-api.md         Stub-based testing strategy
        │   └── code-quality.md         17 rules + code review checklist
        └── examples/
            └── fastapi-hotel-api/      Complete working FastAPI project
                ├── main.py
                ├── models/             Pydantic models + DataInterface Protocol
                ├── operations/         Business logic (accepts Protocol)
                ├── routers/            API endpoints (composition root)
                └── db/                 SQLAlchemy + generic DBInterface

```

## Key Concepts

### Three-Layer Architecture

```
Routers (API)  →  Operations (business logic)  →  Database (persistence)
```

Each layer depends only on the layer below. The router is the composition root where concrete DB implementations are injected into operations via the `DataInterface` Protocol.

### Seven Design Principles

1. High Cohesion — Single responsibility per unit
2. Low Coupling — Minimize dependencies, Law of Demeter
3. Depend on Abstractions — Protocol + Callable for DI
4. Composition over Inheritance — Never mixins, shallow hierarchies only
5. Separate Creation from Use — Dict mapping, creator functions, one composition root
6. Start with the Data — Information Expert, fix data structures first
7. Keep Things Simple — DRY, KISS, YAGNI (but avoid hasty abstractions)

### Pythonic Pattern Defaults

- Protocol over ABC (unless shared superclass state needed)
- `functools.partial` over wrapper classes
- Closures over factory class hierarchies
- `Callable` type aliases over single-method abstract classes
- Dict mapping over if/elif chains
- Readability over dogmatic functional purity
