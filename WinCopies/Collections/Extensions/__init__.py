from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sized, Container as ContainerBase, Iterable, Iterator, Collection as CollectionBase, Sequence as SequenceBase, MutableSequence as MutableSequenceBase
from typing import overload, final, SupportsIndex
from weakref import ReferenceType, ref

from WinCopies import IInterface, IStringable, Abstract
from WinCopies.Collections.Core import (ICountable, IContainer, IClearable,
                                        IReadOnlyCollection as IReadOnlyCollectionBase, ICountableCollection, IReadOnlyCountableList,
                                        ITuple as ITupleAbstract, IEquatableTuple as IEquatableTupleBase, IHashableTuple as IHashableTupleBase,
                                        IArray as IArrayAbstract,
                                        IListBase as IListAbstractBase, IList as IListAbstract,
                                        ISortedTuple as ISortedTupleBase, ISortedList as ISortedListBase,
                                        ICountableList as ICountableListBase,
                                        IReadOnlySet as IReadOnlySetBase, ISet as ISetBase,
                                        IReadOnlyDictionary as IReadOnlyDictionaryBase, IDictionary as IDictionaryBase,
                                        IReadOnlyOrderedSet as IReadOnlyOrderedSetBase, IOrderedSet as IOrderedSetBase)
from WinCopies.Collections.Enumeration import IInvalidatableEnumerator, IReversableCountableEnumerable, ICountableEnumerable, IEquatableEnumerable, IHashableEnumerable, GetIterator, TryAsIterator
from WinCopies.Collections.Enumeration.Resumable import IResumableCountableEnumerable, IInvalidatableResumableEnumerator
from WinCopies.Typing.Comparison import EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import Method, Function
from WinCopies.Typing.Discard import DiscardReason
from WinCopies.Typing.Object import IItem
from WinCopies.Typing.Pairing import IKeyValuePair

class IReadOnlyCollection[T](IReadOnlyCountableList[T], ICountableEnumerable[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsCollection(self) -> CollectionBase[T]:
        ...
    
    def AsSized(self) -> Sized: return self.AsCollection()
    def AsContainer(self) -> ContainerBase[T]: return self.AsCollection()
    def AsIterable(self) -> Iterable[T]: return self.AsCollection()

class IEnumerableCollection[T](IReadOnlyCollection[T], ICountableCollection[T]):
    def __init__(self) -> None: super().__init__()

class ICollection[T](IEnumerableCollection[T], ICountableListBase[T]):
    def __init__(self) -> None: super().__init__()

class ISequence[T](IReadOnlyCollection[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsSequence(self) -> SequenceBase[T]:
        ...

    def AsSized(self) -> Sized: return self.AsSequence()
    def AsContainer(self) -> ContainerBase[T]: return self.AsSequence()
    def AsIterable(self) -> Iterable[T]: return self.AsSequence()
    def AsCollection(self) -> CollectionBase[T]: return self.AsSequence()
class IMutableSequence[T](ISequence[T], ICollection[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsMutableSequence(self) -> MutableSequenceBase[T]:
        ...

    def AsSized(self) -> Sized: return self.AsMutableSequence()
    def AsContainer(self) -> ContainerBase[T]: return self.AsMutableSequence()
    def AsIterable(self) -> Iterable[T]: return self.AsMutableSequence()
    def AsCollection(self) -> CollectionBase[T]: return self.AsMutableSequence()
    def AsSequence(self) -> SequenceBase[T]: return self.AsMutableSequence()

class ReadOnlyCollectionBase[T](CollectionBase[T], IReadOnlyCollection[T]):
    def __init__(self) -> None: super().__init__()
    
    def _TryGetIterator(self) -> Iterator[T]|None: return TryAsIterator(self.TryGetEnumerator())
    
    @final
    def __len__(self) -> int: return self.GetCount()
    
    @final
    def AsSized(self) -> Sized: return self
    @final
    def AsContainer(self) -> ContainerBase[T]: return self
    @final
    def AsIterable(self) -> Iterable[T]: return self
    @final
    def AsCollection(self) -> CollectionBase[T]: return self
class ReadOnlyCollection[T](ReadOnlyCollectionBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def __contains__(self, x: object) -> bool: return self.Contains(x)
    
    @final
    def __iter__(self) -> Iterator[T]: return GetIterator(self._TryGetIterator())

class Container[T](ContainerBase[T], IContainer[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def __contains__(self, x: object) -> bool: return self.Contains(x)

class ReadOnlySequence[T](SequenceBase[T], ReadOnlyCollectionBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def __contains__(self, x: object) -> bool: return self.Contains(x)
    
    @final
    def __iter__(self) -> Iterator[T]: return GetIterator(self._TryGetIterator())

class Sequence[T](ReadOnlySequence[T], ISequence[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def AsSequence(self) -> SequenceBase[T]: return self
class MutableSequence[T](MutableSequenceBase[T], Sequence[T], IMutableSequence[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def AsMutableSequence(self) -> MutableSequenceBase[T]: return self

class IEnumeratorMonitor(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def CreateEnumerator[T](self, items: ITuple[T]) -> IInvalidatableEnumerator[T]:
        ...
class IResumableEnumeratorMonitor(IEnumeratorMonitor):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def CreateResumableEnumerator[T](self, items: ITuple[T]) -> IInvalidatableResumableEnumerator[T]:
        ...

class IRevocableViewMonitor(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def CreateRevocableView[T](self, items: ITuple[T], onDisposed: Method[DiscardReason]|None = None) -> ITuple[T]:
        ...

class ICollectionMonitors(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor:
        ...
    
    @abstractmethod
    def GetRevocableViewMonitor(self) -> IRevocableViewMonitor:
        ...

class ICollectionViewMonitor[T](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetImmutableView(self) -> ITuple[T]:
        ...

class CollectionViewMonitorBase[T](Abstract, ICollectionViewMonitor[T]):
    def __init__(self, items: ITuple[T]) -> None:
        def createView() -> ITuple[T]:
            def getView() -> ITuple[T]:
                view: ITuple[T]|None = _ref()

                return createView() if view is None else view

            view: ITuple[T] = self._CreateView(self._GetItems().AsReadOnly(), onDisposed)

            _ref: ReferenceType[ITuple[T]] = ref(view)

            self.__view = getView

            return view

        def onDisposed(reason: DiscardReason) -> None:
            if reason.IsExplicit(): self.__view = createView

        super().__init__()

        self.__items: ITuple[T] = items
        self.__view: Function[ITuple[T]] = createView # type: ignore[no-redef]

    @abstractmethod
    def _CreateView(self, items: ITuple[T], onDisposed: Method[DiscardReason]) -> ITuple[T]:
        ...

    @final
    def _GetItems(self) -> ITuple[T]: return self.__items

    @final
    def GetImmutableView(self) -> ITuple[T]:
        func: Function[ITuple[T]] = self.__view # For mypy compatibility

        return func()
class CollectionViewMonitor[T](CollectionViewMonitorBase[T]):
    def __init__(self, items: ITuple[T]) -> None: super().__init__(items)

    @final
    def _CreateView(self, items: ITuple[T], onDisposed: Method[DiscardReason]) -> ITuple[T]: return self._GetItems().GetCollectionMonitors().GetRevocableViewMonitor().CreateRevocableView(items, onDisposed)

class ITupleBase[T](ITupleAbstract[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetCollectionMonitors(self) -> ICollectionMonitors:
        ...

    @abstractmethod
    def AsImmutable(self) -> ITuple[T]:
        ...
class ITuple[T](ITupleBase[T], ISequence[T], IReversableCountableEnumerable[T], IResumableCountableEnumerable[T], IStringable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> ITuple[T]:
        ...
    
    @abstractmethod
    def AsReadOnly(self) -> ITuple[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ITuple[T]:
        ...
class IEquatableTuple[T: EquatableProtocol](IEquatableTupleBase[T], IEquatableEnumerable[T], ITuple[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsReversed(self) -> IEquatableTuple[T]:
        ...
    
    @abstractmethod
    def AsReadOnly(self) -> IEquatableTuple[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        ...
class IHashableTuple[T: HashableProtocol](IHashableTupleBase[T], IEquatableTuple[T], IHashableEnumerable[T], IItem):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsReversed(self) -> IHashableTuple[T]:
        ...
    
    @abstractmethod
    def AsReadOnly(self) -> IHashableTuple[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IHashableTuple[T]:
        ...

class IArray[T](ITuple[T], IArrayAbstract[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> IArray[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IArray[T]:
        ...

class IListBase[T](ITuple[T], IListAbstractBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IListBase[T]:
        ...

    @abstractmethod
    def AsReversed(self) -> IListBase[T]:
        ...
class IList[T](IListAbstract[T], IArray[T], IListBase[T], IMutableSequence[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsFixedSize(self) -> IArray[T]:
        ...
    
    @abstractmethod
    def AsReversed(self) -> IList[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IList[T]:
        ...

class ISortedTuple[T](ITuple[T], ISortedTupleBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> ISortedTuple[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ISortedTuple[T]:
        ...
class ISortedList[T](IListBase[T], ISortedListBase[T], ISortedTuple[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> ISortedTuple[T]:
        ...
    
    @abstractmethod
    def AsReversed(self) -> ISortedList[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ISortedList[T]:
        ...

# TODO: Should implement a Mapping abstractor provider.
class IReadOnlyDictionary[TKey: HashableProtocol, TValue](IReadOnlyDictionaryBase[TKey, TValue], ICountableEnumerable[IKeyValuePair[TKey, TValue]], IStringable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetKeys(self) -> ICountableEnumerable[TKey]:
        ...
    @abstractmethod
    def GetValues(self) -> ICountableEnumerable[TValue]:
        ...
# TODO: Should implement a MutableMapping abstractor provider.
class IDictionary[TKey: HashableProtocol, TValue](IDictionaryBase[TKey, TValue], IReadOnlyDictionary[TKey, TValue]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyDictionary[TKey, TValue]:
        ...

class IReadOnlySet[T: HashableProtocol](IReadOnlySetBase[T], ICountableEnumerable[T], IStringable):
    def __init__(self) -> None: super().__init__()
class ISet[T: HashableProtocol](ISetBase[T], IReadOnlySet[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlySet[T]:
        ...

class SequenceAbstract[T](Sequence[T], ITuple[T]):
    def __init__(self) -> None: super().__init__()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|SequenceBase[T]: return self.GetAt(int(index)) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsSequence()
class MutableSequenceAbstract[T](MutableSequence[T], IList[T]):
    def __init__(self) -> None: super().__init__()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> MutableSequenceBase[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|MutableSequenceBase[T]: return self.GetAt(int(index)) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsMutableSequence()

class IReadOnlyOrderedSet[T: HashableProtocol](IReadOnlySet[T], IReadOnlyOrderedSetBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsTuple(self) -> IEquatableTuple[T]:
        ...
class IOrderedSet[T: HashableProtocol](IOrderedSetBase[T], ISet[T], IReadOnlyOrderedSet[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyOrderedSet[T]:
        ...

    @abstractmethod
    def AsList(self) -> IList[T]:
        ...

class IReadOnlyKeyedSet[TKey: HashableProtocol, TValue](ICountableEnumerable[ITuple[TValue]], IReadOnlyCollectionBase):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetKeys(self) -> IReadOnlyOrderedSet[TKey]:
        ...
class IKeyedSet[TKey: HashableProtocol, TValue](IReadOnlyKeyedSet[TKey, TValue], IClearable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryAdd(self, values: ITuple[TValue]) -> bool:
        ...

    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyKeyedSet[TKey, TValue]:
        ...

def GetCount(items: ICountable|Sized) -> int:
    match items:
        case ICountable(): return items.GetCount()
        case Sized(): return len(items)
def TryGetCount(items: ICountable|Sized|None) -> int|None:
        return None if items is None else GetCount(items)

@overload
def Count[T](items: CollectionBase[T]|Iterable[T]) -> tuple[CollectionBase[T], int]: ...
@overload
def Count[T](items: ICountableEnumerable[T]) -> tuple[ICountableEnumerable[T], int]: ...

def Count[T](items: ICountableEnumerable[T]|CollectionBase[T]|Iterable[T]) -> tuple[ICountableEnumerable[T]|CollectionBase[T], int]:
    def getItems(items: CollectionBase[T]) -> tuple[CollectionBase[T], int]: return (items, len(items))

    match items:
        case ICountableEnumerable(): return (items, items.GetCount())
        case CollectionBase(): return getItems(items)
        
        case _:
            return getItems(tuple(items))

@overload
def TryCount[T](items: CollectionBase[T]|Iterable[T]) -> tuple[CollectionBase[T], int]: ...
@overload
def TryCount[T](items: ICountableEnumerable[T]) -> tuple[ICountableEnumerable[T], int]: ...
@overload
def TryCount(items: None) -> None: ...

def TryCount[T](items: ICountableEnumerable[T]|CollectionBase[T]|Iterable[T]|None) -> tuple[ICountableEnumerable[T]|CollectionBase[T]|Iterable[T], int]|None:
    return None if items is None else Count(items)