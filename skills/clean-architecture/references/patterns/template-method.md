# Template Method Pattern

> Content inspired by Arjan Codes' Pythonic Patterns course.

## Problem

Multiple sibling classes implement the same algorithm with duplicated structure, differing only in the individual steps. The algorithm logic is copied across every subclass.

```python
class EthereumTradingBot:
    def get_price_data(self) -> list[float]:
        return [1800.0, 1850.0, 1820.0]

    def get_amount(self) -> float:
        return 5.0

    def should_buy(self, prices: list[float]) -> bool:
        return prices[-1] < prices[0]

    def should_sell(self, prices: list[float]) -> bool:
        return prices[-1] > prices[0]

    def buy(self, amount: float) -> None:
        print(f"Buying {amount} Ethereum")

    def sell(self, amount: float) -> None:
        print(f"Selling {amount} Ethereum")

    def trade(self) -> None:
        prices = self.get_price_data()
        amount = self.get_amount()
        if self.should_buy(prices):
            self.buy(amount)
        elif self.should_sell(prices):
            self.sell(amount)


class BitcoinTradingBot:
    def get_price_data(self) -> list[float]:
        return [42000.0, 41500.0, 43000.0]

    def get_amount(self) -> float:
        return 0.5

    def should_buy(self, prices: list[float]) -> bool:
        return prices[-1] < 40000

    def should_sell(self, prices: list[float]) -> bool:
        return prices[-1] > 42000

    def buy(self, amount: float) -> None:
        print(f"Buying {amount} Bitcoin")

    def sell(self, amount: float) -> None:
        print(f"Selling {amount} Bitcoin")

    def trade(self) -> None:
        prices = self.get_price_data()
        amount = self.get_amount()
        if self.should_buy(prices):
            self.buy(amount)
        elif self.should_sell(prices):
            self.sell(amount)
```

The `trade()` method is identical in both classes. If the trading algorithm changes (add connection error handling, logging, etc.), every bot class must be updated. This violates DRY.

---

## Classic OOP -- ABC with Template Method and Abstract Primitive Steps

Extract the shared algorithm into an abstract base class. The template method (`trade`) is a concrete method that calls abstract primitive operations. Subclasses implement only the steps that vary.

### trading_bot.py

```python
from abc import ABC, abstractmethod


class TradingBot(ABC):
    """Template method pattern: trade() is the fixed algorithm,
    subclasses implement the varying steps."""

    def trade(self) -> None:
        prices = self.get_price_data()
        amount = self.get_amount()
        if self.should_buy(prices):
            self.buy(amount)
        elif self.should_sell(prices):
            self.sell(amount)

    @abstractmethod
    def get_price_data(self) -> list[float]: ...

    @abstractmethod
    def get_amount(self) -> float: ...

    @abstractmethod
    def should_buy(self, prices: list[float]) -> bool: ...

    @abstractmethod
    def should_sell(self, prices: list[float]) -> bool: ...

    @abstractmethod
    def buy(self, amount: float) -> None: ...

    @abstractmethod
    def sell(self, amount: float) -> None: ...
```

### ethereum_bot.py

```python
from trading_bot import TradingBot


class EthereumTradingBot(TradingBot):
    def get_price_data(self) -> list[float]:
        return [1800.0, 1850.0, 1820.0]

    def get_amount(self) -> float:
        return 5.0

    def should_buy(self, prices: list[float]) -> bool:
        return prices[-1] < prices[0]

    def should_sell(self, prices: list[float]) -> bool:
        return prices[-1] > prices[0]

    def buy(self, amount: float) -> None:
        print(f"Buying {amount} Ethereum")

    def sell(self, amount: float) -> None:
        print(f"Selling {amount} Ethereum")
```

### main.py

```python
from ethereum_bot import EthereumTradingBot
from bitcoin_bot import BitcoinTradingBot


def main() -> None:
    eth_bot = EthereumTradingBot()
    btc_bot = BitcoinTradingBot()
    eth_bot.trade()
    btc_bot.trade()
```

If the trading algorithm changes, update `TradingBot.trade()` once. All subclasses inherit the change.

---

## Why Protocols Alone Do Not Work Here

The template method pattern requires inheritance because the shared method (`trade`) must live in a base class and call methods on `self`. A Protocol defines a structural interface but does not provide shared implementation.

```python
from typing import Protocol


class TradingEngine(Protocol):
    def get_price_data(self) -> list[float]: ...
    def get_amount(self) -> float: ...
    def should_buy(self, prices: list[float]) -> bool: ...
    def should_sell(self, prices: list[float]) -> bool: ...
    def buy(self, amount: float) -> None: ...
    def sell(self, amount: float) -> None: ...
```

This Protocol cannot contain the `trade()` algorithm. If you add `trade()` to the Protocol, every implementer must duplicate it. Protocols define shape, not behavior. For shared behavior, you need either inheritance (ABC) or a free function that receives the Protocol as a parameter.

---

## Pythonic -- Free Function with Protocol Parameters

Move the template method out of the class hierarchy entirely. Make it a free function that accepts a Protocol-typed parameter. The concrete classes no longer inherit from anything.

### trading_bot.py

```python
from typing import Protocol


class TradingEngine(Protocol):
    """Structural interface for the varying steps."""

    def get_price_data(self) -> list[float]: ...
    def get_amount(self) -> float: ...
    def should_buy(self, prices: list[float]) -> bool: ...
    def should_sell(self, prices: list[float]) -> bool: ...
    def buy(self, amount: float) -> None: ...
    def sell(self, amount: float) -> None: ...


def trade(engine: TradingEngine) -> None:
    """The template method as a free function."""
    prices = engine.get_price_data()
    amount = engine.get_amount()
    if engine.should_buy(prices):
        engine.buy(amount)
    elif engine.should_sell(prices):
        engine.sell(amount)
```

### ethereum_bot.py

```python
class EthereumTradingBot:
    """No inheritance required -- satisfies TradingEngine via structural typing."""

    def get_price_data(self) -> list[float]:
        return [1800.0, 1850.0, 1820.0]

    def get_amount(self) -> float:
        return 5.0

    def should_buy(self, prices: list[float]) -> bool:
        return prices[-1] < prices[0]

    def should_sell(self, prices: list[float]) -> bool:
        return prices[-1] > prices[0]

    def buy(self, amount: float) -> None:
        print(f"Buying {amount} Ethereum")

    def sell(self, amount: float) -> None:
        print(f"Selling {amount} Ethereum")
```

### main.py

```python
from trading_bot import trade
from ethereum_bot import EthereumTradingBot
from bitcoin_bot import BitcoinTradingBot


def main() -> None:
    eth_bot = EthereumTradingBot()
    btc_bot = BitcoinTradingBot()
    trade(eth_bot)
    trade(btc_bot)
```

The concrete bot classes have no inheritance relationship. They satisfy the `TradingEngine` Protocol through structural typing. The algorithm lives in the `trade()` free function.

---

## Protocol Segregation as "Less Evil Version of Mixins"

When a single Protocol grows large, split it into focused Protocols. Because Protocols use structural typing (duck typing), segregation happens at the Protocol level without affecting the implementing classes.

### trading_bot.py

```python
from typing import Protocol


class TradingEngine(Protocol):
    """Exchange operations: data retrieval and order execution."""

    def get_price_data(self) -> list[float]: ...
    def get_amount(self) -> float: ...
    def buy(self, amount: float) -> None: ...
    def sell(self, amount: float) -> None: ...


class TradingStrategy(Protocol):
    """Decision logic: when to buy or sell."""

    def should_buy(self, prices: list[float]) -> bool: ...
    def should_sell(self, prices: list[float]) -> bool: ...


def trade(engine: TradingEngine, strategy: TradingStrategy) -> None:
    prices = engine.get_price_data()
    amount = engine.get_amount()
    if strategy.should_buy(prices):
        engine.buy(amount)
    elif strategy.should_sell(prices):
        engine.sell(amount)
```

### simple_strategy.py

```python
class SimpleStrategy:
    def should_buy(self, prices: list[float]) -> bool:
        return prices[-1] < prices[0]

    def should_sell(self, prices: list[float]) -> bool:
        return prices[-1] > prices[0]
```

### main.py

```python
from trading_bot import trade
from ethereum_bot import EthereumTradingBot
from bitcoin_bot import BitcoinTradingBot
from simple_strategy import SimpleStrategy


def main() -> None:
    strategy = SimpleStrategy()
    eth_bot = EthereumTradingBot()
    btc_bot = BitcoinTradingBot()
    trade(eth_bot, strategy)
    trade(btc_bot, strategy)
```

Protocol segregation compared to mixins:
- Mixins use multiple inheritance, which creates diamond problems and implicit method resolution.
- Protocol segregation splits the _interface_, not the _implementation_. No inheritance relationship exists between the Protocols and the implementing classes.
- You get the composability benefits of mixins (small, focused interfaces) without the coupling and ambiguity of multiple inheritance.
- Splitting or recombining Protocols requires zero changes to the implementing classes.

---

## When to Use / Trade-offs

**Use the template method when:**
- Multiple classes share the same algorithm structure but differ in individual steps.
- The algorithm is unlikely to change independently of its host (it logically belongs with the steps).
- You want to enforce DRY for a shared procedure.

**Choose ABC + inheritance when:**
- The base class needs to store state used by the template method.
- Subclass authors must be forced to implement all steps (abstract methods enforce this at instantiation time).
- The inheritance hierarchy is shallow (one level of subclasses).

**Choose free function + Protocol when:**
- You want to avoid coupling concrete classes to a base class.
- You benefit from Protocol segregation to split a large interface.
- The concrete classes are used in other contexts beyond the template method.

**Trade-offs:**
- The ABC approach ties subclasses to a single parent. If a class needs to participate in multiple template methods, multiple inheritance becomes necessary.
- The free function approach requires passing the engine explicitly. The template method can no longer access `self` -- it must go through the parameter.
- Protocol segregation adds more type definitions. Use it when the single Protocol grows beyond 4-5 methods or when different callers need different subsets.
- There is no single best approach. ABCs are perfectly valid. The functional + Protocol style offers more flexibility. Choose based on readability and the team's familiarity.
