from enum import Enum, Flag
from typing import cast, overload, Any, Callable, Type

from WinCopies.Assertion import EnsureEnum
from WinCopies.Collections import Generator
from WinCopies.Collections.Iteration import Select, SelectWhereNotNone, GetFirst, GetFirstItem, WhereSelect
from WinCopies.Delegates import Self
from WinCopies.Enum import ToTuple, ToKeyValuePairs
from WinCopies.String import CommaJoin, StringifyIfNone
from WinCopies.Typing.Delegate import Predicate, Converter
from WinCopies.Typing.Enum import Enum as _TypedEnum, StringEnum
from WinCopies.Typing.Pairing import IKeyValuePair

@overload
def IsMemberOf[T](e: Type[_TypedEnum[T]], n: str) -> bool: ...
@overload
def IsMemberOf(e: Type[Enum], n: str) -> bool: ...

def IsMemberOf[T](e: Type[_TypedEnum[T]|Enum], n: str) -> bool:
    """Checks if a name is a member of an enum.

    Args:
        e: The enum type to check against.
        n: The name to search for.

    Returns:
        True if the name exists in the enum, False otherwise.

    Raises:
        AssertionError: If e is not an enum type.
    """
    EnsureEnum(e)

    return n in EnumerateNames(e)
def EnsureMemberOf[T](e: Type[_TypedEnum[T]|Enum], n: str) -> None:
    """Ensures a name is a member of an enum.

    Args:
        e: The enum type to check against.
        n: The name to verify.

    Raises:
        AssertionError: If e is not an enum type.
        ValueError: If the name is not a member of the enum.
    """
    if not IsMemberOf(e, n): raise ValueError()

@overload
def IsValueOf[T](e: Type[_TypedEnum[T]], v: T) -> bool: ...
@overload
def IsValueOf(e: Type[Enum], v: Any) -> bool: ...

def IsValueOf[T](e: Type[_TypedEnum[T]|Enum], v: Any) -> bool:
    """Checks if a value exists in an enum.

    Args:
        e: The enum type to check against.
        v: The value to search for.

    Returns:
        True if the value exists in the enum, False otherwise.

    Raises:
        AssertionError: If e is not an enum type.
    """
    EnsureEnum(e)

    return v in EnumerateValues(e)
def EnsureValueOf[T](e: Type[_TypedEnum[T]|Enum], v: Any) -> None:
    """Ensures a value exists in an enum.

    Args:
        e: The enum type to check against.
        v: The value to verify.

    Raises:
        AssertionError: If e is not an enum type.
        ValueError: If the value does not exist in the enum.
    """
    if not IsValueOf(e, v): raise ValueError()

@overload
def ToTuples[T](e: Type[_TypedEnum[T]]) -> Generator[tuple[str, T]]: ...
@overload
def ToTuples(e: Type[Enum]) -> Generator[tuple[str, Any]]: ...

def ToTuples[T](e: Type[_TypedEnum[T]|Enum]) -> Generator[tuple[str, T|Any]]:
    """Converts all members of an enum to tuples.

    Args:
        e: The enum type to convert.

    Yields:
        Tuples containing name and value for each enum member.
    """
    return Select(e, ToTuple)

@overload
def IsIn[T](e: Type[_TypedEnum[T]], t: tuple[str, T]|IKeyValuePair[str, T]) -> bool: ...
@overload
def IsIn(e: Type[Enum], t: tuple[str, Any]|IKeyValuePair[str, Any]) -> bool: ...

def IsIn[T](e: Type[_TypedEnum[T]|Enum], t: tuple[str, T]|IKeyValuePair[str, T]) -> bool:
    """Checks if a tuple or key-value pair exists in an enum.

    Args:
        e: The enum type to check against.
        t: A tuple (name, value) or IKeyValuePair to search for.

    Returns:
        True if the tuple or key-value pair exists in the enum, False otherwise.

    Raises:
        AssertionError: If e is not an enum type.
    """
    EnsureEnum(e)

    if isinstance(t, tuple): return t in ToTuples(e)

    for item in ToKeyValuePairs(e):
        if t.GetKey() == item.GetKey() and t.GetValue() == item.GetValue(): return True

    return False

@overload
def EnsureIn[T](e: Type[_TypedEnum[T]], t: tuple[str, T]|IKeyValuePair[str, T]) -> None: ...
@overload
def EnsureIn(e: Type[Enum], t: tuple[str, Any]|IKeyValuePair[str, Any]) -> None: ...

def EnsureIn[T](e: Type[_TypedEnum[T]|Enum], t: tuple[str, T]|IKeyValuePair[str, T]) -> None:
    """Ensures a tuple or key-value pair exists in an enum.

    Args:
        e: The enum type to check against.
        t: A tuple (name, value) or IKeyValuePair to verify.

    Raises:
        AssertionError: If e is not an enum type.
        ValueError: If the tuple or key-value pair does not exist in the enum.
    """
    if not IsIn(e, t): raise ValueError()

@overload
def __TryGetMembers[TIn, TOut](e: Type[_TypedEnum[TIn]], predicate: Predicate[_TypedEnum[TIn]], selector: Converter[_TypedEnum[TIn], TOut]) -> Generator[TOut]: ...
@overload
def __TryGetMembers[TEnum: Enum, TOut](e: Type[TEnum], predicate: Predicate[TEnum], selector: Converter[TEnum, TOut]) -> Generator[TOut]: ...

def __TryGetMembers[TIn, TEnum: Enum, TOut](e: Type[_TypedEnum[TIn]|TEnum], predicate: Predicate[_TypedEnum[TIn]]|Predicate[TEnum], selector: Converter[_TypedEnum[TIn], TOut]|Converter[TEnum, TOut]) -> Generator[TOut]:
    return WhereSelect(cast(Generator[_TypedEnum[TIn]|TEnum], Enumerate(e)), cast(Predicate[_TypedEnum[TIn]|TEnum], predicate), cast(Converter[_TypedEnum[TIn]|TEnum, TOut], selector))

def TryGetMembers[TIn, TEnum: Enum, TOut](e: Type[_TypedEnum[TIn]|TEnum], predicate: Predicate[_TypedEnum[TIn]]|Predicate[TEnum], selector: Converter[_TypedEnum[TIn], TOut]|Converter[TEnum, TOut]) -> Generator[TOut]:
    EnsureEnum(e)

    return __TryGetMembers(e, cast(Predicate[_TypedEnum[TIn]|TEnum], predicate), cast(Converter[_TypedEnum[TIn]|TEnum, TOut], selector))

@overload
def __TryGetMember[TIn, TOut](e: Type[_TypedEnum[TIn]], predicate: Predicate[_TypedEnum[TIn]], selector: Converter[_TypedEnum[TIn], TOut]) -> TOut|None: ...
@overload
def __TryGetMember[TEnum: Enum, TOut](e: Type[TEnum], predicate: Predicate[TEnum], selector: Converter[TEnum, TOut]) -> TOut|None: ...

def __TryGetMember[TIn, TEnum: Enum, TOut](e: Type[_TypedEnum[TIn]|TEnum], predicate: Predicate[_TypedEnum[TIn]]|Predicate[TEnum], selector: Converter[_TypedEnum[TIn], TOut]|Converter[TEnum, TOut]) -> TOut|None:
    return GetFirst(__TryGetMembers(e, cast(Predicate[_TypedEnum[TIn]|TEnum], predicate), cast(Converter[_TypedEnum[TIn]|TEnum, TOut], selector))).TryGetValue()

@overload
def TryGetMember[TIn, TOut](e: Type[_TypedEnum[TIn]], predicate: Predicate[_TypedEnum[TIn]], selector: Converter[_TypedEnum[TIn], TOut]) -> TOut|None: ...
@overload
def TryGetMember[TIn: Enum, TOut](e: Type[TIn], predicate: Predicate[TIn], selector: Converter[TIn, TOut]) -> TOut|None: ...

def TryGetMember[TIn, TEnum: Enum, TOut](e: Type[_TypedEnum[TIn]|TEnum], predicate: Predicate[_TypedEnum[TIn]]|Predicate[TEnum], selector: Converter[_TypedEnum[TIn], TOut]|Converter[TEnum, TOut]) -> TOut|None:
    """Tries to get a member from an enum using a predicate and selector.

    Args:
        e: The enum type to search in.
        predicate: A function to filter enum members.
        selector: A function to convert the matching enum member to the desired type.

    Returns:
        The converted value if a matching member is found, None otherwise.

    Raises:
        AssertionError: If e is not an enum type.
    """
    EnsureEnum(e)

    return __TryGetMember(e, cast(Predicate[_TypedEnum[TIn]|TEnum], predicate), cast(Converter[_TypedEnum[TIn]|TEnum, TOut], selector))

def __TryGetFieldValue[TValue, TIn, TOut](e: Type[_TypedEnum[TValue]|Enum], obj: TIn, predicateSelector: Converter[_TypedEnum[TValue]|Enum, TIn], conversionSelector: Converter[_TypedEnum[TValue]|Enum, TOut]) -> TOut|None:
    return __TryGetMember(e, lambda o: predicateSelector(o) == obj, conversionSelector)

@overload
def TryGetName[T](e: Type[_TypedEnum[T]], v: T) -> str|None: ...
@overload
def TryGetName(e: Type[Enum], v: Any) -> str|None: ...

def TryGetName[T](e: Type[_TypedEnum[T]|Enum], v: T|Any) -> str|None:
    """Tries to get the name of an enum member by its value.

    Args:
        e: The enum type to search in.
        v: The value to search for.

    Returns:
        The name of the enum member if found, None otherwise.

    Raises:
        AssertionError: If e is not an enum type.
    """
    EnsureEnum(e)

    return __TryGetFieldValue(e, v, lambda o: o.value, lambda o: o.name)

@overload
def TryGetValue[T](e: Type[_TypedEnum[T]], n: str) -> T|None: ...
@overload
def TryGetValue(e: Type[Enum], n: str) -> Any|None: ...

def TryGetValue[T](e: Type[_TypedEnum[T]|Enum], n: str) -> T|Any|None:
    """Tries to get the value of an enum member by its name.

    Args:
        e: The enum type to search in.
        n: The name to search for.

    Returns:
        The value of the enum member if found, None otherwise.

    Raises:
        AssertionError: If e is not an enum type.
    """
    EnsureEnum(e)

    return __TryGetFieldValue(e, n, lambda o: o.name, lambda o: o.value)

def __TryGetField[T: Enum](e: Type[T], predicate: Predicate[T]) -> T|None:
    return __TryGetMember(e, predicate, Self)

def TryGetField[T: Enum](e: Type[T], predicate: Predicate[T]) -> T|None:
    """Tries to get an enum field using a predicate.

    Args:
        e: The enum type to search in.
        predicate: A function to filter enum members.

    Returns:
        The matching enum member if found, None otherwise.

    Raises:
        AssertionError: If e is not an enum type.
    """
    EnsureEnum(e)

    return __TryGetField(e, predicate)

def TryGetFieldFromName[T: Enum](e: Type[T], n: str) -> T|None:
    """Tries to get an enum field by its name.

    Args:
        e: The enum type to search in.
        n: The name to search for.

    Returns:
        The enum member if found, None otherwise.

    Raises:
        AssertionError: If e is not an enum type.
    """
    EnsureEnum(e)

    return __TryGetField(e, lambda o: o.name == n)

@overload
def TryGetFieldFromValue[TEnum: Enum, TValue](e: Type[TEnum], v: TValue) -> TEnum|None: ... # pyright: ignore[reportInvalidTypeVarUse]
@overload
def TryGetFieldFromValue[T: Enum](e: Type[T], v: Any) -> T|None: ...

def TryGetFieldFromValue[TEnum: Enum, TValue](e: Type[TEnum], v: TValue|Any) -> TEnum|None: # pyright: ignore[reportInvalidTypeVarUse]
    """Tries to get an enum field by its value.

    Args:
        e: The enum type to search in.
        v: The value to search for.

    Returns:
        The enum member if found, None otherwise.

    Raises:
        AssertionError: If e is not an enum type.
    """
    EnsureEnum(e)

    return __TryGetField(e, lambda o: o.value == v)

def TryGetValueFromName(e: Type[StringEnum], n: str) -> str:
    return StringifyIfNone(TryGetFieldFromName(e, n))
def TryGetValueFromValue(e: Type[StringEnum], v: str) -> str:
    return StringifyIfNone(TryGetFieldFromValue(e, v))

def EnumerateNames[T](t: Type[_TypedEnum[T]|Enum]) -> Generator[str]:
    return Select(t, lambda item: item.name)

@overload
def EnumerateValues[T](t: Type[_TypedEnum[T]]) -> Generator[T]: ...
@overload
def EnumerateValues(t: Type[Enum]) -> Generator[Any]: ...

def EnumerateValues[T](t: Type[_TypedEnum[T]|Enum]) -> Generator[T|Any]:
    return Select(t, lambda item: item.value)

def EnumerateFieldNames(value: Flag) -> Generator[str]:
    return SelectWhereNotNone(value, lambda item: item.name)
def EnumerateFieldValues(value: Flag) -> Generator[int]:
    return Select(value, lambda item: item.value)

@overload
def Enumerate[TValue](t: Type[_TypedEnum[TValue]]) -> Generator[_TypedEnum[TValue]]: ...
@overload
def Enumerate[TEnum: Enum](t: Type[TEnum]) -> Generator[TEnum]: ...

def Enumerate[TValue, TEnum: Enum](t: Type[_TypedEnum[TValue]|TEnum]) -> Generator[_TypedEnum[TValue]|TEnum]:
    yield from t

def Print(value: Flag) -> str: return CommaJoin(EnumerateFieldNames(value))

def TryConvertFromString[T: Enum](t: Type[T], value: str, predicate: Callable[[str|None, str], bool]|None = None) -> T|None:
    def getPredicate() -> Predicate[str|None]:
        def __predicate(name: str|None) -> bool: return name is not None and name == value
        
        _predicate: Callable[[str|None, str], bool]|None = predicate
        
        return __predicate if _predicate is None else lambda name: _predicate(name, value)
    
    _predicate: Predicate[str|None] = getPredicate()

    return GetFirstItem(t, lambda item: _predicate(item.name)).TryGetValue()