from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Sized
from typing import Self, overload, final



from WinCopies import IInterface, Abstract

from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Enumeration.Core import IEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Extensions import (IReadOnlyLinkedCursorProvider,
                                              IResumableEnumeratorMonitor, IRevocableViewMonitor,
                                              ICollectionViewMonitor, IEquatableCollectionViewMonitor,
                                              ICollectionMonitors,
                                              ITuple, IEquatableTuple,
                                              CollectionViewMonitor, EquatableCollectionViewMonitor,
                                              SequenceAbstract,
                                              GetTupleString)
from WinCopies.Collections.Linked.Singly import IReadOnlyCountableEnumerableList, IReadOnlyCountableEnumerableQueue, IReadOnlyCountableEnumerableStack
from WinCopies.Collections.Registry import IObjectMonitor, IObjectRegistry
from WinCopies.Collections.Registry.Core import InvalidatableObjectRegistry

from WinCopies.Delegates import ConcatenateMethods

from WinCopies.Typing import INullable
from WinCopies.Typing.Delegate import Method, Function, Converter, EqualityComparison, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Discard import DiscardReason, IInvalidatable, InvalidatableObjectProvider
from WinCopies.Typing.Generic import IGenericConstraint, IGenericConstraintImplementation

class _IRevocableViewCookieAbstract[T](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetItems(self) -> T:
        ...
class _IRevocableViewCookie[T](_IRevocableViewCookieAbstract[T], IInvalidatable):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetDiscardReason(self) -> DiscardReason:
        ...

@final
class _CursorSource[T](Abstract):
    def __init__(self, items: ITuple[T], source: Function[ITuple[T]]) -> None:
        super().__init__()

        self.__items: ITuple[T] = items
        self.__source: Function[ITuple[T]] = source

    @final
    def GetSource(self) -> ITuple[T]:
        return self.__source()
    @final
    def GetItems(self) -> ITuple[T]:
        return self.__items

class _Cursor[T](Abstract, IReadOnlyCountableEnumerableList[T]):
    def __init__(self, source: _CursorSource[T]) -> None:
        super().__init__()

        self.__source: _CursorSource[T] = source

    @final
    def _GetSource(self) -> ITuple[T]:
        return self.__source.GetSource()
    @final
    def _GetItems(self) -> ITuple[T]:
        return self.__source.GetItems()

    @final
    def IsEmpty(self) -> bool: return self._GetItems().IsEmpty()

    @final
    def GetCount(self) -> int: return self._GetItems().GetCount()

    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self._GetItems().TryGetEnumerator()

    @final
    def AsSized(self) -> Sized: return self._GetItems().AsSized()
    @final
    def AsIterable(self) -> Iterable[T]: return self._GetItems().AsIterable()

@final
class _QueuedCursor[T](_Cursor[T], IReadOnlyCountableEnumerableQueue[T]):
    def __init__(self, source: _CursorSource[T]) -> None: super().__init__(source)

    def TryPeek(self) -> INullable[T]: return self._GetSource().AsQueuedCursor().TryPeek()
@final
class _StackedCursor[T](_Cursor[T], IReadOnlyCountableEnumerableStack[T]):
    def __init__(self, source: _CursorSource[T]) -> None: super().__init__(source)

    def TryPeek(self) -> INullable[T]: return self._GetSource().AsStackedCursor().TryPeek()

@final
class _CursorProvider[T](Abstract, IReadOnlyLinkedCursorProvider[T]):
    def __init__(self, source: _CursorSource[T]) -> None:
        super().__init__()

        self.__queued: IReadOnlyCountableEnumerableQueue[T] = _QueuedCursor[T](source)
        self.__stacked: IReadOnlyCountableEnumerableStack[T] = _StackedCursor[T](source)

    def AsQueuedCursor(self) -> IReadOnlyCountableEnumerableQueue[T]: return self.__queued
    def AsStackedCursor(self) -> IReadOnlyCountableEnumerableStack[T]: return self.__stacked
@final
class _CursorProviderUpdater[T](ValueFunctionUpdater[IReadOnlyLinkedCursorProvider[T]]):
    def __init__(self, source: _CursorSource[T], updater: Method[IFunction[IReadOnlyLinkedCursorProvider[T]]]) -> None:
        super().__init__(updater)

        self.__source: _CursorSource[T] = source

    def _GetValue(self) -> IReadOnlyLinkedCursorProvider[T]: return _CursorProvider[T](self.__source)

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
        def dispose(_: DiscardReason) -> None: self.__onDisposed = lambda _: None
        
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
    
    # What a view builds on its source, it hands out only while it lives: asking a revoked view for
    # it raises as reading it does, whether or not it was built before. Built once and kept, it is
    # still handed out again while the view lives.
    @final
    def _ThrowIfRevoked(self) -> None: self._GetSource()
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
    def _AsReversed(self) -> TCollection:
        self._ThrowIfRevoked()

        return self.__reversedCollectionMonitor.GetValue().GetView()
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

class _IRevocableView[TItem, TCollection](_IRevocableViewBase[TItem, TCollection], IReadOnlyLinkedCursorProvider[TItem]):
    def __init__(self) -> None: super().__init__()

    @final
    def _CreateCursorProviderUpdater(self, updater: Method[IFunction[IReadOnlyLinkedCursorProvider[TItem]]]) -> _CursorProviderUpdater[TItem]:
        return _CursorProviderUpdater[TItem](_CursorSource[TItem](self, lambda: self._AsContainer(self._GetSource())), updater)

    @abstractmethod
    def _GetCookie(self) -> _IRevocableViewCookie[TCollection]:
        ...

    @final
    def _GetSource(self) -> TCollection: return self._GetCookie().GetItems()
    
    @abstractmethod
    def _GetCursorProvider(self) -> IFunction[IReadOnlyLinkedCursorProvider[TItem]]:
        ...
    @final
    def __GetCursorProvider(self) -> IReadOnlyLinkedCursorProvider[TItem]:
        self._ThrowIfRevoked()

        return self._GetCursorProvider().GetValue()

    @final
    def AsQueuedCursor(self) -> IReadOnlyCountableEnumerableQueue[TItem]: return self.__GetCursorProvider().AsQueuedCursor()
    @final
    def AsStackedCursor(self) -> IReadOnlyCountableEnumerableStack[TItem]: return self.__GetCursorProvider().AsStackedCursor()

    def ToString(self) -> str:
        cookie: _IRevocableViewCookie[TCollection] = self._GetCookie()

        discardReason: DiscardReason = cookie.GetDiscardReason()

        return GetTupleString(self.AsIterable(), self.GetMutability()) if discardReason == DiscardReason.Null else f"<RevocableView (revoked: view {discardReason.ToString().lower()})>"

@final
class _RevocableView[T](RevocableViewBase[T], _IRevocableView[T, ITuple[T]]):
    def __init__(self, cookie: _IRevocableViewCookie[ITuple[T]]) -> None:
        def update(func: IFunction[IReadOnlyLinkedCursorProvider[T]]) -> None: self.__cursorProvider = func

        super().__init__()

        self.__cookie: _IRevocableViewCookie[ITuple[T]] = cookie
        self.__cursorProvider: IFunction[IReadOnlyLinkedCursorProvider[T]] = self._CreateCursorProviderUpdater(update) # type: ignore[no-redef]

    def _GetCursorProvider(self) -> IFunction[IReadOnlyLinkedCursorProvider[T]]: return self.__cursorProvider

    def _GetCookie(self) -> _IRevocableViewCookie[ITuple[T]]: return self.__cookie

    def _AsReversedView(self, items: ITuple[T]) -> ITuple[T]: return items.AsReversed()

    def _CreateViewProvider(self, items: ITuple[T]) -> IViewProvider[ITuple[T]]: return _ReversedViewProvider[T](items)
@final
class _EquatableRevocableView[T](EquatableRevocableViewBase[T], _IRevocableView[T, IEquatableTuple[T]]):
    def __init__(self, cookie: _IRevocableViewCookie[IEquatableTuple[T]]) -> None:
        def update(func: IFunction[IReadOnlyLinkedCursorProvider[T]]) -> None: self.__cursorProvider = func

        super().__init__()

        self.__cookie: _IRevocableViewCookie[IEquatableTuple[T]] = cookie
        self.__cursorProvider: IFunction[IReadOnlyLinkedCursorProvider[T]] = self._CreateCursorProviderUpdater(update) # type: ignore[no-redef]

    def _GetCursorProvider(self) -> IFunction[IReadOnlyLinkedCursorProvider[T]]: return self.__cursorProvider

    def Equals(self, item: Self|object) -> bool: return self._GetSource().Equals(item)

    def _GetCookie(self) -> _IRevocableViewCookie[IEquatableTuple[T]]: return self.__cookie

    def _AsReversedView(self, items: IEquatableTuple[T]) -> IEquatableTuple[T]: return items.AsReversed()

    def _CreateViewProvider(self, items: IEquatableTuple[T]) -> IViewProvider[IEquatableTuple[T]]: return _ReversedEquatableViewProvider[T](items)

@overload
def _CreateRevocableView[T](items: IEquatableTuple[T], onDisposed: Method[DiscardReason]|None = None) -> tuple[IEquatableTuple[T], IInvalidatable]: ...
@overload
def _CreateRevocableView[T](items: ITuple[T], onDisposed: Method[DiscardReason]|None = None) -> tuple[ITuple[T], IInvalidatable]: ...

def _CreateRevocableView[T](items: IEquatableTuple[T]|ITuple[T], onDisposed: Method[DiscardReason]|None = None) -> tuple[IEquatableTuple[T]|ITuple[T], IInvalidatable]:
    def create[U, V](items: U, selector: Converter[_IRevocableViewCookie[U], V]) -> tuple[V, IInvalidatable]:
        cookie: _IRevocableViewCookie[U] = _RevocableViewCookie[U].Create(items, onDisposed)
        
        return (selector(cookie), cookie)
    
    def createTuple() -> tuple[ITuple[T], IInvalidatable]: return create(items, _RevocableView)
    def createEquatableView(items: IEquatableTuple[T]) -> tuple[IEquatableTuple[T], IInvalidatable]: return create(items, _EquatableRevocableView)
    
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
    def InvalidateObjects(self) -> None: return self._GetRegistry().InvalidateObjects()
    
    @final
    def AsMonitor(self) -> IRevocableViewMonitor: return self.__monitor.GetValue()