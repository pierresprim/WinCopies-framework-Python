from abc import abstractmethod
from collections.abc import Sequence as SequenceBase
from typing import final



from WinCopies import IDisposableBase, Abstract

from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Enumeration import IEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Extensions import IRevocableViewMonitor, ITuple
from WinCopies.Collections.Generation.Factory import IObjectMonitor, IObjectFactory
from WinCopies.Collections.Generation.Factory.Core import DisposableObjectFactory

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
class _RevocableViewCookie(Abstract, IDisposableBase):
    def __init__(self, updater: Action) -> None:
        super().__init__()

        self.__updater: Action = updater

    def Dispose(self) -> None: self.__updater()

class RevocableViewBase[T](Abstract, ITuple[T]):
    def __init__(self) -> None: super().__init__()

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
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self._GetItems().TryGetEnumerator()
    @final
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]|None: return self._GetItems().TryGetResumableEnumerator()

    @final
    def SliceAt(self, key: slice) -> ITuple[T]: return self._GetItems().SliceAt(key)

    @final
    def AsReversed(self) -> ITuple[T]: return self._GetItems().AsReversed()
    
    @final
    def AsReadOnly(self) -> ITuple[T]: return self

    @final
    def AsImmutable(self) -> ITuple[T]: return self

    @final
    def AsSequence(self) -> SequenceBase[T]: return self._GetItems().AsSequence()

    def ToString(self) -> str: return self._GetItems().ToString()
class RevocableView[T](RevocableViewBase[T]):
    def __init__(self, items: ITuple[T]) -> None:
        def getItems() -> ITuple[T]: return items
        
        self.__items: Function[ITuple[T]] = getItems

    def _GetItems(self) -> ITuple[T]: return self.__items()

    @staticmethod
    def Create(items: ITuple[T], onDisposed: Action|None = None) -> tuple[ITuple[T], IDisposableBase]:
        def update() -> None:
            def throw() -> ITuple[T]: raise GetInvalidatedError()

            view.__items = throw

            if onDisposed is not None: onDisposed()

        view: RevocableView[T] = RevocableView[T](items)

        return (view, _RevocableViewCookie(update))

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
        view: tuple[ITuple[T], IDisposableBase] = RevocableView[T].Create(items, onDisposed)

        self._GetFactory().RegisterObject(view[1])

        return view[0]

    @final
    def InvalidateObjects(self) -> None:
        return self._GetFactory().InvalidateObjects()
    
    @final
    def AsMonitor(self) -> IRevocableViewMonitor: return self.__monitor.GetValue()