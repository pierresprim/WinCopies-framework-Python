from abc import abstractmethod
from types import NotImplementedType
from typing import final, Self, Type, cast

from WinCopies import IInterface
from WinCopies.Typing.Delegate import Function, Operator, RichOperator

def ThrowIfNotImplemented[T](value: T|NotImplementedType) -> T:
    if value is NotImplemented: raise NotImplementedError()

    return cast(T, value)

class IOperand[TObject, TValue](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetUnderlyingValue(self) -> TValue:
        ...
    @abstractmethod
    def _CreateNew(self, value: TValue) -> Self:
        ...

    @final
    def __Compute(self, operator: Operator[TValue], other: Self|TObject, value: TValue) -> TValue|NotImplementedType: return operator(self._GetUnderlyingValue(), value) if isinstance(other, type(self)) else NotImplemented
    @final
    def __ComputeValue[T](self, operator: RichOperator[TValue, T], t: Type[T], other: T) -> TValue|NotImplementedType: return operator(self._GetUnderlyingValue(), other) if isinstance(other, t) else NotImplemented

    @final
    def __ComputeObject(self, strict: bool, func: Function[TValue|NotImplementedType]) -> Self|TValue:
        def compute() -> TValue: return ThrowIfNotImplemented(func())
        
        return self._CreateNew(compute()) if strict else compute()
    @final
    def __ComputeItem(self, value: TValue|NotImplementedType) -> Self|NotImplementedType:
        return NotImplemented if value is NotImplemented else self._CreateNew(cast(TValue, value))

    @final
    def _ComputeObject(self, operator: Operator[TValue], other: Self, strict: bool = True) -> Self|TValue:
        return self.__ComputeObject(strict, lambda: self.__Compute(operator, other, other._GetUnderlyingValue()))
    @final
    def _ComputeItem(self, operator: Operator[TValue], other: Self) -> Self|NotImplementedType:
        return self.__ComputeItem(self.__Compute(operator, other, other._GetUnderlyingValue()))

    @final
    def _ComputeObjectValue[T](self, operator: RichOperator[TValue, T], t: Type[T], other: T, strict: bool = True) -> Self|TValue:
        return self.__ComputeObject(strict, lambda: self.__ComputeValue(operator, t, other))
    @final
    def _ComputeValue[T](self, operator: RichOperator[TValue, T], t: Type[T], other: T) -> Self|NotImplementedType:
        return self.__ComputeItem(self.__ComputeValue(operator, t, other))