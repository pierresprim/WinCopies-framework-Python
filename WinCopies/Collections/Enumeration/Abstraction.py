from abc import abstractmethod
from typing import final

from WinCopies.Collections.Enumeration.Core import IEnumeratorBase, IEnumerator, EnumeratorBase
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Converter
from WinCopies.Typing.Generic import GenericConstraint, IGenericConstraintImplementation

class AbstractEnumeratorBase[TIn, TOut, TEnumerator: IEnumeratorBase](EnumeratorBase[TOut], GenericConstraint[TEnumerator, IEnumerator[TIn]]):
    def __init__(self, enumerator: TEnumerator) -> None:
        super().__init__()
        
        self.__enumerator: TEnumerator = enumerator
    
    @final
    def _GetContainer(self) -> TEnumerator: return self.__enumerator
    
    @final
    def IsResetSupported(self) -> bool: return self._GetContainer().IsResetSupported()
    
    def _MoveNextOverride(self) -> bool: return self._GetContainer().MoveNext()
    
    def _OnAborted(self) -> None: self._GetContainer().Stop()
    
    def _ResetOverride(self) -> bool: return self._GetContainer().TryReset() is True
class Selector[TIn, TOut](AbstractEnumeratorBase[TIn, TOut, IEnumerator[TIn]], IGenericConstraintImplementation[IEnumerator[TIn]]):
    def __init__(self, enumerator: IEnumerator[TIn]) -> None: super().__init__(enumerator)
class AbstractEnumerator[T](Selector[T, T]):
    def __init__(self, enumerator: IEnumerator[T]) -> None: super().__init__(enumerator)
    
    def _GetCurrent(self) -> T: return self._GetContainer().GetCurrent()

class AbstractionEnumeratorBase[TIn, TOut, TEnumerator: IEnumeratorBase](AbstractEnumeratorBase[TIn, TOut, TEnumerator]):
    def __init__(self, enumerator: TEnumerator) -> None: super().__init__(enumerator)
    
    def _OnAborting(self, enumerator: TEnumerator) -> None:
        pass
    def _OnAbortedOverride(self) -> None:
        pass
    
    @final
    def _OnAborted(self) -> None:
        enumerator: TEnumerator = self._GetContainer()
        
        if enumerator.IsStarted(): self._OnAborting(enumerator)

        super()._OnAborted()

        self._OnAbortedOverride()
class AbstractionEnumerator[TIn, TOut](AbstractionEnumeratorBase[TIn, TOut, IEnumerator[TIn]], IGenericConstraintImplementation[IEnumerator[TIn]]):
    def __init__(self, enumerator: IEnumerator[TIn]) -> None: super().__init__(enumerator)

class ConverterEnumeratorBase[TIn, TOut](AbstractionEnumerator[TIn, TOut]):
    def __init__(self, enumerator: IEnumerator[TIn]) -> None:
        super().__init__(enumerator)

        self.__current: INullable[TOut] = GetNullValue()
    
    @abstractmethod
    def _Convert(self, value: TIn) -> TOut:
        ...
    
    def _MoveNextOverride(self) -> bool:
        if super()._MoveNextOverride():
            current: TIn = self._GetContainer().GetCurrent()

            self.__current = GetNullable(self._Convert(current))

            return True
        
        return False
    
    def _OnEnded(self) -> None:
        self.__current = GetNullValue()
        
        super()._OnEnded()
    
    def _ResetOverride(self) -> bool: return True
    
    @final
    def _GetCurrent(self) -> TOut: return self.__current.GetValue()
class ConverterEnumerator[TIn, TOut](ConverterEnumeratorBase[TIn, TOut]):
    def __init__(self, enumerator: IEnumerator[TIn], selector: Converter[TIn, TOut]) -> None:
        super().__init__(enumerator)

        self.__selector: Converter[TIn, TOut] = selector
    
    @final
    def _Convert(self, value: TIn) -> TOut:
        return self.__selector(value)