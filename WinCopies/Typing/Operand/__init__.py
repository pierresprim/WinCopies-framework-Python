from abc import abstractmethod
from types import NotImplementedType
from typing import final, Callable, Self, Type

from WinCopies import IInterface
from WinCopies.Typing.Delegate import Operator, RichOperator

def ThrowIfNotImplemented[T](value: T|NotImplementedType) -> T:
    if isinstance(value, NotImplementedType): raise NotImplementedError()

    return value

class IOperand[TObject, TValue](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetUnderlyingValue(self) -> TValue:
        ...
    @abstractmethod
    def _CreateNew(self, value: TValue) -> Self:
        ...

    @final
    def __Compute(self, operator: Operator[TValue], other: Self|TObject) -> TValue|NotImplementedType: return operator(self._GetUnderlyingValue(), other._GetUnderlyingValue()) if isinstance(other, type(self)) else NotImplemented
    @final
    def __ComputeValue[T](self, operator: RichOperator[TValue, T], t: Type[T], other: T) -> TValue|NotImplementedType: return operator(self._GetUnderlyingValue(), other) if isinstance(other, t) else NotImplemented

    @final
    def __ComputeObject[TOperator, TOther](self, operator: TOperator, other: TOther, strict: bool, func: Callable[[TOperator, TOther], TValue|NotImplementedType]) -> Self|TValue:
        def compute() -> TValue: return ThrowIfNotImplemented(func(operator, other))
        
        return self._CreateNew(compute()) if strict else compute()
    @final
    def __ComputeItem(self, value: TValue|NotImplementedType) -> Self|NotImplementedType:
        return NotImplemented if isinstance(value, NotImplementedType) else self._CreateNew(value)

    @final
    def _ComputeObject(self, operator: Operator[TValue], other: Self, strict: bool) -> Self|TValue:
        return self.__ComputeObject(operator, other, strict, self.__Compute)
    @final
    def _ComputeItem(self, operator: Operator[TValue], other: Self) -> Self|NotImplementedType:
        return self.__ComputeItem(self.__Compute(operator, other))

    @final
    def _ComputeObjectValue[T](self, operator: RichOperator[TValue, T], t: Type[T], other: T, strict: bool) -> Self|TValue:
        return self.__ComputeObject(operator, other, strict, lambda operator, other: self.__ComputeValue(operator, t, other))
    @final
    def _ComputeValue[T](self, operator: RichOperator[TValue, T], t: Type[T], other: T) -> Self|NotImplementedType:
        return self.__ComputeItem(self.__ComputeValue(operator, t, other))