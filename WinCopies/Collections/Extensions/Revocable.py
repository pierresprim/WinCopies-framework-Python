from __future__ import annotations

from abc import abstractmethod
from typing import Self, overload, final



from WinCopies import IInterface, Abstract

from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Enumeration.Core import IEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Extensions import (IResumableEnumeratorMonitor, IRevocableViewMonitor,
                                              ICollectionViewMonitor, IEquatableCollectionViewMonitor,
                                              ICollectionMonitors,
                                              ITuple, IEquatableTuple,
                                              CollectionViewMonitor, EquatableCollectionViewMonitor,
                                              SequenceAbstract)
from WinCopies.Collections.Registry import IObjectMonitor, IObjectRegistry
from WinCopies.Collections.Registry.Core import InvalidatableObjectRegistry

from WinCopies.Delegates import ConcatenateMethods

from WinCopies.Typing import INullable
from WinCopies.Typing.Delegate import Method, EqualityComparison, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Discard import DiscardReason, IInvalidatable, InvalidatableObjectProvider
from WinCopies.Typing.Generic import IGenericConstraint, IGenericConstraintImplementation

class IRevocableViewRegistry(IRevocableViewMonitor, IObjectMonitor):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsMonitor(self) -> IRevocableViewMonitor:
        ...

class RevocableViewMonitor(Abstract, IRevocableViewMonitor):
    def __init__(self, registry: IRevocableViewRegistry) -> None:
        super().__init__()

        self.__registry: IRevocableViewRegistry = registry
    
    @final
    def _GetRegistry(self) -> IRevocableViewRegistry: return self.__registry
    
    @overload
    def CreateRevocableView[T](self, items: IEquatableTuple[T], onDisposed: Method[DiscardReason]|None = None) -> IEquatableTuple[T]: ...
    @overload
    def CreateRevocableView[T](self, items: ITuple[T], onDisposed: Method[DiscardReason]|None = None) -> ITuple[T]: ...

    @final
    def CreateRevocableView[T](self, items: IEquatableTuple[T]|ITuple[T], onDisposed: Method[DiscardReason]|None = None) -> IEquatableTuple[T]|ITuple[T]: return self._GetRegistry().CreateRevocableView(items, onDisposed)
@final
class _RevocableViewMonitorUpdater(ValueFunctionUpdater[IRevocableViewMonitor]):
    def __init__(self, registry: IRevocableViewRegistry, updater: Method[IFunction[IRevocableViewMonitor]]) -> None:
        super().__init__(updater)

        self.__registry: IRevocableViewRegistry = registry
    
    def _GetValue(self) -> IRevocableViewMonitor: return RevocableViewMonitor(self.__registry)

class _IRevocableViewCookie[T](IInvalidatable):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetItems(self) -> T:
        ...

    @abstractmethod
    def GetDiscardReason(self) -> DiscardReason:
        ...
@final
class _RevocableViewCookie[T](InvalidatableObjectProvider[T]):
    @final
    class _Cookie[_T](Abstract, _IRevocableViewCookie[_T]):
        def __init__(self, cookie: _RevocableViewCookie[_T]) -> None:
            super().__init__()

            self.__cookie: _RevocableViewCookie[_T] = cookie

        def GetItems(self) -> _T: return self.__cookie._GetItems()

        def GetDiscardReason(self) -> DiscardReason: return self.__cookie.GetDiscardReason()

        def _Dispose(self, reason: DiscardReason) -> None:
            cookie: _RevocableViewCookie[_T] = self.__cookie
            
            match reason:
                case DiscardReason.Disposed: cookie.Dispose()
                case DiscardReason.Invalidated: cookie.Invalidate()

                case _: raise ValueError("Unknown discard reason.")
    
    def __init__(self, items: T, onDisposed: Method[DiscardReason]|None) -> None:
        def getItems() -> T: return items

        def dispose(_: DiscardReason) -> None:
            self.__onDisposed = lambda _: None
        
        super().__init__(getItems)

        self.__onDisposed: Method[DiscardReason] = dispose if onDisposed is None else ConcatenateMethods(dispose, onDisposed) # type: ignore[no-redef]

    def _GetItems(self) -> T:
        return self._GetValue()

    @staticmethod
    def Create(items: T, onDisposed: Method[DiscardReason]|None) -> _IRevocableViewCookie[T]:
        return _RevocableViewCookie._Cookie[T](_RevocableViewCookie[T](items, onDisposed))

    def _DisposeOverride(self, reason: DiscardReason) -> None:
        super()._DisposeOverride(reason)

        onDisposed: Method[DiscardReason] = self.__onDisposed

        return onDisposed(reason)

class IViewProvider[T](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetView(self) -> T:
        ...
class _ReversedViewProviderBase[TCollection, TMonitor](Abstract, IViewProvider[TCollection]):
    def __init__(self, items: TCollection) -> None:
        super().__init__()

        self.__monitor: TMonitor = self._CreateMonitor(items)

    @abstractmethod
    def _CreateMonitor(self, items: TCollection) -> TMonitor:
        ...

    @abstractmethod
    def _GetView(self, monitor: TMonitor) -> TCollection:
        ...
    @final
    def GetView(self) -> TCollection:
        return self._GetView(self.__monitor)

@final
class _ReversedViewProvider[T](_ReversedViewProviderBase[ITuple[T], ICollectionViewMonitor[T]]):
    def __init__(self, items: ITuple[T]) -> None: super().__init__(items)

    def _CreateMonitor(self, items: ITuple[T]) -> ICollectionViewMonitor[T]: return CollectionViewMonitor[T](items)

    def _GetView(self, monitor: ICollectionViewMonitor[T]) -> ITuple[T]: return monitor.GetImmutableView()
@final
class _ReversedEquatableViewProvider[T](_ReversedViewProviderBase[IEquatableTuple[T], IEquatableCollectionViewMonitor[T]]):
    def __init__(self, items: IEquatableTuple[T]) -> None: super().__init__(items)

    def _CreateMonitor(self, items: IEquatableTuple[T]) -> IEquatableCollectionViewMonitor[T]: return EquatableCollectionViewMonitor[T](items)

    def _GetView(self, monitor: IEquatableCollectionViewMonitor[T]) -> IEquatableTuple[T]: return monitor.GetImmutableView()

class _ReversedCollectionViewMonitorUpdater[T](ValueFunctionUpdater[IViewProvider[T]]):
    def __init__(self, updater: Method[IFunction[IViewProvider[T]]]) -> None: super().__init__(updater)

    @abstractmethod
    def _GetItems(self) -> T:
        ...
    
    @abstractmethod
    def _CreateViewProvider(self, items: T) -> IViewProvider[T]:
        ...

    @final
    def _GetValue(self) -> IViewProvider[T]: return self._CreateViewProvider(self._GetItems())

class _IRevocableViewBase[TItem, TCollection](ITuple[TItem], IGenericConstraint[TCollection, ITuple[TItem]]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetSource(self) -> TCollection:
        ...
class RevocableViewAbstract[TItem, TCollection](SequenceAbstract[TItem], _IRevocableViewBase[TItem, TCollection]):
    @final
    class _ReversedCollectionMonitorUpdater[_TItem, _TCollection](_ReversedCollectionViewMonitorUpdater[_TCollection]):
        def __init__(self, items: RevocableViewAbstract[_TItem, _TCollection], updater: Method[IFunction[IViewProvider[_TCollection]]]) -> None:
            super().__init__(updater)

            self.__items: RevocableViewAbstract[_TItem, _TCollection] = items

        def _GetItems(self) -> _TCollection: return self.__items._GetSource() # pyright: ignore[reportPrivateUsage]

        def _CreateViewProvider(self, items: _TCollection) -> IViewProvider[_TCollection]: return self.__items._CreateViewProvider(self.__items._AsReversedView(items))
    
    def __init__(self) -> None:
        def update(func: IFunction[IViewProvider[TCollection]]) -> None: self.__reversedCollectionMonitor = func
        
        super().__init__()

        self.__reversedCollectionMonitor: IFunction[IViewProvider[TCollection]] = RevocableViewAbstract[TItem, TCollection]._ReversedCollectionMonitorUpdater(self, update) # type: ignore[no-redef]

    @final
    def __GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor:
        return self.GetCollectionMonitors().GetEnumeratorMonitor()

    @final
    def _GetItems(self) -> ITuple[TItem]:
        return self._AsContainer(self._GetSource())

    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self._GetItems().GetSourceMutability()

    @final
    def GetCount(self) -> int: return self._GetItems().GetCount()

    @final
    def FindFirstIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int: return self._GetItems().FindFirstIndex(item, predicate)
    @final
    def FindLastIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int: return self._GetItems().FindLastIndex(item, predicate)

    @final
    def Contains(self, value: TItem|object) -> bool: return self._GetItems().Contains(value)

    @final
    def TryGetValue(self, key: int) -> INullable[TItem]: return self._GetItems().TryGetValue(key)

    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetItems().GetCollectionMonitors()

    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]: return self.__GetEnumeratorMonitor().CreateEnumerator(self._GetItems(), True)
    @final
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[TItem]: return self.__GetEnumeratorMonitor().CreateResumableEnumerator(self._GetItems(), True)

    @final
    def _AsReversed(self) -> TCollection: return self.__reversedCollectionMonitor.GetValue().GetView()
    @abstractmethod
    def _AsReversedView(self, items: TCollection) -> TCollection:
        ...
    @abstractmethod
    def _CreateViewProvider(self, items: TCollection) -> IViewProvider[TCollection]:
        ...

class RevocableViewBase[T](RevocableViewAbstract[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def SliceAt(self, key: slice) -> ITuple[T]: return self._GetSource().SliceAt(key) # TODO: The return type should reflect the type of the inner collection (IArray, IList, etc).

    @final
    def AsReversed(self) -> ITuple[T]: return self._AsReversed()
    
    @final
    def AsReadOnly(self) -> ITuple[T]: return self
    @final
    def AsImmutable(self) -> ITuple[T]: return self
class EquatableRevocableViewBase[T](RevocableViewAbstract[T, IEquatableTuple[T]], IEquatableTuple[T], IGenericConstraintImplementation[IEquatableTuple[T]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[T]: return self._GetSource().SliceAt(key) # TODO: The return type should reflect the type of the inner collection (IArray, IList, etc).

    @final
    def AsReversed(self) -> IEquatableTuple[T]: return self._AsReversed()
    
    @final
    def AsReadOnly(self) -> IEquatableTuple[T]: return self
    @final
    def AsImmutable(self) -> IEquatableTuple[T]: return self

class _IRevocableView[TItem, TCollection](_IRevocableViewBase[TItem, TCollection]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetCookie(self) -> _IRevocableViewCookie[TCollection]:
        ...

    def _GetSource(self) -> TCollection: return self._GetCookie().GetItems()

    def ToString(self) -> str:
        cookie: _IRevocableViewCookie[TCollection] = self._GetCookie()

        discardReason: DiscardReason = cookie.GetDiscardReason()

        return self._AsContainer(cookie.GetItems()).ToString() if discardReason == DiscardReason.Null else f"<RevocableView (revoked: view {discardReason.ToString().lower()})>"

@final
class _RevocableView[T](RevocableViewBase[T], _IRevocableView[T, ITuple[T]]):
    def __init__(self, cookie: _IRevocableViewCookie[ITuple[T]]) -> None:
        super().__init__()

        self.__cookie: _IRevocableViewCookie[ITuple[T]] = cookie

    def _GetCookie(self) -> _IRevocableViewCookie[ITuple[T]]: return self.__cookie

    def _AsReversedView(self, items: ITuple[T]) -> ITuple[T]: return items.AsReversed()

    def _CreateViewProvider(self, items: ITuple[T]) -> IViewProvider[ITuple[T]]: return _ReversedViewProvider[T](items)
@final
class _EquatableRevocableView[T](EquatableRevocableViewBase[T], _IRevocableView[T, IEquatableTuple[T]]):
    def __init__(self, cookie: _IRevocableViewCookie[IEquatableTuple[T]]) -> None:
        super().__init__()

        self.__cookie: _IRevocableViewCookie[IEquatableTuple[T]] = cookie

    def Equals(self, item: Self|object) -> bool: return self._GetSource().Equals(item)

    def _GetCookie(self) -> _IRevocableViewCookie[IEquatableTuple[T]]: return self.__cookie

    def _AsReversedView(self, items: IEquatableTuple[T]) -> IEquatableTuple[T]: return items.AsReversed()

    def _CreateViewProvider(self, items: IEquatableTuple[T]) -> IViewProvider[IEquatableTuple[T]]: return _ReversedEquatableViewProvider[T](items)

@overload
def _CreateRevocableView[T](items: IEquatableTuple[T], onDisposed: Method[DiscardReason]|None = None) -> tuple[IEquatableTuple[T], IInvalidatable]: ...
@overload
def _CreateRevocableView[T](items: ITuple[T], onDisposed: Method[DiscardReason]|None = None) -> tuple[ITuple[T], IInvalidatable]: ...

def _CreateRevocableView[T](items: IEquatableTuple[T]|ITuple[T], onDisposed: Method[DiscardReason]|None = None) -> tuple[IEquatableTuple[T]|ITuple[T], IInvalidatable]:
    def createTuple() -> tuple[ITuple[T], IInvalidatable]:
        cookie: _IRevocableViewCookie[ITuple[T]] = _RevocableViewCookie[ITuple[T]].Create(items, onDisposed)
        
        return (_RevocableView[T](cookie), cookie)
    def createEquatableView(items: IEquatableTuple[T]) -> tuple[IEquatableTuple[T], IInvalidatable]:
        cookie: _IRevocableViewCookie[IEquatableTuple[T]] = _RevocableViewCookie[IEquatableTuple[T]].Create(items, onDisposed)

        return (_EquatableRevocableView[T](cookie), cookie)
    
    match items:
        case IEquatableTuple(): return createEquatableView(items)

        case _: return createTuple()

type RevocableView[T] = _RevocableView[T]
type EquatableRevocableView[T] = _EquatableRevocableView[T]

class RevocableViewRegistry(Abstract, IRevocableViewRegistry):
    def __init__(self) -> None:
        def update(func: IFunction[IRevocableViewMonitor]) -> None: self.__monitor = func
        
        super().__init__()

        self.__registry: IObjectRegistry[IInvalidatable] = InvalidatableObjectRegistry[IInvalidatable]()
        self.__monitor: IFunction[IRevocableViewMonitor] = _RevocableViewMonitorUpdater(self, update) # type: ignore[no-redef]

    @final
    def _GetRegistry(self) -> IObjectRegistry[IInvalidatable]:
        return self.__registry
    
    @overload
    def CreateRevocableView[T](self, items: IEquatableTuple[T], onDisposed: Method[DiscardReason]|None = None) -> IEquatableTuple[T]: ...
    @overload
    def CreateRevocableView[T](self, items: ITuple[T], onDisposed: Method[DiscardReason]|None = None) -> ITuple[T]: ...
    
    @final
    def CreateRevocableView[T](self, items: IEquatableTuple[T]|ITuple[T], onDisposed: Method[DiscardReason]|None = None) -> IEquatableTuple[T]|ITuple[T]:
        view: tuple[IEquatableTuple[T]|ITuple[T], IInvalidatable] = _CreateRevocableView(items, onDisposed)

        self._GetRegistry().RegisterObject(view[1])

        return view[0]

    @final
    def InvalidateObjects(self) -> None:
        return self._GetRegistry().InvalidateObjects()
    
    @final
    def AsMonitor(self) -> IRevocableViewMonitor: return self.__monitor.GetValue()