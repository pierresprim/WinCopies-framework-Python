from types import NotImplementedType
from typing import overload, final, Literal, Self

from WinCopies.Typing.Operand import IOperand
from WinCopies.Typing.Protocols.Bitwise import SupportsLogic, SupportsShift, SupportsBitwise

def _And[T: SupportsLogic](x: T, y: T, /) -> T: return x & y
def _Or[T: SupportsLogic](x: T, y: T, /) -> T: return x | y
def _Xor[T: SupportsLogic](x: T, y: T, /) -> T: return x ^ y

def _LeftShift[T: SupportsShift](x: T, y: int, /) -> T: return x << y
def _RightShift[T: SupportsShift](x: T, y: int, /) -> T: return x >> y

class IBitwiseItem[TObject, TValue: SupportsBitwise](IOperand[TObject, TValue]):
    def __init__(self) -> None: super().__init__()

    @overload
    def And(self, other: Self, strict: Literal[True] = True) -> Self: ...
    @overload
    def And(self, other: Self, strict: Literal[False]) -> TValue: ...

    @final
    def And(self, other: Self, strict: bool = True) -> Self|TValue:
        return self._ComputeObject(_And, other, strict)

    @overload
    def Or(self, other: Self, strict: Literal[True] = True) -> Self: ...
    @overload
    def Or(self, other: Self, strict: Literal[False]) -> TValue: ...

    @final
    def Or(self, other: Self, strict: bool = True) -> Self|TValue:
        return self._ComputeObject(_Or, other, strict)

    @overload
    def Xor(self, other: Self, strict: Literal[True] = True) -> Self: ...
    @overload
    def Xor(self, other: Self, strict: Literal[False]) -> TValue: ...

    @final
    def Xor(self, other: Self, strict: bool = True) -> Self|TValue:
        return self._ComputeObject(_Xor, other, strict)

    @overload
    def LeftShift(self, other: int, strict: Literal[True] = True) -> Self: ...
    @overload
    def LeftShift(self, other: int, strict: Literal[False]) -> TValue: ...

    @final
    def LeftShift(self, other: int, strict: bool = True) -> Self|TValue:
        return self._ComputeObjectValue(_LeftShift, int, other, strict)

    @overload
    def RightShift(self, other: int, strict: Literal[True] = True) -> Self: ...
    @overload
    def RightShift(self, other: int, strict: Literal[False]) -> TValue: ...

    @final
    def RightShift(self, other: int, strict: bool = True) -> Self|TValue:
        return self._ComputeObjectValue(_RightShift, int, other, strict)

    @final
    def __and__(self, other: Self, /) -> Self|NotImplementedType:
        return self._ComputeItem(_And, other)
    @final
    def __or__(self, other: Self, /) -> Self|NotImplementedType:
        return self._ComputeItem(_Or, other)
    @final
    def __xor__(self, other: Self, /) -> Self|NotImplementedType:
        return self._ComputeItem(_Xor, other)
    
    @final
    def __lshift__(self, other: int, /) -> Self|NotImplementedType:
        return self._ComputeValue(_LeftShift, int, other)
    @final
    def __rshift__(self, other: int, /) -> Self|NotImplementedType:
        return self._ComputeValue(_RightShift, int, other)