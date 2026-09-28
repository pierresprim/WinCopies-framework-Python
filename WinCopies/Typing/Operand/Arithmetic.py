from abc import abstractmethod
from operator import add, sub
from types import NotImplementedType
from typing import overload, final, Literal, Self, cast

from WinCopies import IInterface
from WinCopies.Typing.Delegate import Operator
from WinCopies.Typing.Operand import ThrowIfNotImplemented
from WinCopies.Typing.Protocols.Arithmetic import SupportsAddSub

class IArithmeticItem[T: SupportsAddSub](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetArithmeticValue(self) -> T:
        ...
    @abstractmethod
    def _CreateNew(self, value: T) -> Self:
        ...

class IAdditionable[TObject, TValue: SupportsAddSub](IArithmeticItem[TValue]):
    def __init__(self) -> None: super().__init__()

    @final
    def __Add(self, operator: Operator[TValue], other: Self|TObject, value: TValue) -> TValue|NotImplementedType: return operator(self._GetArithmeticValue(), value) if isinstance(other, type(self)) else NotImplemented

    @final
    def __AddObject(self, operator: Operator[TValue], other: Self, strict: bool = True) -> Self|TValue:
        def _add() -> TValue: return ThrowIfNotImplemented(self.__Add(operator, other, other._GetArithmeticValue()))
        
        return self._CreateNew(_add()) if strict else _add()
    @final
    def __AddValue(self, operator: Operator[TValue], other: Self) -> Self|NotImplementedType:
        value: TValue|NotImplementedType = self.__Add(operator, other, other._GetArithmeticValue())

        return NotImplemented if value is NotImplemented else self._CreateNew(cast(TValue, value))

    @overload
    def Add(self, other: Self, strict: Literal[True] = True) -> Self: ...
    @overload
    def Add(self, other: Self, strict: Literal[False]) -> TValue: ...

    @final
    def Add(self, other: Self, strict: bool = True) -> Self|TValue:
        return self.__AddObject(add, other, strict)

    @overload
    def Sub(self, other: Self, strict: Literal[True] = True) -> Self: ...
    @overload
    def Sub(self, other: Self, strict: Literal[False]) -> TValue: ...

    @final
    def Sub(self, other: Self, strict: bool = True) -> Self|TValue:
        return self.__AddObject(sub, other, strict)

    @final
    def __add__(self, other: Self, /) -> Self|NotImplementedType:
        return self.__AddValue(add, other)
    @final
    def __sub__(self, other: Self, /) -> Self|NotImplementedType:
        return self.__AddValue(sub, other)