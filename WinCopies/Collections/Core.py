from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sized, Iterable, Container
from typing import overload, final

from WinCopies import IInterface, Abstract
from WinCopies.Collections import Mutability, EmptyException
from WinCopies.Collections.Util import ReverseIndex, GetOffset, GetIndex, ValidateIndex, ReverseRangeStartIndex
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Comparison import IEquatableValue, IHashableValue, HashableProtocol
from WinCopies.Typing.Delegate import Converter, EqualityComparison
from WinCopies.Typing.Pairing import KeyValuePair, DualValueBool
from WinCopies.Typing.Protocols import SupportsRichComparison

class IReadOnlyCollection(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def IsEmpty(self) -> bool:
        pass
    
    def HasItems(self) -> bool:
        return not self.IsEmpty()
    
    def ThrowIfEmpty(self) -> None:
        if self.IsEmpty():
            raise EmptyException()

class IContainer[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Contains(self, value: T|object) -> bool:
        pass

class IReadOnlyList[T](IContainer[T], IReadOnlyCollection):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsContainer(self) -> Container[T]:
        pass

class ReadOnlyList[T](Container[T], IReadOnlyList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def AsContainer(self) -> Container[T]:
        return self
    
    @final
    def __contains__(self, x: object) -> bool:
        return self.Contains(x)

class ICollection[T](IReadOnlyList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Add(self, item: T) -> None:
        pass
    
    def AddRange(self, items: Iterable[T]) -> None:
        for item in items:
            self.Add(item)
    @final
    def TryAddRange(self, items: Iterable[T]|None) -> bool:
        if items is None:
            return False
        
        self.AddRange(items)
        
        return True

    @abstractmethod
    def TryRemoveAt(self, index: int) -> bool|None:
        pass
    @final
    def RemoveAt(self, index: int) -> None:
        if self.TryRemoveAt(index) is not True:
            raise IndexError(index)

    @abstractmethod
    def TryRemove(self, item: T, predicate: EqualityComparison[T]|None = None) -> bool:
        pass
    @final
    def Remove(self, item: T, predicate: EqualityComparison[T]|None = None) -> None:
        if not self.TryRemove(item, predicate):
            raise ValueError(item)
    
    @abstractmethod
    def TryRemoveRange(self, index: int, count: int) -> bool:
        pass
    @final
    def RemoveRange(self, index: int, count: int) -> None:
        if not self.TryRemoveRange(index, count):
            raise IndexError(index)

class ICountable(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetCount(self) -> int:
        pass

    @final
    def GetLastIndex(self) -> int:
        return self.GetCount() - 1
    
    @final
    def ValidateIndex(self, index: int) -> bool:
        return ValidateIndex(index, self.GetCount())
    
    @abstractmethod
    def AsSized(self) -> Sized:
        pass

class Countable(Sized, ICountable):
    def __init__(self) -> None:
        super().__init__()
    
    def AsSized(self) -> Sized:
        return self
    
    @final
    def __len__(self) -> int:
        return self.GetCount()

class IReadOnlyCountableList[T](IReadOnlyList[T], ICountable):
    def __init__(self) -> None:
        super().__init__()

class ICountableCollection[T](IReadOnlyCountableList[T], ICollection[T]):
    def __init__(self) -> None:
        super().__init__()

class IClearable(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Clear(self) -> None:
        pass

class ICountableList[T](ICountableCollection[T], IClearable):
    def __init__(self) -> None:
        super().__init__()

class IKeyableBase[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def ContainsKey(self, key: T) -> bool:
        pass

class IGetter[TKey, TValue](IKeyableBase[TKey]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryGetValue(self, key: TKey) -> INullable[TValue]:
        pass
    
    @final
    def TryGetAt[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValue|TDefault]:
        def getResult(value: TValue|TDefault, info: bool) -> DualValueBool[TValue|TDefault]:
            return DualValueBool[TValue|TDefault](value, info)
        
        result: INullable[TValue] = self.TryGetValue(key)

        return getResult(result.GetValue(), True) if result.HasValue() else getResult(defaultValue, False)
    @final
    def GetAt(self, key: TKey) -> TValue:
        result: INullable[TValue] = self.TryGetValue(key)
        
        if result.HasValue():
            return result.GetValue()
        
        raise KeyError(f"The key {key} does not exist.")
class ISetter[TKey, TValue](IKeyableBase[TKey]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TrySetAt(self, key: TKey, value: TValue) -> bool:
        pass
    @final
    def SetAt(self, key: TKey, value: TValue) -> None:
        if not self.TrySetAt(key, value):
            raise KeyError(f"Key {key} does not exist.")

class IReadOnlyIndexable[T](IGetter[int, T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IReadOnlyIndexable[T]:
        pass
class IWriteOnlyIndexable[T](ISetter[int, T]):
    def __init__(self) -> None:
        super().__init__()

class IReadWriteCollection[TKey, TValue](IGetter[TKey, TValue], ISetter[TKey, TValue]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Move(self, x: TKey, y: TKey) -> None:
        pass
    
    def Swap(self, x: TKey, y: TKey) -> None:
        value: TValue = self.GetAt(x)

        self.SetAt(x, self.GetAt(y))
        self.SetAt(y, value)

class ICountableIndexableBase(IKeyableBase[int], ICountable):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def ContainsKey(self, key: int) -> bool:
        return self.ValidateIndex(key)

class IIndexableCollectionBase(ICountable):
    def __init__(self) -> None:
        super().__init__()
    
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
        start, stop, step = key.indices(self.GetCount())
        
        return slice(self.ReverseIndex(start), self.ReverseIndex(stop), step)
    
    @final
    def ReverseRangeStartIndex(self, index: int, count: int) -> int:
        return ReverseRangeStartIndex(index, count, self.GetCount())
class IIndexableCollection(IIndexableCollectionBase, ICountableIndexableBase):
    def __init__(self) -> None:
        super().__init__()

class IReadOnlyCountableIndexable[T](IReadOnlyIndexable[T], IIndexableCollection):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def TryGetFirst[TDefault](self, defaultValue: TDefault) -> DualValueBool[T|TDefault]:
        return self.TryGetAt(0, defaultValue)
    @final
    def TryGetFirstItem(self) -> INullable[T]:
        return self.TryGetValue(0)
    
    @final
    def TryGetLast[TDefault](self, defaultValue: TDefault) -> DualValueBool[T|TDefault]:
        return self.TryGetAt(self.GetLastIndex(), defaultValue)
    @final
    def TryGetLastItem(self) -> INullable[T]:
        return self.TryGetValue(self.GetLastIndex())
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IReadOnlyCountableIndexable[T]:
        pass
class IWriteOnlyCountableIndexable[T](IWriteOnlyIndexable[T], IIndexableCollection):
    def __init__(self) -> None:
        super().__init__()

class IIndexable[T](IReadOnlyIndexable[T], IWriteOnlyIndexable[T], IReadWriteCollection[int, T]):
    def __init__(self) -> None:
        super().__init__()
class ICountableIndexable[T](IIndexable[T], IReadOnlyCountableIndexable[T], IWriteOnlyCountableIndexable[T]):
    def __init__(self) -> None:
        super().__init__()

class IReadOnlyCountableIndexableList[T](IReadOnlyCountableIndexable[T], IReadOnlyCountableList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int:
        pass
    @abstractmethod
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int:
        pass

class ITuple[T](IReadOnlyCountableIndexableList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def IsEmpty(self) -> bool:
        return self.GetCount() == 0
    
    @abstractmethod
    def GetMutability(self) -> Mutability:
        pass

    @abstractmethod
    def TryGetSourceMutability(self) -> Mutability|None:
        pass
    @final
    def GetSourceMutability(self) -> Mutability:
        result: Mutability|None = self.TryGetSourceMutability()

        return self.GetMutability() if result is None else result
    
    @final
    def IsImmutable(self) -> bool:
        return self.GetSourceMutability() == Mutability.ReadOnly
    
    @abstractmethod
    def AsReversed(self) -> ITuple[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ITuple[T]:
        pass
class IEquatableTuple[T: IEquatableValue](ITuple[T], IEquatableValue):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReversed(self) -> IEquatableTuple[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        pass
class IHashableTuple[T: IHashableValue](IEquatableTuple[T], IHashableValue):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def GetMutability(self) -> Mutability:
        return Mutability.ReadOnly
    
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

class IArray[T](IArrayBase[T], ICountableIndexable[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReversed(self) -> IArray[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IArray[T]:
        pass

class IListBase[T](IArrayBase[T], ICountableList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> IListBase[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IListBase[T]:
        pass
    
    @final
    def TryRemove(self, item: T, predicate: EqualityComparison[T]|None = None) -> bool:
        return self.TryRemoveAt(self.FindFirstIndex(item, predicate)) is True

class IList[T](IArray[T], IListBase[T]):
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
    
    @abstractmethod
    def TryInsert(self, index: int, value: T) -> bool:
        pass
    @final
    def Insert(self, index: int, value: T) -> None:
        if not self.TryInsert(index, value):
            raise IndexError(index)
    
    @abstractmethod
    def TryInsertRange(self, index: int, items: Iterable[T]) -> bool:
        pass
    @final
    def InsertRange(self, index: int, items: Iterable[T]) -> None:
        if not self.TryInsertRange(index, items):
            raise IndexError(index)
    
    @final
    def TryInsertValues(self, index: int, *values: T) -> bool:
        return self.TryInsertRange(index, values)
    @final
    def InsertValues(self, index: int, *values: T) -> None:
        if not self.TryInsertValues(index, *values):
            raise IndexError(index)

class ISortedTuple[T](ITuple[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def BisectLeft[_T: SupportsRichComparison](self, item: _T, converter: Converter[T, _T]) -> int:
        pass
    @abstractmethod
    def BisectRight[_T: SupportsRichComparison](self, item: _T, converter: Converter[T, _T]) -> int:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ISortedTuple[T]:
        pass
    
    @abstractmethod
    def AsReversed(self) -> ISortedTuple[T]:
        pass
class ISortedList[T](IListBase[T], ISortedTuple[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AddLeft(self, item: T) -> None:
        pass

    @abstractmethod
    def AsReversed(self) -> ISortedList[T]:
        pass

    @abstractmethod
    def AsReadOnly(self) -> ISortedTuple[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ISortedList[T]:
        pass

class IReadOnlySet[T: HashableProtocol](IReadOnlyList[T], ICountable):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def IsEmpty(self) -> bool:
        return self.GetCount() < 1
class ISet[T: HashableProtocol](IReadOnlySet[T], IClearable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlySet[T]:
        pass
    
    @abstractmethod
    def TryAdd(self, item: T) -> bool:
        pass
    @abstractmethod
    def Add(self, item: T) -> None:
        pass

    @abstractmethod
    def TryAddRange(self, items: Iterable[T]) -> bool:
        pass
    @final
    def AddRange(self, items: Iterable[T]) -> None:
        if not self.TryAddRange(items):
            raise KeyError()

    @final
    def TryAddValues(self, *values: T) -> bool:
        return self.TryAddRange(values)
    @final
    def AddValues(self, *values: T) -> None:
        if not self.TryAddValues(*values):
            raise KeyError()
    
    @abstractmethod
    def Remove(self, item: T) -> None:
        pass
    @abstractmethod
    def TryRemove(self, item: T) -> bool:
        pass

class IReadOnlyDictionary[TKey: HashableProtocol, TValue](IGetter[TKey, TValue], IReadOnlyCollection, ICountable):
    def __init__(self) -> None:
        super().__init__()
class IDictionary[TKey: HashableProtocol, TValue](IReadOnlyDictionary[TKey, TValue], IReadWriteCollection[TKey, TValue], IClearable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyDictionary[TKey, TValue]:
        pass
    
    @abstractmethod
    def TryAdd(self, key: TKey, value: TValue) -> bool:
        pass
    @abstractmethod
    def Add(self, key: TKey, value: TValue) -> None:
        pass

    @abstractmethod
    def TryAddItem(self, item: KeyValuePair[TKey, TValue]) -> bool:
        pass
    @abstractmethod
    def AddItem(self, item: KeyValuePair[TKey, TValue]) -> None:
        pass

    @abstractmethod
    def AddOrUpdate(self, key: TKey, value: TValue) -> bool:
        pass
    @abstractmethod
    def AddItemOrUpdate(self, item: KeyValuePair[TKey, TValue]) -> bool:
        pass
    
    @overload
    def TryRemove[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValue|TDefault]:
        ...
    @overload
    def TryRemove(self, key: TKey, defaultValue: None = None) -> DualValueBool[TValue]|None:
        ...
    
    @abstractmethod
    def TryRemove[TDefault](self, key: TKey, defaultValue: TDefault|None = None) -> DualValueBool[TValue|TDefault]|None:
        pass
    @final
    def TryRemoveItem(self, key: TKey) -> INullable[TValue]:
        result: DualValueBool[TValue]|None = self.TryRemove(key)

        return GetNullable(result.GetKey()) if result is not None and result.GetValue() else GetNullValue()

    @abstractmethod
    def Remove(self, key: TKey) -> TValue:
        pass

class IReadOnlyOrderedSet[T: IHashableValue](IReadOnlySet[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsTuple(self) -> IEquatableTuple[T]:
        pass
class IOrderedSet[T: IHashableValue](ISet[T], IReadOnlyOrderedSet[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyOrderedSet[T]:
        pass

    @abstractmethod
    def AsList(self) -> IList[T]:
        pass

class Tuple[T](Abstract, ITuple[T]):
    def __init__(self) -> None:
        super().__init__()

class ArrayBase[T](Tuple[T]):
    def __init__(self) -> None:
        super().__init__()
class Array[T](ArrayBase[T], IArray[T]):
    def __init__(self) -> None:
        super().__init__()

class List[T](Array[T], IList[T]):
    def __init__(self) -> None:
        super().__init__()
class SortedList[T](ArrayBase[T], ISortedList[T]):
    def __init__(self) -> None:
        super().__init__()