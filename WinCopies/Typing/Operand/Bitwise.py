from types import NotImplementedType
from typing import overload, final, Literal, Self

from WinCopies.Delegates.Operators import And, Or, Xor, Invert, LeftShift, RightShift
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
        return self._ComputeObject(And, other, strict)

    @overload
    def Or(self, other: Self, strict: Literal[True] = True) -> Self: ...
    @overload
    def Or(self, other: Self, strict: Literal[False]) -> TValue: ...

    @final
    def Or(self, other: Self, strict: bool = True) -> Self|TValue:
        return self._ComputeObject(Or, other, strict)

    @overload
    def Xor(self, other: Self, strict: Literal[True] = True) -> Self: ...
    @overload
    def Xor(self, other: Self, strict: Literal[False]) -> TValue: ...

    @final
    def Xor(self, other: Self, strict: bool = True) -> Self|TValue:
        return self._ComputeObject(Xor, other, strict)

    @overload
    def Invert(self, strict: Literal[True] = True) -> Self: ...
    @overload
    def Invert(self, strict: Literal[False]) -> TValue: ...
    @final
    def Invert(self, strict: bool = True) -> Self|TValue:
        def invert() -> TValue: return Invert(self._GetUnderlyingValue())
        
        return self._CreateNew(invert()) if strict else invert()

    @overload
    def LeftShift(self, other: int, strict: Literal[True] = True) -> Self: ...
    @overload
    def LeftShift(self, other: int, strict: Literal[False]) -> TValue: ...

    @final
    def LeftShift(self, other: int, strict: bool = True) -> Self|TValue:
        return self._ComputeObjectValue(LeftShift, int, other, strict)

    @overload
    def RightShift(self, other: int, strict: Literal[True] = True) -> Self: ...
    @overload
    def RightShift(self, other: int, strict: Literal[False]) -> TValue: ...

    @final
    def RightShift(self, other: int, strict: bool = True) -> Self|TValue:
        return self._ComputeObjectValue(RightShift, int, other, strict)

    @final
    def __and__(self, other: Self, /) -> Self|NotImplementedType:
        return self._ComputeItem(And, other)
    @final
    def __or__(self, other: Self, /) -> Self|NotImplementedType:
        return self._ComputeItem(Or, other)
    @final
    def __xor__(self, other: Self, /) -> Self|NotImplementedType:
        return self._ComputeItem(Xor, other)

    @final
    def __invert__(self) -> Self:
        return self.Invert()
    
    @final
    def __lshift__(self, other: int, /) -> Self|NotImplementedType:
        return self._ComputeValue(LeftShift, int, other)
    @final
    def __rshift__(self, other: int, /) -> Self|NotImplementedType:
        return self._ComputeValue(RightShift, int, other)