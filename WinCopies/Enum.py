from typing import Type
from enum import Enum

from WinCopies.Assertion import EnsureSubclass, EnsureEnum
from WinCopies.Delegates import Self
from WinCopies.Typing.Delegate import Predicate, Converter

def __IsMemberOf[T](e: Type[Enum], obj: T, selector: Converter[Enum, T]) -> bool:
    return obj in [selector(o) for o in e]

def IsMemberOf(e: Type[Enum], n: str) -> bool:
    EnsureEnum(e)

    return __IsMemberOf(e, n, lambda o: o.name)

def IsValueOf(e: Type[Enum], v: int) -> bool:
    EnsureEnum(e)

    return __IsMemberOf(e, v, lambda o: o.value)

def IsFieldOf(e: Type[Enum], f: Enum) -> bool:
    def assertTypes():
        t: Type = type(f)

        EnsureEnum(t)
        EnsureSubclass(e, t)
    
    assertTypes()

    return f in e

def IsIn(e: Type[Enum], t: tuple[str, int]) -> bool:
    EnsureEnum(e)

    return t in [(o.name, o.value) for o in e]

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