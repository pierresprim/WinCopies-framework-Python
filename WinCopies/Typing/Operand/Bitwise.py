from operator import and_, or_, xor, lshift, rshift
from types import NotImplementedType
from typing import overload, final, Literal, Self

from WinCopies.Typing.Operand import IOperand
from WinCopies.Typing.Protocols.Bitwise import SupportsBitwise

class IBitwiseItem[TObject, TValue: SupportsBitwise](IOperand[TObject, TValue]):
    def __init__(self) -> None: super().__init__()

    @overload
    def And(self, other: Self, strict: Literal[True] = True) -> Self: ...
    @overload
    def And(self, other: Self, strict: Literal[False]) -> TValue: ...

    @final
    def And(self, other: Self, strict: bool = True) -> Self|TValue:
        return self._ComputeObject(and_, other, strict)

    @overload
    def Or(self, other: Self, strict: Literal[True] = True) -> Self: ...
    @overload
    def Or(self, other: Self, strict: Literal[False]) -> TValue: ...

    @final
    def Or(self, other: Self, strict: bool = True) -> Self|TValue:
        return self._ComputeObject(or_, other, strict)

    @overload
    def Xor(self, other: Self, strict: Literal[True] = True) -> Self: ...
    @overload
    def Xor(self, other: Self, strict: Literal[False]) -> TValue: ...

    @final
    def Xor(self, other: Self, strict: bool = True) -> Self|TValue:
        return self._ComputeObject(xor, other, strict)

    @overload
    def LeftShift(self, other: int, strict: Literal[True] = True) -> Self: ...
    @overload
    def LeftShift(self, other: int, strict: Literal[False]) -> TValue: ...

    @final
    def LeftShift(self, other: int, strict: bool = True) -> Self|TValue:
        return self._ComputeObjectValue(lshift, int, other, strict)

    @overload
    def RightShift(self, other: int, strict: Literal[True] = True) -> Self: ...
    @overload
    def RightShift(self, other: int, strict: Literal[False]) -> TValue: ...

    @final
    def RightShift(self, other: int, strict: bool = True) -> Self|TValue:
        return self._ComputeObjectValue(rshift, int, other, strict)

    @final
    def __and__(self, other: Self, /) -> Self|NotImplementedType:
        return self._ComputeItem(and_, other)
    @final
    def __or__(self, other: Self, /) -> Self|NotImplementedType:
        return self._ComputeItem(or_, other)
    @final
    def __xor__(self, other: Self, /) -> Self|NotImplementedType:
        return self._ComputeItem(xor, other)
    
    @final
    def __lshift__(self, other: int, /) -> Self|NotImplementedType:
        return self._ComputeValue(lshift, int, other)
    @final
    def __rshift__(self, other: int, /) -> Self|NotImplementedType:
        return self._ComputeValue(rshift, int, other)