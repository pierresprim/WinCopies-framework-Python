from sys import maxsize
from typing import Final

from WinCopies.Typing.Pairing import DualValueBool, CreateDualValueBool

_MAX_WORD_LENGTH: Final[int] = maxsize.bit_length() + 1

# Default limit of every family: the maximum value of an unsigned machine word.
_DEFAULT_LIMIT: Final[int] = (1 << _MAX_WORD_LENGTH) - 1

def GetMaxWordLength() -> int:
    return _MAX_WORD_LENGTH

def GetMaxValue(bits: int) -> int:
    if bits < 0: raise ValueError("Bits must be non-negative.")

    return (1 << bits) - 1

# Validation

def _GetLimit(limit: int|None) -> int:
    if limit is None: return _DEFAULT_LIMIT
    if limit < 0: raise ValueError("'limit' must be non-negative.")

    return limit

def _CheckOperand(name: str, value: int, limit: int) -> None:
    def throw(msg: str) -> None: raise ValueError(f"'{name}' must {msg}.")

    if value < 0: throw(f"be non-negative")
    if value > limit: throw(f"not exceed limit")

def _GetLimitFor(x: int, y: int, limit: int|None) -> int:
    _CheckOperand("x", x, limit := _GetLimit(limit))
    _CheckOperand("y", y, limit)

    return limit

def _GetLimitForPow(x: int, exponent: int, limit: int|None) -> int:
    _CheckOperand("x", x, limit := _GetLimit(limit))

    if exponent < 0: raise ValueError("Exponent must be non-negative.")

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

# Checked: None on overflow.

def TryAdd(x: int, y: int, limit: int|None = None) -> int|None:
    limit = _GetLimitFor(x, y, limit)

    return None if y > limit - x else x + y

def TrySub(x: int, y: int, limit: int|None = None) -> int|None:
    _GetLimitFor(x, y, limit)

    return None if y > x else x - y

def TryMul(x: int, y: int, limit: int|None = None) -> int|None:
    return _Mul(x, y, _GetLimitFor(x, y, limit))

def TryPow(x: int, exponent: int, limit: int|None = None) -> int|None:
    return _Pow(x, exponent, _GetLimitForPow(x, exponent, limit))

# Saturating: clamped to [0, limit].

def SaturatingAdd(x: int, y: int, limit: int|None = None) -> int:
    return min(x + y, _GetLimitFor(x, y, limit))

def SaturatingSub(x: int, y: int, limit: int|None = None) -> int:
    _GetLimitFor(x, y, limit)

    return 0 if y > x else x - y

def SaturatingMul(x: int, y: int, limit: int|None = None) -> int:
    result: int|None = _Mul(x, y, limit := _GetLimitFor(x, y, limit))

    return limit if result is None else result

def SaturatingPow(x: int, exponent: int, limit: int|None = None) -> int:
    result: int|None = _Pow(x, exponent, limit := _GetLimitForPow(x, exponent, limit))

    return limit if result is None else result

# Wrapping: modulo limit + 1 (C unsigned semantics when limit == GetMaxValue(n)).

def _Wrap(value: int, x: int, y: int, limit: int|None) -> int:
    return value % (_GetLimitFor(x, y, limit) + 1)

def WrappingAdd(x: int, y: int, limit: int|None = None) -> int:
    return _Wrap(x + y, x, y, limit)

def WrappingSub(x: int, y: int, limit: int|None = None) -> int:
    return _Wrap(x - y, x, y, limit)

def WrappingMul(x: int, y: int, limit: int|None = None) -> int:
    return _Wrap(x * y, x, y, limit)

def WrappingPow(x: int, exponent: int, limit: int|None = None) -> int:
    return pow(x, exponent, _GetLimitForPow(x, exponent, limit) + 1)

# Overflowing: wrapped result and overflow flag.
# Invariant: OverflowingX(...) == (WrappingX(...), X(...) is None)

def _Overflow(result: int, limit: int) -> DualValueBool[int]:
    return CreateDualValueBool(result % (limit + 1), result > limit)

def OverflowingAdd(x: int, y: int, limit: int|None = None) -> DualValueBool[int]:
    return _Overflow(x + y, _GetLimitFor(x, y, limit))

def OverflowingSub(x: int, y: int, limit: int|None = None) -> DualValueBool[int]:
    return CreateDualValueBool((x - y) % (_GetLimitFor(x, y, limit) + 1), y > x)

def OverflowingMul(x: int, y: int, limit: int|None = None) -> DualValueBool[int]:
    return _Overflow(x * y, _GetLimitFor(x, y, limit))

def OverflowingPow(x: int, exponent: int, limit: int|None = None) -> DualValueBool[int]:
    limit = _GetLimitForPow(x, exponent, limit)

    return CreateDualValueBool(pow(x, exponent, limit + 1), _Pow(x, exponent, limit) is None)