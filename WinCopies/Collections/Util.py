from collections.abc import Iterable, Sequence, MutableSequence
from typing import overload

from WinCopies import Not
from WinCopies.Collections import ReadOnlyArray, Generator
from WinCopies.Delegates import CompareEquality
from WinCopies.String import StringifyIfNone
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Comparison import Between, Outside
from WinCopies.Typing.Delegate import Converter, Function, EqualityComparison
from WinCopies.Typing.Pairing import DualNullableValueInfo

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

        if inStart < 0: inStart += length

        return -inStart if outStart < 0 else inStart
    
    raise IndexError(paramName)

def GetIndex(start: int, totalLength: int, offset: int) -> tuple[int, int]:
    offset %= totalLength

    match offset:
        case 0: return (start, offset)
        case 1: return ((start + 1) % totalLength, offset)
        case -1: return (totalLength - 1 if start == 0 else start - 1, offset)
        
        case _: pass

    if offset > 0:
        if start == 0: return (offset, offset)

        tmp: int = totalLength - start

        return (0 if offset == tmp else ((start - (totalLength - offset)) if offset > tmp else start + offset), offset)

    return (totalLength + offset + start if abs(offset) > start else start + offset, offset)

def GetLastIndex[T](l: Sequence[T]) -> int:
    return len(l) - 1

def GetLastItem[T](l: Sequence[T]) -> T:
    return l[-1]
def TryGetLastItem[T](l: Sequence[T]) -> INullable[T]:
    index: int = GetLastIndex(l)

    return GetNullValue() if index < 0 else GetNullable(l[index])

def ReverseIndexFromLast(index: int, lastIndex: int) -> int:
    return lastIndex - index
def ReverseIndex(index: int, length: int) -> int:
    return ReverseIndexFromLast(length - 1, index)

def ReverseRangeStartIndex(index: int, count: int, totalLength: int) -> int:
    return GetIndex(ReverseIndex(index, totalLength), totalLength, -(count - 1))[0]

def TryGetAt[TValue, TDefault](l: Sequence[TValue], index: int, default: TDefault|None = None) -> TValue|TDefault|None:
    return l[index] if ValidateIndex(index, len(l)) else default
def TryGetValue[T](l: Sequence[T], index: int) -> INullable[T]:
    return GetNullable(l[index]) if ValidateIndex(index, len(l)) else GetNullValue()

def TryGetAtStr(l: Sequence[str], index: int) -> str:
    return StringifyIfNone(TryGetAt(l, index, ''))

def TrySetAt[T](l: MutableSequence[T], index: int, value: T) -> bool:
    if ValidateIndex(index, len(l)):
        l[index] = value

        return True
    
    return False

def Move[T](l: MutableSequence[T], x: int, y: int) -> None:
    if x == y: return
    
    item: T = l.pop(x)

    if y == len(l): l.append(item)
    else: l.insert(y, item)

def TryGetIndex[T](l: Sequence[T], index: int, ifTrue: Converter[int, T], ifFalse: Function[T]) -> T:
    return ifTrue(index) if ValidateIndex(index, len(l)) else ifFalse()
def TryGetItem[TIn, TOut](l: Sequence[TIn], index: int, ifTrue: Converter[TIn, TOut], ifFalse: Function[TOut]) -> TOut:
    return ifTrue(l[index]) if ValidateIndex(index, len(l)) else ifFalse()

@overload
def SliceFromSecond[T](l: MutableSequence[T]) -> MutableSequence[T]: ...
@overload
def SliceFromSecond[T](l: Sequence[T]) -> Sequence[T]: ...

def SliceFromSecond[T](l: MutableSequence[T]|Sequence[T]) -> MutableSequence[T]|Sequence[T]:
    return l[1:]

@overload
def SliceToPenultimate[T](l: MutableSequence[T]) -> MutableSequence[T]: ...
@overload
def SliceToPenultimate[T](l: Sequence[T]) -> Sequence[T]: ...

def SliceToPenultimate[T](l: MutableSequence[T]|Sequence[T]) -> MutableSequence[T]|Sequence[T]:
    return l[:-1]

def GetIndexOf[T](l: Sequence[T], value: T, i: int = 0, length: int|None = None, predicate: EqualityComparison[T]|None = None) -> DualNullableValueInfo[int, int]|None:
    def getReturnValue(value: int|None, info: int) -> DualNullableValueInfo[int, int]: return DualNullableValueInfo[int, int](value, info)
    def getNullValue(length: int) -> DualNullableValueInfo[int, int]: return getReturnValue(None, length)
    
    def validate(length: int|None, listLength: int) -> int|None: return listLength if length is None else (None if Outside(0, length, listLength) else length)
    
    if (length := validate(length, len(l))) is None: return None
    
    if length == 0 or i < 0: return getNullValue(length)
    
    if predicate is None: predicate = CompareEquality
    
    while i < length:
        if predicate(l[i], value): return getReturnValue(i, length)

        i += 1
    
    return getNullValue(length)

def IndexOf[T](l: Sequence[T], value: T, predicate: EqualityComparison[T]|None = None) -> int|None:
    result: DualNullableValueInfo[int, int]|None = GetIndexOf(l, value, predicate = predicate)
    
    if result is None: raise NotImplementedError() # Should not end up here
    
    return result.GetKey()

def GetIndexOfSequence[T](l: Sequence[T], values: Sequence[T], i: int = 0) -> tuple[int|None, int, int]:
    length: int = len(l)
    valuesLength: int = len(values)
    
    def getResult(result: int|None) -> tuple[int|None, int, int]: return (result, length, valuesLength)

    if length == 0 or valuesLength == 0 or valuesLength > length: return getResult(None)
    
    if valuesLength == 1:
        result: DualNullableValueInfo[int, int]|None = GetIndexOf(l, values[0])
        
        if result is None: raise NotImplementedError() # Should not end up here
        
        return (result.GetKey(), result.GetValue(), valuesLength)
    
    j: int = 0

    while i < length:
        if l[i] == values[j]:
            j += 1

            if j == valuesLength: return getResult(i)
        
        else:
            j = 0

        i += 1
    
    return getResult(None)

def IndexOfSequence[T](l: Sequence[T], values: Sequence[T]) -> int|None: return GetIndexOfSequence(l, values)[0]

def ContainsMultipleTimes[T](l: Sequence[T], value: T, i: int = 0, length: int|None = None) -> tuple[bool|None, int|None, int]|None:
    result: DualNullableValueInfo[int, int]|None = GetIndexOf(l, value, i, length)

    if result is None: return None

    index: int|None = result.GetKey()
    length = result.GetValue()
    
    if index is None: return (None, None, length)
    
    result = GetIndexOf(l, value, index + 1, length - 1 - (index - i))
    
    return None if result is None else (result.GetKey() is not None, result.GetKey(), result.GetValue())

def ContainsMultiple[T](l: Sequence[T], value: T) -> INullable[bool]|None:
    result: tuple[bool|None, int|None, int]|None = ContainsMultipleTimes(l, value)
    
    if result is None: return None
    
    _result: bool|None = result[0]

    return GetNullValue() if _result is None else GetNullable(_result)

def ContainsOnlyOne[T](l: Sequence[T], value: T, i: int = 0, length: int|None = None) -> tuple[bool|None, int|None, int]|None:
    result: tuple[bool|None, int|None, int]|None = ContainsMultipleTimes(l, value, i, length)

    return None if result is None else (Not(result[0]), result[1], result[2])
    
def ContainsOne[T](l: Sequence[T], value: T) -> INullable[bool]|None:
    result: INullable[bool]|None = ContainsMultiple(l, value)

    if result is None: return None
    
    _result: bool|None = Not(result.TryGetValue())
    
    return GetNullValue() if _result is None else GetNullable(_result)

def ContainsSequenceMultipleTimes[T](l: Sequence[T], values: Sequence[T], i: int = 0) -> tuple[bool|None, int|None, int, int]:
    result: tuple[int|None, int, int] = GetIndexOfSequence(l, values, i)
    
    initialResult: int|None = result[0]

    if initialResult is None: return (None, None, result[1], result[2])
    
    result = GetIndexOfSequence(l, values, initialResult + 1)
    
    return (result[0] is not None, initialResult, result[1], result[2])
def ContainsMultipleSequences[T](l: Sequence[T], values: Sequence[T]) -> bool|None:
    return ContainsSequenceMultipleTimes(l, values)[0]

def ContainsOnlyOneSequence[T](l: Sequence[T], values: Sequence[T], i: int = 0) -> tuple[bool|None, int|None, int, int]:
    result: tuple[bool|None, int|None, int, int] = ContainsSequenceMultipleTimes(l, values, i)

    return (Not(result[0]), result[1], result[2], result[3])
    
def ContainsOneSequence[T](l: Sequence[T], values: Sequence[T]) -> bool|None:
    return Not(ContainsMultipleSequences(l, values))

def Enumerate[T](items: Iterable[T]) -> Generator[T]:
    yield from items

def MakeSequence[T](*items: T) -> ReadOnlyArray[T]:
    return items
def MakeGenerator[T](*items: T) -> Generator[T]:
    return Enumerate(items)

def MakeList[T](count: int, value: T|None = None) -> list[T|None]:
    return [value] * count
    
def FindIndex[T](sequence: Sequence[T], item: T, predicate: EqualityComparison[T]|None) -> int:
    result: int|None = IndexOf(sequence, item, predicate)

    return -1 if result is None else result

def __CreateReadOnlyArray[T](items: Sequence[T]|Iterable[T]) -> ReadOnlyArray[T]:
    return tuple[T, ...](items)
def __CreateSequence[T](items: Sequence[T]|Iterable[T]) -> Sequence[T]:
    return items if isinstance(items, Sequence) else __CreateReadOnlyArray(items)
def __CreateTuple[T](items: Sequence[T]|Iterable[T]) -> ReadOnlyArray[T]:
    return items if isinstance(items, tuple) else __CreateReadOnlyArray(items)
def __CreateList[T](items: MutableSequence[T]|Iterable[T]) -> MutableSequence[T]:
    return items if isinstance(items, MutableSequence) else list[T](items)

def CreateSequence[T](items: Sequence[T]|Iterable[T]|None) -> Sequence[T]:
    return MakeSequence() if items is None else __CreateSequence(items)
def TryCreateSequence[T](items: Sequence[T]|Iterable[T]|None) -> Sequence[T]|None:
    return None if items is None else __CreateSequence(items)

def CreateTuple[T](items: Sequence[T]|Iterable[T]|None) -> ReadOnlyArray[T]:
    return MakeSequence() if items is None else __CreateTuple(items)
def TryCreateTuple[T](items: Sequence[T]|Iterable[T]|None) -> ReadOnlyArray[T]|None:
    return None if items is None else __CreateTuple(items)

def CreateList[T](items: MutableSequence[T]|Iterable[T]|None) -> MutableSequence[T]:
    return list[T]() if items is None else __CreateList(items)
def TryCreateList[T](items: MutableSequence[T]|Iterable[T]|None) -> MutableSequence[T]|None:
    return None if items is None else __CreateList(items)