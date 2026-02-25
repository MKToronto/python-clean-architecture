---
name: scaffold-tests
description: Generate stub-based tests for existing operations using DataInterfaceStub
argument-hint: [path]
---

Generate tests for the code at `$ARGUMENTS` (or the current working directory if no path given) using the DataInterfaceStub pattern — no database needed.

## Process

1. **Read the code** — Find and read ALL Python files in the target path recursively. Identify:
   - Operations files (business logic functions that accept `DataInterface` or similar Protocol)
   - Pydantic models (Create, Read, Update models)
   - Any existing test files (to avoid duplication and match existing test conventions)

2. **Create DataInterfaceStub** — If not already present, generate a `tests/conftest.py` with:

   ```python
   from typing import Any

   DataObject = dict[str, Any]

   class DataInterfaceStub:
       def __init__(self):
           self.data: dict[str, DataObject] = {}
       def read_by_id(self, id: str) -> DataObject:
           if id not in self.data:
               raise KeyError(f"Not found: {id}")
           return self.data[id]
       def read_all(self) -> list[DataObject]:
           return list(self.data.values())
       def create(self, data: DataObject) -> DataObject:
           self.data[data["id"]] = data
           return data
       def update(self, id: str, data: DataObject) -> DataObject:
           if id not in self.data:
               raise KeyError(f"Not found: {id}")
           self.data[id].update(data)
           return self.data[id]
       def delete(self, id: str) -> None:
           if id not in self.data:
               raise KeyError(f"Not found: {id}")
           del self.data[id]
   ```

3. **Generate test files** — For each operations module, create `tests/test_{entity}.py` with:
   - **Happy path tests** — create, read, list, update, delete all succeed
   - **Not-found tests** — read/update/delete with invalid ID raises `KeyError`
   - **Business logic tests** — any computed values (prices, totals, derived fields) verified with known inputs
   - **Edge cases** — empty lists, partial updates (exclude_none), duplicate creation

4. **Test structure** — Each test file follows:
   ```python
   import pytest
   from conftest import DataInterfaceStub
   from operations.{entity} import create_{entity}, read_{entity}, ...

   @pytest.fixture
   def stub():
       return DataInterfaceStub()

   def test_create_{entity}(stub):
       ...

   def test_read_{entity}_not_found(stub):
       with pytest.raises(KeyError):
           ...
   ```

5. **Ask before writing** — Use AskUserQuestion to confirm: "Generate these test files?" Show the list of files that will be created.

6. **Write the test files** — Create all test files in the `tests/` directory.

For testing patterns and advanced techniques, consult:
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/testable-api.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/references/testing-advanced.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/clean-architecture/examples/fastapi-hotel-api/` (working reference)
