"""Bounded unsigned integer arithmetic.

Arithmetic on unsigned integers restricted to the inclusive range [0, limit],
in four families that differ only in how they report overflow:

- ``Try*``: the result, or ``None`` on overflow.
- ``Saturating*``: the result clamped to [0, limit].
- ``Wrapping*``: the result modulo ``limit + 1``. With
  ``limit == GetMaxValue(n)``, this matches C unsigned n-bit arithmetic.
- ``Overflowing*``: the wrapped result paired with an overflow flag.
  Invariant: ``OverflowingX(...) == (WrappingX(...), TryX(...) is None)``.

Contract shared by every family:

- ``limit`` is an inclusive upper bound. ``None`` selects the default limit,
  ``GetMaxValue(GetMaxWordLength())`` (``2**64 - 1`` on 64-bit platforms).
- Operands ``x`` and ``y`` must lie within [0, limit].
- ``exponent`` must be non-negative. It is a repetition count, not a value of
  the domain, and is therefore not bounded by ``limit``.
- An invalid argument raises ``ValueError``. Overflow is never an error: each
  family reports it in its own way.
- For subtraction, overflow means a result below zero.
- ``x ** 0 == 1`` for any ``x``, including ``0``; with ``limit == 0``, it
  therefore overflows.
- Certain overflow of a product or a power is detected from bit lengths, in
  constant time, without computing the full result.
- Argument types are not checked at runtime: non-``int`` arguments give
  unspecified results.
"""

from operator import add, sub, mul
from sys import maxsize
from typing import Final, NoReturn

from WinCopies.Typing.Delegate import Operator
from WinCopies.Typing.Pairing import DualValueBool, CreateDualValueBool

_MAX_WORD_LENGTH: Final[int] = maxsize.bit_length() + 1

# Default limit of every family: the maximum value of an unsigned machine word.
_DEFAULT_LIMIT: Final[int] = (1 << _MAX_WORD_LENGTH) - 1

def GetMaxWordLength() -> int:
    """Return the bit width of an unsigned machine word on this platform.

    Derived from ``sys.maxsize``, i.e. the width of ``Py_ssize_t``: 64 on
    64-bit platforms, 32 on 32-bit platforms.
    """
    return _MAX_WORD_LENGTH

def GetMaxValue(bits: int) -> int:
    """Return the maximum value of an unsigned integer of ``bits`` bits: ``2**bits - 1``.

    Raises ``ValueError`` if ``bits`` is negative.
    """
    if bits < 0: raise ValueError("'bits' must be non-negative.")

    return (1 << bits) - 1

# Validation

def _GetLimit(limit: int|None) -> int:
    if limit is None: return _DEFAULT_LIMIT
    if limit < 0: raise ValueError("'limit' must be non-negative.")

    return limit

def _CheckOperand(name: str, value: int, limit: int) -> None:
    def throw(msg: str) -> NoReturn: raise ValueError(f"'{name}' must {msg}.")

    if value < 0: throw(f"be non-negative")
    if value > limit: throw(f"not exceed limit")

def _GetLimitFor(x: int, y: int, limit: int|None) -> int:
    _CheckOperand("x", x, limit := _GetLimit(limit))
    _CheckOperand("y", y, limit)

    return limit

def _GetLimitForPow(x: int, exponent: int, limit: int|None) -> int:
    _CheckOperand("x", x, limit := _GetLimit(limit))

    if exponent < 0: raise ValueError("'exponent' must be non-negative.")

    return limit

# Unchecked cores: arguments are assumed to be validated.

def _Mul(x: int, y: int, limit: int) -> int|None:
    if x == 0 or y == 0: return 0

    # The product has x.bit_length() + y.bit_length() - 1 bits at least:
    # certain overflow is rejected in constant time, without computing the product.
    if x.bit_length() + y.bit_length() - 1 > limit.bit_length(): return None

    result: int = x * y

    return None if result > limit else result

def _Pow(x: int, exponent: int, limit: int) -> int|None:
    if exponent == 0: return 1 if limit >= 1 else None
    if x < 2: return x

    # x ** exponent has exponent * (x.bit_length() - 1) + 1 bits at least.
    if exponent * (x.bit_length() - 1) + 1 > limit.bit_length(): return None

    result: int = x ** exponent

    return None if result > limit else result

# Try: None on overflow.

def TryAdd(x: int, y: int, limit: int|None = None) -> int|None:
    """Return ``x + y``, or ``None`` if it exceeds ``limit``."""

    limit = _GetLimitFor(x, y, limit)

    return None if y > limit - x else x + y

def TrySub(x: int, y: int, limit: int|None = None) -> int|None:
    """Return ``x - y``, or ``None`` if ``y > x``."""

    _GetLimitFor(x, y, limit)

    return None if y > x else x - y

def TryMul(x: int, y: int, limit: int|None = None) -> int|None:
    """Return ``x * y``, or ``None`` if it exceeds ``limit``."""

    return _Mul(x, y, _GetLimitFor(x, y, limit))

def TryPow(x: int, exponent: int, limit: int|None = None) -> int|None:
    """Return ``x ** exponent``, or ``None`` if it exceeds ``limit``."""

    return _Pow(x, exponent, _GetLimitForPow(x, exponent, limit))

# Saturating: clamped to [0, limit].

def SaturatingAdd(x: int, y: int, limit: int|None = None) -> int:
    """Return ``x + y``, clamped to ``limit``."""

    def add(limit: int) -> int: return min(x + y, limit)

    return add(_GetLimitFor(x, y, limit))

def SaturatingSub(x: int, y: int, limit: int|None = None) -> int:
    """Return ``x - y``, clamped to ``0``."""

    _GetLimitFor(x, y, limit)

    return 0 if y > x else x - y

def SaturatingMul(x: int, y: int, limit: int|None = None) -> int:
    """Return ``x * y``, clamped to ``limit``."""

    result: int|None = _Mul(x, y, limit := _GetLimitFor(x, y, limit))

    return limit if result is None else result

def SaturatingPow(x: int, exponent: int, limit: int|None = None) -> int:
    """Return ``x ** exponent``, clamped to ``limit``."""

    result: int|None = _Pow(x, exponent, limit := _GetLimitForPow(x, exponent, limit))

    return limit if result is None else result

# Wrapping: modulo limit + 1 (C unsigned semantics when limit == GetMaxValue(n)).

def _Wrap(operator: Operator[int], x: int, y: int, limit: int|None) -> int:
    def wrap(limit: int) -> int: return operator(x, y) % limit

    return wrap(_GetLimitFor(x, y, limit) + 1)

def WrappingAdd(x: int, y: int, limit: int|None = None) -> int:
    """Return ``(x + y) % (limit + 1)``."""

    return _Wrap(add, x, y, limit)

def WrappingSub(x: int, y: int, limit: int|None = None) -> int:
    """Return ``(x - y) % (limit + 1)``."""

    return _Wrap(sub, x, y, limit)

def WrappingMul(x: int, y: int, limit: int|None = None) -> int:
    """Return ``(x * y) % (limit + 1)``."""

    return _Wrap(mul, x, y, limit)

def WrappingPow(x: int, exponent: int, limit: int|None = None) -> int:
    """Return ``(x ** exponent) % (limit + 1)``.

    Uses modular exponentiation: the full power is never computed.
    """
    return pow(x, exponent, _GetLimitForPow(x, exponent, limit) + 1)

# Overflowing: wrapped result and overflow flag.
# Invariant: OverflowingX(...) == (WrappingX(...), TryX(...) is None)

def _Overflow(operator: Operator[int], x: int, y: int, limit: int|None) -> DualValueBool[int]:
    def overflow(limit: int) -> DualValueBool[int]:
        result: int = operator(x, y)

        return CreateDualValueBool(result % (limit + 1), not 0 <= result <= limit)

    return overflow(_GetLimitFor(x, y, limit))

def OverflowingAdd(x: int, y: int, limit: int|None = None) -> DualValueBool[int]:
    """Return ``(x + y) % (limit + 1)``, paired with whether ``x + y`` exceeds ``limit``."""

    return _Overflow(add, x, y, limit)

def OverflowingSub(x: int, y: int, limit: int|None = None) -> DualValueBool[int]:
    """Return ``(x - y) % (limit + 1)``, paired with whether ``y > x``."""

    return _Overflow(sub, x, y, limit)

def OverflowingMul(x: int, y: int, limit: int|None = None) -> DualValueBool[int]:
    """Return ``(x * y) % (limit + 1)``, paired with whether ``x * y`` exceeds ``limit``."""

    return _Overflow(mul, x, y, limit)

def OverflowingPow(x: int, exponent: int, limit: int|None = None) -> DualValueBool[int]:
    """Return ``(x ** exponent) % (limit + 1)``, paired with whether ``x ** exponent`` exceeds ``limit``.

    Neither the result nor the flag requires computing the full power.
    """
    def _pow(limit: int) -> DualValueBool[int]:
        return CreateDualValueBool(pow(x, exponent, limit + 1), _Pow(x, exponent, limit) is None)

    return _pow(_GetLimitForPow(x, exponent, limit))