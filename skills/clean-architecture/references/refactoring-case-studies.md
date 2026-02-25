# Refactoring Case Studies Reference

Recurring refactoring transformations extracted from real-world Python code reviews. Each entry describes a before pattern, why it's problematic, the after pattern, and which principle drives the fix.

> Content derived from Arjan Codes' *Code Roast* series and refactoring tutorials.

---

## How to Use This Reference

This is a catalog of **recurring transformations**, not a gallery of projects. When reviewing code, scan for the "before" patterns. When you find one, apply the corresponding transformation.

---

## 1. Guard Clauses to Reduce Indentation

Replace nested if-else branches with early returns that handle error/edge cases first, leaving the happy path at shallow indentation.

```python
# BEFORE — logic buried 4 levels deep
def process_order(order):
    if order:
        if order.items:
            for item in order.items:
                if item.price > 0:
                    # actual logic here

# AFTER — guard clauses flatten the structure
def process_order(order):
    if not order or not order.items:
        return
    for item in order.items:
        if item.price <= 0:
            continue
        # actual logic at shallow depth
```

**Principle:** Reduce cognitive load. Readers skip guard clauses and focus on the main path.

---

## 2. Extract Named Helper Functions

Move complex conditional logic into self-documenting functions. The function name replaces the need for comments.

```python
# BEFORE — complex inline condition
if order.amount > 1000 and order.type == "bulk" and not user.is_trial:
    approve_order()

# AFTER — named function makes intent clear
def is_eligible_for_approval(order: Order, user: User) -> bool:
    return order.amount > 1000 and order.type == "bulk" and not user.is_trial

if is_eligible_for_approval(order, user):
    approve_order()
```

**Principle:** Self-documenting code. If you need a comment to explain a condition, extract it into a function.

---

## 3. Replace Raw Data Structures with Domain Classes

Move data and related operations from dictionaries/lists/tuples into proper classes or dataclasses.

```python
# BEFORE — parallel data in raw structures
board = [[0 for _ in range(5)] for _ in range(5)]

def place_ship(board, row, col):
    board[row][col] = "S"

# AFTER — domain class with encapsulated operations
@dataclass
class Board:
    grid: list[list[str]] = field(default_factory=lambda: [["O"] * 5 for _ in range(5)])

    def place_ship(self, row: int, col: int) -> None:
        self.grid[row][col] = SHIP
```

**Principle:** Encapsulation. Data and the operations on that data belong together.

---

## 4. Separate UI/IO from Business Logic

Extract all printing, input reading, and display code into a separate layer. Business logic should never import `print` or `input`.

```python
# BEFORE — game class does everything
class Game:
    def __init__(self):
        print("Welcome!")  # UI mixed with init
        self.board = self._create_board()

    def play_round(self):
        guess = input("Enter guess: ")  # IO mixed with logic
        result = self._check_guess(guess)
        print(f"Result: {result}")  # UI mixed with logic

# AFTER — UI injected as dependency
class ConsoleUI:
    def show_welcome(self) -> None:
        print("Welcome!")

    def read_guess(self) -> str:
        return input("Enter guess: ")

    def show_result(self, result: str) -> None:
        print(f"Result: {result}")

class Game:
    def __init__(self, ui: ConsoleUI, board: Board):
        self.ui = ui
        self.board = board

    def play_round(self) -> None:
        guess = self.ui.read_guess()
        result = self._check_guess(guess)
        self.ui.show_result(result)
```

**Principle:** Separation of concerns. Testable logic requires no console interaction.

---

## 5. Replace Magic Numbers with Named Constants

Extract hardcoded values to module-level constants with descriptive names.

```python
# BEFORE
self.board = [[0 for _ in range(5)] for _ in range(5)]
if guesses_remaining == 5:
    print("Game over")

# AFTER
BOARD_ROWS = 5
BOARD_COLS = 5
MAX_GUESSES = 5

self.board = [[0 for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
if guesses_remaining == MAX_GUESSES:
    print("Game over")
```

**Principle:** Single source of truth. Change one constant, not twenty scattered literals.

---

## 6. Replace String Comparisons with Enums

Convert scattered string literals into Enums for type safety and IDE support.

```python
# BEFORE — string comparisons are typo-prone
if choice == "rock":
    ...
elif choice == "paper":
    ...
elif choice == "scisssors":  # typo goes undetected!
    ...

# AFTER — Enum catches errors at definition time
class Move(str, Enum):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"

if choice == Move.ROCK:
    ...
```

**Principle:** Type safety. The type system catches mistakes that string comparisons hide.

---

## 7. Consolidate Rules into Data Structures

Replace multiple separate if-statements with a unified collection of rules.

```python
# BEFORE — scattered rejection logic
if not user.is_premium:
    return reject
if not is_eligible_amount(order, user):
    return reject
if order.has_discount and not is_valid_currency(order, user):
    return reject

# AFTER — data-driven rules
RejectionRule = Callable[[Order, User], bool]

rejection_rules: list[RejectionRule] = [
    lambda o, u: not u.is_premium,
    lambda o, u: not is_eligible_amount(o, u),
    lambda o, u: o.has_discount and not is_valid_currency(o, u),
]

if any(rule(order, user) for rule in rejection_rules):
    return reject
```

**Principle:** Open-closed. Add new rules by extending the list, not modifying existing code.

---

## 8. Replace Catch-All Exception Handling

Replace bare `except:` or `except Exception:` with specific exception types and informative messages.

```python
# BEFORE — catches everything, masks bugs
try:
    amount = int(user_input)
except:
    return "error"

# AFTER — specific catch, clear feedback
try:
    amount = int(user_input)
except ValueError:
    raise InvalidAmountError(f"Expected a number, got: {user_input!r}")
```

**Principle:** Fail explicitly. Generic catches hide real bugs.

---

## 9. Encapsulate Data Structure Access

Don't let calling code directly modify internal data structures. Provide methods that describe the operation.

```python
# BEFORE — Law of Demeter violation
game.scoreboard.points[player_name] += 1
game.board[row][col] = "X"

# AFTER — encapsulated operations
game.scoreboard.add_point(player_name)
game.board.place_guess(row, col)
```

**Principle:** Law of Demeter. Each object controls access to its own data.

---

## 10. Remove Unnecessary Class Wrappers

Replace classes that only wrap simple functions with standalone functions or plain data.

```python
# BEFORE — class adds no value
class InputReader:
    def __init__(self):
        pass

    def read_integer(self, prompt):
        return int(input(prompt))

# AFTER — plain function
def read_integer(prompt: str, min_val: int, max_val: int) -> int:
    while True:
        try:
            value = int(input(prompt))
            if min_val <= value <= max_val:
                return value
        except ValueError:
            pass
        print(f"Enter a number between {min_val} and {max_val}")
```

**Principle:** KISS. Don't use a class when a function will do.

---

## 11. Keep __init__ Focused on Initialization

Move setup logic, printing, and complex operations out of `__init__`.

```python
# BEFORE — __init__ does too much
class Game:
    def __init__(self, player_name):
        print("Welcome!")
        self.board = self._create_board()
        self._register_player(player_name)
        self._start_game()

# AFTER — __init__ only stores state
class Game:
    def __init__(self, board: Board, player: Player):
        self.board = board
        self.player = player

    def start(self) -> None:
        self._register_player()
        # game loop here
```

**Principle:** Separate creation from use. `__init__` receives ready-made dependencies.

---

## 12. Use Comprehensions Over Loops

Replace verbose loop-and-append patterns with list/dict/set comprehensions.

```python
# BEFORE
result = []
for row in grid:
    for cell in row:
        if cell.is_alive:
            result.append(cell)

# AFTER
result = [cell for row in grid for cell in row if cell.is_alive]
```

**Principle:** Pythonic code. Comprehensions express the intent more clearly.

---

## 13. Replace Recursion with Iteration for Retry Logic

Use `while True` loops instead of recursive calls for input validation / retry patterns.

```python
# BEFORE — recursion for retry (stack overflow risk)
def read_input(self):
    value = input("Enter: ")
    if not is_valid(value):
        print("Invalid")
        return self.read_input()

# AFTER — while loop
def read_input(self) -> str:
    while True:
        value = input("Enter: ")
        if is_valid(value):
            return value
        print("Invalid")
```

**Principle:** Stack safety. Recursion should model recursive problems, not loops.

---

## 14. Ensure Consistent Return Types

Functions should always return the same type, regardless of path taken.

```python
# BEFORE — returns Command or bool (inconsistent)
def parse_input(text: str) -> Command | bool:
    if command_found:
        return Command(text)
    return False

# AFTER — returns Command or None (consistent)
def parse_input(text: str) -> Command | None:
    if command_found:
        return Command(text)
    return None
```

**Principle:** Type safety. Inconsistent return types force callers to check with isinstance.

---

## Refactoring Process Template

When refactoring existing code:

1. **Read and understand** — Don't change anything until you understand what the code does
2. **Add characterization tests** — Capture current behavior before changing it
3. **Identify the worst smell** — Start with the transformation that reduces the most complexity
4. **Apply one pattern at a time** — Don't refactor everything at once
5. **Run tests after each change** — Verify behavior is preserved
6. **Repeat** — Tackle the next smell

> Content inspired by Arjan Codes' *Code Roast* series covering Battleship, Tower Defense, Chess, Yahtzee, Conway's Game of Life, Rock Paper Scissors Lizard Spock, PDF Scraper, and CLI Shell refactoring.
