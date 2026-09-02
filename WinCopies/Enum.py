from collections.abc import Iterable
from enum import Enum, Flag
from typing import overload, Any, Callable, Type

from WinCopies.Assertion import EnsureEnum
from WinCopies.Collections import Generator
from WinCopies.Collections.Iteration import Select, SelectWhereNotNone, GetFirstItem
from WinCopies.Delegates import Self
from WinCopies.String import CommaJoin
from WinCopies.Typing import IEnumBase, IEnum, INullable, GetNullable, GetNullableValue
from WinCopies.Typing.Delegate import Predicate, Converter
from WinCopies.Typing.Enum import IntegerEnum, StringEnum
from WinCopies.Typing.Pairing import IKeyValuePair, KeyValuePair

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

def ToKeyValuePair(e: Enum) -> KeyValuePair[str, Any]:
    """Converts an enum member to a key-value pair.

    Args:
        e: The enum member to convert.

    Returns:
        A KeyValuePair with the enum's name as key and value as value.
    """
    return KeyValuePair(e.name, e.value)

def ToKeyValuePairs(e: Type[Enum]) -> Generator[KeyValuePair[str, Any]]:
    """Converts all members of an enum to key-value pairs.

    Args:
        e: The enum type to convert.

    Yields:
        KeyValuePair objects for each enum member.
    """
    for value in e: yield ToKeyValuePair(value)

def ToTuple(e: Enum) -> tuple[str, Any]:
    """Converts an enum member to a tuple.

    Args:
        e: The enum member to convert.

    Returns:
        A tuple with the enum's name and value.
    """
    return (e.name, e.value)

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

def StringifyIfNone(e: StringEnum|None) -> str:
    return '' if e is None else (e if isinstance(e, str) else e.value)

def TryGetValueFromName(e: Type[StringEnum], n: str) -> str:
    return StringifyIfNone(TryGetFieldFromName(e, n))
def TryGetValueFromValue(e: Type[StringEnum], v: str) -> str:
    return StringifyIfNone(TryGetFieldFromValue(e, v))

def EnumerateFlags[T: Flag](e: T) -> Iterable[T]:
    yield from e

def HasFlag[T: Flag](e: T, v: T) -> bool:
    """Checks if a flag is set in a Flag enum.

    Args:
        e: The Flag enum to check.
        v: The flag value to check for.

    Returns:
        True if the flag is set, False otherwise.
    """
    return v in EnumerateFlags(e)
def EnsureHasFlag[T: Flag](e: T, v: T) -> None:
    """Ensures a flag is set in a Flag enum.

    Args:
        e: The Flag enum to check.
        v: The flag value to verify.

    Raises:
        ValueError: If the flag is not set in the enum.
    """
    if not HasFlag(e, v): raise ValueError(f"{v} is not in {e}.")

def AddFlag[T: Flag](e: T, v: T) -> T:
    return e | v
def RemoveFlag[T: Flag](e: T, v: T) -> T:
    return e & ~v

def __GetNormalizedFlag(value: int) -> int:
    return value & (value - 1)

def HasMultipleFlags(e: Flag) -> bool|None:
    value: int = e.value

    return None if value == 0 else __GetNormalizedFlag(value) != 0
def EnsureMultipleFlags(e: Flag) -> None:
    if HasMultipleFlags(e) is not True: raise ValueError(f"Multiple values were expected; got {e}.")

def HasOnlyOneFlag(e: Flag) -> bool|None:
    value: int = e.value

    return None if value == 0 else __GetNormalizedFlag(value) == 0
def EnsureOnlyOneFlag(e: Flag) -> None:
    if HasMultipleFlags(e) is True: raise ValueError(f"Only one value was expected; got {e}.")

def HasOneAndOnlyOneFlag(e: Flag) -> bool:
    return HasOnlyOneFlag(e) is True
def EnsureOneAndOnlyOneFlag(e: Flag) -> None:
    if not HasOneAndOnlyOneFlag(e): raise ValueError(f"One and only one value was expected; got {e}.")

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

@overload
def AsEnumValue[T: IntegerEnum](item: IEnum[T]|IntegerEnum) -> IntegerEnum: ...
@overload
def AsEnumValue[T: StringEnum](item: IEnum[T]|StringEnum) -> StringEnum: ...
@overload
def AsEnumValue(item: IEnumBase|Enum) -> Enum: ...

def AsEnumValue[T: IntegerEnum|StringEnum|Enum](item: IEnum[T]|IEnumBase|IntegerEnum|StringEnum|Enum) -> IntegerEnum|StringEnum|Enum: return item.GetEnumValue() if isinstance(item, IEnumBase) else item

def AsUnderlyingEnumValue(item: IEnumBase|Enum) -> Any: return AsEnumValue(item).value

def AreEnumsEqual(x: IEnumBase|Enum, y: IEnumBase|Enum) -> bool: return AsEnumValue(x) == AsEnumValue(y)
def TryAreEnumsEqual(x: IEnumBase|Enum|None, y: IEnumBase|Enum|None) -> bool: return False if x is None or y is None else AreEnumsEqual(x, y)

def CompareEnums(x: IEnum[IntegerEnum]|IntegerEnum, y: IEnum[IntegerEnum]|IntegerEnum) -> bool|None:
    def compare(x: int, y: int) -> bool|None:
        return None if x == y else y > x
    
    return compare(AsUnderlyingEnumValue(x), AsUnderlyingEnumValue(y))
def TryCompare(x: IEnum[IntegerEnum]|IntegerEnum|None, y: IEnum[IntegerEnum]|IntegerEnum|None) -> INullable[bool|None]:
    return GetNullable(y is None) if x is None else (GetNullable(False) if y is None else GetNullableValue(CompareEnums(x, y)))

def TryConvertFromString[T: Enum](t: Type[T], value: str, predicate: Callable[[str|None, str], bool]|None = None) -> T|None:
    def getPredicate() -> Predicate[str|None]:
        def __predicate(name: str|None) -> bool: return name is not None and name == value
        
        _predicate: Callable[[str|None, str], bool]|None = predicate
        
        return __predicate if _predicate is None else lambda name: _predicate(name, value)
    
    _predicate: Predicate[str|None] = getPredicate()

    return GetFirstItem(t, lambda item: _predicate(item.name)).TryGetValue()