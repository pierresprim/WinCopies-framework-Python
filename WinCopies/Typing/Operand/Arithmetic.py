from operator import add, sub
from types import NotImplementedType
from typing import overload, final, Literal, Self

from WinCopies.Typing.Operand import IOperand
from WinCopies.Typing.Protocols.Arithmetic import SupportsAddSub

class IAdditionableItem[TObject, TValue: SupportsAddSub](IOperand[TObject, TValue]):
    def __init__(self) -> None: super().__init__()

    @overload
    def Add(self, other: Self, strict: Literal[True] = True) -> Self: ...
    @overload
    def Add(self, other: Self, strict: Literal[False]) -> TValue: ...

    @final
    def Add(self, other: Self, strict: bool = True) -> Self|TValue:
        return self._ComputeObject(add, other, strict)

    @overload
    def Sub(self, other: Self, strict: Literal[True] = True) -> Self: ...
    @overload
    def Sub(self, other: Self, strict: Literal[False]) -> TValue: ...

    @final
    def Sub(self, other: Self, strict: bool = True) -> Self|TValue:
        return self._ComputeObject(sub, other, strict)

    @final
    def __add__(self, other: Self, /) -> Self|NotImplementedType:
        return self._ComputeItem(add, other)
    @final
    def __sub__(self, other: Self, /) -> Self|NotImplementedType:
        return self._ComputeItem(sub, other)