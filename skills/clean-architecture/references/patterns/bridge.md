# Bridge Pattern

Decouple two independent hierarchies so each can vary without affecting the other.

> Content inspired by Arjan Codes' Pythonic Patterns course.

---

## 1. Problem

Consider a trading system with two axes of variation: **exchanges** (Coinbase, Binance, ...) and **trading strategies** (average-based, min/max threshold, ...). Without the Bridge pattern, every combination demands its own class -- a Cartesian product explosion:

```
CoinbaseAverageTradingBot
CoinbaseMinMaxTradingBot
BinanceAverageTradingBot
BinanceMinMaxTradingBot
...
```

Add one exchange and you must write N new bot classes. Add one strategy and you must write M new exchange-specific classes. The two hierarchies are fused at the concrete level, so neither can change independently.

The Bridge pattern fixes this by connecting the two hierarchies at the **abstract** level. Each hierarchy evolves on its own; the link between them is made once, through an abstraction.

---

## 2. Classic OOP Solution -- ABC-Based Bridge

### The Exchange hierarchy

Define an abstract base class for all exchanges:

```python
# exchange.py
from abc import ABC, abstractmethod


class Exchange(ABC):
    @abstractmethod
    def get_prices(self, symbol: str) -> list[int]:
        """Get the prices of the given symbol."""

    @abstractmethod
    def buy(self, symbol: str, amount: int) -> None:
        """Buy the given amount of the given symbol."""

    @abstractmethod
    def sell(self, symbol: str, amount: int) -> None:
        """Sell the given amount of the given symbol."""
```

Concrete exchanges inherit from it:

```python
# binance.py
from exchange import Exchange

PRICE_DATA: dict[str, list[int]] = {
    "BTC/USD": [
        35_842_00, 34_209_00, 32_917_00, 33_931_00,
        33_370_00, 34_445_00, 32_901_00, 33_013_00,
    ],
    "ETH/USD": [
        2_381_00, 2_233_00, 2_300_00, 2_342_00,
        2_137_00, 2_156_00, 2_103_00, 2_165_00,
    ],
}


class Binance(Exchange):
    def get_prices(self, symbol: str) -> list[int]:
        return PRICE_DATA[symbol]

    def buy(self, symbol: str, amount: int) -> None:
        print(f"[Binance] Buying amount {amount} in market {symbol}.")

    def sell(self, symbol: str, amount: int) -> None:
        print(f"[Binance] Selling amount {amount} in market {symbol}.")
```

### The TradingBot hierarchy -- with the bridge

The abstract `TradingBot` stores a reference to the abstract `Exchange`. This reference **is** the bridge:

```python
# trading_bot.py
from abc import ABC, abstractmethod
from exchange import Exchange


class TradingBot(ABC):
    def __init__(self, exchange: Exchange) -> None:
        self.exchange = exchange

    @abstractmethod
    def should_buy(self, symbol: str) -> bool:
        """Should the bot buy the given symbol?"""

    @abstractmethod
    def should_sell(self, symbol: str) -> bool:
        """Should the bot sell the given symbol?"""
```

Note the import: `from exchange import Exchange` -- not `Coinbase`, not `Binance`. The trading bot depends on the abstraction.

### Concrete trading bots

```python
# avg_trading_bot.py
import statistics
from trading_bot import TradingBot


class AverageTradingBot(TradingBot):
    def should_buy(self, symbol: str) -> bool:
        prices = self.exchange.get_prices(symbol)
        list_window = prices[-3:]
        return prices[-1] < statistics.mean(list_window)

    def should_sell(self, symbol: str) -> bool:
        prices = self.exchange.get_prices(symbol)
        list_window = prices[-3:]
        return prices[-1] > statistics.mean(list_window)
```

```python
# minmax_trading_bot.py
from trading_bot import TradingBot


class MinMaxTradingBot(TradingBot):
    def should_buy(self, symbol: str) -> bool:
        prices = self.exchange.get_prices(symbol)
        return prices[-1] < 32_000_00

    def should_sell(self, symbol: str) -> bool:
        prices = self.exchange.get_prices(symbol)
        return prices[-1] > 33_000_00
```

### Wiring in main

```python
# main.py
from binance import Binance
from avg_trading_bot import AverageTradingBot


def main() -> None:
    symbol = "BTC/USD"
    trade_amount = 10

    exchange = Binance()
    trading_bot = AverageTradingBot(exchange)

    should_buy = trading_bot.should_buy(symbol)
    should_sell = trading_bot.should_sell(symbol)

    if should_buy:
        exchange.buy(symbol, trade_amount)
    elif should_sell:
        exchange.sell(symbol, trade_amount)
    else:
        print("No action needed.")


if __name__ == "__main__":
    main()
```

Swap `AverageTradingBot` for `MinMaxTradingBot` -- no exchange code changes. Swap `Binance` for `Coinbase` -- no trading bot code changes. Each hierarchy varies independently because the bridge lives at the abstract level.

### Why it works

The `TradingBot` ABC stores `self.exchange` typed as `Exchange` (the abstract class). Subclasses call `self.exchange.get_prices(symbol)` without knowing whether they talk to Binance or Coinbase. The exchange, in turn, knows nothing about trading bots at all. The connection is one-directional and abstract.

Think of it as the **depend on abstractions** principle applied structurally: two class trees, one abstract reference joining them.

### When ABC is the right choice for Bridge

The ABC-based bridge has a unique advantage: the abstract superclass can store **shared state** (`self.exchange`) that all subclasses inherit. With Protocols, each concrete bot must declare its own `exchange` attribute — duplication that grows with the number of concrete implementations. If the bridge side carries multiple shared attributes or helper methods, ABC eliminates that repetition:

```python
class TradingBot(ABC):
    def __init__(self, exchange: Exchange, risk_limit: int = 1000) -> None:
        self.exchange = exchange
        self.risk_limit = risk_limit

    def _check_risk(self, amount: int) -> bool:
        """Shared helper — available to all concrete bots."""
        return amount <= self.risk_limit

    @abstractmethod
    def should_buy(self, symbol: str) -> bool: ...

    @abstractmethod
    def should_sell(self, symbol: str) -> bool: ...
```

This shared implementation cannot exist in a Protocol. Use ABC when the bridge superclass is more than just an interface — when it provides reusable behavior that concrete implementations build upon.

---

## 3. Pythonic Progression

### Step A: Replace ABCs with Protocols

With ABCs, the superclass stores shared state (`self.exchange`) and subclasses inherit it. Protocols cannot do this because you do not inherit from a Protocol -- it is just an interface definition.

The workaround: move the `exchange` attribute into each concrete bot using a dataclass, and define both `Exchange` and `TradingBot` as Protocols:

```python
# exchange.py
from typing import Protocol


class Exchange(Protocol):
    def get_prices(self, symbol: str) -> list[int]: ...
    def buy(self, symbol: str, amount: int) -> None: ...
    def sell(self, symbol: str, amount: int) -> None: ...
```

```python
# trading_bot.py
from typing import Protocol


class TradingBot(Protocol):
    def should_buy(self, symbol: str) -> bool: ...
    def should_sell(self, symbol: str) -> bool: ...
```

```python
# avg_trading_bot.py
import statistics
from dataclasses import dataclass
from exchange import Exchange


@dataclass
class AverageTradingBot:
    exchange: Exchange

    def should_buy(self, symbol: str) -> bool:
        prices = self.exchange.get_prices(symbol)
        list_window = prices[-3:]
        return prices[-1] < statistics.mean(list_window)

    def should_sell(self, symbol: str) -> bool:
        prices = self.exchange.get_prices(symbol)
        list_window = prices[-3:]
        return prices[-1] > statistics.mean(list_window)
```

The bridge still exists. It just moved from the abstract superclass down into each concrete bot. The trade-off: there is some duplication (each bot declares `exchange: Exchange`), but you gain duck typing flexibility and no ABC inheritance.

Concrete exchanges like `Binance` stay the same -- they no longer inherit from `Exchange` explicitly, but they satisfy its protocol structurally.

### Step B: Functions taking objects

The `AverageTradingBot` class has no meaningful state beyond the exchange reference. Its two methods are really just two functions. Extract them:

```python
# avg_trading_bot.py
import statistics
from exchange import Exchange


def should_buy_avg(exchange: Exchange, symbol: str) -> bool:
    prices = exchange.get_prices(symbol)
    list_window = prices[-3:]
    return prices[-1] < statistics.mean(list_window)


def should_sell_avg(exchange: Exchange, symbol: str) -> bool:
    prices = exchange.get_prices(symbol)
    list_window = prices[-3:]
    return prices[-1] > statistics.mean(list_window)
```

```python
# main.py
from binance import Binance
from avg_trading_bot import should_buy_avg, should_sell_avg


def main() -> None:
    symbol = "BTC/USD"
    trade_amount = 10

    exchange = Binance()

    should_buy = should_buy_avg(exchange, symbol)
    should_sell = should_sell_avg(exchange, symbol)

    if should_buy:
        exchange.buy(symbol, trade_amount)
    elif should_sell:
        exchange.sell(symbol, trade_amount)
    else:
        print("No action needed.")
```

The `TradingBot` class and its protocol are gone entirely. The bridge is now implicit in the function signature: `should_buy_avg` accepts any object that satisfies `Exchange`.

### Step C: Higher-order functions with Callable type aliases

The functions above accept an `Exchange` object, but the only thing they call on it is `get_prices`. Replace the object dependency with a function dependency:

```python
# trading.py
from typing import Callable

GetPricesFunction = Callable[[str], list[int]]
```

```python
# avg_trading_bot.py
import statistics
from trading import GetPricesFunction


def should_buy_avg(get_prices: GetPricesFunction, symbol: str) -> bool:
    prices = get_prices(symbol)
    list_window = prices[-3:]
    return prices[-1] < statistics.mean(list_window)


def should_sell_avg(get_prices: GetPricesFunction, symbol: str) -> bool:
    prices = get_prices(symbol)
    list_window = prices[-3:]
    return prices[-1] > statistics.mean(list_window)
```

The trading bot functions no longer know about the `Exchange` class at all. They accept any callable that maps a symbol string to a list of prices.

### Step D: Bound methods as the bridge

In `main`, pass the bound method `exchange.get_prices` directly:

```python
# main.py
from binance import Binance
from avg_trading_bot import should_buy_avg, should_sell_avg


def main() -> None:
    symbol = "BTC/USD"
    trade_amount = 10

    exchange = Binance()

    should_buy = should_buy_avg(exchange.get_prices, symbol)
    should_sell = should_sell_avg(exchange.get_prices, symbol)

    if should_buy:
        exchange.buy(symbol, trade_amount)
    elif should_sell:
        exchange.sell(symbol, trade_amount)
    else:
        print("No action needed.")
```

Writing `exchange.get_prices` produces a callable bound to the `exchange` object. The strategy functions receive a `GetPricesFunction` -- they do not know an object exists behind it.

The bridge is now a **Callable type alias**. You can introduce new functions that fetch prices from different exchanges, and new trading strategies that accept a `GetPricesFunction`, and they never need to know about each other.

### Step E: functools.partial for full configuration

Define additional type aliases and a `run_bot` orchestrator that takes all its dependencies as functions:

```python
# trading.py
from typing import Callable

GetPricesFunction = Callable[[str], list[int]]
DecideFunction = Callable[[GetPricesFunction, str], bool]
BuySellFunction = Callable[[str, int], None]


def run_bot(
    get_prices: GetPricesFunction,
    should_buy: DecideFunction,
    should_sell: DecideFunction,
    buy: BuySellFunction,
    sell: BuySellFunction,
    symbol: str,
    trade_amount: int,
) -> None:
    if should_buy(get_prices, symbol):
        buy(symbol, trade_amount)
    elif should_sell(get_prices, symbol):
        sell(symbol, trade_amount)
    else:
        print("No action needed.")
```

Use `functools.partial` to pre-bind arguments and simplify the call site:

```python
# main.py
from functools import partial
from binance import Binance
from avg_trading_bot import should_buy_avg, should_sell_avg
from trading import run_bot


def main() -> None:
    symbol = "BTC/USD"
    trade_amount = 10

    exchange = Binance()

    run_bot(
        exchange.get_prices,
        should_buy_avg,
        should_sell_avg,
        exchange.buy,
        exchange.sell,
        symbol,
        trade_amount,
    )
```

Push partial application further to eliminate pass-through parameters entirely:

```python
# main.py
from functools import partial
from binance import buy, sell, get_prices  # now plain functions
from avg_trading_bot import should_buy_avg, should_sell_avg
from trading import run_bot


def main() -> None:
    symbol = "BTC/USD"
    trade_amount = 10

    get_prices_btc = partial(get_prices, symbol)
    should_buy = partial(should_buy_avg, symbol=symbol, get_prices=get_prices_btc)
    should_sell = partial(should_sell_avg, symbol=symbol, get_prices=get_prices_btc)
    buy_fn = partial(buy, symbol=symbol, amount=trade_amount)
    sell_fn = partial(sell, symbol=symbol, amount=trade_amount)

    run_bot(
        get_prices_btc,
        should_buy,
        should_sell,
        buy_fn,
        sell_fn,
    )
```

At this point `run_bot` receives fully-configured zero-argument (or near-zero-argument) callables. It is completely decoupled from exchanges, strategies, symbols, and amounts. Every dependency is a function, and `partial` wires them together at the composition root.

---

## 4. When to Stop

The fully functional version is possible, but it is not automatically better.

Observe what happened to `run_bot` at the extreme: it does almost nothing. It receives pre-configured functions and calls them in sequence. The orchestration logic is trivial, and the complexity has migrated into the `partial` calls in `main`. An object -- a group of functions with shared context -- would express this more clearly.

**The warning:** do not treat functional programming as the end-all-be-all. Going fully functional can obscure intent just as badly as deep inheritance hierarchies. The goal is clear, readable code with abstractions at the right level.

**Find the happy medium.** In practice, this usually means:

- Use **Step C or D** (higher-order functions with `Callable` type aliases, bound methods) as the default Pythonic bridge.
- Reach for **Step E** (full `functools.partial` composition) only when the dependencies genuinely need to be composed dynamically at startup.
- Fall back to **Step A** (Protocol-based classes) when the two sides of the bridge carry meaningful state or have more than two or three methods each.
- Reserve **classic ABCs** for when you need shared implementation in the superclass, not just an interface.

---

## 5. Trade-offs

| Approach | Strengths | Weaknesses |
|---|---|---|
| **ABC bridge** (classic) | Shared state in superclass; familiar OOP; IDE support for abstract method enforcement | Tight coupling via inheritance; verbose boilerplate; hard to test in isolation |
| **Protocol bridge** | Duck typing; no inheritance required; works with third-party classes | Duplicated attribute declarations in each concrete class; no shared implementation |
| **Functions taking objects** | Simpler; easy to test; no class needed for stateless strategies | Still depends on the object type (Exchange) |
| **Higher-order functions + Callable aliases** | Maximum decoupling; bridge is just a type alias; trivial to test with lambdas | Lose grouping of related functions; naming must compensate |
| **Bound methods** | Natural Python idiom; object stays coherent; consumer sees only a callable | Caller must know to pass `obj.method` rather than `obj` |
| **functools.partial** | Full configuration at the composition root; zero-arg callables everywhere | Can obscure what is happening; debugging partial chains is harder; over-engineering risk |

**Rule of thumb:** start with the simplest approach that keeps the two hierarchies independent. Escalate only when you hit a concrete problem -- not because a more functional version exists.

---

## 6. Related Patterns

### Bridge vs. Strategy

The Bridge pattern is structurally similar to Strategy. The key difference is scope:

- **Strategy** decouples *one* axis of variation. A class holds a reference to a single interchangeable behavior (one function or one interface).
- **Bridge** decouples *two* axes of variation. Two hierarchies each evolve independently, connected by an abstract reference.

Think of Bridge as **two strategies connected**: the `TradingBot` hierarchy is one strategy axis, and the `Exchange` hierarchy is the other. The bridge is the abstract link between them.

### Bridge vs. Adapter

- **Adapter** makes an existing interface conform to an expected one. It operates after the fact.
- **Bridge** separates hierarchies up front, by design. It prevents the Cartesian product problem before it arises.

### Bridge vs. Dependency Injection

The classic ABC bridge (`TradingBot.__init__(self, exchange: Exchange)`) is literally constructor injection. The Pythonic functional bridge (`should_buy_avg(get_prices, symbol)`) is parameter injection. Bridge is a structural pattern that *uses* dependency injection as its mechanism.
