from typing import Type
from enum import Enum

from WinCopies.Delegates import Self

def Assert(e: Type[Enum]):
    assert(issubclass(e, Enum))

def __IsMemberOf(e: Type[Enum], obj: object, selector: callable) -> bool:
    return obj in [selector(o) for o in e]

def IsMemberOf(e: Type[Enum], n: str) -> bool:
    Assert(e)

    return __IsMemberOf(e, n, lambda o: o.name)

def IsValueOf(e: Type[Enum], v: int) -> bool:
    Assert(e)

    return __IsMemberOf(e, v, lambda o: o.value)

def IsFieldOf(e: Type[Enum], f: Enum) -> bool:
    def assertTypes():
        nonlocal e
        nonlocal f

        t: Type = type(f)

        Assert(t)
        assert(issubclass(e, t))
    
    assertTypes()

    return f in e

def IsIn(e: Type[Enum], t: tuple[str, int]) -> bool:
    Assert(e)

    return t in [(o.name, o.value) for o in e]

def __TryGetMember(e: Type[Enum], predicate: callable, selector: callable) -> object|None:
    for o in e:
        if predicate(o):
            return selector(o)
    
    return None

def TryGetMember(e: Type[Enum], predicate: callable, selector: callable) -> object|None:
    Assert(e)
    
    return __TryGetMember(e, predicate, selector)

def __TryGetFieldValue(e: Type[Enum], obj: object, predicateSelector: callable, conversionSelector: callable) -> object|None:
    return __TryGetMember(e, lambda o: predicateSelector(o) == obj, conversionSelector)

def TryGetName(e: Type[Enum], v: int) -> str|None:
    Assert(e)
    
    return __TryGetFieldValue(e, v, lambda o: o.value, lambda o: o.name)

def TryGetValue(e: Type[Enum], n: str) -> int|None:
    Assert(e)
    
    return __TryGetFieldValue(e, n, lambda o: o.name, lambda o: o.value)

def __TryGetField[T: Enum](e: Type[T], predicate: callable) -> T|None:
    return __TryGetMember(e, predicate, Self)

def TryGetField[T: Enum](e: Type[T], predicate: callable) -> T|None:
    Assert(e)

    return __TryGetField(e, predicate)

def TryGetFieldFromName[T: Enum](e: Type[T], n: str) -> T|None:
    Assert(e)
    
    return __TryGetField(e, lambda o: o.name == n)

def TryGetFieldFromValue[T: Enum](e: Type[T], v: int) -> T|None:
    Assert(e)
    
    return __TryGetField(e, lambda o: o.value == v)