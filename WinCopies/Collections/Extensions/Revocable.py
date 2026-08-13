from __future__ import annotations

from abc import abstractmethod
from typing import final



from WinCopies import IDisposableBase, Abstract

from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Enumeration import IEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Extensions import ICollectionViewMonitor, ICollectionMonitors, IRevocableViewMonitor, ITuple, CollectionViewMonitor, SequenceAbstract
from WinCopies.Collections.Generation.Factory import IObjectMonitor, IObjectFactory
from WinCopies.Collections.Generation.Factory.Core import DisposableObjectFactory

from WinCopies.Delegates import NoAction, ConcatenateActions

from WinCopies.Typing import INullable, GetInvalidatedError
from WinCopies.Typing.Delegate import Action, Method, Function, EqualityComparison, IFunction, ValueFunctionUpdater

class IRevocableViewFactory(IRevocableViewMonitor, IObjectMonitor):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsMonitor(self) -> IRevocableViewMonitor:
        ...

class RevocableViewMonitor(Abstract, IRevocableViewMonitor):
    def __init__(self, factory: IRevocableViewFactory) -> None:
        super().__init__()

        self.__factory: IRevocableViewFactory = factory
    
    @final
    def _GetFactory(self) -> IRevocableViewFactory: return self.__factory
    
    @final
    def CreateRevocableView[T](self, items: ITuple[T], onDisposed: Action|None = None) -> ITuple[T]: return self._GetFactory().CreateRevocableView(items, onDisposed)
@final
class _RevocableViewMonitorUpdater(ValueFunctionUpdater[IRevocableViewMonitor]):
    def __init__(self, factory: IRevocableViewFactory, updater: Method[IFunction[IRevocableViewMonitor]]) -> None:
        super().__init__(updater)

        self.__factory: IRevocableViewFactory = factory
    
    def _GetValue(self) -> IRevocableViewMonitor: return RevocableViewMonitor(self.__factory)

@final
class _RevocableViewCookie[T](Abstract, IDisposableBase):
    def __init__(self, items: ITuple[T], onDisposed: Action|None) -> None:
        def getItems() -> ITuple[T]: return items

        def dispose() -> None:
            def throw() -> ITuple[T]: raise GetInvalidatedError()

            self.__items = throw
            self.__onDisposed = NoAction
        
        super().__init__()

        self.__items: Function[ITuple[T]] = getItems # type: ignore[no-redef]

        self.__onDisposed: Action = dispose if onDisposed is None else ConcatenateActions(dispose, onDisposed) # type: ignore[no-redef]

    def GetItems(self) -> ITuple[T]:
        return self.__items()

    def Dispose(self) -> None: self.__onDisposed()

class _CollectionViewMonitorUpdater[T](ValueFunctionUpdater[ICollectionViewMonitor[T]]):
    def __init__(self, updater: Method[IFunction[ICollectionViewMonitor[T]]]) -> None: super().__init__(updater)

    @abstractmethod
    def _GetItems(self) -> ITuple[T]:
        ...

    @final
    def _GetValue(self) -> ICollectionViewMonitor[T]: return CollectionViewMonitor[T](self._GetItems().AsReversed())

class RevocableViewBase[T](SequenceAbstract[T]):
    @final
    class _MonitorUpdater[_T](_CollectionViewMonitorUpdater[_T]):
        def __init__(self, items: RevocableViewBase[_T], updater: Method[IFunction[ICollectionViewMonitor[_T]]]) -> None:
            super().__init__(updater)

            self.__items: RevocableViewBase[_T] = items

        def _GetItems(self) -> ITuple[_T]: return self.__items._GetItems()
    
    def __init__(self) -> None:
        def update(func: IFunction[ICollectionViewMonitor[T]]) -> None: self.__monitor = func
        
        super().__init__()

        self.__monitor: IFunction[ICollectionViewMonitor[T]] = RevocableViewBase._MonitorUpdater[T](self, update) # type: ignore[no-redef]

    @abstractmethod
    def _GetItems(self) -> ITuple[T]:
        ...

    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self._GetItems().GetSourceMutability()

    @final
    def GetCount(self) -> int: return self._GetItems().GetCount()

    @final
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return self._GetItems().FindFirstIndex(item, predicate)
    @final
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return self._GetItems().FindLastIndex(item, predicate)

    @final
    def Contains(self, value: T|object) -> bool: return self._GetItems().Contains(value)

    @final
    def TryGetValue(self, key: int) -> INullable[T]: return self._GetItems().TryGetValue(key)

    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetItems().GetCollectionMonitors()

    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self._GetItems().TryGetEnumerator()
    @final
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]|None: return self._GetItems().TryGetResumableEnumerator()

    @final
    def SliceAt(self, key: slice) -> ITuple[T]: return self._GetItems().SliceAt(key) # TODO: The return type should reflect the type of the inner collection (IArray, IList, etc).

    @final
    def AsReversed(self) -> ITuple[T]: return self.__monitor.GetValue().GetImmutableView()
    
    @final
    def AsReadOnly(self) -> ITuple[T]: return self

    @final
    def AsImmutable(self) -> ITuple[T]: return self

    def ToString(self) -> str: return self._GetItems().ToString()
@final
class _RevocableView[T](RevocableViewBase[T]):
    def __init__(self, cookie: _RevocableViewCookie[T]) -> None:
        super().__init__()

        self.__cookie: _RevocableViewCookie[T] = cookie

    def _GetItems(self) -> ITuple[T]: return self.__cookie.GetItems()

def _CreateRevocableView[T](items: ITuple[T], onDisposed: Action|None = None) -> tuple[ITuple[T], IDisposableBase]:
    cookie: _RevocableViewCookie[T] = _RevocableViewCookie(items, onDisposed)
    view: _RevocableView[T] = _RevocableView[T](cookie)

    return (view, cookie)

type RevocableView[T] = _RevocableView[T]

class RevocableViewFactory(Abstract, IRevocableViewFactory):
    def __init__(self) -> None:
        def update(func: IFunction[IRevocableViewMonitor]) -> None: self.__monitor = func
        
        super().__init__()

        self.__factory: IObjectFactory[IDisposableBase] = DisposableObjectFactory[IDisposableBase]()
        self.__monitor: IFunction[IRevocableViewMonitor] = _RevocableViewMonitorUpdater(self, update) # type: ignore[no-redef]

    @final
    def _GetFactory(self) -> IObjectFactory[IDisposableBase]:
        return self.__factory
    
    @final
    def CreateRevocableView[T](self, items: ITuple[T], onDisposed: Action|None = None) -> ITuple[T]:
        view: tuple[ITuple[T], IDisposableBase] = _CreateRevocableView(items, onDisposed)

        self._GetFactory().RegisterObject(view[1])

        return view[0]

    @final
    def InvalidateObjects(self) -> None:
        return self._GetFactory().InvalidateObjects()
    
    @final
    def AsMonitor(self) -> IRevocableViewMonitor: return self.__monitor.GetValue()