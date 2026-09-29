from types import NotImplementedType
from typing import final, Self

from WinCopies import IsTruthy, IsFalsy
from WinCopies.Typing.Delegate import Converter
from WinCopies.Typing.Operand import IOperandBase, ThrowIfNotImplemented
from WinCopies.Typing.Protocols import SupportsEqualityComparison, SupportsEqualityAndRichComparison

# Same semantics as WinCopies.Comparison.CompareTo, which cannot be imported here: WinCopies.Comparison imports WinCopies.Enum and thus WinCopies.Typing.Enum,
# which imports this module.
def _CompareValues[T: SupportsEqualityAndRichComparison](x: T, y: T) -> bool|None:
    return None if x == y else x > y

# Unlike the interfaces of WinCopies.Typing.Comparison, these compare an operand only with an operand of its own type, never with a raw value. Operators return
# NotImplemented for any other operand: == then falls back to identity and yields False, while ordering operators raise TypeError.

class IEquatableOperand[TValue: SupportsEqualityComparison](IOperandBase[TValue]):
    def __init__(self) -> None: super().__init__()

    @final
    def __Equals(self, other: object) -> bool|None:
        return self._GetUnderlyingValue() == other._GetUnderlyingValue() if isinstance(other, type(self)) else None

    @final
    def Equals(self, other: Self) -> bool: return self.__Equals(other) is True

    @final
    def __eq__(self, other: object, /) -> bool:
        result: bool|None = self.__Equals(other)

        return NotImplemented if result is None else result

# IHashableOperand must precede IEquatableOperand in the MRO: defining __eq__ sets __hash__ to None in IEquatableOperand.
class IHashableOperand[TValue: SupportsEqualityComparison](IEquatableOperand[TValue]):
    def __init__(self) -> None: super().__init__()

    @final
    def Hash(self) -> int: return hash(self._GetUnderlyingValue())

    @final
    def __hash__(self) -> int:
        return self.Hash()

class IComparableOperand[TValue: SupportsEqualityAndRichComparison](IEquatableOperand[TValue]):
    def __init__(self) -> None: super().__init__()

    @final
    def __CompareTo(self, other: Self) -> bool|None|NotImplementedType:
        return _CompareValues(self._GetUnderlyingValue(), other._GetUnderlyingValue()) if isinstance(other, type(self)) else NotImplemented

    @final
    def __Compare(self, other: Self, selector: Converter[bool|None, bool]) -> bool:
        result: bool|None|NotImplementedType = self.__CompareTo(other)

        return NotImplemented if isinstance(result, NotImplementedType) else selector(result)

    @final
    def CompareTo(self, other: Self) -> bool|None:
        return ThrowIfNotImplemented(self.__CompareTo(other))

    @final
    def IsLessThan(self, other: Self) -> bool:
        return self.CompareTo(other) is False
    @final
    def IsLessThanOrEqual(self, other: Self) -> bool:
        return IsFalsy(self.CompareTo(other))
    @final
    def IsGreaterThan(self, other: Self) -> bool:
        return IsTruthy(self.CompareTo(other))
    @final
    def IsGreaterThanOrEqual(self, other: Self) -> bool:
        return self.CompareTo(other) is not False

    @final
    def __lt__(self, other: Self, /) -> bool:
        return self.__Compare(other, lambda result: result is False)
    @final
    def __le__(self, other: Self, /) -> bool:
        return self.__Compare(other, IsFalsy)
    @final
    def __gt__(self, other: Self, /) -> bool:
        return self.__Compare(other, IsTruthy)
    @final
    def __ge__(self, other: Self, /) -> bool:
        return self.__Compare(other, lambda result: result is not False)

class IHashableComparableOperand[TValue: SupportsEqualityAndRichComparison](IHashableOperand[TValue], IComparableOperand[TValue]):
    def __init__(self) -> None: super().__init__()