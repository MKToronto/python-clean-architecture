# GRASP Principles

General Responsibility Assignment Software Patterns — nine principles for deciding where to place responsibilities in your code. Published by Craig Larman in *Applying UML and Patterns* (1997). These principles may be better suited to Python than SOLID because they apply equally well to functions, modules, and classes — not just class hierarchies.

> Content inspired by Arjan Codes' coverage of GRASP principles.

---

## Why GRASP Over SOLID for Python?

SOLID is strongly object-oriented — Liskov Substitution, for example, only matters when using inheritance. GRASP concepts like cohesion, coupling, and information expert apply to functions, modules, and classes equally. Python's multi-paradigm nature (OOP + functional + procedural) makes GRASP a more natural fit.

That said, there is significant overlap. The important thing is to keep these principles in the back of your mind — they will subconsciously steer you toward better designs.

---

## 1. Creator

**Question:** Where should I create objects?

**Rule:** Class B should create instances of class A if:
- B is composed with A (B contains or aggregates A)
- B closely uses A and nothing else does
- B has the information needed to create A

```python
# BAD: main creates SaleLineItems and passes them to Sale
line1 = SaleLineItem(product=headset, quantity=2)
line2 = SaleLineItem(product=keyboard, quantity=1)
sale = Sale(items=[line1, line2])

# GOOD: Sale creates its own line items — it controls them
sale = Sale()
sale.add_item(product=headset, quantity=2)
sale.add_item(product=keyboard, quantity=1)
```

The caller doesn't need to know how Sale is structured internally — only that it can accept products with quantities. The Factory pattern is a direct application of the Creator principle.

**In FastAPI:** The router (composition root) creates `DBInterface` instances because it has the session and model class needed to construct them. Operations never create their own data access objects.

---

## 2. Information Expert

**Question:** Where should I put this new behavior?

**Rule:** Assign the responsibility to the class/module that has the information needed to fulfill it.

```python
# BAD: compute total outside Sale
total = sum(item.product.price * item.quantity for item in sale.items)

# GOOD: Sale has the items, so it computes the total
@dataclass
class Sale:
    items: list[SaleLineItem] = field(default_factory=list)

    @property
    def total_price(self) -> int:
        return sum(item.subtotal for item in self.items)
```

Total price doesn't need any external arguments — Sale already has everything it needs. This is closely related to **Tell, Don't Ask**: instead of pulling data out of an object to compute externally, tell the object to do the computation itself.

**Caveat:** Don't take this too far. If discounts depend on the whole order plus external rules, you may end up with a god class. Sometimes a separate function or service is the right home.

---

## 3. Controller

**Question:** Who should handle system events (button clicks, HTTP requests)?

**Rule:** Create a non-UI object that handles system events and delegates to the appropriate business logic.

```python
# BAD: UI class handles both display AND business logic
class App(tk.Tk):
    def add_product(self):
        name = simpledialog.askstring("Name", "Product name:")
        price = simpledialog.askfloat("Price", "Product price:")
        self.model.insert(Product(name=name, price=price))
        self.update_list()

# GOOD: Controller separates behavior from UI
class ProductController:
    def __init__(self, model: ProductModel, view: AppInterface):
        self.model = model
        self.view = view
        view.bind_add_product(self.add_product)

    def add_product(self) -> None:
        name, price = self.view.ask_product_name_price()
        self.model.insert(Product(name=name, price=price))
        self.view.update_product_list(self.model.get_all())
```

**In FastAPI:** The three-layer architecture naturally applies this — routers are controllers that delegate to operations.

---

## 4. Low Coupling

**Question:** How do I minimize dependencies?

**Rule:** Assign responsibilities so that coupling stays low. Prefer designs where changes in one module don't ripple through the system.

```python
# BAD: Sale knows implementation details of each payment method
def total_discounted_price(self, method) -> float:
    if isinstance(method, CashPayment):
        return self.total * (1 - method.discount)
    elif isinstance(method, CreditCard):
        return self.total * (1 + method.fee)

# GOOD: Payment method provides its own net price calculation
class PaymentMethod(Protocol):
    def net_price(self, amount: float) -> float: ...

def total_discounted_price(self, method: PaymentMethod) -> float:
    return method.net_price(self.total)
```

Adding PayPal now requires zero changes to Sale. And as Arjan notes — you can do exactly the same thing with functions instead of classes.

---

## 5. High Cohesion

**Question:** Is this class/function focused on one thing?

**Rule:** Keep responsibilities narrow. Low coupling and high cohesion work together — splitting responsibilities (higher cohesion) usually reduces dependencies (lower coupling).

**Concrete signs of low cohesion:**
- Class with too many responsibilities (god class)
- More than 5-7 instance attributes
- Too many methods in a single class
- A function that handles I/O, computation, and presentation

**Tip:** Make classes either data-focused (mostly fields, few methods) or behavior-focused (mostly methods, minimal state). This makes them easier to compose later.

---

## 6. Polymorphism

**Question:** How do I handle type-dependent behavior?

**Rule:** Use polymorphism (Protocol/ABC + implementations) instead of if/elif chains on type.

```python
# BAD: if/elif chain checking types
def convert(value: float, conversion_type: str) -> float:
    if conversion_type == "inches_to_cm":
        return value * 2.54
    elif conversion_type == "miles_to_km":
        return value * 1.60934
    # ... grows forever

# GOOD (Pythonic): functions as polymorphic units
ConversionFn = Callable[[float], float]

def inches_to_cm(value: float) -> float:
    return value * 2.54

def convert(value: float, converter: ConversionFn) -> float:
    return converter(value)
```

In Python, you often don't need class hierarchies for polymorphism — functions and `Callable` type aliases achieve the same thing more simply.

---

## 7. Indirection

**Question:** How do I decouple two objects that are directly connected?

**Rule:** Introduce an intermediate object to remove direct coupling.

```python
# BAD: Order directly accesses Customer to compute discount
class Order:
    customer: Customer

    def get_discount(self) -> float:
        lifetime = (date.today() - self.customer.created_at).days
        return 0.2 if lifetime > 365 else 0.0

# GOOD: Discount as an intermediate concept
@dataclass
class Discount:
    percentage: float

def compute_discount(customer: Customer) -> Discount:
    lifetime = (date.today() - customer.created_at).days
    return Discount(0.2 if lifetime > 365 else 0.0)

@dataclass
class Order:
    discount: Discount  # no longer coupled to Customer
```

Design patterns that apply indirection: Adapter, Facade, Observer, Mediator.

---

## 8. Protected Variations

**Question:** How do I protect against changes in external dependencies?

**Rule:** Introduce abstraction (Protocol/interface) at points of anticipated variation.

```python
# Controller depends on a Protocol, not on tkinter directly
class AppInterface(Protocol):
    def bind_add_product(self, handler: Callable) -> None: ...
    def bind_delete_product(self, handler: Callable) -> None: ...
    def update_product_list(self, products: list[Product]) -> None: ...

class ProductController:
    def __init__(self, model: ProductModel, view: AppInterface):
        ...  # works with tkinter, Qt, or any UI framework
```

This is the same principle behind `DataInterface` in the three-layer architecture — operations are protected from changes in the database layer.

---

## 9. Pure Fabrication

**Question:** Where do I put behavior that doesn't belong to any existing domain class?

**Rule:** Create a new class/module that exists purely for design purposes, not because it represents a domain concept.

```python
# Payment shouldn't also handle transaction storage
# Create a separate class for that responsibility
class TransactionStore:
    def save(self, record: TransactionRecord) -> None: ...

class PaymentHandler:
    def __init__(self, payment: Payment, store: TransactionStore):
        self.payment = payment
        self.store = store

    def process(self) -> None:
        self.payment.execute()
        self.store.save(TransactionRecord(amount=self.payment.amount))
```

`TransactionStore` and `PaymentHandler` don't represent domain objects — they exist to keep `Payment` focused. The `DBInterface` class in the three-layer architecture is a pure fabrication: it exists for design purposes (decoupling), not because "database interface" is a domain concept.

---

## GRASP vs SOLID Mapping

| GRASP | Closest SOLID Equivalent |
|---|---|
| High Cohesion | Single Responsibility (SRP) |
| Low Coupling | Dependency Inversion (DIP) |
| Polymorphism | Open-Closed (OCP), Liskov Substitution (LSP) |
| Protected Variations | Dependency Inversion (DIP) |
| Information Expert | — (no direct equivalent) |
| Creator | — (no direct equivalent) |
| Controller | — (architectural, not in SOLID) |
| Indirection | — (design tactic) |
| Pure Fabrication | — (design tactic) |

The overlap is real, but GRASP provides more practical guidance for responsibility assignment — especially in Python where you're not always working with class hierarchies.
