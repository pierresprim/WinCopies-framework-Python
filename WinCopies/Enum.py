from typing import Type
from enum import Enum, Flag
from typing import Self as SelfType

from WinCopies.Assertion import EnsureEnum
from WinCopies.Collections import Generator
from WinCopies.Collections.Iteration import SelectWhereNotNone
from WinCopies.Delegates import Self
from WinCopies.String import CommaJoin
from WinCopies.Typing import IEnum, INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Predicate, Converter
from WinCopies.Typing.Pairing import IKeyValuePair, KeyValuePair
from WinCopies.Typing.Reflection import AreFromSameClass

class OrderedEnum(Enum):
    def __lt__(self, other: SelfType) -> bool:
        return self.value < other.value if AreFromSameClass(self, other) else NotImplemented
    
    def __le__(self, other: SelfType) -> bool:
        return self.value <= other.value if AreFromSameClass(self, other) else NotImplemented
    
    def __gt__(self, other: SelfType) -> bool:
        return self.value > other.value if AreFromSameClass(self, other) else NotImplemented
    
    def __ge__(self, other: SelfType) -> bool:
        return self.value >= other.value if AreFromSameClass(self, other) else NotImplemented

def __IsMemberOf[T](e: Type[Enum], obj: T, selector: Converter[Enum, T]) -> bool:
    return obj in [selector(o) for o in e]

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
    if not IsMemberOf(e, n):
        raise ValueError()

def IsValueOf(e: Type[Enum], v: int) -> bool:
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
def EnsureValueOf(e: Type[Enum], v: int) -> None:
    """Ensures a value exists in an enum.

    Args:
        e: The enum type to check against.
        v: The value to verify.

    Raises:
        AssertionError: If e is not an enum type.
        ValueError: If the value does not exist in the enum.
    """
    if not IsValueOf(e, v):
        raise ValueError()

def ToKeyValuePair(e: Enum) -> KeyValuePair[str, int]:
    """Converts an enum member to a key-value pair.

    Args:
        e: The enum member to convert.

    Returns:
        A KeyValuePair with the enum's name as key and value as value.
    """
    return KeyValuePair(e.name, e.value)

def ToKeyValuePairs(e: Type[Enum]) -> Generator[KeyValuePair[str, int]]:
    """Converts all members of an enum to key-value pairs.

    Args:
        e: The enum type to convert.

    Yields:
        KeyValuePair objects for each enum member.
    """
    for value in e:
        yield ToKeyValuePair(value)

def ToTuple(e: Enum) -> tuple[str, int]:
    """Converts an enum member to a tuple.

    Args:
        e: The enum member to convert.

    Returns:
        A tuple with the enum's name and value.
    """
    return (e.name, e.value)

def ToTuples(e: Type[Enum]) -> Generator[tuple[str, int]]:
    """Converts all members of an enum to tuples.

    Args:
        e: The enum type to convert.

    Yields:
        Tuples containing name and value for each enum member.
    """
    for value in e:
        yield ToTuple(value)

def IsIn(e: Type[Enum], t: tuple[str, int]|IKeyValuePair[str, int]) -> bool:
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

    if isinstance(t, tuple):
        return t in ToTuples(e)

    for item in ToKeyValuePairs(e):
        if t.GetKey() == item.GetKey() and t.GetValue() == item.GetValue():
            return True

    return False
def EnsureIn(e: Type[Enum], t: tuple[str, int]|IKeyValuePair[str, int]) -> None:
    """Ensures a tuple or key-value pair exists in an enum.

    Args:
        e: The enum type to check against.
        t: A tuple (name, value) or IKeyValuePair to verify.

    Raises:
        AssertionError: If e is not an enum type.
        ValueError: If the tuple or key-value pair does not exist in the enum.
    """
    if not IsIn(e, t):
        raise ValueError()

def __TryGetMember[TIn: Enum, TOut](e: Type[TIn], predicate: Predicate[TIn], selector: Converter[TIn, TOut]) -> TOut|None:
    for o in e:
        if predicate(o):
            return selector(o)
    
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

def TryGetName(e: Type[Enum], v: int) -> str|None:
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

def TryGetValue(e: Type[Enum], n: str) -> int|None:
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

def TryGetFieldFromValue[T: Enum](e: Type[T], v: int) -> T|None:
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

def HasFlag[T: Flag](e: T, v: T) -> bool:
    """Checks if a flag is set in a Flag enum.

    Args:
        e: The Flag enum to check.
        v: The flag value to check for.

    Returns:
        True if the flag is set, False otherwise.
    """
    return v in e
def EnsureHasFlag[T: Flag](e: T, v: T) -> None:
    """Ensures a flag is set in a Flag enum.

    Args:
        e: The Flag enum to check.
        v: The flag value to verify.

    Raises:
        ValueError: If the flag is not set in the enum.
    """
    if not HasFlag(e, v):
        raise ValueError(f"{v} is not in {e}.")

def EnumerateNames(t: Type[Enum]) -> Generator[str]:
    for item in t:
        yield item.name
def EnumerateValues(t: Type[Enum]) -> Generator[int]:
    for item in t:
        yield item.value

def EnumerateFieldNames(value: Flag) -> Generator[str]:
    return SelectWhereNotNone(value, lambda value: value.name)
def EnumerateFieldValues(value: Flag) -> Generator[int]:
    for item in value:
        yield item.value

def Print(value: Flag) -> str:
    return CommaJoin(EnumerateFieldNames(value))

def AsEnumValue(item: IEnum|Enum) -> Enum:
    return item.GetEnumValue() if isinstance(item, IEnum) else item

def AsUnderlyingEnumValue(item: IEnum|Enum) -> object:
    return AsEnumValue(item).value
def TryAsUnderlyingEnumValue(item: IEnum|Enum) -> int|None:
    value: object = AsUnderlyingEnumValue(item)

    return value if isinstance(value, int) else None

def AreEnumsEqual(x: IEnum|Enum, y: IEnum|Enum) -> bool:
    return AsEnumValue(x) == AsEnumValue(y)
def TryAreEnumsEqual(x: IEnum|Enum|None, y: IEnum|Enum|None) -> bool:
    return False if x is None or y is None else AreEnumsEqual(x, y)

def CompareEnums(x: IEnum|Enum, y: IEnum|Enum) -> INullable[bool|None]:
    def compare(x: int|None, y: int|None) -> INullable[bool|None]:
        def compare(x: int, y: int) -> bool|None:
            return None if x == y else y > x

        return (GetNullValue() if y is None else GetNullable(True)) if x is None else GetNullable(False if y is None else compare(x, y))
    
    return compare(TryAsUnderlyingEnumValue(x), TryAsUnderlyingEnumValue(y))
def TryCompare(x: IEnum|Enum|None, y: IEnum|Enum|None) -> INullable[bool|None]:
    return GetNullable(y is None) if x is None else (GetNullable(False) if y is None else CompareEnums(x, y))