from __future__ import annotations

from abc import abstractmethod
from collections.abc import Generator as GeneratorBase, Sized, Iterable, Container, Sequence, MutableSequence
from contextlib import AbstractContextManager
from typing import final, Callable

from WinCopies import IInterface, Abstract, BooleanableEnum, NullableBoolean, Not
from WinCopies.Delegates import CompareEquality
from WinCopies.Math import Between, Outside
from WinCopies.String import StringifyIfNone
from WinCopies.Typing import INullable, IEquatableItem, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Converter, Function, Predicate, EqualityComparison
from WinCopies.Typing.Pairing import KeyValuePair, DualNullableValueInfo, DualValueBool

type Generator[T] = GeneratorBase[T, None, None]

class IterableScanResult(BooleanableEnum):
    DoesNotExist = -2
    Empty = -1
    Success = 0
    Error = 1
    
    def Not(self) -> IterableScanResult:
        return (IterableScanResult.Error if self == IterableScanResult.Success else IterableScanResult.Success) if self else self
class IterationResult(BooleanableEnum):
    Error = -1
    Success = 0
    Empty = 1
    Null = 2
    
    def ToNullableBool(self) -> bool|None:
        return True if self == IterationResult.Success else (None if self.value > 0 else False)
    
    def ToNullableBoolean(self) -> NullableBoolean:
        return NullableBoolean.BoolTrue if self == IterationResult.Success else (NullableBoolean.Null if self.value > 0 else NullableBoolean.BoolFalse)

def ValidateIndex(index: int, length: int) -> bool:
    return Between(0, index, length, True, False)

def GetOffset(inStart: int, outStart: int, length: int) -> int:
    paramName: str|None = None

    def check(value: int, _paramName: str) -> bool:
        nonlocal paramName

        paramName = _paramName

        return ValidateIndex(value, length)
    
    if check(inStart, "inStart") and check(outStart, "outStart"):
        inStart = outStart - inStart

        if inStart < 0:
            inStart += length

        return -inStart if outStart < 0 else inStart
    
    raise IndexError(paramName)

def GetIndex(start: int, totalLength: int, offset: int) -> tuple[int, int]:
    offset %= totalLength

    match offset:
        case 0:
            return (start, offset)

        case 1:
            return ((start + 1) % totalLength, offset)

        case -1:
            return (totalLength - 1 if start == 0 else start - 1, offset)
        
        case _:
            pass

    if offset > 0:
        if start == 0:
            return (offset, offset)

        tmp: int = totalLength - start

        return (0 if offset == tmp else ((start - (totalLength - offset)) if offset > tmp else start + offset), offset)

    return (totalLength + offset + start if abs(offset) > start else start + offset, offset)

def GetLastIndex[T](l: Sequence[T]) -> int:
    return len(l) - 1

def ReverseIndex(index: int, length: int) -> int:
    return length - 1 - index

def TryGetAt[T](l: Sequence[T], index: int, default: T|None = None) -> T|None:
    return l[index] if ValidateIndex(index, len(l)) else default
def TryGetAtStr(l: Sequence[str], index: int) -> str:
    return StringifyIfNone(TryGetAt(l, index, ''))

def TrySetAt[T](l: MutableSequence[T], index: int, value: T) -> bool:
    if ValidateIndex(index, len(l)):
        l[index] = value

        return True
    
    return False

def Move[T](l: MutableSequence[T], x: int, y: int) -> None:
    if x == y:
        return
    
    item: T = l.pop(x)

    if y == len(l):
        l.append(item)
    
    else:
        l.insert(y, item)

def TryGetIndex[T](l: Sequence[T], index: int, ifTrue: Converter[int, T], ifFalse: Function[T]) -> T:
    return ifTrue(index) if ValidateIndex(index, len(l)) else ifFalse()
def TryGetItem[TIn, TOut](l: Sequence[TIn], index: int, ifTrue: Converter[TIn, TOut], ifFalse: Function[TOut]) -> TOut:
    return ifTrue(l[index]) if ValidateIndex(index, len(l)) else ifFalse()

def GetIndexOf[T](l: Sequence[T], value: T, i: int = 0, length: int|None = None, predicate: EqualityComparison[T]|None = None) -> DualNullableValueInfo[int, int]|None:
    def getReturnValue(value: int|None, info: int) -> DualNullableValueInfo[int, int]:
        return DualNullableValueInfo[int, int](value, info)
    def getNullValue(length: int) -> DualNullableValueInfo[int, int]:
        return getReturnValue(None, length)
    
    def validate(length: int|None, listLength: int) -> int|None:
        return listLength if length is None else (None if Outside(0, length, listLength) else length)
    
    if (length := validate(length, len(l))) is None:
        return None
    
    if length == 0 or i < 0:
        return getNullValue(length)
    
    if predicate is None:
        predicate = CompareEquality
    
    while i < length:
        if predicate(l[i], value):
            return getReturnValue(i, length)

        i += 1
    
    return getNullValue(length)

def IndexOf[T](l: Sequence[T], value: T, predicate: EqualityComparison[T]|None = None) -> int|None:
    result: DualNullableValueInfo[int, int]|None = GetIndexOf(l, value, predicate = predicate)
    
    if result is None:
        raise NotImplementedError() # Should not end up here
    
    return result.GetKey()

def GetIndexOfSequence[T](l: Sequence[T], values: Sequence[T], i: int = 0) -> tuple[int|None, int, int]:
    length: int = len(l)
    valuesLength: int = len(values)
    
    def getResult(result: int|None) -> tuple[int|None, int, int]:
        return (result, length, valuesLength)

    if length == 0 or valuesLength == 0 or valuesLength > length:
        return getResult(None)
    
    if valuesLength == 1:
        result: DualNullableValueInfo[int, int]|None = GetIndexOf(l, values[0])
        
        if result is None:
            raise NotImplementedError() # Should not end up here
        
        return (result.GetKey(), result.GetValue(), valuesLength)
    
    j: int = 0

    while i < length:
        if l[i] == values[j]:
            j += 1

            if j == valuesLength:
                return getResult(i)
        
        else:
            j = 0

        i += 1
    
    return getResult(None)

def IndexOfSequence[T](l: Sequence[T], values: Sequence[T]) -> int|None:
    return GetIndexOfSequence(l, values)[0]

def ContainsMultipleTimes[T](l: Sequence[T], value: T, i: int = 0, length: int|None = None) -> tuple[bool|None, int|None, int]|None:
    result: DualNullableValueInfo[int, int]|None = GetIndexOf(l, value, i, length)

    if result is None:
        return None

    index: int|None = result.GetKey()
    length = result.GetValue()
    
    if index is None:
        return (None, None, length)
    
    result = GetIndexOf(l, value, index + 1, length - 1 - (index - i))
    
    return None if result is None else (result.GetKey() is not None, result.GetKey(), result.GetValue())

def ContainsMultiple[T](l: Sequence[T], value: T) -> INullable[bool]|None:
    result: tuple[bool|None, int|None, int]|None = ContainsMultipleTimes(l, value)
    
    if result is None:
        return None
    
    _result: bool|None = result[0]

    return GetNullValue() if _result is None else GetNullable(_result)

def ContainsOnlyOne[T](l: Sequence[T], value: T, i: int = 0, length: int|None = None) -> tuple[bool|None, int|None, int]|None:
    result: tuple[bool|None, int|None, int]|None = ContainsMultipleTimes(l, value, i, length)

    return None if result is None else (Not(result[0]), result[1], result[2])
    
def ContainsOne[T](l: Sequence[T], value: T) -> INullable[bool]|None:
    result: INullable[bool]|None = ContainsMultiple(l, value)

    if result is None:
        return None
    
    _result: bool|None = Not(result.TryGetValue())
    
    return GetNullValue() if _result is None else GetNullable(_result)

def ContainsSequenceMultipleTimes[T](l: Sequence[T], values: Sequence[T], i: int = 0) -> tuple[bool|None, int|None, int, int]:
    result: tuple[int|None, int, int] = GetIndexOfSequence(l, values, i)
    
    initialResult: int|None = result[0]

    if initialResult is None:
        return (None, None, result[1], result[2])
    
    result = GetIndexOfSequence(l, values, initialResult + 1)
    
    return (result[0] is not None, initialResult, result[1], result[2])
def ContainsMultipleSequences[T](l: Sequence[T], values: Sequence[T]) -> bool|None:
    return ContainsSequenceMultipleTimes(l, values)[0]

def ContainsOnlyOneSequence[T](l: Sequence[T], values: Sequence[T], i: int = 0) -> tuple[bool|None, int|None, int, int]:
    result: tuple[bool|None, int|None, int, int] = ContainsSequenceMultipleTimes(l, values, i)

    return (Not(result[0]), result[1], result[2], result[3])
    
def ContainsOneSequence[T](l: Sequence[T], values: Sequence[T]) -> bool|None:
    return Not(ContainsMultipleSequences(l, values))

def MakeSequence[T](*items: T) -> Sequence[T]:
    return items
def MakeGenerator[T](*items: T) -> Generator[T]:
    return (item for item in items)

def IterateWith[T](itemsProvider: Function[AbstractContextManager[Iterable[T]]], func: Converter[Iterable[T], bool|None]) -> bool|None:
    with itemsProvider() as items:
        return func(items)
def IterateFrom[TIn, TOut](value: TIn, itemsProvider: Converter[TIn, AbstractContextManager[Iterable[TOut]]], func: Converter[Iterable[TOut], bool|None]) -> bool|None:
    return IterateWith(lambda: itemsProvider(value), func)

def TryIterateWith[T](checker: Function[bool], itemsProvider: Function[AbstractContextManager[Iterable[T]]], func: Converter[Iterable[T], bool|None]) -> IterableScanResult:
    if checker():
        result: bool|None = IterateWith(itemsProvider, func)

        return IterableScanResult.Empty if result == None else (IterableScanResult.Success if result else IterableScanResult.Error)
    
    return IterableScanResult.DoesNotExist
def TryIterateFrom[TIn, TOut](value: TIn, checker: Predicate[TIn], itemsProvider: Converter[TIn, AbstractContextManager[Iterable[TOut]]], func: Converter[Iterable[TOut], bool|None]) -> IterableScanResult:
    return TryIterateWith(lambda: checker(value), lambda: itemsProvider(value), func)

class EmptyException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class IReadOnlyCollection(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def IsEmpty(self) -> bool:
        pass
    
    def HasItems(self) -> bool:
        return not self.IsEmpty()
    
    def ThrowIfEmpty(self) -> None:
        if self.IsEmpty():
            raise EmptyException()
class IReadOnlyList[T](IReadOnlyCollection):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Contains(self, value: T|object) -> bool:
        pass

    @abstractmethod
    def AsContainer(self) -> Container[T]:
        pass

class ReadOnlyList[T](Container[T], IReadOnlyList[T]):
    def __init__(self):
        super().__init__()
    
    def AsContainer(self) -> Container[T]:
        return self
    
    @final
    def __contains__(self, x: object) -> bool:
        return self.Contains(x)

class ICollection[T](IReadOnlyList[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Add(self, item: T) -> None:
        pass

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

class ICountable(IInterface):
    def __init__(self):
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
    def __init__(self):
        super().__init__()
    
    def AsSized(self) -> Sized:
        return self
    
    @final
    def __len__(self) -> int:
        return self.GetCount()

class IReadOnlyCountableList[T](IReadOnlyList[T], ICountable):
    def __init__(self):
        super().__init__()

class ICountableCollection[T](IReadOnlyCountableList[T], ICollection[T]):
    def __init__(self):
        super().__init__()

class IClearable(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Clear(self) -> None:
        pass

class ICountableList[T](ICountableCollection[T], IClearable):
    def __init__(self):
        super().__init__()

class IKeyableBase[T](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def ContainsKey(self, key: T) -> bool:
        pass

class IGetter[TKey, TValue](IKeyableBase[TKey]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def TryGetAt[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValue|TDefault]:
        pass
    @final
    def TryGetItem(self, key: TKey) -> INullable[TValue]:
        result: DualValueBool[TValue|None] = self.TryGetAt(key, None)

        return GetNullable(result.GetKey()) if result.GetValue() else GetNullValue() # type: ignore
    @final
    def GetAt(self, key: TKey) -> TValue:
        result: INullable[TValue] = self.TryGetItem(key)
        
        if result.HasValue():
            return result.GetValue()
        
        raise KeyError(f"Key {key} does not exist.")
class ISetter[TKey, TValue](IKeyableBase[TKey]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def TrySetAt(self, key: TKey, value: TValue) -> bool:
        pass
    @final
    def SetAt(self, key: TKey, value: TValue) -> None:
        if not self.TrySetAt(key, value):
            raise KeyError(f"Key {key} does not exist.")

class IReadOnlyKeyable[TKey, TValue](IGetter[TKey, TValue]):
    def __init__(self):
        super().__init__()
class IWriteOnlyKeyable[TKey, TValue](ISetter[TKey, TValue]):
    def __init__(self):
        super().__init__()

class IReadOnlyIndexable[T](IGetter[int, T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IReadOnlyIndexable[T]:
        pass
class IWriteOnlyIndexable[T](IWriteOnlyKeyable[int, T]):
    def __init__(self):
        super().__init__()

class IReadWriteCollection[TKey, TValue](IGetter[TKey, TValue], IWriteOnlyKeyable[TKey, TValue]):
    def __init__(self):
        super().__init__()
    
    @final
    def Swap(self, x: TKey, y: TKey) -> None:
        value: TValue = self.GetAt(x)

        self.SetAt(x, self.GetAt(y))
        self.SetAt(y, value)
class IKeyable[TKey, TValue](IReadWriteCollection[TKey, TValue], IReadOnlyKeyable[TKey, TValue]):
    def __init__(self):
        super().__init__()

class ICountableIndexableBase(IKeyableBase[int], ICountable):
    def __init__(self):
        super().__init__()
    
    @final
    def ContainsKey(self, key: int) -> bool:
        return self.ValidateIndex(key)

class IReadOnlyCountableIndexable[T](IReadOnlyIndexable[T], ICountableIndexableBase):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IReadOnlyCountableIndexable[T]:
        pass
class IWriteOnlyCountableIndexable[T](IWriteOnlyIndexable[T], ICountableIndexableBase):
    def __init__(self):
        super().__init__()

class IIndexable[T](IReadOnlyIndexable[T], IWriteOnlyIndexable[T], IReadWriteCollection[int, T]):
    def __init__(self):
        super().__init__()
class ICountableIndexable[T](IIndexable[T], IReadOnlyCountableIndexable[T], IWriteOnlyCountableIndexable[T]):
    def __init__(self):
        super().__init__()

class IReadOnlyCountableIndexableList[T](IReadOnlyCountableIndexable[T], IReadOnlyCountableList[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int:
        pass
    @abstractmethod
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int:
        pass

class ITuple[T](IReadOnlyCountableIndexableList[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> ITuple[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ITuple[T]:
        pass
class IEquatableTuple[T: IEquatableItem](ITuple[T]):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def AsReversed(self) -> IEquatableTuple[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        pass

class IArray[T](ITuple[T], ICountableIndexable[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> ITuple[T]:
        pass

    @abstractmethod
    def AsReversed(self) -> IArray[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IArray[T]:
        pass

class IList[T](IArray[T], ICountableList[T]):
    def __init__(self):
        super().__init__()

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
    
    @final
    def TryRemove(self, item: T, predicate: EqualityComparison[T]|None = None) -> bool:
        return self.TryRemoveAt(self.FindFirstIndex(item, predicate)) is True

class IReadOnlySet(ICountable, IReadOnlyCollection):
    def __init__(self):
        super().__init__()
    
    @final
    def IsEmpty(self) -> bool:
        return self.GetCount() == 0
class ISet[T: IEquatableItem](IReadOnlySet, IClearable):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlySet:
        pass
    
    @abstractmethod
    def TryAdd(self, item: T) -> bool:
        pass
    @abstractmethod
    def Add(self, item: T) -> None:
        pass
    
    @abstractmethod
    def Remove(self, item: T) -> None:
        pass
    @abstractmethod
    def TryRemove(self, item: T) -> bool:
        pass

class IReadOnlyDictionary[TKey: IEquatableItem, TValue](IReadOnlyKeyable[TKey, TValue], ICountable):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def TryGetValue(self, key: TKey) -> INullable[TValue]:
        pass
class IDictionary[TKey: IEquatableItem, TValue](IReadOnlyDictionary[TKey, TValue], IKeyable[TKey, TValue], IClearable):
    def __init__(self):
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
    def TryRemove[TDefault](self, key: TKey, defaultValue: TDefault) -> TValue|TDefault:
        pass
    @abstractmethod
    def TryRemoveValue(self, key: TKey) -> INullable[TValue]:
        pass

    @abstractmethod
    def Remove(self, key: TKey) -> None:
        pass

class Tuple[T](Abstract, ITuple[T]):
    def __init__(self):
        super().__init__()
    
    def IsEmpty(self) -> bool:
        return self.GetCount() == 0

class Array[T](Tuple[T], IArray[T]):
    def __init__(self):
        super().__init__()

class List[T](Array[T], IList[T]):
    def __init__(self):
        super().__init__()

class FinderPredicate[T](IInterface):
    def __init__(self):
        super().__init__()
        
        self.__Reset()
    
    def __Reset(self) -> None:
        self.__result: INullable[T] = GetNullValue()
    
    def __Set(self, result: T) -> None:
        self.__result = GetNullable(result)

    def __Scan(self, entry: T, predicate: Predicate[T]) -> bool:
        if predicate(entry):
            self.__Set(entry)
            
            return True
        
        return False

    def __Validate(self, entry: T, predicate: Predicate[T]) -> bool:
        if predicate(entry):
            return True
        
        self.__Set(entry)
        
        return False
    
    def __GetPredicate(self, predicate: Predicate[T], func: Callable[[T, Predicate[T]], bool]) -> Predicate[T]:
        self.__Reset()

        return lambda entry: func(entry, predicate)
    
    def GetPredicate(self, predicate: Predicate[T]) -> Predicate[T]:
        return self.__GetPredicate(predicate, self.__Scan)
    
    def GetValidationPredicate(self, predicate: Predicate[T]) -> Predicate[T]:
        return self.__GetPredicate(predicate, self.__Validate)
    
    def GetResult(self) -> INullable[T]:
        return self.__result

def CreateList[T](count: int, value: T|None = None) -> list[T|None]:
    return [value] * count