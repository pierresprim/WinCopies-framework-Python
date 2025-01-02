from typing import Callable
from collections.abc import Iterable

from WinCopies.Collections import Loop

def Replace(string: str, esc: str, newEsc: str, *args: str) -> str:
    string = string.replace(esc + esc, esc)
    
    for arg in args:
        
        string = string.replace(esc + arg, newEsc + arg)
    
    return string

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

        result += separator + value

    Loop.DoForEachAndFirst(values, firstAction, action)
    
    return result
def ConcatenateFromValues(*values: str, separator: str, selector: Callable[[str], str]) -> str:
    return ConcatenateFrom(values, separator, selector)

def Contains(value: str, subValue: str, start: int|None = None, end: int|None = None) -> bool:
    return value.find(subValue, start, end) >= 0
def ContainsR(value: str, subValue: str, start: int|None = None, end: int|None = None) -> bool:
    return value.rfind(subValue, start, end) >= 0

def Omit(value: str, subValue: str, start: int|None = None, end: int|None = None) -> bool:
    return value.find(subValue, start, end) < 0
def OmitR(value: str, subValue: str, start: int|None = None, end: int|None = None) -> bool:
    return value.rfind(subValue, start, end) < 0