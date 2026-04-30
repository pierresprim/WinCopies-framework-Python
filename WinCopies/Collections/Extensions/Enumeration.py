from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import Abstract, IDisposableBase
from WinCopies.Collections.Enumeration import IEnumerator, IncrementalEnumerator, ToDisposableEnumerator
from WinCopies.Collections.Extensions import ITuple, IEnumeratorMonitor
from WinCopies.Collections.Generation.Factory import IObjectFactory, ObjectFactory
from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import GenericConstraint, IGenericConstraintImplementation

class TupleEnumeratorBase[TItem, TList](IncrementalEnumerator[TItem], GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__list: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__list
    
    @final
    def _GetMaxValue(self) -> int:
        return self._GetInnerContainer().GetCount()
    
    @final
    def _GetCurrent(self) -> TItem:
        return self._GetInnerContainer().GetAt(self._GetValue())
class TupleEnumerator[T](TupleEnumeratorBase[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None:
        super().__init__(items)

class IEnumeratorFactory[T](IObjectFactory[IEnumerator[T]], IEnumeratorMonitor[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsMonitor(self) -> IEnumeratorMonitor[T]:
        pass

@final
class _EnumeratorMonitor[T](Abstract, IEnumeratorMonitor[T]):
    def __init__(self, factory: IEnumeratorFactory[T]) -> None:
        super().__init__()

        self.__factory: IEnumeratorFactory[T] = factory
    
    def CreateEnumerator(self, items: ITuple[T]) -> IEnumerator[T]:
        return self.__factory.CreateEnumerator(items)
@final
class _EnumeratorMonitorUpdater[T](ValueFunctionUpdater[IEnumeratorMonitor[T]]):
    def __init__(self, factory: IEnumeratorFactory[T], updater: Method[IFunction[IEnumeratorMonitor[T]]]) -> None:
        super().__init__(updater)

        self.__factory: IEnumeratorFactory[T] = factory
    
    def _GetValue(self) -> IEnumeratorMonitor[T]:
        return _EnumeratorMonitor[T](self.__factory)

class EnumeratorFactory[T](ObjectFactory[IEnumerator[T]], IEnumeratorFactory[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IEnumeratorMonitor[T]]) -> None:
            self.__monitor = func
        
        super().__init__()

        self.__monitor: IFunction[IEnumeratorMonitor[T]] = _EnumeratorMonitorUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def _Convert(self, item: IEnumerator[T]) -> IDisposableBase:
        return ToDisposableEnumerator(item)
    
    @final
    def CreateEnumerator(self, items: ITuple[T]) -> IEnumerator[T]:
        enumerator: IEnumerator[T] = TupleEnumerator[T](items)

        self._Push(enumerator)

        return enumerator
    
    @final
    def AsMonitor(self) -> IEnumeratorMonitor[T]:
        return self.__monitor.GetValue()