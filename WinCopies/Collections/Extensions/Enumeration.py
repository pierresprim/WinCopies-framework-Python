from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import Abstract, IDisposableBase
from WinCopies.Collections.Enumeration import IEnumeratorBase, IEnumerator, IncrementalEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Enumeration.Resumable.Indexable import ResumableIncrementalEnumerator
from WinCopies.Collections.Extensions import ITuple, IEnumeratorMonitor, IResumableEnumeratorMonitor
from WinCopies.Collections.Generation.Factory import IObjectFactory
from WinCopies.Collections.Generation.Factory.Core import ObjectFactory
from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import GenericConstraint, IGenericConstraintImplementation

class TupleEnumeratorBase[TItem, TList](IncrementalEnumerator[TItem], GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__list: TList = items
    
    @final
    def _GetContainer(self) -> TList: return self.__list
    
    @final
    def _GetMaxValue(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def _GetCurrent(self) -> TItem: return self._GetInnerContainer().GetAt(self._GetValue())
class TupleEnumerator[T](TupleEnumeratorBase[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None: super().__init__(items)

class ResumableTupleEnumeratorBase[TItem, TList](ResumableIncrementalEnumerator[TItem], GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__list: TList = items
    
    @final
    def _GetContainer(self) -> TList: return self.__list
    
    @final
    def _GetMaxValue(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def _GetCurrent(self) -> TItem: return self._GetInnerContainer().GetAt(self._GetValue())
class ResumableTupleEnumerator[T](ResumableTupleEnumeratorBase[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None: super().__init__(items)

class IEnumeratorFactory(IObjectFactory[IEnumeratorBase], IEnumeratorMonitor):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsMonitor(self) -> IEnumeratorMonitor:
        ...
class IResumableEnumeratorFactory(IEnumeratorFactory, IResumableEnumeratorMonitor):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsMonitor(self) -> IResumableEnumeratorMonitor:
        ...

class EnumeratorMonitor[T](Abstract, IEnumeratorMonitor, GenericConstraint[T, IEnumeratorFactory]):
    def __init__(self, factory: T) -> None:
        super().__init__()

        self.__factory: T = factory
    
    @final
    def _GetContainer(self) -> T: return self.__factory
    
    @final
    def CreateEnumerator[U](self, items: ITuple[U]) -> IEnumerator[U]: return self._GetInnerContainer().CreateEnumerator(items)
class EnumeratorMonitorUpdater[TMonitor, TFactory](ValueFunctionUpdater[TMonitor]):
    def __init__(self, factory: TFactory, updater: Method[IFunction[TMonitor]]) -> None:
        super().__init__(updater)

        self.__factory: TFactory = factory
    
    @final
    def _GetFactory(self) -> TFactory:
        return self.__factory

@final
class _EnumeratorMonitor(EnumeratorMonitor[IEnumeratorFactory]):
    def __init__(self, factory: IEnumeratorFactory) -> None: super().__init__(factory)
    
    def _AsContainer(self, container: IEnumeratorFactory) -> IEnumeratorFactory: return container
@final
class _EnumeratorMonitorUpdater(EnumeratorMonitorUpdater[IEnumeratorMonitor, IEnumeratorFactory]):
    def __init__(self, factory: IEnumeratorFactory, updater: Method[IFunction[IEnumeratorMonitor]]) -> None: super().__init__(factory, updater)
    
    def _GetValue(self) -> IEnumeratorMonitor: return _EnumeratorMonitor(self._GetFactory())

@final
class _ResumableEnumeratorMonitor(EnumeratorMonitor[IResumableEnumeratorFactory], IResumableEnumeratorMonitor):
    def __init__(self, factory: IResumableEnumeratorFactory) -> None: super().__init__(factory)
    
    def _AsContainer(self, container: IResumableEnumeratorFactory) -> IResumableEnumeratorFactory: return container
    
    def CreateResumableEnumerator[U](self, items: ITuple[U]) -> IResumableEnumerator[U]:
        return self._GetContainer().CreateResumableEnumerator(items)
@final
class _ResumableEnumeratorMonitorUpdater(EnumeratorMonitorUpdater[IResumableEnumeratorMonitor, IResumableEnumeratorFactory]):
    def __init__(self, factory: IResumableEnumeratorFactory, updater: Method[IFunction[IResumableEnumeratorMonitor]]) -> None: super().__init__(factory, updater)
    
    def _GetValue(self) -> IResumableEnumeratorMonitor: return _ResumableEnumeratorMonitor(self._GetFactory())

class EnumeratorFactoryBase[T](ObjectFactory[IEnumeratorBase], IEnumeratorFactory):
    def __init__(self) -> None:
        def update(func: IFunction[T]) -> None: self.__monitor = func
        
        super().__init__()

        self.__monitor: IFunction[T] = self._CreateUpdater(update) # type: ignore[no-redef]
    
    @abstractmethod
    def _CreateUpdater(self, updater: Method[IFunction[T]]) -> EnumeratorMonitorUpdater[T, IEnumeratorFactory]:
        ...
    
    @final
    def _Convert(self, item: IEnumeratorBase) -> IDisposableBase: return item.ToDisposable()
    
    @final
    def CreateEnumerator[U](self, items: ITuple[U]) -> IEnumerator[U]:
        enumerator: IEnumeratorBase = TupleEnumerator[U](items)

        self._Push(enumerator)

        return enumerator
    
    @final
    def _AsMonitor(self) -> T:
        return self.__monitor.GetValue()

class EnumeratorFactory(EnumeratorFactoryBase[IEnumeratorMonitor]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _CreateUpdater(self, updater: Method[IFunction[IEnumeratorMonitor]]) -> EnumeratorMonitorUpdater[IEnumeratorMonitor, IEnumeratorFactory]:
        return _EnumeratorMonitorUpdater(self, updater)
    
    @final
    def AsMonitor(self) -> IEnumeratorMonitor:
        return self._AsMonitor()
class ResumableEnumeratorFactory(EnumeratorFactoryBase[IResumableEnumeratorMonitor], IResumableEnumeratorFactory):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _CreateUpdater(self, updater: Method[IFunction[IResumableEnumeratorMonitor]]) -> EnumeratorMonitorUpdater[IResumableEnumeratorMonitor, IResumableEnumeratorFactory]:
        return _ResumableEnumeratorMonitorUpdater(self, updater)
    
    @final
    def CreateResumableEnumerator[U](self, items: ITuple[U]) -> IResumableEnumerator[U]:
        enumerator: IResumableEnumerator[U] = ResumableTupleEnumerator[U](items)

        self._Push(enumerator)

        return enumerator
    
    @final
    def AsMonitor(self) -> IResumableEnumeratorMonitor:
        return self._AsMonitor()