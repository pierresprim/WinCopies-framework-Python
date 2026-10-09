from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sized, Container as ContainerBase, Iterable, Iterator, Collection as CollectionBase, Sequence as SequenceBase, MutableSequence as MutableSequenceBase
from typing import overload, final, Literal, SupportsIndex
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
from WinCopies.Collections.Enumeration.Core import IInvalidatableEnumerator, IReversableCountableEnumerable, ICountableEnumerable, IEquatableEnumerable, IHashableEnumerable, GetIterator, TryAsIterator
from WinCopies.Collections.Enumeration.Resumable import IResumableCountableEnumerable, IInvalidatableResumableEnumerator
from WinCopies.Collections.Registry import IObjectMonitor, ICollectionRegistrar
from WinCopies.Collections.Util import CreateSequence
from WinCopies.Typing.Comparison import EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import Method, Function, Converter
from WinCopies.Typing.Discard import DiscardReason
from WinCopies.Typing.Generic import GenericConstraint, IGenericConstraintImplementation
from WinCopies.Typing.Object import IItem
from WinCopies.Typing.Pairing import IKeyValuePair
from WinCopies.Typing.Protocols import SupportsEqualityAndRichComparison

class IReadOnlyCollection[T](IReadOnlyCountableList[T], ICountableEnumerable[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def IsResumable(self) -> bool|None: return True
    
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

class _IMutableSequence[T](IMutableSequence[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _ReverseDefault(self) -> None:
        ...

    @abstractmethod
    def _Reverse(self) -> None:
        ...

class Sequence[T](ReadOnlySequence[T], ISequence[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def AsSequence(self) -> SequenceBase[T]: return self
class MutableSequence[T](MutableSequenceBase[T], Sequence[T], _IMutableSequence[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def _ReverseDefault(self) -> None:
        return super().reverse()
    
    @final
    def AsMutableSequence(self) -> MutableSequenceBase[T]: return self

    @final
    def reverse(self) -> None:
        self._Reverse()

    # Sealed for the same reason as the reversal: the inherited mixin writes it as repeated
    # append, so the act is seen as its elements. No hook of its own, unlike the reversal,
    # because the act already has a named form here -- AddRange -- which every class reached
    # possesses and four of them override.
    @final
    def extend(self, values: Iterable[T]) -> None:
        self.AddRange(values)

class IDefaultMutableSequence[T](_IMutableSequence[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def _Reverse(self) -> None: self._ReverseDefault()

class IEnumeratorMonitor(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def CreateEnumerator[T](self, items: ITuple[T], strict: bool = False) -> IInvalidatableEnumerator[T]:
        ...
class IResumableEnumeratorMonitor(IEnumeratorMonitor):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def CreateResumableEnumerator[T](self, items: ITuple[T], strict: bool = False) -> IInvalidatableResumableEnumerator[T]:
        ...

class IRevocableViewMonitor(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @overload
    def CreateRevocableView[T](self, items: IEquatableTuple[T], onDisposed: Method[DiscardReason]|None = None) -> IEquatableTuple[T]: ...
    @overload
    def CreateRevocableView[T](self, items: ITuple[T], onDisposed: Method[DiscardReason]|None = None) -> ITuple[T]: ...
    
    @abstractmethod
    def CreateRevocableView[T](self, items: IEquatableTuple[T]|ITuple[T], onDisposed: Method[DiscardReason]|None = None) -> IEquatableTuple[T]|ITuple[T]:
        ...

class ICollectionMonitors(ICollectionRegistrar[IObjectMonitor]):
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

class IEquatableCollectionViewMonitor[T](ICollectionViewMonitor[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetImmutableView(self) -> IEquatableTuple[T]:
        ...
class IHashableCollectionViewMonitor[T](ICollectionViewMonitor[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetImmutableView(self) -> IHashableTuple[T]:
        ...

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
    def AsImmutable(self) -> IEquatableTuple[T]:
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
    
    @final
    def AsImmutable(self) -> IHashableTuple[T]:
        return self
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
    
    # Asked before anything is written, because a span replacement cannot be taken back: the
    # removal that frees the positions runs first, so a refusal arriving after it has already
    # destroyed what it took -- measured on a sized list, where l[1:3] = (7, 8, 9) left [0, 3]
    # of [0, 1, 2, 3]. Undoing it is no answer either, since the restoration would go back
    # through TryInsertRange, the very member whose refusal triggered it, and its success is a
    # property of one container rather than of this contract.
    #
    # The positions arrive as a range because a range says what leaves: a container holding an
    # invariant over its content judges the arriving items against what remains, not against
    # what it still holds -- which is why l[1:3] = (3, 9) is legitimate on an ordered set that
    # already holds that 3 inside the span. The contiguous span and the stepped one are the
    # same question, told apart by the step.
    #
    # No default answer. One that said True would reopen the defect, silently, for every
    # constrained container that forgot to narrow it -- which is exactly how the reversal hook
    # came to be a no-op that a whole commit did not notice.
    @abstractmethod
    def CanSetRange(self, indices: range, items: ICountableEnumerable[T]) -> bool:
        ...
    
    @abstractmethod
    def AsFixedSize(self) -> IArray[T]:
        ...
    
    @abstractmethod
    def AsReversed(self) -> IList[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IList[T]:
        ...

class ISortedTuple[T: SupportsEqualityAndRichComparison](ITuple[T], ISortedTupleBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> ISortedTuple[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ISortedTuple[T]:
        ...
class ISortedList[T: SupportsEqualityAndRichComparison](IListBase[T], ISortedListBase[T], ISortedTuple[T]):
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

class ISizedList[T](IList[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetMaxLength(self) -> int:
        ...
    
    @abstractmethod
    def ValidateLength(self, count: int) -> bool:
        ...
    
    @abstractmethod
    def TryInsertAt(self, index: int, value: T) -> bool|None:
        ...
    @final
    def TryInsert(self, index: int, value: T) -> bool: return self.TryInsertAt(index, value) is True

# TODO: Should implement a Mapping abstractor provider.
class IReadOnlyDictionary[TKey: HashableProtocol, TValue](IReadOnlyDictionaryBase[TKey, TValue], ICountableEnumerable[IKeyValuePair[TKey, TValue]], IStringable):
    def __init__(self) -> None: super().__init__()

    @final
    def IsResumable(self) -> bool|None: return True
    
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

    @final
    def IsResumable(self) -> bool|None: return True
class ISet[T: HashableProtocol](ISetBase[T], IReadOnlySet[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlySet[T]:
        ...

class GenericCollectionViewMonitor[TContainer, TInterface](GenericConstraint[TContainer, TInterface]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _AsReadOnly(self, collection: TContainer) -> TContainer: return collection
class IGenericCollectionViewMonitorImplementation[T](GenericCollectionViewMonitor[T, T], IGenericConstraintImplementation[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def _AsReadOnly(self, collection: T) -> T: return collection

class CollectionViewMonitorAbstract[TItem, TCollection](Abstract, ICollectionViewMonitor[TItem], GenericCollectionViewMonitor[TCollection, ITuple[TItem]]):
    def __init__(self, items: TCollection) -> None:
        def createView() -> TCollection:
            def getView() -> TCollection:
                view: TCollection|None = _ref()

                return createView() if view is None else view

            view: TCollection = self._CreateView(self._AsReadOnly(self._GetContainer()), onDisposed)

            _ref: ReferenceType[TCollection] = ref(view)

            self.__view = getView

            return view

        def onDisposed(reason: DiscardReason) -> None:
            if reason.IsExplicit(): self.__view = createView

        super().__init__()

        self.__items: TCollection = items
        self.__view: Function[TCollection] = createView # type: ignore[no-redef]

    @abstractmethod
    def _CreateView(self, items: TCollection, onDisposed: Method[DiscardReason]) -> TCollection:
        ...

    @final
    def _GetContainer(self) -> TCollection: return self.__items

    @final
    def _GetImmutableView(self) -> TCollection:
        func: Function[TCollection] = self.__view # For mypy compatibility

        return func()

    @final
    def _GetMonitor(self) -> IRevocableViewMonitor:
        return self._GetInnerContainer().GetCollectionMonitors().GetRevocableViewMonitor()

class CollectionViewMonitorBase[T](CollectionViewMonitorAbstract[T, ITuple[T]], IGenericCollectionViewMonitorImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None: super().__init__(items)

    @final
    def GetImmutableView(self) -> ITuple[T]: return self._GetImmutableView()
class CollectionViewMonitor[T](CollectionViewMonitorBase[T]):
    def __init__(self, items: ITuple[T]) -> None: super().__init__(items)

    @final
    def _CreateView(self, items: ITuple[T], onDisposed: Method[DiscardReason]) -> ITuple[T]: return self._GetMonitor().CreateRevocableView(items, onDisposed)

class EquatableCollectionViewMonitorBase[T](CollectionViewMonitorAbstract[T, IEquatableTuple[T]], IEquatableCollectionViewMonitor[T], IGenericCollectionViewMonitorImplementation[IEquatableTuple[T]]):
    def __init__(self, items: IEquatableTuple[T]) -> None: super().__init__(items)

    @final
    def GetImmutableView(self) -> IEquatableTuple[T]: return self._GetImmutableView()
class EquatableCollectionViewMonitor[T](EquatableCollectionViewMonitorBase[T]):
    def __init__(self, items: IEquatableTuple[T]) -> None: super().__init__(items)

    @final
    def _CreateView(self, items: IEquatableTuple[T], onDisposed: Method[DiscardReason]) -> IEquatableTuple[T]: return self._GetMonitor().CreateRevocableView(items, onDisposed)

class HashableCollectionViewMonitorBase[T](CollectionViewMonitorAbstract[T, IHashableTuple[T]], IHashableCollectionViewMonitor[T], IGenericCollectionViewMonitorImplementation[IHashableTuple[T]]):
    def __init__(self, items: IHashableTuple[T]) -> None: super().__init__(items)

    @final
    def GetImmutableView(self) -> IHashableTuple[T]: return self._GetImmutableView()
# A HashableCollectionViewMonitor would not make sense as IHashableTuple always returns itself as its immutable view.

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

    @final
    def IsResumable(self) -> bool|None: return True
    
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

def __GetItems[T](items: CollectionBase[T]) -> tuple[CollectionBase[T], int]: return (items, len(items))

@overload
def TryCountFromContainer[TItem, TList](items: ICountableEnumerable[TItem], asIterable: Literal[True], selector: Converter[Iterable[TItem], tuple[TList, int]]|None = None) -> tuple[Iterable[TItem], int]: ...
@overload
def TryCountFromContainer[TItem, TList](items: ICountableEnumerable[TItem], asIterable: Literal[False], selector: Converter[Iterable[TItem], tuple[TList, int]]|None = None) -> tuple[ICountableEnumerable[TItem], int]: ...
@overload
def TryCountFromContainer[T](items: Iterable[T], asIterable: Literal[False] = False, selector: None = None) -> None: ...
@overload
def TryCountFromContainer[TItem, TList](items: Iterable[TItem], asIterable: bool, selector: Converter[Iterable[TItem], tuple[TList, int]]) -> tuple[TList, int]: ...
@overload
def TryCountFromContainer[TItem, TList](items: None, asIterable: bool = False, selector: Converter[Iterable[TItem], tuple[TList, int]]|None = None) -> None: ...
@overload
def TryCountFromContainer[TItem, TList](items: CollectionBase[TItem], asIterable: Literal[False] = False, selector: Converter[Iterable[TItem], tuple[TList, int]]|None = None) -> tuple[CollectionBase[TItem]|TList, int]|None: ...

def TryCountFromContainer[TItem, TList](items: ICountableEnumerable[TItem]|CollectionBase[TItem]|Iterable[TItem]|None, asIterable: bool = False, selector: Converter[Iterable[TItem], tuple[TList, int]]|None = None) -> tuple[ICountableEnumerable[TItem]|CollectionBase[TItem]|Iterable[TItem]|TList, int]|None:
    match items:
        case None: return None

        case ICountableEnumerable(): return (items.AsIterable() if asIterable else items, items.GetCount())
        case CollectionBase(): return __GetItems(items)
        
        case _: return None if selector is None else selector(items)

@overload
def Count[T](items: ICountableEnumerable[T]) -> tuple[ICountableEnumerable[T], int]: ...
@overload
def Count[T](items: CollectionBase[T]|Iterable[T]) -> tuple[CollectionBase[T], int]: ...
@overload
def Count(items: None) -> None: ...

def Count[T](items: ICountableEnumerable[T]|CollectionBase[T]|Iterable[T]|None) -> tuple[ICountableEnumerable[T]|CollectionBase[T], int]|None:
    return TryCountFromContainer(items, False, lambda items: __GetItems(CreateSequence(items)))

@overload
def CountAsIterable[T](items: ICountableEnumerable[T]) -> tuple[Iterable[T], int]: ...
@overload
def CountAsIterable[T](items: CollectionBase[T]|Iterable[T]) -> tuple[CollectionBase[T], int]: ...
@overload
def CountAsIterable(items: None) -> None: ...

def CountAsIterable[T](items: ICountableEnumerable[T]|CollectionBase[T]|Iterable[T]|None) -> tuple[CollectionBase[T]|Iterable[T], int]|None:
    return TryCountFromContainer(items, True, lambda items: __GetItems(CreateSequence(items)))