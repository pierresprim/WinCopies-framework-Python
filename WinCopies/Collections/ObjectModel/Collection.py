from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, MutableSequence as MutableSequenceBase
from enum import Enum
from typing import overload, final, SupportsIndex

from WinCopies import IInterface, IDisposable, Abstract
from WinCopies.Collections import Mutability
from WinCopies.Collections.Enumeration import IEnumerator
from WinCopies.Collections.Extensions import IEnumeratorMonitor, ITuple, IArray, IList, MutableSequence, SequenceAbstract
from WinCopies.Collections.Extensions.Collection import KeyableBase, CollectionAbstract
from WinCopies.Collections.Range import SetItems, RemoveItems
from WinCopies.Typing import IMonitor, INullable, Monitor, InvalidOperationError
from WinCopies.Typing.Delegate import Method, IFunction, EqualityComparison, ValueFunctionUpdater
from WinCopies.Typing.Delegate.Event import IEvent, IEventManager, EventHandler, EventManager
from WinCopies.Typing.Generic import IGenericConstraintImplementation, GenericConstraint

class CollectionAbstractor[T](MutableSequence[T], KeyableBase[int, T], IList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def GetMutability(self) -> Mutability:
        return Mutability.Mutable
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> MutableSequenceBase[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|MutableSequenceBase[T]:
        return self.GetAt(int(index)) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsMutableSequence()

class CollectionBase[TItem, TList](CollectionAbstractor[TItem], GenericConstraint[TList, IList[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__items: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__items
    
    def _SetItem(self, index: int, item: TItem) -> bool:
        return self._GetInnerContainer().TrySetAt(index, item)
    
    def _MoveItem(self, x: int, y: int) -> None:
        self._GetInnerContainer().Move(x, y)
    
    def _SwapItems(self, x: int, y: int) -> None:
        self._GetInnerContainer().Swap(x, y)
    
    def _InsertItem(self, index: int|None, item: TItem) -> bool:
        if index is None:
            self._GetInnerContainer().Add(item)

            return True
        
        return self._GetInnerContainer().TryInsert(index, item)
    
    def _InsertItems(self, index: int, items: Iterable[TItem]) -> bool:
        return self._GetInnerContainer().TryInsertRange(index, items)
    
    def _RemoveItemsAt(self, index: int, count: int) -> bool:
        return self._GetInnerContainer().TryRemoveRange(index, count)
    
    def _RemoveItemAt(self, index: int) -> bool|None:
        return self._GetInnerContainer().TryRemoveAt(index)
    
    def _ClearItems(self) -> None:
        self._GetInnerContainer().Clear()
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None:
        return self._GetInnerContainer().TryGetSourceMutability()
    
    @final
    def GetCount(self) -> int:
        return self._GetInnerContainer().GetCount()
    
    @final
    def Contains(self, value: TItem|object) -> bool:
        return self._GetInnerContainer().Contains(value)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None:
        return self._GetInnerContainer().TryGetEnumerator()
    
    @final
    def FindFirstIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int:
        return self._GetInnerContainer().FindFirstIndex(item, predicate)
    @final
    def FindLastIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int:
        return self._GetInnerContainer().FindLastIndex(item, predicate)
    
    @final
    def _GetAt(self, key: int) -> TItem:
        return self._GetInnerContainer().GetAt(key)
    @final
    def _SetAt(self, key: int, value: TItem) -> None:
        self._SetItem(key, value)
    
    @final
    def Move(self, x: int, y: int) -> None:
        self._MoveItem(x, y)
    
    @final
    def Swap(self, x: int, y: int) -> None:
        self._SwapItems(x, y)
    
    @final
    def SliceAt(self, key: slice) -> IList[TItem]:
        return self._GetInnerContainer().SliceAt(key)
    
    @final
    def Add(self, item: TItem) -> None:
        self._InsertItem(None, item)
    @final
    def TryInsert(self, index: int, value: TItem) -> bool:
        return self._InsertItem(index, value)
    
    @final
    def TryInsertRange(self, index: int, items: Iterable[TItem]) -> bool:
        return self._InsertItems(index, items)
    
    @final
    def TryRemoveRange(self, index: int, count: int) -> bool:
        return self._RemoveItemsAt(index, count)
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        return self._RemoveItemAt(index)
    
    @final
    def Clear(self) -> None:
        self._ClearItems()
    
    @final
    def ToString(self) -> str:
        return self._GetInnerContainer().ToString()
    
    @final
    def insert(self, index: int, value: TItem) -> None:
        self.Insert(index, value)
    
    @overload
    def __setitem__(self, index: SupportsIndex, value: TItem) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[TItem]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: TItem|Iterable[TItem]) -> None:
        SetItems(self, index, value)
    
    @final
    def __delitem__(self, index: int|slice) -> None:
        RemoveItems(self, index)
class Collection[T](CollectionBase[T, IList[T]], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, items: IList[T]) -> None:
        super().__init__(items)

class IObservableCollectionEvents[T](IInterface):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def OnItemAdded(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        pass
    @abstractmethod
    def OnItemUpdated(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        pass
    @abstractmethod
    def OnItemsSwapped(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        pass
    @abstractmethod
    def OnItemMoved(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        pass
    @abstractmethod
    def OnItemRemoved(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        pass

@final
class _ObservableCollectionEvent[T](Abstract):
    def __init__(self) -> None:
        super().__init__()
        
        self.__itemAddedEvents: IEventManager[IObservableCollection[T], CollectionChangedEventArgs] = EventManager[IObservableCollection[T], CollectionChangedEventArgs]()
        self.__itemUpdatedEvents: IEventManager[IObservableCollection[T], CollectionChangedEventArgs] = EventManager[IObservableCollection[T], CollectionChangedEventArgs]()
        self.__itemsSwappedEvents: IEventManager[IObservableCollection[T], CollectionChangedEventArgs] = EventManager[IObservableCollection[T], CollectionChangedEventArgs]()
        self.__itemMovedEvents: IEventManager[IObservableCollection[T], CollectionChangedEventArgs] = EventManager[IObservableCollection[T], CollectionChangedEventArgs]()
        self.__itemRemovedEvents: IEventManager[IObservableCollection[T], CollectionChangedEventArgs] = EventManager[IObservableCollection[T], CollectionChangedEventArgs]()
    
    def GetAdded(self) -> IEventManager[IObservableCollection[T], CollectionChangedEventArgs]:
        return self.__itemAddedEvents
    def GetUpdated(self) -> IEventManager[IObservableCollection[T], CollectionChangedEventArgs]:
        return self.__itemUpdatedEvents
    def GetSwapped(self) -> IEventManager[IObservableCollection[T], CollectionChangedEventArgs]:
        return self.__itemsSwappedEvents
    def GetMoved(self) -> IEventManager[IObservableCollection[T], CollectionChangedEventArgs]:
        return self.__itemMovedEvents
    def GetRemoved(self) -> IEventManager[IObservableCollection[T], CollectionChangedEventArgs]:
        return self.__itemRemovedEvents
@final
class _ObservableCollectionEventManager[T](Abstract, IObservableCollectionEvents[T]):
    def __init__(self, events: _ObservableCollectionEvents[T]) -> None:
        super().__init__()

        self.__events: _ObservableCollectionEvents[T] = events

    def OnItemAdded(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        return self.__events.OnItemAdded(handler)
    def OnItemUpdated(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        return self.__events.OnItemUpdated(handler)
    def OnItemsSwapped(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        return self.__events.OnItemsSwapped(handler)
    def OnItemMoved(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        return self.__events.OnItemMoved(handler)
    def OnItemRemoved(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        return self.__events.OnItemRemoved(handler)
@final
class _ObservableCollectionEventInvoker[T](Abstract):
    def __init__(self, sender: IObservableCollection[T], events: _ObservableCollectionEvent[T]) -> None:
        super().__init__()

        self.__sender: IObservableCollection[T] = sender
        self.__events: _ObservableCollectionEvent[T] = events
    
    def __OnCollectionChanged(self, eventManager: IEventManager[IObservableCollection[T], CollectionChangedEventArgs], args: CollectionChangedEventArgs) -> None:
        eventManager.Invoke(self.__sender, args)
    
    def OnItemAdded(self, args: CollectionChangedEventArgs) -> None:
        self.__OnCollectionChanged(self.__events.GetAdded(), args)
    def OnItemUpdated(self, args: CollectionChangedEventArgs) -> None:
        self.__OnCollectionChanged(self.__events.GetUpdated(), args)
    def OnItemsSwapped(self, args: CollectionChangedEventArgs) -> None:
        self.__OnCollectionChanged(self.__events.GetSwapped(), args)
    def OnItemMoved(self, args: CollectionChangedEventArgs) -> None:
        self.__OnCollectionChanged(self.__events.GetMoved(), args)
    def OnItemRemoved(self, args: CollectionChangedEventArgs) -> None:
        self.__OnCollectionChanged(self.__events.GetRemoved(), args)

@final
class _ObservableCollectionEvents[T](Abstract, IObservableCollectionEvents[T]):
    def __init__(self, sender: IObservableCollection[T]) -> None:
        super().__init__()

        events: _ObservableCollectionEvent[T] = _ObservableCollectionEvent[T]()
        
        self.__eventManager: _ObservableCollectionEventManager[T] = _ObservableCollectionEventManager[T](self)
        self.__invoker: _ObservableCollectionEventInvoker[T] = _ObservableCollectionEventInvoker[T](sender, events)
        self.__events: _ObservableCollectionEvent[T] = events
        
        self.__monitor: IMonitor = Monitor()
    
    def AsEventManager(self) -> IObservableCollectionEvents[T]:
        return self.__eventManager
    def AsInvoker(self) -> _ObservableCollectionEventInvoker[T]:
        return self.__invoker
    
    def AssertReentrancy(self) -> None:
        if self.__monitor.IsBusy():
            raise InvalidOperationError("No reentrancy allowed.")
    def __BlockReentrancy(self) -> IDisposable:
        self.__monitor.Initialize()

        return self.__monitor
    
    def __OnCollectionChanged(self, eventManager: IEventManager[IObservableCollection[T], CollectionChangedEventArgs], handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        with self.__BlockReentrancy():
            return eventManager.Add(handler)
        
        raise

    def OnItemAdded(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        return self.__OnCollectionChanged(self.__events.GetAdded(), handler)
    def OnItemUpdated(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        return self.__OnCollectionChanged(self.__events.GetUpdated(), handler)
    def OnItemsSwapped(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        return self.__OnCollectionChanged(self.__events.GetSwapped(), handler)
    def OnItemMoved(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        return self.__OnCollectionChanged(self.__events.GetMoved(), handler)
    def OnItemRemoved(self, handler: EventHandler[IObservableCollection[T], CollectionChangedEventArgs]) -> IEvent:
        return self.__OnCollectionChanged(self.__events.GetRemoved(), handler)

class IReadOnlyObservableCollection[T](ITuple[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetEventManager(self) -> IObservableCollectionEvents[T]:
        pass
class IFixedSizeObservableCollection[T](IReadOnlyObservableCollection[T], IArray[T]):
    def __init__(self) -> None:
        super().__init__()
class IObservableCollection[T](IFixedSizeObservableCollection[T], IList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyObservableCollection[T]:
        pass

class _ReadOnlyObservableCollectionBase[TItem, TList](SequenceAbstract[TItem], IReadOnlyObservableCollection[TItem], GenericConstraint[TList, IFixedSizeObservableCollection[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__items: TList = items
    
    def _GetContainer(self) -> TList:
        return self.__items
    
    @final
    def GetMutability(self) -> Mutability:
        return Mutability.ReadOnly
    @final
    def TryGetSourceMutability(self) -> Mutability|None:
        return self._GetInnerContainer().TryGetSourceMutability()
    
    @final
    def GetCount(self) -> int:
        return self._GetInnerContainer().GetCount()
    
    @final
    def FindFirstIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int:
        return self._GetInnerContainer().FindFirstIndex(item, predicate)
    @final
    def FindLastIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int:
        return self._GetInnerContainer().FindLastIndex(item, predicate)
    
    @final
    def Contains(self, value: TItem|object) -> bool:
        return self._GetInnerContainer().Contains(value)
    
    @final
    def TryGetValue(self, key: int) -> INullable[TItem]:
        return self._GetInnerContainer().TryGetValue(key)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None:
        return self._GetInnerContainer().TryGetEnumerator()
    @final
    def GetEnumeratorMonitor(self) -> IEnumeratorMonitor[TItem]:
        return self._GetInnerContainer().GetEnumeratorMonitor()
    
    @final
    def ToString(self) -> str:
        return self._GetInnerContainer().ToString()
    
    @final
    def GetEventManager(self) -> IObservableCollectionEvents[TItem]:
        return self._GetInnerContainer().GetEventManager()
@final
class _ReadOnlyObservableCollection[T](_ReadOnlyObservableCollectionBase[T, IFixedSizeObservableCollection[T]], IGenericConstraintImplementation[IFixedSizeObservableCollection[T]]):
    def __init__(self, items: IFixedSizeObservableCollection[T]) -> None:
        super().__init__(items)
    
    def SliceAt(self, key: slice) -> ITuple[T]:
        return self._GetContainer().SliceAt(key)
    
    def AsReversed(self) -> ITuple[T]:
        return self._GetContainer().AsReversed().AsReadOnly()
@final
class _FixedSizeObservableCollection[T](_ReadOnlyObservableCollectionBase[T, IObservableCollection[T]], IFixedSizeObservableCollection[T], IGenericConstraintImplementation[IObservableCollection[T]]):
    def __init__(self, items: IObservableCollection[T]) -> None:
        super().__init__(items)
    
    def TrySetAt(self, key: int, value: T) -> bool:
        return self._GetContainer().TrySetAt(key, value)
    
    def Move(self, x: int, y: int) -> None:
        return self._GetContainer().Move(x, y)
    
    def SliceAt(self, key: slice) -> IArray[T]:
        return self._GetContainer().SliceAt(key)
    
    def AsReversed(self) -> IArray[T]:
        return self._GetContainer().AsReversed().AsFixedSize()
    def AsReadOnly(self) -> ITuple[T]:
        return self._GetContainer().AsReadOnly()

class _ReadOnlyObservableCollectionUpdater[T](ValueFunctionUpdater[IReadOnlyObservableCollection[T]]):
    def __init__(self, items: IObservableCollection[T], updater: Method[IFunction[IReadOnlyObservableCollection[T]]]) -> None:
        super().__init__(updater)

        self.__items: IObservableCollection[T] = items
    
    def _GetValue(self) -> IReadOnlyObservableCollection[T]:
        return _ReadOnlyObservableCollection[T](self.__items)
class _FixedSizeObservableCollectionUpdater[T](ValueFunctionUpdater[IFixedSizeObservableCollection[T]]):
    def __init__(self, items: IObservableCollection[T], updater: Method[IFunction[IFixedSizeObservableCollection[T]]]) -> None:
        super().__init__(updater)

        self.__items: IObservableCollection[T] = items
    
    def _GetValue(self) -> IFixedSizeObservableCollection[T]:
        return _FixedSizeObservableCollection[T](self.__items)

class ObservableCollection[T](Collection[T], CollectionAbstract[T], IObservableCollection[T]):
    def __init__(self, items: IList[T]) -> None:
        def updateReadOnly(func: IFunction[IReadOnlyObservableCollection[T]]) -> None:
            self.__readOnly = func
        def updateFixedSize(func: IFunction[IFixedSizeObservableCollection[T]]) -> None:
            self.__fixedSize = func
        
        def updateReversed(func: IFunction[IList[T]]) -> None:
            self.__reversed = func
        
        super().__init__(items)

        events: _ObservableCollectionEvents[T] = _ObservableCollectionEvents[T](self)

        self.__invoker: _ObservableCollectionEventInvoker[T] = events.AsInvoker()
        self.__events: _ObservableCollectionEvents[T] = events

        self.__readOnly: IFunction[IReadOnlyObservableCollection[T]] = _ReadOnlyObservableCollectionUpdater[T](self, updateReadOnly) #type: ignore[no-redef]
        self.__fixedSize: IFunction[IFixedSizeObservableCollection[T]] = _FixedSizeObservableCollectionUpdater[T](self, updateFixedSize) #type: ignore[no-redef]
        
        self.__reversed: IFunction[IList[T]] = self._GetUpdater(items.GetEnumeratorMonitor(), updateReversed) #type: ignore[no-redef]
    
    @final
    def GetEventManager(self) -> IObservableCollectionEvents[T]:
        return self.__events.AsEventManager()
    
    @final
    def __AssertReentrancy(self) -> None:
        self.__events.AssertReentrancy()
    
    @final
    def AsReversed(self) -> IList[T]:
        return self.__reversed.GetValue()
    
    @final
    def AsReadOnly(self) -> IReadOnlyObservableCollection[T]:
        return self.__readOnly.GetValue()
    @final
    def AsFixedSize(self) -> IFixedSizeObservableCollection[T]:
        return self.__fixedSize.GetValue()
    
    def _InsertItem(self, index: int|None, item: T) -> bool:
        self.__AssertReentrancy()

        if super()._InsertItem(index, item):
            self.__invoker.OnItemAdded(CollectionChangedEventArgs(CollectionChangedAction.Add))

            return True
        
        return False
    
    def _InsertItems(self, index: int, items: Iterable[T]) -> bool:
        self.__AssertReentrancy()

        if super()._InsertItems(index, items):
            self.__invoker.OnItemAdded(CollectionChangedEventArgs(CollectionChangedAction.Add))

            return True
        
        return False
    
    def _MoveItem(self, x: int, y: int) -> None:
        self.__AssertReentrancy()

        super()._MoveItem(x, y)

        self.__invoker.OnItemMoved(CollectionChangedEventArgs(CollectionChangedAction.Move))
    
    def _SwapItems(self, x: int, y: int) -> None:
        self.__AssertReentrancy()

        super()._SwapItems(x, y)

        self.__invoker.OnItemsSwapped(CollectionChangedEventArgs(CollectionChangedAction.Swap))
    
    def _SetItem(self, index: int, item: T) -> bool:
        self.__AssertReentrancy()

        if super()._SetItem(index, item):
            self.__invoker.OnItemUpdated(CollectionChangedEventArgs(CollectionChangedAction.Update))

            return True
        
        return False
    
    def _RemoveItemsAt(self, index: int, count: int) -> bool:
        self.__AssertReentrancy()

        if super()._RemoveItemsAt(index, count):
            self.__invoker.OnItemRemoved(CollectionChangedEventArgs(CollectionChangedAction.Remove))

            return True
        
        return False
    
    def _RemoveItemAt(self, index: int) -> bool|None:
        self.__AssertReentrancy()

        if super()._RemoveItemAt(index):
            self.__invoker.OnItemRemoved(CollectionChangedEventArgs(CollectionChangedAction.Remove))

            return True
        
        return False
    
    def _ClearItems(self) -> None:
        self.__AssertReentrancy()
        
        super()._ClearItems()

        self.__invoker.OnItemRemoved(CollectionChangedEventArgs(CollectionChangedAction.Remove))

class CollectionChangedAction(Enum):
    Null = 0
    Add = 1
    Update = 2
    Swap = 3
    Move = 4
    Remove = 5

class CollectionChangedEventArgs(Abstract):
    def __init__(self, action: CollectionChangedAction) -> None:
        super().__init__()

        self.__action: CollectionChangedAction = action
    
    @final
    def GetAction(self) -> CollectionChangedAction:
        return self.__action