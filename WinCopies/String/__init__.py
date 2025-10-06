from collections.abc import Iterable
from typing import Callable

def NullifyIfEmpty(value: str) -> str|None:
    """Converts an empty string to None.

    Args:
        value: The string to check.

    Returns:
        None if the string is empty, otherwise the original string.
    """
    return None if value == '' else value
def StringifyIfNone(value: str|None) -> str:
    """Converts None to an empty string.

    Args:
        value: The value to check.

    Returns:
        An empty string if value is None, otherwise the original string.
    """
    return '' if value == None else value

def IsNoneOrEmpty(value: str|None) -> bool:
    """Checks if a value is None or an empty string.

    Args:
        value: The value to check.

    Returns:
        True if the value is None or empty, False otherwise.
    """
    return value is None or value == ''

def Replace(string: str, esc: str, newEsc: str, args: Iterable[str]) -> str:
    """Replaces escape sequences in a string.

    Args:
        string: The string to process.
        esc: The current escape character.
        newEsc: The new escape character.
        args: The sequences to replace after the escape character.

    Returns:
        The string with replaced escape sequences.
    """
    string = string.replace(esc + esc, esc)

    for arg in args:
        string = string.replace(esc + arg, newEsc + arg)

    return string
def ReplaceValues(string: str, esc: str, newEsc: str, *args: str) -> str:
    """Replaces escape sequences in a string using variadic arguments.

    Args:
        string: The string to process.
        esc: The current escape character.
        newEsc: The new escape character.
        *args: The sequences to replace after the escape character.

    Returns:
        The string with replaced escape sequences.
    """
    return Replace(string, esc, newEsc, args)

def SurroundWith(prefix: str|None, string: str|None, suffix: str|None) -> str:
    """Surrounds a string with a prefix and suffix.

    Args:
        prefix: The prefix to add (None becomes empty string).
        string: The string to surround (None becomes empty string).
        suffix: The suffix to add (None becomes empty string).

    Returns:
        The concatenated string with prefix, string, and suffix.
    """
    return f"{StringifyIfNone(prefix)}{StringifyIfNone(string)}{StringifyIfNone(suffix)}"
def TrySurroundWith(prefix: str|None, string: str|None, suffix: str|None) -> str|None:
    """Tries to surround a string with a prefix and suffix.

    Args:
        prefix: The prefix to add.
        string: The string to surround.
        suffix: The suffix to add.

    Returns:
        None if string is None, otherwise the concatenated result.
    """
    return None if string is None else SurroundWith(prefix, string, suffix)

def Surround(string: str|None, value: str|None) -> str:
    """Surrounds a string with the same value on both sides.

    Args:
        string: The string to surround.
        value: The value to use as both prefix and suffix.

    Returns:
        The string surrounded by the specified value.
    """
    return SurroundWith(value, string, value)
def TrySurround(string: str|None, value: str|None) -> str|None:
    """Tries to surround a string with the same value on both sides.

    Args:
        string: The string to surround.
        value: The value to use as both prefix and suffix.

    Returns:
        None if string is None, otherwise the surrounded string.
    """
    return TrySurroundWith(value, string, value)

def SurroundWithSpace(prefix: str|None, suffix: str|None) -> str:
    """Surrounds a space with a prefix and suffix.

    Args:
        prefix: The prefix to add.
        suffix: The suffix to add.

    Returns:
        The space surrounded by the prefix and suffix.
    """
    return SurroundWith(prefix, ' ', suffix)
def TrySurroundWithSpace(prefix: str|None, suffix: str|None) -> str|None:
    """Tries to surround a space with a prefix and suffix.

    Args:
        prefix: The prefix to add.
        suffix: The suffix to add.

    Returns:
        The space surrounded by the prefix and suffix (never None since the space is literal).
    """
    return TrySurroundWith(prefix, ' ', suffix)

def QuoteSurround(string: str|None) -> str:
    """Surrounds a string with single quotes.

    Args:
        string: The string to surround.

    Returns:
        The string surrounded by single quotes.
    """
    return Surround(string, "'")
def TryQuoteSurround(string: str|None) -> str|None:
    """Tries to surround a string with single quotes.

    Args:
        string: The string to surround.

    Returns:
        None if string is None, otherwise the string surrounded by single quotes.
    """
    return TrySurround(string, "'")

def DoubleQuoteSurround(string: str|None) -> str:
    """Surrounds a string with double quotes.

    Args:
        string: The string to surround.

    Returns:
        The string surrounded by double quotes.
    """
    return Surround(string, '"')
def TryDoubleQuoteSurround(string: str|None) -> str|None:
    """Tries to surround a string with double quotes.

    Args:
        string: The string to surround.

    Returns:
        None if string is None, otherwise the string surrounded by double quotes.
    """
    return TrySurround(string, '"')

def SpaceJoin(values: Iterable[str]) -> str:
    """Joins strings with spaces.

    Args:
        values: The strings to join.

    Returns:
        The joined string with spaces as separators.
    """
    return ' '.join(values)
def SpaceJoinValues(*values: str) -> str:
    """Joins variadic strings with spaces.

    Args:
        *values: The strings to join.

    Returns:
        The joined string with spaces as separators.
    """
    return SpaceJoin(values)

def CommaJoin(values: Iterable[str]) -> str:
    """Joins strings with commas.

    Args:
        values: The strings to join.

    Returns:
        The joined string with commas as separators.
    """
    return ','.join(values)
def CommaJoinValues(*values: str) -> str:
    """Joins variadic strings with commas.

    Args:
        *values: The strings to join.

    Returns:
        The joined string with commas as separators.
    """
    return CommaJoin(values)

def SemicolonJoin(values: Iterable[str]) -> str:
    """Joins strings with semicolons.

    Args:
        values: The strings to join.

    Returns:
        The joined string with semicolons as separators.
    """
    return ';'.join(values)
def SemicolonJoinValues(*values: str) -> str:
    """Joins variadic strings with semicolons.

    Args:
        *values: The strings to join.

    Returns:
        The joined string with semicolons as separators.
    """
    return SemicolonJoin(values)

def ColonJoin(values: Iterable[str]) -> str:
    """Joins strings with colons.

    Args:
        values: The strings to join.

    Returns:
        The joined string with colons as separators.
    """
    return ':'.join(values)
def ColonJoinValues(*values: str) -> str:
    """Joins variadic strings with colons.

    Args:
        *values: The strings to join.

    Returns:
        The joined string with colons as separators.
    """
    return ColonJoin(values)

def Join(values: Iterable[str]) -> str:
    """Joins strings without separator.

    Args:
        values: The strings to join.

    Returns:
        The concatenated string.
    """
    return ''.join(values)
def JoinValues(*values: str) -> str:
    """Joins variadic strings without separator.

    Args:
        *values: The strings to join.

    Returns:
        The concatenated string.
    """
    return Join(values)

def Contains(value: str, subValue: str, start: int|None = None, end: int|None = None) -> bool:
    """Checks if a string contains a substring.

    Args:
        value: The string to search in.
        subValue: The substring to search for.
        start: Optional start index for the search.
        end: Optional end index for the search.

    Returns:
        True if the substring is found, False otherwise.
    """
    return value.find(subValue, start, end) >= 0
def ContainsR(value: str, subValue: str, start: int|None = None, end: int|None = None) -> bool:
    """Checks if a string contains a substring searching from the right.

    Args:
        value: The string to search in.
        subValue: The substring to search for.
        start: Optional start index for the search.
        end: Optional end index for the search.

    Returns:
        True if the substring is found, False otherwise.
    """
    return value.rfind(subValue, start, end) >= 0

def Omits(value: str, subValue: str, start: int|None = None, end: int|None = None) -> bool:
    """Checks if a string does not contain a substring.

    Args:
        value: The string to search in.
        subValue: The substring to search for.
        start: Optional start index for the search.
        end: Optional end index for the search.

    Returns:
        True if the substring is not found, False otherwise.
    """
    return value.find(subValue, start, end) < 0
def OmitsR(value: str, subValue: str, start: int|None = None, end: int|None = None) -> bool:
    """Checks if a string does not contain a substring searching from the right.

    Args:
        value: The string to search in.
        subValue: The substring to search for.
        start: Optional start index for the search.
        end: Optional end index for the search.

    Returns:
        True if the substring is not found, False otherwise.
    """
    return value.rfind(subValue, start, end) < 0

def TrySplitAt(value: str, i: int) -> list[str]|None:
    """Tries to split a string at a specific index.

    Args:
        value: The string to split.
        i: The index at which to split.

    Returns:
        None if the index is invalid, a list with the original string if index is 0,
        otherwise a list with two parts.
    """
    return None if i < 0 or len(value) <= i else ([value] if i == 0 else [value[0:i - 1], value[i:]])
def SplitAt(value: str, i: int) -> list[str]:
    """Splits a string at a specific index.

    Args:
        value: The string to split.
        i: The index at which to split.

    Returns:
        A list with the split parts.

    Raises:
        ValueError: If the index is out of range.
    """
    result: list[str]|None = TrySplitAt(value, i)

    if result is None:
        raise ValueError(f"Value out of range. Value length: {len(value)}; index: {i}.")

    return result

def __Split(value: str, find: str, func: Callable[[str, str], list[str]|None]) -> list[str]:
    result: list[str]|None = func(value, find)

    return [value] if result is None else result

def TrySplit(value: str, find: str) -> list[str]|None:
    """Tries to split a string at the first occurrence of a substring.

    Args:
        value: The string to split.
        find: The substring to find.

    Returns:
        None if the substring is not found, otherwise a list with the split parts.
    """
    return TrySplitAt(value, value.find(find))
def TrySplitFromLast(value: str, find: str) -> list[str]|None:
    """Tries to split a string at the last occurrence of a substring.

    Args:
        value: The string to split.
        find: The substring to find.

    Returns:
        None if the substring is not found, otherwise a list with the split parts.
    """
    return TrySplitAt(value, value.rfind(find))

def Split(value: str, find: str) -> list[str]:
    """Splits a string at the first occurrence of a substring.

    Args:
        value: The string to split.
        find: The substring to find.

    Returns:
        A list with the original string if not found, otherwise the split parts.
    """
    return __Split(value, find, TrySplit)
def SplitFromLast(value: str, find: str) -> list[str]:
    """Splits a string at the last occurrence of a substring.

    Args:
        value: The string to split.
        find: The substring to find.

    Returns:
        A list with the original string if not found, otherwise the split parts.
    """
    return __Split(value, find, TrySplitFromLast)

def __TryGet(value: str, find: str, i: int, func: Callable[[str, str], list[str]|None]) -> str|None:
    result: list[str]|None = func(value, find)
    
    return None if result is None else result[i]
def __TryGetKey(value: str, find: str, func: Callable[[str, str], list[str]|None]) -> str|None:
    return __TryGet(value, find, 0, func)
def __TryGetValue(value: str, find: str, func: Callable[[str, str], list[str]|None]) -> str|None:
    return __TryGet(value, find, 1, func)

def TryGetKey(value: str, find: str) -> str|None:
    """Tries to get the part before the first occurrence of a substring.

    Args:
        value: The string to search in.
        find: The substring to find.

    Returns:
        None if the substring is not found, otherwise the part before it.
    """
    return __TryGetKey(value, find, TrySplit)
def TryGetKeyFromLast(value: str, find: str) -> str|None:
    """Tries to get the part before the last occurrence of a substring.

    Args:
        value: The string to search in.
        find: The substring to find.

    Returns:
        None if the substring is not found, otherwise the part before it.
    """
    return __TryGetKey(value, find, TrySplitFromLast)

def TryGetValue(value: str, find: str) -> str|None:
    """Tries to get the part after the first occurrence of a substring.

    Args:
        value: The string to search in.
        find: The substring to find.

    Returns:
        None if the substring is not found, otherwise the part after it.
    """
    return __TryGetValue(value, find, TrySplit)
def TryGetValueFromLast(value: str, find: str) -> str|None:
    """Tries to get the part after the last occurrence of a substring.

    Args:
        value: The string to search in.
        find: The substring to find.

    Returns:
        None if the substring is not found, otherwise the part after it.
    """
    return __TryGetValue(value, find, TrySplitFromLast)

def __Get(value: str, find: str, func: Callable[[str, str], str|None]) -> str:
    result: str|None = func(value, find)

    return value if result is None else result

def GetKey(value: str, find: str) -> str:
    """Gets the part before the first occurrence of a substring.

    Args:
        value: The string to search in.
        find: The substring to find.

    Returns:
        The original string if not found, otherwise the part before the substring.
    """
    return __Get(value, find, TryGetKey)
def GetKeyFromLast(value: str, find: str) -> str:
    """Gets the part before the last occurrence of a substring.

    Args:
        value: The string to search in.
        find: The substring to find.

    Returns:
        The original string if not found, otherwise the part before the substring.
    """
    return __Get(value, find, TryGetKeyFromLast)

def GetValue(value: str, find: str) -> str:
    """Gets the part after the first occurrence of a substring.

    Args:
        value: The string to search in.
        find: The substring to find.

    Returns:
        The original string if not found, otherwise the part after the substring.
    """
    return __Get(value, find, TryGetValue)
def GetValueFromLast(value: str, find: str) -> str:
    """Gets the part after the last occurrence of a substring.

    Args:
        value: The string to search in.
        find: The substring to find.

    Returns:
        The original string if not found, otherwise the part after the substring.
    """
    return __Get(value, find, TryGetValueFromLast)

def TryRemoveFromStart(value: str, find: str) -> str|None:
    """Tries to remove a substring from the start of a string.

    Args:
        value: The string to process.
        find: The substring to remove.

    Returns:
        None if the string doesn't start with the substring, otherwise the string without the prefix.
    """
    if value.startswith(find):
        length: int = len(find)

        return value[length + 1:] if len(value) > length else ''

    return None
def TryRemoveFromEnd(value: str, find: str) -> str|None:
    """Tries to remove a substring from the end of a string.

    Args:
        value: The string to process.
        find: The substring to remove.

    Returns:
        None if the string doesn't end with the substring, otherwise the string without the suffix.
    """
    if value.endswith(find):
        length: int = len(find)

        return value[:-length] if len(value) > length else ''

    return None

def __RemoveFrom(value: str, find: str, func: Callable[[str, str], str|None]) -> str:
    result: str|None = func(value, find)

    return value if result is None else result

def RemoveFromStart(value: str, find: str) -> str:
    """Removes a substring from the start of a string.

    Args:
        value: The string to process.
        find: The substring to remove.

    Returns:
        The original string if it doesn't start with the substring, otherwise the string without the prefix.
    """
    return __RemoveFrom(value, find, TryRemoveFromStart)
    
def RemoveFromEnd(value: str, find: str) -> str:
    """Removes a substring from the end of a string.

    Args:
        value: The string to process.
        find: The substring to remove.

    Returns:
        The original string if it doesn't end with the substring, otherwise the string without the suffix.
    """
    return __RemoveFrom(value, find, TryRemoveFromEnd)

def Append(string: str, value: str) -> str:
    """Appends a value to the end of a string.

    Args:
        string: The original string.
        value: The value to append.

    Returns:
        The concatenated string.
    """
    return string + value
def Prepend(string: str, value: str) -> str:
    """Prepends a value to the start of a string.

    Args:
        string: The original string.
        value: The value to prepend.

    Returns:
        The concatenated string.
    """
    return Append(value, string)