from typing import Callable
from collections.abc import Iterable

from WinCopies.Collections import Loop

def Replace(string: str, esc: str, newEsc: str, args: Iterable[str]) -> str:
    string = string.replace(esc + esc, esc)
    
    for arg in args:
        string = string.replace(esc + arg, newEsc + arg)
    
    return string
def ReplaceValues(string: str, esc: str, newEsc: str, *args: str) -> str:
    return Replace(string, esc, newEsc, args)

def SurroundWith(prefix: str, string: str, suffix: str) -> str:
    return f"{prefix}{string}{suffix}"
def TrySurroundWith(prefix: str, string: str|None, suffix: str) -> str|None:
    return None if string is None else SurroundWith(prefix, string, suffix)

def Surround(string: str, value: str) -> str:
    return SurroundWith(value, string, value)
def TrySurround(string: str|None, value: str) -> str|None:
    return TrySurroundWith(value, string, value)

def QuoteSurround(string: str) -> str:
    return Surround(string, "'")
def TryQuoteSurround(string: str) -> str:
    return TrySurround(string, "'")

def DoubleQuoteSurround(string: str) -> str:
    return Surround(string, '"')
def TryDoubleQuoteSurround(string: str) -> str:
    return TrySurround(string, '"')

def SpaceJoin(values: Iterable[str]) -> str:
    return ' '.join(values)
def SpaceJoinValues(*values: str) -> str:
    return SpaceJoin(values)

def CommaJoin(values: Iterable[str]) -> str:
    return ','.join(values)
def CommaJoinValues(*values: str) -> str:
    return CommaJoin(values)

def SemicolonJoin(values: Iterable[str]) -> str:
    return ';'.join(values)
def SemicolonJoinValues(*values: str) -> str:
    return SemicolonJoin(values)

def ColonJoin(values: Iterable[str]) -> str:
    return ':'.join(values)
def ColonJoinValues(*values: str) -> str:
    return ColonJoin(values)
def Join(values: Iterable[str]) -> str:
    result: str = ''

    for value in values:
        result += value
    
    return result
def JoinValues(*values: str) -> str:
    return Join(values)

def BuildFrom(values: Iterable[str], selector: Callable[[str], str]) -> str:
    result: str = ''

    for value in values:
        result += selector(value)
    
    return result
def BuildFromValues(*values: str, selector: Callable[[str], str]) -> str:
    return BuildFrom(values, selector)

def ConcatenateFrom(values: Iterable[str], separator: str, selector: Callable[[str], str]) -> str:
    result: str = ''
    
    def firstAction(value: str):
        nonlocal result

        result += value

    def action(value: str):
        nonlocal result
        nonlocal separator

        result += separator + selector(value)

    Loop.DoForEachAndFirst(values, firstAction, action)
    
    return result
def ConcatenateFromValues(separator: str, selector: Callable[[str], str], *values: str) -> str:
    return ConcatenateFrom(values, separator, selector)

def Contains(value: str, subValue: str, start: int|None = None, end: int|None = None) -> bool:
    return value.find(subValue, start, end) >= 0
def ContainsR(value: str, subValue: str, start: int|None = None, end: int|None = None) -> bool:
    return value.rfind(subValue, start, end) >= 0

def Omits(value: str, subValue: str, start: int|None = None, end: int|None = None) -> bool:
    return value.find(subValue, start, end) < 0
def OmitsR(value: str, subValue: str, start: int|None = None, end: int|None = None) -> bool:
    return value.rfind(subValue, start, end) < 0

def TrySplitAt(value: str, i: int) -> list[str]|None:
    return None if i < 0 or len(value) <= i else ([value] if i == 0 else [value[0:i - 1], value[i:]])
def SplitAt(value: str, i: int) -> list[str]:
    result: list[str]|None = TrySplitAt(value, i)

    if result is None:
        raise ValueError(f"Value out of range. Value length: {len(value)}; index: {i}.")
    
    return result

def __Split(value: str, find: str, func: Callable[[str, str], list[str]|None]) -> list[str]:
    result: list[str]|None = func(value, find)

    return [value if result is None else result]

def TrySplit(value: str, find: str) -> list[str]|None:
    return TrySplitAt(value, value.find(find))
def TrySplitFromLast(value: str, find: str) -> list[str]|None:
    return TrySplitAt(value, value.rfind(find))

def Split(value: str, find: str) -> list[str]:
    return __Split(value, find, TrySplit)
def SplitFromLast(value: str, find: str) -> list[str]:
    return __Split(value, find, TrySplitFromLast)

def __TryGet(value: str, find: str, i: int, func: Callable[[str, str], list[str]|None]) -> str|None:
    result: list[str]|None = func(value, find)
    
    return None if result is None else result[i]
def __TryGetKey(value: str, find: str, func: Callable[[str, str], list[str]|None]) -> str|None:
    return __TryGet(value, find, 0, func)
def __TryGetValue(value: str, find: str, func: Callable[[str, str], list[str]|None]) -> str|None:
    return __TryGet(value, find, 1, func)

def TryGetKey(value: str, find: str) -> str|None:
    return __TryGetKey(value, find, TrySplit)
def TryGetKeyFromLast(value: str, find: str) -> str|None:
    return __TryGetKey(value, find, TrySplitFromLast)

def TryGetValue(value: str, find: str) -> str|None:
    return __TryGetValue(value, find, TrySplit)
def TryGetValueFromLast(value: str, find: str) -> str|None:
    return __TryGetValue(value, find, TrySplitFromLast)

def __Get(value: str, find: str, func: Callable[[str, str], str|None]) -> str:
    result: str = func(value, find)

    return value if result is None else result

def GetKey(value: str, find: str) -> str:
    return __Get(value, find, TryGetKey)
def GetKeyFromLast(value: str, find: str) -> str:
    return __Get(value, find, TryGetKeyFromLast)

def GetValue(value: str, find: str) -> str:
    return __Get(value, find, TryGetValue)
def GetValueFromLast(value: str, find: str) -> str:
    return __Get(value, find, TryGetValueFromLast)

def TryRemoveFromStart(value: str, find: str) -> str|None:
    if value.startswith(find):
        length: int = len(find)

        return value[length + 1:] if len(value) > length else ''
    
    return None
def TryRemoveFromEnd(value: str, find: str) -> str|None:
    if value.endswith(find):
        length: int = len(find)

        return value[:-length] if len(value) > length else ''
    
    return None

def __RemoveFrom(value: str, find: str, func: Callable[[str, str], str|None]) -> str:
    result: str|None = func(value, find)

    return value if result is None else result

def RemoveFromStart(value: str, find: str) -> str:
    return __RemoveFrom(value, find, TryRemoveFromStart)
    
def RemoveFromEnd(value: str, find: str) -> str:
    return __RemoveFrom(value, find, TryRemoveFromEnd)