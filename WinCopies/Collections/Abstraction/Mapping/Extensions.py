from __future__ import annotations

from collections.abc import Container, Iterable, Sequence, MutableSequence
from typing import overload, final, SupportsIndex

from WinCopies import Abstract
from WinCopies.Collections.Abstraction.Collection import List, CreateTuple
from WinCopies.Collections.Abstraction.Enumeration import TryCreateEnumerator
from WinCopies.Collections.Abstraction.Mapping import Set, HasDuplicate
from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Enumeration.Buffering import BuildIterable
from WinCopies.Collections.Enumeration.Core import IEnumerable, ICountableEnumerable, IEnumerator, CountableEnumerable, AsEnumerable, AsEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Extensions import Count, Collection, ICollectionMonitors, IEquatableCollectionViewMonitor, IReadOnlyOrderedSet, ITuple, IEquatableTuple, IArray, IList, IReadOnlyKeyedSet, ISet, IOrderedSet, IKeyedSet, EquatableCollectionViewMonitor, SequenceAbstract, MutableSequence
from WinCopies.Collections.Extensions.Collection import MutableList
from WinCopies.Collections.Iteration.Enumeration import Any
from WinCopies.Collections.Linked.Singly import ICountableEnumerableQueue, CreateCountableEnumerableQueue
from WinCopies.Collections.Range import RemoveItems
from WinCopies.Collections.Range.Extensions import SetOrderedItems, TrySetOrderedValue
from WinCopies.Typing import INullable
from WinCopies.Typing.Comparison import INotHashableValue, HashableProtocol
from WinCopies.Typing.Delegate import Method, IFunction, EqualityComparison, ValueFunctionUpdater
from WinCopies.Typing.Generic import GenericConstraint, IGenericConstraintImplementation

@final
class _OrderedSetList[T: HashableProtocol](Abstract, MutableList[T], Collection.CollectionAbstract[T]):
    def __init__(self, items: IOrderedSet[T], l: IList[T], s: ISet[T], innerSet: set[T]) -> None:
        def updateReversed(func: IFunction[IList[T]]) -> None: self.__reversed = func
        def updateFixedSize(func: IFunction[IArray[T]]) -> None: self.__fixedSize = func
        
        super().__init__()

        self.__items: IOrderedSet[T] = items
        self.__list: IList[T] = l
        self.__set: ISet[T] = s
        self.__innerSet: set[T] = innerSet

        self.__fixedSize: IFunction[IArray[T]] = self._GetFixedSizeUpdater(updateFixedSize) # type: ignore[no-redef]
        self.__reversed: IFunction[IList[T]] = self._GetReversedUpdater(updateReversed) # type: ignore[no-redef]
    
    def GetMutability(self) -> Mutability: return Mutability.Mutable
    def TryGetSourceMutability(self) -> None: return None
    
    def GetCount(self) -> int: return self.__items.GetCount()
    
    def Contains(self, value: T|object) -> bool: return self.__set.Contains(value)
    
    def _Move(self, x: int, y: int) -> None: self.__list.Move(x, y)
    # An exchange is a permutation too, so it goes to the order alone. The default
    # implementation performs it as two positional writes, the first of which holds a
    # momentary duplicate that the unicity rule refuses.
    def _Swap(self, x: int, y: int) -> None: self.__list.Swap(x, y)
    # A permutation leaves membership untouched, so it goes to the order alone, exactly as
    # _Move does. The inherited protocol implementation reverses by pairwise positional
    # assignment instead, and each of those assignments momentarily holds a duplicate that
    # the unicity rule refuses -- rightly per assignment, wrongly for the operation.
    def _Reverse(self) -> None: self.__list.AsMutableSequence().reverse()
    
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return self.__list.FindFirstIndex(item, predicate)
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return self.__list.FindLastIndex(item, predicate)
    
    def TryGetValue(self, key: int) -> INullable[T]: return self.__list.TryGetValue(key)
    
    # TrySetAt is bivalent by contract (IWriter), so the trivalence of the shared rule is
    # collapsed here deliberately: a refused index and a refused value are both a failure
    # to set. The protocol route keeps the distinction, since it raises rather than returns.
    def TrySetAt(self, key: int, value: T) -> bool: return TrySetOrderedValue(self.__list, self.__innerSet, key, value) is True
    
    # The unicity clause, asked of the whole span at once. What sits inside the span leaves,
    # so it is out of the test: l[1:3] = (3, 9) is legitimate on (1, 2, 3, 4) because the 3
    # this set holds is at position 2 and goes. That is the rule SetOrderedValues applies in
    # its own validation phase; answered as a boolean here because the caller is the generic
    # primitive, which raises on its own behalf.
    @final
    def CanSetRange(self, indices: range, items: ICountableEnumerable[T]) -> bool:
        if HasDuplicate(items.AsIterable()): return False
        
        leaving: set[T] = {self.__list.GetAt(index) for index in indices}
        
        return not Any(items, lambda item: item in self.__innerSet and item not in leaving)
    
    def Add(self, item: T) -> None: return self.__items.Add(item)
    
    def TryInsert(self, index: int, value: T) -> bool:
        if self.ValidateIndex(index, True) and self.__set.TryAdd(value):
            self.__list.Insert(index, value)

            return True
        
        return False
    
    # None is a refusal, whatever its cause -- the index, or a value the set already holds
    # elsewhere -- and False is an empty range, which is nothing to do rather than a failure.
    # That is the house form, which SizedList already follows for its capacity, and it is what
    # lets InsertRange raise on None alone. Answering False for a refused value put it in the
    # one state the non-Try form is bound to let pass, so a refused range went in silently.
    # The emptiness is counted here rather than read from the set's own answer, which conflates
    # the two cases as D-24 records.
    @final
    def TryInsertRange(self, index: int, items: Iterable[T]) -> bool|None:
        if not self.ValidateIndex(index, True): return None

        # Buffered because both the count and the set's own pass read it.
        items, length = Count(BuildIterable(items))

        if length == 0: return False

        # The set's boolean cannot answer this, so it is asked of the range itself: measured
        # at TryInsertRange(1, (7, 7)) on CreateOrderedSet((1, 2, 3, 4)), which answered True
        # and left the order (1, 7, 7, 2, 3, 4). None, not False, because False is the empty
        # range this very method has just let through.
        if HasDuplicate(items): return None

        if self.__set.TryAddRange(items):
            self.__list.InsertRange(index, items)

            return True
        
        return None
    
    @final
    def _RemoveRange(self, index: int, count: int) -> None: return super(MutableList, self)._RemoveRange(index, count)
    
    def TryRemoveAt(self, index: int) -> bool|None:
        if index < 0: return None
        if index >= self.GetCount(): return False
        
        self.__set.Remove(self.__list.GetAt(index))
        self.__list.RemoveAt(index)
        
        return True
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self.__list.TryGetEnumerator()
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]|None: return self.__list.TryGetResumableEnumerator()
    
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self.__list.GetCollectionMonitors()
    
    def Clear(self) -> None: self.__items.Clear()
    
    def SliceAt(self, key: slice) -> IList[T]: return self.__list.SliceAt(key)
    
    def ToString(self) -> str: return self.__items.ToString()
    
    def AsReversed(self) -> IList[T]: return self.__reversed.GetValue()
    def AsReadOnly(self) -> IEquatableTuple[T]: return self.__items.AsReadOnly().AsTuple()
    def AsFixedSize(self) -> IArray[T]: return self.__fixedSize.GetValue()
    def AsImmutable(self) -> ITuple[T]: return self.__list.AsImmutable()
    
    def insert(self, index: int, value: T) -> None: self.Insert(index, value)
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> MutableSequence[T]: ...
    
    def __getitem__(self, index: SupportsIndex|slice) -> T|MutableSequence[T]: return self.GetAt(int(index)) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsMutableSequence()
    
    @overload
    def __setitem__(self, index: SupportsIndex, value: T) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...
    
    def __setitem__(self, index: SupportsIndex|slice, value: T|Iterable[T]) -> None: SetOrderedItems(self.__list, self.__innerSet, index, value) # type: ignore
    
    def __delitem__(self, index: int|slice) -> None: RemoveItems(self, index)
@final
class _OrderedSetListUpdater[T: HashableProtocol](ValueFunctionUpdater[IList[T]]):
    def __init__(self, items: IOrderedSet[T], l: IList[T], s: ISet[T], innerSet: set[T], updater: Method[IFunction[IList[T]]]) -> None:
        super().__init__(updater)

        self.__items: IOrderedSet[T] = items
        self.__list: IList[T] = l
        self.__set: ISet[T] = s
        self.__innerSet: set[T] = innerSet
    
    def _GetValue(self) -> IList[T]: return _OrderedSetList[T](self.__items, self.__list, self.__set, self.__innerSet)

class _ReadOnlyOrderedSetTupleBase[TItem: HashableProtocol, TCollection](SequenceAbstract[TItem], IEquatableTuple[TItem], INotHashableValue, GenericConstraint[TCollection, ITuple[TItem]]):
    def __init__(self, items: TCollection) -> None:
        super().__init__()
        
        self.__items: TCollection = items
        self.__monitor: IEquatableCollectionViewMonitor[TItem] = EquatableCollectionViewMonitor[TItem](self)
    
    @final
    def _GetContainer(self) -> TCollection: return self.__items
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self._GetInnerContainer().GetSourceMutability()
    
    @final
    def GetCount(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def Contains(self, value: TItem|object) -> bool: return self._GetInnerContainer().Contains(value)
    
    @staticmethod
    def _Equals(items: ITuple[TItem], item: object) -> bool:
        def equals(x: ITuple[TItem], y: ITuple[TItem]) -> bool:
            if x.GetCount() == y.GetCount():
                for item in zip(x.AsIterable(), y.AsIterable()):
                    if not item[0] == item[1]: return False
            
                return True
            
            return False
        def sequenceEquals(x: ITuple[TItem], y: Sequence[TItem]) -> bool: return equals(x, CreateTuple(y))
        
        def iterableEquals(x: ITuple[TItem], y: Iterable[TItem]) -> bool:
            _x: IEnumerator[TItem]|None = x.TryGetEnumerator()

            if _x is None: return False
            
            _y: IEnumerator[TItem] = AsEnumerator(iter(y))
            
            for item in zip(_x.AsIterator(), _y.AsIterator()):
                if not item[0] == item[1]: return False
            
            return not (_x.MoveNext() or _y.MoveNext())

        return item is items or (isinstance(item, ITuple) and equals(items, item)) or (isinstance(item, Sequence) and sequenceEquals(items, item) or (isinstance(item, Iterable) and iterableEquals(items, item))) # pyright: ignore[reportUnknownArgumentType]
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None: return self._GetInnerContainer().TryGetEnumerator()
    @final
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[TItem]|None: return self._GetInnerContainer().TryGetResumableEnumerator()
    
    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetInnerContainer().GetCollectionMonitors()

    @final
    def AsReadOnly(self) -> IEquatableTuple[TItem]: return self
    @final
    def AsImmutable(self) -> IEquatableTuple[TItem]: return self.__monitor.GetImmutableView()
    
    @final
    def ToString(self) -> str: return self._GetInnerContainer().ToString()

@final
class _ReadOnlyOrderedSetReversedTuple[T: HashableProtocol](_ReadOnlyOrderedSetTupleBase[T, IEquatableTuple[T]], IGenericConstraintImplementation[IEquatableTuple[T]]):
    def __init__(self, items: IEquatableTuple[T]) -> None: super().__init__(items)
    
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return self._GetContainer().FindLastIndex(item, predicate)
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return self._GetContainer().FindFirstIndex(item, predicate)
    
    def Equals(self, item: object) -> bool: return item is self or item == self if isinstance(item, IEquatableTuple) else self._Equals(self._GetContainer(), item)
    
    def TryGetValue(self, key: int) -> INullable[T]: return self._GetContainer().TryGetValue(self.ReverseIndex(key))
    
    def SliceAt(self, key: slice) -> IEquatableTuple[T]: return _ReadOnlyOrderedSetTuple(self._GetContainer().SliceAt(self.ReverseKey(key)))
    
    def AsReversed(self) -> IEquatableTuple[T]: return self._GetContainer()
@final
class _ReadOnlyOrderedSetReversedTupleUpdater[T: HashableProtocol](ValueFunctionUpdater[IEquatableTuple[T]]):
    def __init__(self, items: IEquatableTuple[T], updater: Method[IFunction[IEquatableTuple[T]]]) -> None:
        super().__init__(updater)

        self.__items: IEquatableTuple[T] = items
    
    def _GetValue(self) -> IEquatableTuple[T]: return _ReadOnlyOrderedSetReversedTuple[T](self.__items) # The _ReadOnlyOrderedSetReversedTuple type already reverses indices.

@final
class _ReadOnlyOrderedSetTuple[T: HashableProtocol](_ReadOnlyOrderedSetTupleBase[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None:
        def update(func: IFunction[IEquatableTuple[T]]) -> None: self.__reversed = func
        
        super().__init__(items)

        self.__reversed: IFunction[IEquatableTuple[T]] = _ReadOnlyOrderedSetReversedTupleUpdater[T](self, update) # type: ignore[no-redef]
    
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return self._GetContainer().FindFirstIndex(item, predicate)
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return self._GetContainer().FindLastIndex(item, predicate)
    
    def Equals(self, item: object) -> bool: return item is self or self._Equals(self._GetContainer(), item)
    
    def TryGetValue(self, key: int) -> INullable[T]: return self._GetContainer().TryGetValue(key)
    
    def SliceAt(self, key: slice) -> IEquatableTuple[T]: return _ReadOnlyOrderedSetTuple(self._GetContainer().SliceAt(key))
    
    def AsReversed(self) -> IEquatableTuple[T]: return self.__reversed.GetValue()
@final
class _ReadOnlyOrderedSetTupleUpdater[T: HashableProtocol](ValueFunctionUpdater[IEquatableTuple[T]]):
    def __init__(self, items: IOrderedSet[T], updater: Method[IFunction[IEquatableTuple[T]]]) -> None:
        super().__init__(updater)

        self.__items: IOrderedSet[T] = items
    
    def _GetValue(self) -> IEquatableTuple[T]: return _ReadOnlyOrderedSetTuple[T](self.__items.AsList())

@final
class _ReadOnlyOrderedSetList[T: HashableProtocol](CountableEnumerable[T], IReadOnlyOrderedSet[T]):
    def __init__(self, items: IOrderedSet[T]) -> None:
        super().__init__()

        self.__items: IOrderedSet[T] = items
    
    def GetCount(self) -> int: return self.__items.GetCount()
    
    def Contains(self, value: T|object) -> bool: return self.__items.Contains(value)
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self.__items.TryGetEnumerator()
    
    def ToString(self) -> str: return self.__items.ToString()

    @final
    def AsTuple(self) -> IEquatableTuple[T]: return self.__items.AsTuple()
    
    def AsContainer(self) -> Container[T]: return self.__items.AsContainer()
@final
class _ReadOnlyOrderedSetListUpdater[T: HashableProtocol](ValueFunctionUpdater[IReadOnlyOrderedSet[T]]):
    def __init__(self, items: IOrderedSet[T], updater: Method[IFunction[IReadOnlyOrderedSet[T]]]) -> None:
        super().__init__(updater)

        self.__items: IOrderedSet[T] = items
    
    def _GetValue(self) -> IReadOnlyOrderedSet[T]: return _ReadOnlyOrderedSetList[T](self.__items)

class OrderedSet[T: HashableProtocol](CountableEnumerable[T], IOrderedSet[T]):
    def __init__(self, items: IEnumerable[T]|None = None) -> None:
        def updateReadOnly(func: IFunction[IReadOnlyOrderedSet[T]]) -> None: self.__readOnly = func
        
        def updateList(func: IFunction[IList[T]]) -> None: self.__list = func
        def updateTuple(func: IFunction[IEquatableTuple[T]]) -> None: self.__tuple = func
        
        super().__init__()

        innerSet: set[T] = set[T]()

        l: IList[T] = List[T]()
        s: ISet[T] = Set[T](innerSet)
        
        self.__set: ISet[T] = s
        self.__items: IList[T] = l

        self.__readOnly: IFunction[IReadOnlyOrderedSet[T]] = _ReadOnlyOrderedSetListUpdater[T](self, updateReadOnly) # type: ignore[no-redef]
        self.__list: IFunction[IList[T]] = _OrderedSetListUpdater[T](self, l, s, innerSet, updateList) # type: ignore[no-redef]
        self.__tuple: IFunction[IEquatableTuple[T]] = _ReadOnlyOrderedSetTupleUpdater[T](self, updateTuple) # type: ignore[no-redef]

        if items is not None:
            for item in items.AsIterable(): self.Add(item)
    
    @final
    def GetCount(self) -> int: return self.__items.GetCount()
    
    @final
    def Contains(self, value: T|object) -> bool: return self.__set.Contains(value)
    
    @final
    def TryAdd(self, item: T) -> bool:
        if self.__set.TryAdd(item):
            self.__items.Add(item)

            return True
        
        return False
    @final
    def Add(self, item: T) -> None:
        self.__set.Add(item)
        self.__items.Add(item)
    
    @final
    def TryAddRange(self, items: Iterable[T]) -> bool:
        # The same question the list view asks, on the type's own API: measured at
        # TryAddRange((7, 7)) on CreateOrderedSet((1, 2, 3, 4)), which answered True and left
        # the order (1, 2, 3, 4, 7, 7) against a count of 6. False, not None, because
        # ISetBase.TryAddRange is bivalent by contract and AddRange raises on the False
        # alone; this family therefore cannot tell a refused range from an empty one, which
        # is D-24's open complaint against it and not something to settle here.
        # Buffered because this method reads the range three times -- the duplicate pass, the
        # set's own pass, and the add -- so a one-pass iterable reached the first and nothing
        # else: TryAddRange(iter([7, 8])) left the order without them. The list view buffers
        # for the same reason, two readers down.
        if HasDuplicate(items := BuildIterable(items)): return False

        if self.__set.TryAddRange(items):
            self.__items.AddRange(items)

            return True
        
        return False
    
    @final
    def TryRemove(self, item: T) -> bool: return self.__items.TryRemove(item) and self.__set.TryRemove(item)
    @final
    def Remove(self, item: T) -> None:
        self.__set.Remove(item)
        self.__items.Remove(item)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self.__items.TryGetEnumerator()
    
    @final
    def Clear(self) -> None:
        self.__set.Clear()
        self.__items.Clear()
    
    @final
    def ToString(self) -> str: return self.__items.ToString()
    
    @final
    def AsReadOnly(self) -> IReadOnlyOrderedSet[T]: return self.__readOnly.GetValue()
    
    @final
    def AsContainer(self) -> Container[T]: return self.AsReadOnly().AsContainer()
    @final
    def AsTuple(self) -> IEquatableTuple[T]: return self.__tuple.GetValue()
    @final
    def AsList(self) -> IList[T]: return self.__list.GetValue()

class _ReadOnlyKeyedSet[TKey: HashableProtocol, TValue](CountableEnumerable[ITuple[TValue]], IReadOnlyKeyedSet[TKey, TValue]):
    def __init__(self, items: IReadOnlyKeyedSet[TKey, TValue]) -> None:
        super().__init__()

        self.__set: IReadOnlyKeyedSet[TKey, TValue] = items
    
    @final
    def _GetItems(self) -> IReadOnlyKeyedSet[TKey, TValue]:
        return self.__set
    
    @final
    def GetKeys(self) -> IReadOnlyOrderedSet[TKey]: return self._GetItems().GetKeys()
    
    @final
    def IsEmpty(self) -> bool: return self._GetItems().IsEmpty()
    
    @final
    def GetCount(self) -> int: return self._GetItems().GetCount()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[ITuple[TValue]]|None: return TryCreateEnumerator(self._GetItems().TryGetEnumerator())
@final
class _ReadOnlyKeyedSetUpdater[TKey: HashableProtocol, TValue](ValueFunctionUpdater[IReadOnlyKeyedSet[TKey, TValue]]):
    def __init__(self, items: KeyedSet[TKey, TValue], updater: Method[IFunction[IReadOnlyKeyedSet[TKey, TValue]]]) -> None:
        super().__init__(updater)

        self.__items: KeyedSet[TKey, TValue] = items
    
    def _GetValue(self) -> IReadOnlyKeyedSet[TKey, TValue]: return _ReadOnlyKeyedSet[TKey, TValue](self.__items)
class KeyedSet[TKey: HashableProtocol, TValue](CountableEnumerable[ITuple[TValue]], IKeyedSet[TKey, TValue]):
    def __init__(self, keys: Iterable[TKey], values: Iterable[ITuple[TValue]]|None = None) -> None:
        def update(func: IFunction[IReadOnlyKeyedSet[TKey, TValue]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__keys: IReadOnlyOrderedSet[TKey] = CreateOrderedSet(keys).AsReadOnly()
        self.__values: ICountableEnumerableQueue[ITuple[TValue]] = CreateCountableEnumerableQueue(values)

        self.__readOnly: IFunction[IReadOnlyKeyedSet[TKey, TValue]] = _ReadOnlyKeyedSetUpdater[TKey, TValue](self, update) # type: ignore[no-redef]
    
    @final
    def _GetValues(self) -> ICountableEnumerableQueue[ITuple[TValue]]:
        return self.__values
    
    @final
    def IsEmpty(self) -> bool: return self.GetCount() < 1
    
    @final
    def GetKeys(self) -> IReadOnlyOrderedSet[TKey]: return self.__keys
    
    @final
    def GetCount(self) -> int: return self._GetValues().GetCount()
    
    @final
    def TryAdd(self, values: ITuple[TValue]) -> bool:
        if values.GetCount() == self.GetKeys().GetCount():
            self._GetValues().Push(values)

            return True
        
        return False
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[ITuple[TValue]]|None: return self._GetValues().TryGetEnumerator()
    
    @final
    def Clear(self) -> None: return self._GetValues().Clear()

    @final
    def AsReadOnly(self) -> IReadOnlyKeyedSet[TKey, TValue]: return self.__readOnly.GetValue()

def CreateOrderedSet[T: HashableProtocol](items: Iterable[T]) -> IOrderedSet[T]:
    return OrderedSet[T](AsEnumerable(items))
def MakeOrderedSet[T: HashableProtocol](*items: T) -> IOrderedSet[T]:
    return CreateOrderedSet(items)

def CreateKeyedSet[TKey: HashableProtocol, TValue](keys: Iterable[TKey], values: Iterable[ITuple[TValue]]|None = None) -> IKeyedSet[TKey, TValue]:
    return KeyedSet[TKey, TValue](keys, values)
def MakeKeyedSet[TKey: HashableProtocol, TValue](keys: Iterable[TKey], *values: ITuple[TValue]) -> IKeyedSet[TKey, TValue]:
    return CreateKeyedSet(keys, values)

def MakeKeyedSetFromKeys[TKey: HashableProtocol, TValue](values: Iterable[ITuple[TValue]], *keys: TKey) -> IKeyedSet[TKey, TValue]:
    return CreateKeyedSet(keys, values)