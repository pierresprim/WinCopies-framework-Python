from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sized, Container as ContainerBase, Iterable, Iterator, Collection as CollectionBase, Sequence as SequenceBase, MutableSequence as MutableSequenceBase
from typing import overload, final, SupportsIndex

from WinCopies import Collections, IInterface, IStringable
from WinCopies.Collections import ICountable, IReadOnlyCollection as IReadOnlyCollectionBase, IContainer, ICountableCollection, IReadOnlyCountableList, ICountableList as ICountableListBase, IClearable
from WinCopies.Collections.Enumeration import IEnumerator, IReversableCountableEnumerable, ICountableEnumerable, IEquatableEnumerable, IHashableEnumerable, GetIterator, TryAsIterator
from WinCopies.Collections.Enumeration.Resumable import IResumableCountableEnumerable, IResumableEnumerator
from WinCopies.Typing.Comparison import IEquatableValue, IHashableValue, HashableProtocol
from WinCopies.Typing.Object import IItem
from WinCopies.Typing.Pairing import IKeyValuePair

class IReadOnlyCollection[T](IReadOnlyCountableList[T], ICountableEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsCollection(self) -> CollectionBase[T]:
        pass
    
    def AsSized(self) -> Sized:
        return self.AsCollection()
    def AsContainer(self) -> ContainerBase[T]:
        return self.AsCollection()
    def AsIterable(self) -> Iterable[T]:
        return self.AsCollection()

class IEnumerableCollection[T](IReadOnlyCollection[T], ICountableCollection[T]):
    def __init__(self) -> None:
        super().__init__()

class ICollection[T](IEnumerableCollection[T], ICountableListBase[T]):
    def __init__(self) -> None:
        super().__init__()

class ISequence[T](IReadOnlyCollection[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsSequence(self) -> SequenceBase[T]:
        pass

    def AsSized(self) -> Sized:
        return self.AsSequence()
    def AsContainer(self) -> ContainerBase[T]:
        return self.AsSequence()
    def AsIterable(self) -> Iterable[T]:
        return self.AsSequence()
    def AsCollection(self) -> CollectionBase[T]:
        return self.AsSequence()
class IMutableSequence[T](ISequence[T], ICollection[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsMutableSequence(self) -> MutableSequenceBase[T]:
        pass

    def AsSized(self) -> Sized:
        return self.AsMutableSequence()
    def AsContainer(self) -> ContainerBase[T]:
        return self.AsMutableSequence()
    def AsIterable(self) -> Iterable[T]:
        return self.AsMutableSequence()
    def AsCollection(self) -> CollectionBase[T]:
        return self.AsMutableSequence()
    def AsSequence(self) -> SequenceBase[T]:
        return self.AsMutableSequence()

class ReadOnlyCollectionBase[T](CollectionBase[T], IReadOnlyCollection[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def _TryGetIterator(self) -> Iterator[T]|None:
        return TryAsIterator(self.TryGetEnumerator())
    
    @final
    def __len__(self) -> int:
        return self.GetCount()
    
    @final
    def AsSized(self) -> Sized:
        return self
    @final
    def AsContainer(self) -> ContainerBase[T]:
        return self
    @final
    def AsIterable(self) -> Iterable[T]:
        return self
    @final
    def AsCollection(self) -> CollectionBase[T]:
        return self
class ReadOnlyCollection[T](ReadOnlyCollectionBase[T], IReadOnlyCollection[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def __contains__(self, x: object) -> bool:
        return self.Contains(x)
    
    @final
    def __iter__(self) -> Iterator[T]:
        return GetIterator(self._TryGetIterator())

class Container[T](ContainerBase[T], IContainer[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def __contains__(self, x: object) -> bool:
        return self.Contains(x)

class ReadOnlySequence[T](SequenceBase[T], ReadOnlyCollectionBase[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def __contains__(self, x: object) -> bool:
        return self.Contains(x)
    
    @final
    def __iter__(self) -> Iterator[T]:
        return GetIterator(self._TryGetIterator())

class Sequence[T](ReadOnlySequence[T], ISequence[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def AsSequence(self) -> SequenceBase[T]:
        return self
class MutableSequence[T](MutableSequenceBase[T], Sequence[T], IMutableSequence[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def AsMutableSequence(self) -> MutableSequenceBase[T]:
        return self

class IEnumeratorMonitor[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def CreateEnumerator(self, items: ITuple[T]) -> IEnumerator[T]:
        pass
class IResumableEnumeratorMonitor[T](IEnumeratorMonitor[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def CreateResumableEnumerator(self, items: ITuple[T]) -> IResumableEnumerator[T]:
        pass

class ITuple[T](Collections.ITuple[T], ISequence[T], IReversableCountableEnumerable[T], IResumableCountableEnumerable[T], IStringable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor[T]:
        pass
    
    @abstractmethod
    def AsReversed(self) -> ITuple[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ITuple[T]:
        pass
class IEquatableTuple[T: IEquatableValue](Collections.IEquatableTuple[T], IEquatableEnumerable[T], ITuple[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReversed(self) -> IEquatableTuple[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        pass
class IHashableTuple[T: IHashableValue](Collections.IHashableTuple[T], IEquatableTuple[T], IHashableEnumerable[T], IItem):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReversed(self) -> IHashableTuple[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IHashableTuple[T]:
        pass

class IArrayBase[T](ITuple[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> ITuple[T]:
        pass
    
    @abstractmethod
    def AsReversed(self) -> IArrayBase[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IArrayBase[T]:
        pass
class IArray[T](IArrayBase[T], Collections.IArray[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> IArray[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IArray[T]:
        pass

class IListBase[T](IArrayBase[T], Collections.IListBase[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IListBase[T]:
        pass

    @abstractmethod
    def AsReversed(self) -> IListBase[T]:
        pass
class IList[T](Collections.IList[T], IArray[T], IListBase[T], IMutableSequence[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsFixedSize(self) -> IArray[T]:
        pass
    
    @abstractmethod
    def AsReversed(self) -> IList[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IList[T]:
        pass

class ISortedTuple[T](ITuple[T], Collections.ISortedTuple[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> ISortedTuple[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ISortedTuple[T]:
        pass
class ISortedList[T](IListBase[T], Collections.ISortedList[T], ISortedTuple[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> ISortedTuple[T]:
        pass
    
    @abstractmethod
    def AsReversed(self) -> ISortedList[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ISortedList[T]:
        pass

# TODO: Should implement a Mapping abstractor provider.
class IReadOnlyDictionary[TKey: HashableProtocol, TValue](Collections.IReadOnlyDictionary[TKey, TValue], ICountableEnumerable[IKeyValuePair[TKey, TValue]], IStringable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetKeys(self) -> ICountableEnumerable[TKey]:
        pass
    @abstractmethod
    def GetValues(self) -> ICountableEnumerable[TValue]:
        pass
# TODO: Should implement a MutableMapping abstractor provider.
class IDictionary[TKey: HashableProtocol, TValue](Collections.IDictionary[TKey, TValue], IReadOnlyDictionary[TKey, TValue]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyDictionary[TKey, TValue]:
        pass

class IReadOnlySet[T: HashableProtocol](Collections.IReadOnlySet[T], ICountableEnumerable[T], IStringable):
    def __init__(self) -> None:
        super().__init__()
class ISet[T: HashableProtocol](Collections.ISet[T], IReadOnlySet[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlySet[T]:
        pass

class SequenceAbstract[T](Sequence[T], ITuple[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|SequenceBase[T]:
        return self.GetAt(int(index)) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsSequence()
class MutableSequenceAbstract[T](MutableSequence[T], IList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> MutableSequenceBase[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|MutableSequenceBase[T]:
        return self.GetAt(int(index)) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsMutableSequence()

class IReadOnlyOrderedSet[T: IHashableValue](IReadOnlySet[T], Collections.IReadOnlyOrderedSet[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsTuple(self) -> IEquatableTuple[T]:
        pass
class IOrderedSet[T: IHashableValue](Collections.IOrderedSet[T], ISet[T], IReadOnlyOrderedSet[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyOrderedSet[T]:
        pass

    @abstractmethod
    def AsList(self) -> IList[T]:
        pass

class IReadOnlyKeyedSet[TKey: IHashableValue, TValue](ICountableEnumerable[ITuple[TValue]], IReadOnlyCollectionBase):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetKeys(self) -> IReadOnlyOrderedSet[TKey]:
        pass
class IKeyedSet[TKey: IHashableValue, TValue](IReadOnlyKeyedSet[TKey, TValue], IClearable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryAdd(self, values: ITuple[TValue]) -> bool:
        pass

    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyKeyedSet[TKey, TValue]:
        pass

def GetCount(items: ICountable|Sized) -> int:
    match items:
        case ICountable():
            return items.GetCount()
        
        case Sized():
            return len(items)
def TryGetCount(items: ICountable|Sized|None) -> int|None:
        return None if items is None else GetCount(items)

def Count[T](items: ICountableEnumerable[T]|CollectionBase[T]|Iterable[T]) -> tuple[Iterable[T], int]:
    match items:
        case ICountableEnumerable():
            return (items.AsIterable(), items.GetCount())
        
        case CollectionBase():
            return (items, len(items))
        
        case _:
            items = tuple(items)

            return (items, len(items))
def TryCount[T](items: Iterable[T]|None) -> tuple[Iterable[T], int]|None:
    return None if items is None else Count(items)