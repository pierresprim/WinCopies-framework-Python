from collections.abc import Iterable
from typing import Type
from enum import Enum

from WinCopies.Assertion import EnsureSubclass, EnsureEnum
from WinCopies.Delegates import Self
from WinCopies.Typing.Delegate import Predicate, Converter
from WinCopies.Typing.Pairing import IKeyValuePair, KeyValuePair

def __IsMemberOf[T](e: Type[Enum], obj: T, selector: Converter[Enum, T]) -> bool:
    return obj in [selector(o) for o in e]

def IsMemberOf(e: Type[Enum], n: str) -> bool:
    EnsureEnum(e)

    return __IsMemberOf(e, n, lambda o: o.name)
def EnsureMemberOf(e: Type[Enum], n: str) -> None:
    if not IsMemberOf(e, n):
        raise ValueError()

def IsValueOf(e: Type[Enum], v: int) -> bool:
    EnsureEnum(e)

    return __IsMemberOf(e, v, lambda o: o.value)
def EnsureValueOf(e: Type[Enum], v: int) -> None:
    if not IsValueOf(e, v):
        raise ValueError()

def IsFieldOf(e: Type[Enum], f: Enum) -> bool:
    def ensureTypes() -> None:
        nonlocal e
        nonlocal f

        t: Type = type(f)

        EnsureEnum(t)
        EnsureSubclass(e, t)
    
    ensureTypes()

    return f in e
def EnsureFieldOf(e: Type[Enum], f: Enum) -> None:
    if not IsFieldOf(e, f):
        raise ValueError

def AsKeyValuePair(e: Enum) -> KeyValuePair[str, int]:
    return KeyValuePair(e.name, e.value)

def AsKeyValuePairs(e: Type[Enum]) -> Iterable[KeyValuePair[str, int]]:
    for value in e:
        yield AsKeyValuePair(value)

def AsTuple(e: Enum) -> tuple[str, int]:
    return (e.name, e.value)

def AsTuples(e: Type[Enum]) -> Iterable[tuple[str, int]]:
    for value in e:
        yield AsTuple(value)

def IsIn(e: Type[Enum], t: tuple[str, int]|IKeyValuePair[str, int]) -> bool:
    EnsureEnum(e)

    if isinstance(t, tuple):
        return t in AsTuples(e)
    
    for item in AsKeyValuePairs(e):
        if t.GetKey() == item.GetKey() and t.GetValue() == item.GetValue():
            return True
    
    return False
def EnsureIn(e: Type[Enum], t: tuple[str, int]|IKeyValuePair[str, int]) -> None:
    if not IsIn(e, t):
        raise ValueError()

def __TryGetMember[T](e: Type[Enum], predicate: Predicate[Enum], selector: Converter[Enum, T]) -> T|None:
    for o in e:
        if predicate(o):
            return selector(o)
    
    return None

def TryGetMember[T](e: Type[Enum], predicate: Predicate[Enum], selector: Converter[Enum, T]) -> T|None:
    EnsureEnum(e)
    
    return __TryGetMember(e, predicate, selector)

def __TryGetFieldValue[T](e: Type[Enum], obj: T, predicateSelector: Predicate[Enum], conversionSelector: Converter[Enum, T]) -> T|None:
    return __TryGetMember(e, lambda o: predicateSelector(o) == obj, conversionSelector)

def TryGetName(e: Type[Enum], v: int) -> str|None:
    EnsureEnum(e)
    
    return __TryGetFieldValue(e, v, lambda o: o.value, lambda o: o.name)

def TryGetValue(e: Type[Enum], n: str) -> int|None:
    EnsureEnum(e)
    
    return __TryGetFieldValue(e, n, lambda o: o.name, lambda o: o.value)

def __TryGetField[T: Enum](e: Type[T], predicate: Predicate[Enum]) -> T|None:
    return __TryGetMember(e, predicate, Self)

def TryGetField[T: Enum](e: Type[T], predicate: Predicate[Enum]) -> T|None:
    EnsureEnum(e)

    return __TryGetField(e, predicate)

def TryGetFieldFromName[T: Enum](e: Type[T], n: str) -> T|None:
    EnsureEnum(e)
    
    return __TryGetField(e, lambda o: o.name == n)

def TryGetFieldFromValue[T: Enum](e: Type[T], v: int) -> T|None:
    EnsureEnum(e)
    
    return __TryGetField(e, lambda o: o.value == v)