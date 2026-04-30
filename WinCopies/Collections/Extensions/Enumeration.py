from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import Abstract, IDisposableBase
from WinCopies.Collections.Enumeration import IEnumerator, IncrementalEnumerator, ToDisposableEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator, IncrementalResumableEnumerator
from WinCopies.Collections.Extensions import ITuple, IEnumeratorMonitor, IResumableEnumeratorMonitor
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

class ResumableTupleEnumeratorBase[TItem, TList](IncrementalResumableEnumerator[TItem], GenericConstraint[TList, ITuple[TItem]]):
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
class ResumableTupleEnumerator[T](ResumableTupleEnumeratorBase[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None:
        super().__init__(items)

class IEnumeratorFactory[T](IObjectFactory[IEnumerator[T]], IEnumeratorMonitor[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsMonitor(self) -> IEnumeratorMonitor[T]:
        pass
class IResumableEnumeratorFactory[T](IEnumeratorFactory[T], IResumableEnumeratorMonitor[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsMonitor(self) -> IResumableEnumeratorMonitor[T]:
        pass

class EnumeratorMonitor[TItem, TFactory](Abstract, IEnumeratorMonitor[TItem], GenericConstraint[TFactory, IEnumeratorFactory[TItem]]):
    def __init__(self, factory: TFactory) -> None:
        super().__init__()

        self.__factory: TFactory = factory
    
    @final
    def _GetContainer(self) -> TFactory:
        return self.__factory
    
    @final
    def CreateEnumerator(self, items: ITuple[TItem]) -> IEnumerator[TItem]:
        return self._GetInnerContainer().CreateEnumerator(items)
class EnumeratorMonitorUpdater[TMonitor, TFactory](ValueFunctionUpdater[TMonitor]):
    def __init__(self, factory: TFactory, updater: Method[IFunction[TMonitor]]) -> None:
        super().__init__(updater)

        self.__factory: TFactory = factory
    
    @final
    def _GetFactory(self) -> TFactory:
        return self.__factory

@final
class _EnumeratorMonitor[T](EnumeratorMonitor[T, IEnumeratorFactory[T]]):
    def __init__(self, factory: IEnumeratorFactory[T]) -> None:
        super().__init__(factory)
    
    def _AsContainer(self, container: IEnumeratorFactory[T]) -> IEnumeratorFactory[T]:
        return container
@final
class _EnumeratorMonitorUpdater[T](EnumeratorMonitorUpdater[IEnumeratorMonitor[T], IEnumeratorFactory[T]]):
    def __init__(self, factory: IEnumeratorFactory[T], updater: Method[IFunction[IEnumeratorMonitor[T]]]) -> None:
        super().__init__(factory, updater)
    
    def _GetValue(self) -> IEnumeratorMonitor[T]:
        return _EnumeratorMonitor[T](self._GetFactory())

@final
class _ResumableEnumeratorMonitor[T](EnumeratorMonitor[T, IResumableEnumeratorFactory[T]], IResumableEnumeratorMonitor[T]):
    def __init__(self, factory: IResumableEnumeratorFactory[T]) -> None:
        super().__init__(factory)
    
    def _AsContainer(self, container: IResumableEnumeratorFactory[T]) -> IResumableEnumeratorFactory[T]:
        return container
    
    def CreateResumableEnumerator(self, items: ITuple[T]) -> IResumableEnumerator[T]:
        return self._GetContainer().CreateResumableEnumerator(items)
@final
class _ResumableEnumeratorMonitorUpdater[T](EnumeratorMonitorUpdater[IResumableEnumeratorMonitor[T], IResumableEnumeratorFactory[T]]):
    def __init__(self, factory: IResumableEnumeratorFactory[T], updater: Method[IFunction[IResumableEnumeratorMonitor[T]]]) -> None:
        super().__init__(factory, updater)
    
    def _GetValue(self) -> IResumableEnumeratorMonitor[T]:
        return _ResumableEnumeratorMonitor[T](self._GetFactory())

class EnumeratorFactoryBase[TItem, TMonitor](ObjectFactory[IEnumerator[TItem]], IEnumeratorFactory[TItem]):
    def __init__(self) -> None:
        def update(func: IFunction[TMonitor]) -> None:
            self.__monitor = func
        
        super().__init__()

        self.__monitor: IFunction[TMonitor] = self._CreateUpdater(update) # type: ignore[no-redef]
    
    @abstractmethod
    def _CreateUpdater(self, updater: Method[IFunction[TMonitor]]) -> EnumeratorMonitorUpdater[TMonitor, IEnumeratorFactory[TItem]]:
        pass
    
    @final
    def _Convert(self, item: IEnumerator[TItem]) -> IDisposableBase:
        return ToDisposableEnumerator(item)
    
    @final
    def CreateEnumerator(self, items: ITuple[TItem]) -> IEnumerator[TItem]:
        enumerator: IEnumerator[TItem] = TupleEnumerator[TItem](items)

        self._Push(enumerator)

        return enumerator
    
    @final
    def _AsMonitor(self) -> TMonitor:
        return self.__monitor.GetValue()

class EnumeratorFactory[T](EnumeratorFactoryBase[T, IEnumeratorMonitor[T]]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _CreateUpdater(self, updater: Method[IFunction[IEnumeratorMonitor[T]]]) -> EnumeratorMonitorUpdater[IEnumeratorMonitor[T], IEnumeratorFactory[T]]:
        return _EnumeratorMonitorUpdater[T](self, updater)
    
    @final
    def AsMonitor(self) -> IEnumeratorMonitor[T]:
        return self._AsMonitor()
class ResumableEnumeratorFactory[T](EnumeratorFactoryBase[T, IResumableEnumeratorMonitor[T]], IResumableEnumeratorFactory[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _CreateUpdater(self, updater: Method[IFunction[IResumableEnumeratorMonitor[T]]]) -> EnumeratorMonitorUpdater[IResumableEnumeratorMonitor[T], IResumableEnumeratorFactory[T]]:
        return _ResumableEnumeratorMonitorUpdater[T](self, updater)
    
    @final
    def CreateResumableEnumerator(self, items: ITuple[T]) -> IResumableEnumerator[T]:
        enumerator: IEnumerator[T] = ResumableTupleEnumerator[T](items)

        self._Push(enumerator)

        return enumerator
    
    @final
    def AsMonitor(self) -> IResumableEnumeratorMonitor[T]:
        return self._AsMonitor()