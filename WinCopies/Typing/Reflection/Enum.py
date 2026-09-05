from enum import Enum, Flag
from typing import Any, Callable, Type

from WinCopies.Assertion import EnsureEnum
from WinCopies.Collections import Generator
from WinCopies.Collections.Iteration import Select, SelectWhereNotNone, GetFirstItem
from WinCopies.Delegates import Self
from WinCopies.Enum import ToTuple, ToKeyValuePairs
from WinCopies.String import CommaJoin, StringifyIfNone
from WinCopies.Typing.Delegate import Predicate, Converter
from WinCopies.Typing.Enum import StringEnum
from WinCopies.Typing.Pairing import IKeyValuePair

def __IsMemberOf[T](e: Type[Enum], obj: T, selector: Converter[Enum, T]) -> bool:
    return obj in Select(e, selector)

def IsMemberOf(e: Type[Enum], n: str) -> bool:
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

    return __IsMemberOf(e, n, lambda o: o.name)
def EnsureMemberOf(e: Type[Enum], n: str) -> None:
    """Ensures a name is a member of an enum.

    Args:
        e: The enum type to check against.
        n: The name to verify.

    Raises:
        AssertionError: If e is not an enum type.
        ValueError: If the name is not a member of the enum.
    """
    if not IsMemberOf(e, n): raise ValueError()

def IsValueOf(e: Type[Enum], v: Any) -> bool:
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

    return __IsMemberOf(e, v, lambda o: o.value)
def EnsureValueOf(e: Type[Enum], v: Any) -> None:
    """Ensures a value exists in an enum.

    Args:
        e: The enum type to check against.
        v: The value to verify.

    Raises:
        AssertionError: If e is not an enum type.
        ValueError: If the value does not exist in the enum.
    """
    if not IsValueOf(e, v): raise ValueError()

def ToTuples(e: Type[Enum]) -> Generator[tuple[str, Any]]:
    """Converts all members of an enum to tuples.

    Args:
        e: The enum type to convert.

    Yields:
        Tuples containing name and value for each enum member.
    """
    for value in e: yield ToTuple(value)

def IsIn(e: Type[Enum], t: tuple[str, Any]|IKeyValuePair[str, Any]) -> bool:
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
def EnsureIn(e: Type[Enum], t: tuple[str, Any]|IKeyValuePair[str, Any]) -> None:
    """Ensures a tuple or key-value pair exists in an enum.

    Args:
        e: The enum type to check against.
        t: A tuple (name, value) or IKeyValuePair to verify.

    Raises:
        AssertionError: If e is not an enum type.
        ValueError: If the tuple or key-value pair does not exist in the enum.
    """
    if not IsIn(e, t): raise ValueError()

def __TryGetMember[TIn: Enum, TOut](e: Type[TIn], predicate: Predicate[TIn], selector: Converter[TIn, TOut]) -> TOut|None:
    for o in e:
        if predicate(o): return selector(o)
    
    return None

def TryGetMember[T](e: Type[Enum], predicate: Predicate[Enum], selector: Converter[Enum, T]) -> T|None:
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

    return __TryGetMember(e, predicate, selector)

def __TryGetFieldValue[TIn, TOut](e: Type[Enum], obj: TIn, predicateSelector: Converter[Enum, TIn], conversionSelector: Converter[Enum, TOut]) -> TOut|None:
    return __TryGetMember(e, lambda o: predicateSelector(o) == obj, conversionSelector)

def TryGetName(e: Type[Enum], v: Any) -> str|None:
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

def TryGetValue(e: Type[Enum], n: str) -> Any|None:
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

def __TryGetField[T: Enum](e: Type[T], predicate: Predicate[Enum]) -> T|None:
    return __TryGetMember(e, predicate, Self)

def TryGetField[T: Enum](e: Type[T], predicate: Predicate[Enum]) -> T|None:
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
def TryGetFieldFromValue[T: Enum](e: Type[T], v: Any) -> T|None:
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

def EnumerateNames(t: Type[Enum]) -> Generator[str]:
    return Select(t, lambda item: item.name)
def EnumerateValues(t: Type[Enum]) -> Generator[Any]:
    return Select(t, lambda item: item.value)

def EnumerateFieldNames(value: Flag) -> Generator[str]:
    return SelectWhereNotNone(value, lambda value: value.name)
def EnumerateFieldValues(value: Flag) -> Generator[int]:
    return Select(value, lambda item: item.value)

def Enumerate[T: Enum](t: Type[T]) -> Generator[T]:
    return Select(t, lambda value: value)

def Print(value: Flag) -> str: return CommaJoin(EnumerateFieldNames(value))

def TryConvertFromString[T: Enum](t: Type[T], value: str, predicate: Callable[[str|None, str], bool]|None = None) -> T|None:
    def getPredicate() -> Predicate[str|None]:
        def __predicate(name: str|None) -> bool: return name is not None and name == value
        
        _predicate: Callable[[str|None, str], bool]|None = predicate
        
        return __predicate if _predicate is None else lambda name: _predicate(name, value)
    
    _predicate: Predicate[str|None] = getPredicate()

    return GetFirstItem(t, lambda item: _predicate(item.name)).TryGetValue()