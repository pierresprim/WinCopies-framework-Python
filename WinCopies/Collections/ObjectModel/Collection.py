from abc import abstractmethod
from collections.abc import Iterable, Sequence
from enum import Enum
from typing import overload, final, SupportsIndex

from WinCopies import IDisposable, Abstract
from WinCopies.Collections.Enumeration import IEnumerator
from WinCopies.Collections.Extensions import ITuple, IList, KeyableBase, MutableSequence
from WinCopies.Collections.Range import SetItems, RemoveItems
from WinCopies.Typing import IMonitor, Monitor, InvalidOperationError, IGenericConstraintImplementation, GenericConstraint
from WinCopies.Typing.Delegate import EqualityComparison
from WinCopies.Typing.Delegate.Event import IEvent, IEventManager, EventHandler, EventManager

class __CollectionAbstractor[T](Sequence[T], KeyableBase[int, T], IList[T]):
    def __init__(self):
        super().__init__()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|Sequence[T]:
        return self.GetAt(int(index)) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsSequence()
class CollectionAbstractor[T](__CollectionAbstractor[T], MutableSequence[T]):
    def __init__(self):
        super().__init__()

class CollectionBase[TItem, TList](CollectionAbstractor[TItem], GenericConstraint[TList, IList[TItem]]):
    def __init__(self, items: TList):
        super().__init__()

        self.__items: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__items
    
    @abstractmethod
    def Duplicate(self, items: IList[TItem]) -> CollectionAbstractor[TItem]:
        pass

    @final
    def AsReversed(self) -> IList[TItem]:
        return self.Duplicate(self._GetInnerContainer().AsReversed())

    @final
    def AsReadOnly(self) -> ITuple[TItem]:
        return self._GetInnerContainer().AsReadOnly()
    
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
    
    def _RemoveItemAt(self, index: int) -> bool|None:
        return self._GetInnerContainer().TryRemoveAt(index)
    
    def _ClearItems(self) -> None:
        self._GetInnerContainer().Clear()
    
    @final
    def GetCount(self) -> int:
        return self._GetInnerContainer().GetCount()
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    
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
    def TryRemoveAt(self, index: int) -> bool|None:
        self._RemoveItemAt(index)
    
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
    def __delitem__(self, index: int|slice):
        RemoveItems(self, index)
class Collection[T](CollectionBase[T, IList[T]], IList[T], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, items: IList[T]):
        super().__init__(items)
    
    def Duplicate(self, items: IList[T]) -> CollectionAbstractor[T]:
        return Collection[T](items)

class ObservableCollection[T](Collection[T]):
    def __init__(self, items: IList[T]):
        super().__init__(items)

        self.__itemAddedEvents: IEventManager[ObservableCollection[T], CollectionChangedEventArgs] = EventManager[ObservableCollection[T], CollectionChangedEventArgs]()
        self.__itemUpdatedEvents: IEventManager[ObservableCollection[T], CollectionChangedEventArgs] = EventManager[ObservableCollection[T], CollectionChangedEventArgs]()
        self.__itemsSwappedEvents: IEventManager[ObservableCollection[T], CollectionChangedEventArgs] = EventManager[ObservableCollection[T], CollectionChangedEventArgs]()
        self.__itemMovedEvents: IEventManager[ObservableCollection[T], CollectionChangedEventArgs] = EventManager[ObservableCollection[T], CollectionChangedEventArgs]()
        self.__itemRemovedEvents: IEventManager[ObservableCollection[T], CollectionChangedEventArgs] = EventManager[ObservableCollection[T], CollectionChangedEventArgs]()

        self.__monitor: IMonitor = Monitor()
    
    @final
    def __AssertReentrancy(self) -> None:
        if self.__monitor.IsBusy():
            raise InvalidOperationError("No reentrancy allowed.")
    @final
    def __BlockReentrancy(self) -> IDisposable:
        self.__monitor.Initialize()

        return self.__monitor
    
    @final
    def OnCollectionChanged(self, eventManager: IEventManager[ObservableCollection[T], CollectionChangedEventArgs], handler: EventHandler[ObservableCollection[T], CollectionChangedEventArgs]) -> IEvent[ObservableCollection[T]]:
        with self.__BlockReentrancy():
            return eventManager.Add(handler)
        
        raise

    @final
    def OnItemAdded(self, handler: EventHandler[ObservableCollection[T], CollectionChangedEventArgs]) -> IEvent[ObservableCollection[T]]:
        return self.OnCollectionChanged(self.__itemAddedEvents, handler)
    @final
    def OnItemUpdated(self, handler: EventHandler[ObservableCollection[T], CollectionChangedEventArgs]) -> IEvent[ObservableCollection[T]]:
        return self.OnCollectionChanged(self.__itemUpdatedEvents, handler)
    @final
    def OnItemsSwapped(self, handler: EventHandler[ObservableCollection[T], CollectionChangedEventArgs]) -> IEvent[ObservableCollection[T]]:
        return self.OnCollectionChanged(self.__itemsSwappedEvents, handler)
    @final
    def OnItemMoved(self, handler: EventHandler[ObservableCollection[T], CollectionChangedEventArgs]) -> IEvent[ObservableCollection[T]]:
        return self.OnCollectionChanged(self.__itemMovedEvents, handler)
    @final
    def OnItemRemoved(self, handler: EventHandler[ObservableCollection[T], CollectionChangedEventArgs]) -> IEvent[ObservableCollection[T]]:
        return self.OnCollectionChanged(self.__itemRemovedEvents, handler)
    
    def _InsertItem(self, index: int|None, item: T) -> bool:
        self.__AssertReentrancy()

        if super()._InsertItem(index, item):
            self.__itemAddedEvents.Invoke(self, CollectionChangedEventArgs(CollectionChangedAction.Add))

            return True
        
        return False
    
    def _MoveItem(self, x: int, y: int) -> None:
        self.__AssertReentrancy()

        super()._MoveItem(x, y)

        self.__itemMovedEvents.Invoke(self, CollectionChangedEventArgs(CollectionChangedAction.Move))
    
    def _SwapItems(self, x: int, y: int) -> None:
        self.__AssertReentrancy()

        super()._SwapItems(x, y)

        self.__itemsSwappedEvents.Invoke(self, CollectionChangedEventArgs(CollectionChangedAction.Swap))
    
    def _SetItem(self, index: int, item: T) -> bool:
        self.__AssertReentrancy()

        if super()._SetItem(index, item):
            self.__itemUpdatedEvents.Invoke(self, CollectionChangedEventArgs(CollectionChangedAction.Update))

            return True
        
        return False
    
    def _RemoveItemAt(self, index: int) -> bool|None:
        self.__AssertReentrancy()

        if super()._RemoveItemAt(index):
            self.__itemRemovedEvents.Invoke(self, CollectionChangedEventArgs(CollectionChangedAction.Remove))

            return True
        
        return False
    
    def _ClearItems(self) -> None:
        self.__AssertReentrancy()
        
        super()._ClearItems()

        self.__itemRemovedEvents.Invoke(self, CollectionChangedEventArgs(CollectionChangedAction.Remove))

class CollectionChangedAction(Enum):
    Null = 0
    Add = 1
    Update = 2
    Swap = 3
    Move = 4
    Remove = 5

class CollectionChangedEventArgs(Abstract):
    def __init__(self, action: CollectionChangedAction):
        super().__init__()

        self.__action: CollectionChangedAction = action
    
    @final
    def GetAction(self) -> CollectionChangedAction:
        return self.__action