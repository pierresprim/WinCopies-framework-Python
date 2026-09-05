from enum import Enum, Flag
from typing import overload, Any, Type

from WinCopies.Collections import Generator
from WinCopies.Typing import IEnumBase, IEnum, INullable, GetNullable, GetNullableValue
from WinCopies.Typing.Enum import IntegerEnum, StringEnum
from WinCopies.Typing.Pairing import IKeyValuePair, KeyValuePair

def ToKeyValuePair(e: Enum) -> IKeyValuePair[str, Any]:
    """Converts an enum member to a key-value pair.

    Args:
        e: The enum member to convert.

    Returns:
        A KeyValuePair with the enum's name as key and value as value.
    """
    return KeyValuePair(e.name, e.value)

def ToKeyValuePairs(e: Type[Enum]) -> Generator[IKeyValuePair[str, Any]]:
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

def StringifyIfNone(e: StringEnum|None) -> str:
    return '' if e is None else (e if isinstance(e, str) else e.value)

def EnumerateFlags[T: Flag](e: T) -> Generator[T]:
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