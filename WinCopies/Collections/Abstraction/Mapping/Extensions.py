from __future__ import annotations

from collections.abc import Container, Iterable, Sequence, MutableSequence
from typing import overload, final, SupportsIndex

from WinCopies import Abstract
from WinCopies.Collections.Abstraction.Collection import List, CreateTuple
from WinCopies.Collections.Abstraction.Enumeration import TryCreateEnumerator
from WinCopies.Collections.Abstraction.Mapping import Set
from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, CountableEnumerable, CreateIterable, AsEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Extensions import Collection, IResumableEnumeratorMonitor, IReadOnlyOrderedSet, ITuple, IEquatableTuple, IArray, IList, IReadOnlyKeyedSet, ISet, IOrderedSet, IKeyedSet, SequenceAbstract, MutableSequence
from WinCopies.Collections.Extensions.Collection import MutableList
from WinCopies.Collections.Linked.Singly import ICountableEnumerableQueue, CreateCountableEnumerableQueue
from WinCopies.Collections.Range import RemoveItems
from WinCopies.Collections.Range.Extensions import SetOrderedItems
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

        self.__fixedSize: IFunction[IArray[T]] = self._GetReversedUpdater(l.GetEnumeratorMonitor(), updateFixedSize) # type: ignore[no-redef]
        self.__reversed: IFunction[IList[T]] = self._GetUpdater(l.GetEnumeratorMonitor(), updateReversed) # type: ignore[no-redef]
    
    def __TryAdd(self, index: int, value: T) -> bool:
        return self.ValidateIndex(index) and self.__set.TryAdd(value)
    
    def GetMutability(self) -> Mutability: return Mutability.Mutable
    def TryGetSourceMutability(self) -> None: return None
    
    def GetCount(self) -> int: return self.__items.GetCount()
    
    def Contains(self, value: T|object) -> bool: return self.__set.Contains(value)
    
    def Move(self, x: int, y: int) -> None: self.__list.Move(x, y)
    
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return self.__list.FindFirstIndex(item, predicate)
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return self.__list.FindLastIndex(item, predicate)
    
    def TryGetValue(self, key: int) -> INullable[T]: return self.__list.TryGetValue(key)
    
    def TrySetAt(self, key: int, value: T) -> bool:
        if self.__TryAdd(key, value):
            self.__set.Remove(value)
            self.__list.SetAt(key, value)

            return True
        
        return False
    
    def Add(self, item: T) -> None: return self.__items.Add(item)
    
    def TryInsert(self, index: int, value: T) -> bool:
        if self.__TryAdd(index, value):
            self.__list.Insert(index, value)

            return True
        
        return False
    
    @final
    def TryInsertRange(self, index: int, items: Iterable[T]) -> bool:
        if self.ValidateIndex(index):
            if self.__set.TryAddRange(items):
                self.__list.InsertRange(index, items)

                return True
        
        return False
    
    @final
    def TryRemoveRange(self, index: int, count: int) -> bool:
        if self.ValidateIndex(index):
            for i in range(count): self.RemoveAt(index + i)

            return True
        
        return False
    
    def TryRemoveAt(self, index: int) -> bool|None:
        if index < 0: return None
        if index >= self.GetCount(): return False
        
        self.__set.Remove(self.__list.GetAt(index))
        self.__list.RemoveAt(index)
        
        return True
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self.__list.TryGetEnumerator()
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]|None: return self.__list.TryGetResumableEnumerator()
    
    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor[T]: return self.__list.GetEnumeratorMonitor()
    
    def Clear(self) -> None: self.__items.Clear()
    
    def SliceAt(self, key: slice) -> IList[T]: return self.__list.SliceAt(key)
    
    def ToString(self) -> str: return self.__items.ToString()
    
    def AsReadOnly(self) -> IEquatableTuple[T]: return self.__items.AsReadOnly().AsTuple()
    def AsReversed(self) -> IList[T]: return self.__reversed.GetValue()
    def AsFixedSize(self) -> IArray[T]: return self.__fixedSize.GetValue()
    
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
    
    @final
    def _GetContainer(self) -> TCollection: return self.__items
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self._GetInnerContainer().TryGetSourceMutability()
    
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
    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor[TItem]: return self._GetInnerContainer().GetEnumeratorMonitor()
    
    @final
    def ToString(self) -> str: return self.ToString()

@final
class _ReadOnlyOrderedSetReversedTuple[T: HashableProtocol](_ReadOnlyOrderedSetTupleBase[T, IEquatableTuple[T]], IGenericConstraintImplementation[IEquatableTuple[T]]):
    def __init__(self, items: IEquatableTuple[T]) -> None: super().__init__(items)
    
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return self._GetContainer().FindLastIndex(item, predicate)
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return self._GetContainer().FindFirstIndex(item, predicate)
    
    def Equals(self, item: object) -> bool: return item is self or item.Equals(self) if isinstance(item, IEquatableTuple) else self._Equals(self._GetContainer(), item)
    
    def TryGetValue(self, key: int) -> INullable[T]: return self._GetContainer().TryGetValue(self.ReverseIndex(key))
    
    def SliceAt(self, key: slice) -> IEquatableTuple[T]: return _ReadOnlyOrderedSetTuple(self._GetContainer().SliceAt(self.ReverseKey(key)))
    
    def AsReversed(self) -> IEquatableTuple[T]: return self._GetContainer()
@final
class _ReadOnlyOrderedSetReversedTupleUpdater[T: HashableProtocol](ValueFunctionUpdater[IEquatableTuple[T]]):
    def __init__(self, items: IEquatableTuple[T], updater: Method[IFunction[IEquatableTuple[T]]]) -> None:
        super().__init__(updater)

        self.__items: IEquatableTuple[T] = items
    
    def _GetValue(self) -> IEquatableTuple[T]: return _ReadOnlyOrderedSetReversedTuple[T](self.__items.AsReversed())

@final
class _ReadOnlyOrderedSetTuple[T: HashableProtocol](_ReadOnlyOrderedSetTupleBase[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None:
        def update(func: IFunction[IEquatableTuple[T]]) -> None:
            self.__reversed = func
        
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
    
    def _GetValue(self) -> IEquatableTuple[T]: return _ReadOnlyOrderedSetTuple[T](self.__items.AsList().AsReadOnly())

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
    
    def _GetValue(self) -> IReadOnlyKeyedSet[TKey, TValue]:
        return _ReadOnlyKeyedSet[TKey, TValue](self.__items)
class KeyedSet[TKey: HashableProtocol, TValue](CountableEnumerable[ITuple[TValue]], IKeyedSet[TKey, TValue]):
    def __init__(self, keys: Iterable[TKey], values: Iterable[ITuple[TValue]]|None = None) -> None:
        def update(func: IFunction[IReadOnlyKeyedSet[TKey, TValue]]) -> None:
            self.__readOnly = func
        
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
    return OrderedSet[T](CreateIterable(items))
def MakeOrderedSet[T: HashableProtocol](*items: T) -> IOrderedSet[T]:
    return CreateOrderedSet(items)

def CreateKeyedSet[TKey: HashableProtocol, TValue](keys: Iterable[TKey], values: Iterable[ITuple[TValue]]|None = None) -> IKeyedSet[TKey, TValue]:
    return KeyedSet[TKey, TValue](keys, values)
def MakeKeyedSet[TKey: HashableProtocol, TValue](keys: Iterable[TKey], *values: ITuple[TValue]) -> IKeyedSet[TKey, TValue]:
    return CreateKeyedSet(keys, values)

def MakeKeyedSetFromKeys[TKey: HashableProtocol, TValue](values: Iterable[ITuple[TValue]], *keys: TKey) -> IKeyedSet[TKey, TValue]:
    return CreateKeyedSet(keys, values)