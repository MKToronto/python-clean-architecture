# Domain-Driven Design

A high-level approach to software design that puts the **domain model** — not the code — at the center of the development process. The core insight: code is a temporary expression of the domain model. If the domain model is wrong, even perfectly designed code is useless.

> Content inspired by Arjan Codes' coverage of Domain-Driven Design and Eric Evans' *Domain-Driven Design* (2004).

---

## Core Concept: The Domain Model

A **domain model** is a conceptual representation of a domain that captures both data and behavior:

- **HR software** → employees, contracts, salaries, departments
- **Hotel booking** → rooms, bookings, customers, pricing rules
- **Quiz platform** → questions, quizzes, scores, question types

The domain model is not code. It is the shared understanding of what the system represents and how its concepts relate to each other. Code is one expression of it.

---

## Five Steps of Domain-Driven Design

### 1. Bind Model and Implementation Early

Start with a crude prototype — a tangible starting point you can iterate on. Don't spend months on requirements before writing code. Having a working prototype lets you discover problems and refine the domain model simultaneously.

This aligns with the three-layer architecture approach: scaffold a minimal FastAPI project with one entity, then iterate.

### 2. Cultivate a Ubiquitous Language

Develop a shared vocabulary between developers and domain experts (customers, stakeholders). Both groups must use the same terms for the same concepts.

```
Domain expert says:  "A booking has a check-in date and a check-out date"
Developer models:    BookingCreate(from_date: date, to_date: date)
```

If the developer calls it `start_date` / `end_date` while the domain expert says "check-in" / "check-out", misunderstandings will creep in. The code should use the language of the domain.

### 3. Build Knowledge-Rich Models

The domain model should encode behavior, not just data structures. Iterate with domain experts to deepen the model.

```python
# Shallow model — just data
@dataclass
class Booking:
    room_id: str
    from_date: date
    to_date: date
    price: int

# Knowledge-rich model — encodes domain rules
@dataclass
class Booking:
    room_id: str
    from_date: date
    to_date: date
    price: int

    @property
    def nights(self) -> int:
        return (self.to_date - self.from_date).days

    def overlaps(self, other: "Booking") -> bool:
        return self.from_date < other.to_date and other.from_date < self.to_date
```

### 4. Distill the Model

Remove concepts that don't earn their keep. If a distinction (e.g., "quiz" vs "exam") doesn't affect behavior, collapse it. Simpler models are easier to implement, test, and explain.

### 5. Brainstorm and Experiment

Walk through scenarios with the domain model. Ask "what happens when...?" questions. This is where developers provide unique value — translating domain concepts into technically feasible systems.

---

## Code as Temporary Expression

The domain model persists and evolves. Code is rewritten to match it.

This means:
- **Optimize for iteration speed** — make it easy to throw away and replace code
- **Design patterns help** — Strategy lets you swap behavior, low coupling lets you replace modules
- **Smaller functions** with single responsibilities are easier to discard without breaking other things
- **Tests protect the domain model**, not the implementation details

---

## DDD in the Three-Layer Architecture

The three-layer architecture naturally supports DDD thinking:

| DDD Concept | Three-Layer Implementation |
|---|---|
| Domain Model | Pydantic models in `models/` |
| Domain Behavior | Operations functions in `operations/` |
| Repository | `DataInterface` Protocol + `DBInterface` |
| Ubiquitous Language | Model field names match domain terms |
| Bounded Context | Separate entity modules (rooms, bookings, customers) |

---

## When to Apply DDD Thinking

- **Always:** Use ubiquitous language. Name your models, fields, and functions after domain concepts.
- **For complex domains:** Build knowledge-rich models. Encode rules and relationships in the domain layer.
- **For evolving projects:** Distill aggressively. Remove concepts that don't justify their complexity.
- **For AI-assisted development:** AI tools help express the domain model in code faster — the developer's value is in understanding the domain and its constraints, not in typing code.

## Relationship to Other Concepts

- **Value Objects** (`patterns/value-objects.md`) — DDD uses value objects extensively to wrap domain primitives (Price, EmailAddress)
- **Event Sourcing** (`patterns/event-sourcing.md`) — an advanced DDD technique for capturing domain events
- **GRASP Principles** (`references/grasp-principles.md`) — Information Expert and Creator are DDD-compatible responsibility assignment rules
