# Domain Modeling Reference

Start every project by modeling the domain — the data structures, entities, and their relationships. The domain model is the conceptual representation that captures both data AND behavior of the business problem.

> Content derived from Arjan Codes' *Complete Extension* (Domain Model) and DDD tutorials.

---

## 1. What Is Domain Modeling?

A domain model is a conceptual representation of the problem you're solving. It captures:
- **Entities** — things with identity (User, Order, Room)
- **Value objects** — things without identity (Price, Email, DateRange)
- **Relationships** — how entities relate to each other
- **Behavior** — what operations are valid on each entity

**Key insight:** Code is a temporary expression of the domain model. The model persists; code gets refactored. Optimize for easy code replacement,