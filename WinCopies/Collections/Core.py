from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sized, Iterable, Container, Collection
from typing import overload, final, Any, Callable

from WinCopies import IInterface, Abstract
from WinCopies.Collections import EmptyException
from WinCopies.Collections.Util import GetKeyError, ThrowKeyError, ThrowKeyValueError, ReverseIndex, ReverseIndexFromLast, GetOffset, GetIndex, ValidateIndex, ReverseRangeStartIndex, TryGetRangeLength
from WinCopies.Typing import INullable
from WinCopies.Typing.Comparison import IEquatableValue, IHashableValue, EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import Converter, EqualityComparison, IndexedValueComparison
from WinCopies.Typing.Enum import IntEnum
from WinCopies.Typing.Pairing import KeyValuePair, DualValueBool, CreateDualValueBool
from WinCopies.Typing.Protocols import SupportsEqualityAndRichComparison

class Mutability(IntEnum):
    ReadOnly = 0
    FixedSize = 1
    Mutable = 2

class IReadOnlyCollection(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def IsEmpty(self) -> bool:
        ...
    
    def HasItems(self) -> bool: return not self.IsEmpty()
    
    def ThrowIfEmpty(self) -> None:
        if self.IsEmpty(): raise EmptyException()

class IContainer[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Contains(self, value: T|object) -> bool:
        ...

class IReadOnlyList[T](IContainer[T], IReadOnlyCollection):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsContainer(self) -> Container[T]:
        ...

class ReadOnlyList[T](Container[T], IReadOnlyList[T]):
    def __init__(self) -> None: super().__init__()
    
    def AsContainer(self) -> Container[T]: return self
    
    @final
    def __contains__(self, x: object) -> bool: return self.Contains(x)

class ICollection[T](IReadOnlyList[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def _NormalizeItems(self, items: Iterable[T]|None) -> Iterable[T]|None:
        def normalize(items: Iterable[T]) -> Iterable[T]|None:
            def iterate(items: Iterable[T]) -> tuple[T, Iterable[T]]|None:
                for item in (items := items.__iter__()): return (item, items)

                return None
            def enumerate(first: T, other: Iterable[T]) -> Iterable[T]:
                yield first

                yield from other

            result: tuple[T, Iterable[T]]|None = iterate(items)
            
            return None if result is None else enumerate(*result)
        
        match items:
            case None: return None

            case Collection(): return None if len(items) < 1 else items

            case _: return normalize(items)
    
    @abstractmethod
    def Add(self, item: T) -> None:
        ...
    def TryAdd(self, item: T) -> bool:
        self.Add(item)

        return True

    @abstractmethod
    def AddRange(self, items: Iterable[T]|None) -> None:
        ...
    
    def _TryAddRange(self, items: Iterable[T]) -> bool:
        self.AddRange(items)

        return True
    @final
    def TryAddRange(self, items: Iterable[T]|None) -> bool|None:
        return None if (items := self._NormalizeItems(items)) is None else self._TryAddRange(items)

    @abstractmethod
    def TryRemoveAt(self, index: int) -> bool|None:
        ...
    @final
    def RemoveAt(self, index: int) -> None:
        if self.TryRemoveAt(index) is not True: raise IndexError(index)

    @abstractmethod
    def TryRemove(self, item: T, predicate: EqualityComparison[T]|None = None) -> bool:
        ...
    @final
    def Remove(self, item: T, predicate: EqualityComparison[T]|None = None) -> None:
        if not self.TryRemove(item, predicate): raise ValueError(item)
    
    @abstractmethod
    def TryRemoveRange(self, index: int, count: int|None) -> bool:
        ...
    @final
    def RemoveRange(self, index: int, count: int|None) -> None:
        if not self.TryRemoveRange(index, count): raise IndexError(index)

class ICountable(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetCount(self) -> int:
        ...

    @final
    def GetLastIndex(self) -> int:
        return self.GetCount() - 1
    
    @final
    def ValidateIndex(self, index: int, permissive: bool = False) -> bool:
        return ValidateIndex(index, self.GetCount(), permissive)
    
    @abstractmethod
    def AsSized(self) -> Sized:
        ...

class Countable(Sized, ICountable):
    def __init__(self) -> None: super().__init__()
    
    def AsSized(self) -> Sized: return self
    
    @final
    def __len__(self) -> int: return self.GetCount()

class IReadOnlyCountableList[T](IReadOnlyList[T], ICountable):
    def __init__(self) -> None: super().__init__()

class ICountableCollection[T](IReadOnlyCountableList[T], ICollection[T]):
    def __init__(self) -> None: super().__init__()

class IClearable(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Clear(self) -> None:
        ...

class ICountableList[T](ICountableCollection[T], IClearable):
    def __init__(self) -> None: super().__init__()

class IKeyableBase[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def ContainsKey(self, key: T) -> bool:
        ...

class IGetter[TKey, TValue](IKeyableBase[TKey]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryGetValue(self, key: TKey) -> INullable[TValue]:
        ...
    
    @final
    def TryGetAt[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValue|TDefault]:
        def getResult(value: TValue|TDefault, info: bool) -> DualValueBool[TValue|TDefault]: return CreateDualValueBool(value, info)
        
        result: INullable[TValue] = self.TryGetValue(key)

        return getResult(result.GetValue(), True) if result.HasValue() else getResult(defaultValue, False)
    @final
    def GetAt(self, key: TKey) -> TValue:
        result: INullable[TValue] = self.TryGetValue(key)
        
        if result.HasValue(): return result.GetValue()
        
        raise KeyError(f"The key {key} does not exist.")
class ISetter[TKey, TValue](IKeyableBase[TKey]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TrySetAt(self, key: TKey, value: TValue) -> bool:
        ...
    @final
    def SetAt(self, key: TKey, value: TValue) -> None:
        if not self.TrySetAt(key, value): raise KeyError(f"Key {key} does not exist.")

class IReadOnlyIndexable[T](IGetter[int, T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IReadOnlyIndexable[T]:
        ...
class IWriteOnlyIndexable[T](ISetter[int, T]):
    def __init__(self) -> None: super().__init__()

class IReadWriteCollection[TKey, TValue](IGetter[TKey, TValue], ISetter[TKey, TValue]):
    def __init__(self) -> None: super().__init__()

    @final
    def __ChangePosition(self, x: TKey, y: TKey, updater: Callable[[TKey, TKey], bool|None]) -> None:
        if updater(x, y) is None: raise IndexError(f"Position {x} or {y} does not exist.")

    @abstractmethod
    def TryMove(self, x: TKey, y: TKey) -> bool|None:
        ...
    @final
    def Move(self, x: TKey, y: TKey) -> None:
        self.__ChangePosition(x, y, self.TryMove)
    
    @abstractmethod
    def TrySwap(self, x: TKey, y: TKey) -> bool|None:
        ...
    @final
    def Swap(self, x: TKey, y: TKey) -> None:
        self.__ChangePosition(x, y, self.TrySwap)

class ICountableIndexableBase(IKeyableBase[int], ICountable):
    def __init__(self) -> None: super().__init__()
    
    @final
    def ContainsKey(self, key: int) -> bool: return self.ValidateIndex(key)

class IIndexableCollectionBase(ICountable):
    def __init__(self) -> None: super().__init__()
    
    @final
    def ReverseIndexFromLast(self, index: int) -> int:
        return ReverseIndexFromLast(index, self.GetLastIndex())
    @final
    def ReverseIndex(self, index: int) -> int:
        return ReverseIndex(index, self.GetCount())
    
    @final
    def GetOffset(self, inStart: int, outStart: int) -> int:
        return GetOffset(inStart, outStart, self.GetCount())
    @final
    def GetIndex(self, start: int, offset: int) -> tuple[int, int]:
        return GetIndex(start, self.GetCount(), offset)
    
    @final
    def ReverseKey(self, key: slice) -> slice:
        indices: range = range(*key.indices(self.GetCount()))
        
        # An empty span designates no element, so there is no direction to mirror -- but it
        # does designate a position, and that position is the one this used to discard: every
        # empty span came back as slice(0, 0), which is the mirror of exactly one of them. A
        # caller writing through the answer therefore placed its items at the wrong end,
        # measured at six of seven empty keys on a four-element view.
        #
        # The position is the count less the resolved start, not the last index less it: what
        # is mirrored here is an insertion point and not an element, and the two differ by one.
        #
        # The step comes back as given rather than negated, unlike the branch below, and that
        # is not a matter of consistency: CPython reads a step of 1 as resizable and anything
        # else as an extended slice, by the step itself and not by its magnitude. Negating
        # would turn an empty resizable span into an extended one, which refuses the very
        # insertion this answer exists to place -- measured, l[1:1] = (7, 8) inserts where
        # l[1:1:-1] = (7, 8) raises. Away from a magnitude of 1 the sign is unobservable on
        # all three operations, measured, so one rule serves both without a special case.
        if len(indices) == 0:
            position: int = self.GetCount() - indices.start
            
            return slice(position, position, indices.step)
        
        step: int = -indices.step
        stop: int = self.ReverseIndex(indices[-1]) + step
        
        return slice(self.ReverseIndex(indices[0]), None if stop < 0 else stop, step)
    
    @final
    def ReverseRangeStartIndex(self, index: int, count: int) -> int:
        return ReverseRangeStartIndex(index, count, self.GetCount())
class IIndexableCollection(IIndexableCollectionBase, ICountableIndexableBase):
    def __init__(self) -> None: super().__init__()

class IReadOnlyCountableIndexable[T](IReadOnlyIndexable[T], IIndexableCollection):
    def __init__(self) -> None: super().__init__()
    
    @final
    def TryGetFirst[TDefault](self, defaultValue: TDefault) -> DualValueBool[T|TDefault]:
        return self.TryGetAt(0, defaultValue)
    @final
    def TryGetFirstItem(self) -> INullable[T]:
        return self.TryGetValue(0)

    @final
    def GetFirstItem(self) -> T:
        return self.GetAt(0)
    
    @final
    def TryGetLast[TDefault](self, defaultValue: TDefault) -> DualValueBool[T|TDefault]:
        return self.TryGetAt(self.GetLastIndex(), defaultValue)
    @final
    def TryGetLastItem(self) -> INullable[T]:
        return self.TryGetValue(self.GetLastIndex())

    @final
    def GetLastItem(self) -> T:
        return self.GetAt(self.GetLastIndex())
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IReadOnlyCountableIndexable[T]:
        ...
class IWriteOnlyCountableIndexable[T](IWriteOnlyIndexable[T], IIndexableCollection):
    def __init__(self) -> None: super().__init__()

class IIndexable[T](IReadOnlyIndexable[T], IWriteOnlyIndexable[T], IReadWriteCollection[int, T]):
    def __init__(self) -> None: super().__init__()
class ICountableIndexable[T](IIndexable[T], IReadOnlyCountableIndexable[T], IWriteOnlyCountableIndexable[T]):
    def __init__(self) -> None: super().__init__()

class IReadOnlyCountableIndexableList[T](IReadOnlyCountableIndexable[T], IReadOnlyCountableList[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int:
        ...
    @abstractmethod
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int:
        ...

class ITuple[T](IReadOnlyCountableIndexableList[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def IsEmpty(self) -> bool: return self.GetCount() < 1
    
    @abstractmethod
    def GetMutability(self) -> Mutability:
        ...

    @abstractmethod
    def TryGetSourceMutability(self) -> Mutability|None:
        ...
    @final
    def GetSourceMutability(self) -> Mutability:
        result: Mutability|None = self.TryGetSourceMutability()

        return self.GetMutability() if result is None else result
    
    @final
    def IsImmutable(self) -> bool:
        return self.GetSourceMutability() == Mutability.ReadOnly
    
    @abstractmethod
    def AsReversed(self) -> ITuple[T]:
        ...

    @abstractmethod
    def AsImmutable(self) -> ITuple[T]:
        ...
    @abstractmethod
    def AsReadOnly(self) -> ITuple[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ITuple[T]:
        ...
class IEquatableTuple[T: EquatableProtocol](ITuple[T], IEquatableValue):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsReversed(self) -> IEquatableTuple[T]:
        ...
    
    @abstractmethod
    def AsImmutable(self) -> IEquatableTuple[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        ...
class IHashableTuple[T: HashableProtocol](IEquatableTuple[T], IHashableValue):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    
    @abstractmethod
    def AsReversed(self) -> IHashableTuple[T]:
        ...
    
    @abstractmethod
    def AsImmutable(self) -> IHashableTuple[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IHashableTuple[T]:
        ...

def _ChangePosition[T](x: T, y: T, validator: Callable[[T, T], bool], updater: Callable[[T, T], None]) -> bool|None:
    if validator(x, y):
        if x == y: return False

        updater(x, y)

        return True

    return None

class _ISwappable[TKey, TValue](IReadWriteCollection[TKey, TValue]):
    def __init__(self) -> None: super().__init__()

    @final
    def _SwapDefault(self, x: TKey, y: TKey) -> None:
        value: TValue = self.GetAt(x)
        
        self.SetAt(x, self.GetAt(y))
        self.SetAt(y, value)
    
    @abstractmethod
    def _Swap(self, x: TKey, y: TKey) -> None:
        ...
class ISwappable[TKey, TValue](_ISwappable[TKey, TValue]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Swap(self, x: TKey, y: TKey) -> None:
        self._SwapDefault(x, y)

class IArray[T](ITuple[T], ICountableIndexable[T], _ISwappable[int, T]):
    def __init__(self) -> None: super().__init__()

    @final
    def __ChangePosition(self, x: int, y: int, updater: Callable[[int, int], None]) -> bool|None: return _ChangePosition(x, y, self.ValidateIndices, updater)

    def ValidateIndices(self, x: int, y: int) -> bool:
        return self.ValidateIndex(x) and self.ValidateIndex(y)

    @abstractmethod
    def _Move(self, x: int, y: int) -> None:
        ...
    @final
    def TryMove(self, x: int, y: int) -> bool|None: return self.__ChangePosition(x, y, self._Move)

    @final
    def TrySwap(self, x: int, y: int) -> bool|None: return self.__ChangePosition(x, y, self._Swap)

    @abstractmethod
    def AsReversed(self) -> IArray[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IArray[T]:
        ...

class IListBase[T](ITuple[T], ICountableList[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> IListBase[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IListBase[T]:
        ...
    
    @final
    def TryRemove(self, item: T, predicate: EqualityComparison[T]|None = None) -> bool:
        return self.TryRemoveAt(self.FindFirstIndex(item, predicate)) is True

    def _RemoveRange(self, index: int, count: int) -> None:
        for _ in range(count): self.RemoveAt(index)
    @final
    def TryRemoveRange(self, index: int, count: int|None) -> bool:
        if (count := TryGetRangeLength(index, self.GetCount(), count)) is None: return False

        self._RemoveRange(index, count)
        
        return True

class IList[T](IArray[T], IListBase[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def __Insert(self, index: int, value: T, adder: IndexedValueComparison[T]) -> bool:
        return self.ValidateIndex(index, True) and adder(index, value)
    @final
    def __InsertRange(self, index: int, items: Iterable[T]|None, adder: IndexedValueComparison[Iterable[T]]) -> bool|None:
        return (False if (items := self._NormalizeItems(items)) is None else (True if adder(index, items) else None)) if self.ValidateIndex(index, True) else None
    
    @abstractmethod
    def AsFixedSize(self) -> IArray[T]:
        ...

    @abstractmethod
    def AsReversed(self) -> IList[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IList[T]:
        ...
    
    @abstractmethod
    def _Insert(self, index: int, value: T) -> None:
        ...
    @final
    def Insert(self, index: int, value: T) -> None:
        def insert(index: int, value: T) -> bool:
            self._Insert(index, value)

            return True
        
        if not self.__Insert(index, value, insert): raise IndexError(index)

    def _TryInsert(self, index: int, value: T) -> bool:
        self._Insert(index, value)

        return True
    @final
    def TryInsert(self, index: int, value: T) -> bool:
        return self.__Insert(index, value, self._TryInsert)

    @abstractmethod
    def _InsertRange(self, index: int, items: Iterable[T]) -> None:
        ...
    @final
    def InsertRange(self, index: int, items: Iterable[T]|None) -> None:
        def insert(index: int, value: Iterable[T]) -> bool:
            self._InsertRange(index, value)

            return True
        
        if self.__InsertRange(index, items, insert) is None: raise IndexError(index)

    def _TryInsertRange(self, index: int, items: Iterable[T]) -> bool:
        self._InsertRange(index, items)

        return True
    @final
    def TryInsertRange(self, index: int, items: Iterable[T]|None) -> bool|None:
        return self.__InsertRange(index, items, self._TryInsertRange)

    @final
    def TryAdd(self, item: T) -> bool:
        return self.TryInsert(self.GetCount(), item)
    @final
    def Add(self, item: T) -> None:
        return self.Insert(self.GetCount(), item)

    @final
    def _TryAddRange(self, items: Iterable[T]) -> bool: return self.TryInsertRange(self.GetCount(), items) is True
    @final
    def AddRange(self, items: Iterable[T]|None) -> None: self.InsertRange(self.GetCount(), items)

    @final
    def TryInsertValues(self, index: int, *values: T) -> bool|None: return self.TryInsertRange(index, values)
    @final
    def InsertValues(self, index: int, *values: T) -> None:
        if self.TryInsertValues(index, *values) is None: raise IndexError(index)

class ISortedTuple[T: SupportsEqualityAndRichComparison](ITuple[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryBisect(self, item: T, right: bool = False) -> DualValueBool[int]:
        ...
    @abstractmethod
    def TryBisectWithKey[_T: SupportsEqualityAndRichComparison](self, item: _T, converter: Converter[T, _T], right: bool = False) -> DualValueBool[int]:
        ...
    
    @final
    def Bisect(self, item: T, right: bool = False) -> int:
        return self.TryBisect(item, right).GetKey()
    @final
    def BisectWithKey[_T: SupportsEqualityAndRichComparison](self, item: _T, converter: Converter[T, _T], right: bool = False) -> int:
        return self.TryBisectWithKey(item, converter, right).GetKey()
    
    @overload
    def ContainsValue(self, value: T, converter: None = None) -> bool:
        ...
    @overload
    def ContainsValue[_T: SupportsEqualityAndRichComparison](self, value: _T, converter: Converter[T, _T]) -> bool:
        ...
    
    @final
    def ContainsValue[_T: SupportsEqualityAndRichComparison](self, value: T|_T, converter: Converter[T, _T]|None = None) -> bool:
        def contains(value: Any) -> bool: return (self.TryBisect(value) if converter is None else self.TryBisectWithKey(value, converter)).GetValue()

        return contains(value)
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ISortedTuple[T]:
        ...
    
    @abstractmethod
    def AsReversed(self) -> ISortedTuple[T]:
        ...
class ISortedList[T: SupportsEqualityAndRichComparison](IListBase[T], ISortedTuple[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AddLeft(self, item: T) -> None:
        ...

    @abstractmethod
    def AsReversed(self) -> ISortedList[T]:
        ...

    @abstractmethod
    def AsReadOnly(self) -> ISortedTuple[T]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ISortedList[T]:
        ...

class IReadOnlySet[T: HashableProtocol](IReadOnlyList[T], ICountable):
    def __init__(self) -> None: super().__init__()
    
    @final
    def IsEmpty(self) -> bool: return self.GetCount() < 1
class ISet[T: HashableProtocol](IReadOnlySet[T], IClearable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlySet[T]:
        ...
    
    @abstractmethod
    def TryAdd(self, item: T) -> bool:
        ...
    @final
    def Add(self, item: T) -> None:
        if not self.TryAdd(item): ThrowKeyError(item)

    @abstractmethod
    def TryAddRange(self, items: Iterable[T]) -> bool|None:
        ...
    @final
    def AddRange(self, items: Iterable[T]) -> None:
        result: bool|None = self.TryAddRange(items)

        if result is None: raise KeyError()

    @final
    def TryAddValues(self, *values: T) -> bool:
        return True if self.TryAddRange(values) is True else False
    @final
    def AddValues(self, *values: T) -> None:
        self.AddRange(values)
    
    @abstractmethod
    def TryRemove(self, item: T) -> bool:
        ...
    @final
    def Remove(self, item: T) -> None:
        if not self.TryRemove(item): ThrowKeyError(True)

class IReadOnlyDictionary[TKey: HashableProtocol, TValue](IGetter[TKey, TValue], IReadOnlyCollection, ICountable):
    def __init__(self) -> None: super().__init__()
class IDictionary[TKey: HashableProtocol, TValue](IReadOnlyDictionary[TKey, TValue], _ISwappable[TKey, TValue], IClearable):
    def __init__(self) -> None: super().__init__()

    @final
    def __ChangePosition(self, x: TKey, y: TKey, updater: Callable[[TKey, TKey], None]) -> bool|None: return _ChangePosition(x, y, self.ValidateKeys, updater)

    def ValidateKeys(self, x: TKey, y: TKey) -> bool:
        return self.ContainsKey(x) and self.ContainsKey(y)

    @abstractmethod
    def _Move(self, x: TKey, y: TKey) -> None:
        ...
    @final
    def TryMove(self, x: TKey, y: TKey) -> bool|None: return self.__ChangePosition(x, y, self._Move)

    @final
    def TrySwap(self, x: TKey, y: TKey) -> bool|None: return self.__ChangePosition(x, y, self._Swap)
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyDictionary[TKey, TValue]:
        ...
    
    @abstractmethod
    def TryAdd(self, key: TKey, value: TValue) -> bool:
        ...
    @final
    def Add(self, key: TKey, value: TValue) -> None:
        if not self.TryAdd(key, value): ThrowKeyValueError(key, value)

    @final
    def TryAddItem(self, item: KeyValuePair[TKey, TValue]) -> bool:
        return self.TryAdd(item.GetKey(), item.GetValue())
    @final
    def AddItem(self, item: KeyValuePair[TKey, TValue]) -> None:
        self.Add(item.GetKey(), item.GetValue())

    @abstractmethod
    def AddOrUpdate(self, key: TKey, value: TValue) -> bool:
        ...
    @final
    def AddItemOrUpdate(self, item: KeyValuePair[TKey, TValue]) -> bool:
        return self.AddOrUpdate(item.GetKey(), item.GetValue())

    @abstractmethod
    def TryRemoveItem(self, key: TKey) -> INullable[TValue]:
        ...
    
    @overload
    def TryRemove[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValue|TDefault]: ...
    @overload
    def TryRemove(self, key: TKey, defaultValue: None = None) -> DualValueBool[TValue|None]: ...

    @final
    def TryRemove[TDefault](self, key: TKey, defaultValue: TDefault|None = None) -> DualValueBool[TValue|TDefault|None]:
        result: INullable[TValue] = self.TryRemoveItem(key)

        return DualValueBool[TValue](result.GetValue(), True) if result.HasValue() else DualValueBool[TDefault|None](defaultValue, False)

    @final
    def Remove(self, key: TKey) -> TValue:
        result: INullable[TValue] = self.TryRemoveItem(key)

        if result.HasValue(): return result.GetValue()

        raise GetKeyError(key, True)

class IReadOnlyOrderedSet[T: HashableProtocol](IReadOnlySet[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsTuple(self) -> IEquatableTuple[T]:
        ...
class IOrderedSet[T: HashableProtocol](ISet[T], IReadOnlyOrderedSet[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyOrderedSet[T]:
        ...

    @abstractmethod
    def AsList(self) -> IList[T]:
        ...

class Tuple[T](Abstract, ITuple[T]):
    def __init__(self) -> None: super().__init__()

class ArrayBase[T](Tuple[T]):
    def __init__(self) -> None: super().__init__()
class Array[T](ArrayBase[T], IArray[T]):
    def __init__(self) -> None: super().__init__()

class List[T](Array[T], IList[T]):
    def __init__(self) -> None: super().__init__()
class SortedList[T: SupportsEqualityAndRichComparison](ArrayBase[T], ISortedList[T]):
    def __init__(self) -> None: super().__init__()