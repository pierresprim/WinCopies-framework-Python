from typing import Type
from enum import Enum

from WinCopies.Delegates import Self

def AssertEnum(e: Type[Enum]):
    assert(issubclass(e, Enum))

def __IsMemberOfEnum(e: Type[Enum], obj: object, selector: callable) -> bool:
    return obj in [selector(o) for o in e]

def IsMemberOfEnum(e: Type[Enum], n: str) -> bool:
    AssertEnum(e)

    return __IsMemberOfEnum(e, n, lambda o: o.name)

def IsValueOfEnum(e: Type[Enum], v: int) -> bool:
    AssertEnum(e)

    return __IsMemberOfEnum(e, v, lambda o: o.value)

def IsFieldOfEnum(e: Type[Enum], f: Enum) -> bool:
    def assertTypes():
        nonlocal e
        nonlocal f

        t: Type = type(f)

        AssertEnum(t)
        assert(issubclass(e, t))
    
    assertTypes()

    return f in e

def IsInEnum(e: Type[Enum], t: tuple[str, int]) -> bool:
    AssertEnum(e)

    return t in [(o.name, o.value) for o in e]

def __TryGetEnumMember(e: Type[Enum], predicate: callable, selector: callable) -> object|None:
    for o in e:
        if predicate(o):
            return selector(o)
    
    return None

def TryGetEnumMember(e: Type[Enum], predicate: callable, selector: callable) -> object|None:
    AssertEnum(e)
    
    return __TryGetEnumMember(e, predicate, selector)

def __TryGetEnumFieldValue(e: Type[Enum], obj: object, predicateSelector: callable, conversionSelector: callable) -> object|None:
    return __TryGetEnumMember(e, lambda o: predicateSelector(o) == obj, conversionSelector)

def TryGetEnumName(e: Type[Enum], v: int) -> str|None:
    AssertEnum(e)
    
    return __TryGetEnumFieldValue(e, v, lambda o: o.value, lambda o: o.name)

def TryGetEnumValue(e: Type[Enum], n: str) -> int|None:
    AssertEnum(e)
    
    return __TryGetEnumFieldValue(e, n, lambda o: o.name, lambda o: o.value)

def __TryGetEnumField[T: Enum](e: Type[T], predicate: callable) -> T|None:
    return __TryGetEnumMember(e, predicate, Self)

def TryGetEnumField[T: Enum](e: Type[T], predicate: callable) -> T|None:
    AssertEnum(e)

    return __TryGetEnumField(e, predicate)

def TryGetEnumFieldFromName[T: Enum](e: Type[T], n: str) -> T|None:
    AssertEnum(e)
    
    return __TryGetEnumField(e, lambda o: o.name == n)

def TryGetEnumFieldFromValue[T: Enum](e: Type[T], v: int) -> T|None:
    AssertEnum(e)
    
    return __TryGetEnumField(e, lambda o: o.value == v)