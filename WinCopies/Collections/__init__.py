import collections.abc

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from enum import Enum
from typing import Callable, List, Self

from WinCopies import Not
from WinCopies.Math import Between, Outside
from WinCopies.Typing.Delegate import Converter, Function, Predicate
from WinCopies.Typing.Pairing import DualNullableValueInfo, DualNullableValueBool

type Generator[T] = collections.abc.Generator[T, None, None]

class IterableScanResult(Enum):
    DoesNotExist = -2
    Empty = -1
    Success = 0
    Error = 1

    def __bool__(self) -> bool:
        return self >= 0
    
    def Not(self) -> Self:
        return (IterableScanResult.Error if self == IterableScanResult.Success else IterableScanResult.Success) if self else self

def GetOffset(inStart: int, outStart: int, length: int) -> int:
    paramName: str

    def check(value: int, _paramName: str) -> bool:
        nonlocal paramName

        paramName = _paramName

        return Between(0, value, length, True, False)
    
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

    if offset > 0:
        if start == 0:
            return (offset, offset)

        tmp: int = totalLength - start

        return (0 if offset == tmp else ((start - (totalLength - offset)) if offset > tmp else start + offset), offset)

    return (totalLength + offset + start if abs(offset) > start else start + offset, offset)

def GetLastIndex(l: Sequence) -> int:
    return len(l) - 1

def TrySetAt[T](l: List[T], index: int, ifTrue: Converter[int, T], ifFalse: Function[T]) -> T:
    return ifTrue(index) if Between(0, index, len(l)) else ifFalse()

def TryGetAt[T](l: List[T], index: int, default: T|None = None) -> T|None:
    return l[index] if Between(0, index, len(l)) else default
def TryGetAtFunc[TIn, TOut](l: List[TIn], index: int, ifTrue: Converter[TIn, TOut], ifFalse: Function[TOut]) -> TOut:
    return TrySetAt(l, index, lambda i: ifTrue(l[i]), ifFalse)
def TryGetAtStr(l: List[str], index: int) -> str:
    return TryGetAt(l, index, '')

def GetIndexOf[T](l: list[T], value: T, i: int = 0, length: int|None = None, predicate: EqualityComparison[T]|None = None) -> DualNullableValueInfo[int, int]:
    def getReturnValue(value: int|None, info: int) -> DualNullableValueInfo[int, int]:
        return DualNullableValueInfo[int, int](value, info)
    def getNullValue() -> DualNullableValueInfo[int, int]:
        return getReturnValue(None, length)
    
    def validate(listLength: int) -> None:
        nonlocal length
        
        if length is None:
            length = listLength
        
        elif Outside(0, length, listLength):
            raise ValueError("The given length can not be less than zero or greater than the length of the given list.", listLength, length)
    
    validate(len(l))

    if length == 0 or i < 0:
        return getNullValue()
    
    if predicate is None:
        predicate = CompareEquality
    
    while i < length:
        if predicate(l[i], value):
            return getReturnValue(i, length)

        i += 1
    
    return getNullValue()

def IndexOf[T](l: list[T], value: T, predicate: EqualityComparison[T]|None = None) -> int|None:
    return GetIndexOf(l, value, predicate).GetKey()

def GetIndexOfSequence[T](l: list[T], values: list[T], i: int = 0) -> tuple[int|None, int, int]:
    length: int = len(list)
    valuesLength: int = len(values)
    
    def getResult(result: int|None) -> tuple[int|None, int, int]:
        return (result, length, valuesLength)

    if length == 0 or valuesLength == 0 or valuesLength > length:
        return getResult(None)
    
    if valuesLength == 1:
        result: DualNullableValueInfo[int, int] = GetIndexOf(l, values[0])
        
        return (result.GetValue(), result.GetInfo(), valuesLength)
    
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

def IndexOfSequence[T](l: list[T], values: list[T]) -> int|None:
    return GetIndexOfSequence(l, values)[0]

def ContainsMultipleTimes[T](l: list[T], value: T, i: int = 0, length: int|None = None) -> tuple[bool|None, int|None, int]:
    result: DualNullableValueInfo[int, int] = GetIndexOf(l, value, i, length)

    if (i := result.GetKey()) is None:
        return (None, None, result.GetValue())
    
    result = GetIndexOf(l, value, i + 1)
    
    return (result.GetValue() is int, result.GetKey(), result.GetValue())

def ContainsMultiple[T](l: list[T], value: T) -> bool|None:
    return ContainsMultipleTimes(l, value)[0]

def ContainsOnlyOne[T](l: list[T], value: T, i: int = 0, length: int|None = None) -> tuple[bool|None, int|None, int]:
    result: tuple[bool|None, int|None, int] = ContainsMultipleTimes(l, value, i, length)

    return (Not(result[0]), result[1], result[2])
    
def ContainsOne[T](l: list[T], value: T) -> bool|None:
    return Not(ContainsMultiple(l, value))

def ContainsSequenceMultipleTimes[T](l: list[T], values: list[T], i: int = 0) -> tuple[bool|None, int|None, int, int]:
    result: tuple[int|None, int, int] = GetIndexOfSequence(l, values, i)
    
    initialResult: int = result[0]

    if initialResult is None:
        return (None, None, result[1], result[2])
    
    result = GetIndexOfSequence(l, values, result[0] + 1)
    
    return (result[0] is int, initialResult, result[1], result[2])
def ContainsMultipleSequences[T](l: list[T], values: list[T]) -> bool|None:
    return ContainsSequenceMultipleTimes(l, values)[0]

def ContainsOnlyOneSequence[T](l: list[T], value: T, i: int = 0) -> tuple[bool|None, int|None, int]:
    result: tuple[bool|None, int|None, int, int] = ContainsSequenceMultipleTimes(l, value, i)

    return (Not(result[0]), result[1], result[2], result[3])
    
def ContainsOneSequence[T](l: list[T], value: T) -> bool|None:
    return Not(ContainsMultipleSequences(l, value))

def MakeIterable[T](*items: T) -> Iterable[T]:
    return items

def IterateWith[T](itemsProvider: Function[Iterable[T]], func: Converter[Iterable[T], bool|None]) -> bool|None:
    with itemsProvider() as items:
        return func(items)
def IterateFrom[TIn, TOut](value: TIn, itemsProvider: Converter[TIn, Iterable[TOut]], func: Converter[Iterable[TOut], bool|None]) -> bool|None:
    return IterateWith(lambda: itemsProvider(value), func)

def TryIterateWith[T](checker: Function[bool], itemsProvider: Function[Iterable[T]], func: Converter[Iterable[T], bool|None]) -> IterableScanResult:
    if checker():
        result: bool|None = IterateWith(itemsProvider, func)

        return IterableScanResult.Empty if result == None else (IterableScanResult.Success if result else IterableScanResult.Error)
    
    return IterableScanResult.DoesNotExist
def TryIterateFrom[TIn, TOut](value: TIn, checker: Predicate[TIn], itemsProvider: Converter[TIn, Iterable[TOut]], func: Converter[Iterable[TOut], bool|None]) -> IterableScanResult:
    return TryIterateWith(lambda: checker(value), lambda: itemsProvider(value), func)

class EmptyException(Exception):
    def __init__(self):
        pass

class Collection(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    def IsEmpty(self) -> bool:
        pass
    
    def HasItems(self) -> bool:
        return not self.IsEmpty()
    
    def ThrowIfEmpty(self) -> None:
        if self.IsEmpty():
            raise EmptyException()

class FinderPredicate[T]:
    def __init__(self):
        self.__Reset()
    
    def __Reset(self):
        self.__result: T|None = None
        self.__hasValue: bool = False
    
    def __Set(self, result: T):
        self.__result = result
        self.__hasValue = True

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
    
    def TryGetResult(self) -> DualNullableValueBool[T]:
        return DualNullableValueBool[T](self.__result, self.__hasValue)
    
    def GetResult(self) -> T:
        if self.__hasValue:
            return self.__result
        
        raise ValueError('This object contains no value.')