# Project Organization Reference

Structure a Python project so that any stakeholder can navigate it by intuition. The folder hierarchy is the first architectural statement a project makes.

## 1. Modules and Packages

Every `.py` file is a **module**. Every folder containing an `__init__.py` is a **package**.

### Rules

- Always create an `__init__.py` in every package folder. Without it, Python will not recognize the folder as a package and imports will break.
- Add an `__init__.py` in every subfolder (sub-package) as well. Missing one at any level breaks the import chain.
- Keep `__init__.py` files empty. You can use them to re-export symbols, but this is rarely necessary and adds indirection.
- Name modules and packages with lowercase_snake_case. Never use hyphens or spaces.

### Basic Structure

```
src/
    __init__.py
    main.py
    customers/
        __init__.py
        models.py
        operations.py
    contracts/
        __init__.py
        models.py
        operations.py
        sub_package/
            __init__.py
            validation.py
```

### What Modules and Packages Give You

- **Modules** let you group related functions, classes, and constants into a single file with a meaningful name.
- **Packages** let you group related modules into a folder hierarchy that mirrors how the application is conceptually organized.
- **Sub-packages** let you nest further when a package grows large enough to warrant subdivision.

---

## 2. Import Conventions

### Absolute Imports (Preferred)

Use the full package path from the project root. Absolute imports are explicit about where things come from and work identically regardless of which file contains them.

```python
# GOOD: absolute import — clear origin
from customers.models import Customer
from contracts.operations import create_contract
```

### Relative Imports (Within a Package Only)

Use dot notation to import from sibling modules or parent packages. One dot means "same package," two dots means "parent package," and so on.

```python
# Inside contracts/operations.py, importing from contracts/models.py
from .models import Contract

# Inside contracts/sub_package/validation.py, importing from contracts/models.py
from ..models import Contract
```

Relative imports are **not allowed between top-level packages**. This will fail:

```python
# WRONG: relative import across packages
# Inside contracts/operations.py trying to reach customers/
from ..customers.models import Customer  # ImportError

# CORRECT: use absolute import instead
from customers.models import Customer
```

### Aliased Imports

Use aliases when fully-qualified names are long or when a well-known convention exists.

```python
import numpy as np
import pandas as pd
from customers import models as customer_models
```

### Import Style Summary

| Style | Example | When to Use |
|---|---|---|
| `from package.module import name` | `from customers.models import Customer` | Default choice. Explicit and concise. |
| `import package.module` | `import customers.models` | When you use many names from the module and want `customers.models.Customer` for clarity. |
| `from .module import name` | `from .models import Contract` | Within the same package for sibling imports. |
| `import package.module as alias` | `import customers.models as cm` | When the fully-qualified name is too long. |

---

## 3. Anti-Patterns

### Never Use Wildcard Imports

```python
# NEVER do this
from customers.models import *
```

Wildcard imports dump every public name from a module into the current namespace. With larger modules and multiple wildcard imports, it becomes impossible to tell which function came from which module. Refactoring becomes dangerous because you cannot trace dependencies by reading the import block.

Always import specific names:

```python
# GOOD: explicit about what you need
from customers.models import Customer, CustomerStatus
```

### Never Name Packages "utils", "managers", or "handlers"

These names are symptoms of incomplete design thinking. They signal that you have not figured out where something belongs.

```
# BAD: "utils" is a junk drawer
src/
    utils/
        helpers.py        # helpers for what?
        misc.py           # miscellaneous what?
        common.py         # common to what?

# BAD: "managers" tells you nothing about the domain
src/
    managers/
        data_manager.py
        user_manager.py
```

A `utils` folder inevitably becomes a kitchen sink where unrelated functions accumulate. Instead, identify what those functions actually do and place them in the package where they belong.

```
# GOOD: each function lives in its domain
src/
    customers/
        validation.py     # was "utils/validate_customer.py"
        formatting.py     # was "utils/format_address.py"
    pricing/
        calculations.py   # was "utils/calculate_discount.py"
```

If you cannot find a home for a function, that is a design signal. The function either belongs in an existing domain package or reveals a missing domain concept that deserves its own package.

---

## 4. Organizing by Domain

Structure packages around business domains, not around technical types. The folder tree should read like a table of contents for the application, not like a programming textbook.

### Architecture-First (by Technical Type)

```
src/
    models/
        customer.py
        contract.py
        invoice.py
    services/
        customer_service.py
        contract_service.py
        invoice_service.py
    repositories/
        customer_repo.py
        contract_repo.py
        invoice_repo.py
```

Top-level folders represent architectural layers. This is the approach used in the skill's scaffolding template and the paid course. It makes the architecture immediately visible.

**Trade-off:** A developer working on "contracts" must jump between three folders.

### Domain-First (by Business Domain)

```
src/
    customers/
        models.py
        operations.py
        repository.py
    contracts/
        models.py
        operations.py
        repository.py
    invoices/
        models.py
        operations.py
        repository.py
```

Top-level folders represent business domains. All contract-related code lives together — a developer can understand the contracts domain by reading one folder.

**Trade-off:** The architecture is less visible at the top level; each domain folder must replicate the same internal structure.

### Domain Grouping Examples

**UI Components** — Group by interaction purpose, not by widget type:

```
ui/
    input/          # text fields, dropdowns, checkboxes
    navigation/     # menus, breadcrumbs, tabs
    layout/         # grids, containers, sidebars
    feedback/       # alerts, dialogs, toasts, progress bars
    data_display/   # tables, lists, cards, charts
```

**Business Operations** — Group by domain area:

```
operations/
    customers/      # create, update, delete customers
    contracts/      # create, send, sign contracts
    billing/        # generate invoices, process payments
```

**Data Processing** — Group by direction:

```
importers/
    csv_importer.py
    database_importer.py
    json_importer.py
exporters/
    csv_exporter.py
    excel_exporter.py
    pdf_exporter.py
```

**Web Pages or API Routes** — Mirror the URL structure:

```
# If your API has routes: /auth, /users, /data
routes/
    auth/
        login.py
        register.py
    users/
        profile.py
        settings.py
    data/
        upload.py
        export.py
```

When the folder structure mirrors the application's own structure (its URL paths, its domain concepts, its UI layout), any stakeholder can locate code by reasoning about the product rather than about implementation details.

---

## 5. Architecture-Driven Structure

Let the chosen software architecture dictate the top-level folder hierarchy. When someone opens the project, the folder names should immediately communicate which architecture is in use.

### MVC (Model-View-Controller)

```
src/
    models/         # data representations
    views/          # UI templates, rendering
    controllers/    # business logic, request handling
```

### Data Pipeline

```
src/
    pipeline_elements/
        ingest.py
        transform.py
        validate.py
        load.py
    pipeline.py     # orchestrates the elements
```

### Clean Architecture (FastAPI Example)

```
src/
    routers/        # HTTP layer — request/response handling
        customers.py
        contracts.py
    operations/     # business logic — pure domain rules
        customers.py
        contracts.py
    db/             # persistence layer — database access
        customers.py
        contracts.py
    models/         # shared data structures (Pydantic, dataclasses)
        customers.py
        contracts.py
```

### Choosing Between Domain-First and Architecture-First

These two strategies are not mutually exclusive. Use architecture-driven top-level folders, then organize by domain within each layer:

```
src/
    routers/
        customers.py      # domain within architectural layer
        contracts.py
    operations/
        customers.py
        contracts.py
    db/
        customers.py
        contracts.py
```

Or use domain-driven top-level folders, then separate by architectural layer within each domain:

```
src/
    customers/
        router.py         # architectural layer within domain
        operations.py
        db.py
        models.py
    contracts/
        router.py
        operations.py
        db.py
        models.py
```

Pick one approach and apply it consistently across the entire project. The architecture should be visible in the folder tree, regardless of which axis comes first.

---

## 6. Multiple Stakeholders

A project serves more than just the developer writing code. Consider every stakeholder when structuring the repository.

### Stakeholders and What They Need

| Stakeholder | What They Look For |
|---|---|
| **Developers on the team** | Source code, tests, linter config, editor settings, dev tools |
| **New contributors** | README, contributing guide, wiki, license |
| **Managers / clients** | Project structure overview, documentation, test reports |
| **End users** | Documentation, API reference, examples |
| **CI/CD systems** | Config files, test directories, requirements |

### Repository Root Structure

Organize the repository root to serve all stakeholders at a glance:

```
project-root/
    .vscode/            # shared editor settings (format-on-save, linting)
    .gitignore          # keep generated files out of version control
    .pylintrc           # shared linter config — everyone uses the same rules
    LICENSE             # legal clarity for open-source consumers
    README.md           # about, install, usage, examples, contributing
    requirements.txt    # or pyproject.toml — reproducible dependencies
    assets/             # images, data files, PDFs the app needs at runtime
    docs/               # user-facing documentation
    wiki/               # developer-facing documentation (style guides, architecture decisions)
    locales/            # translations for multi-language applications
    src/                # all application source code
    tests/              # all test code, mirroring src/ structure
    tools/              # dev scripts (DB reset, migrations, code generation)
    vendor/             # vendored third-party dependencies (if needed)
```

### Key Principles

- **Put shared configuration in the repository.** Linter settings, editor config, and formatting rules belong in version control so every developer works with identical tooling. Do not let style drift between team members.
- **Separate source from everything else.** The `src/` folder contains only application code. Tests, tools, docs, and assets live at the same level, not mixed into source packages.
- **Never commit secrets.** Database credentials, API keys, and passwords must never enter the repository. Use environment variables, `.env` files (added to `.gitignore`), or separate configuration files distributed outside version control. Libraries like `python-decouple` or `python-dotenv` help manage this.

---

*Content inspired by Arjan Codes' Software Designer Mindset course.*
