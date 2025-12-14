from collections.abc import Iterable, Iterator

from WinCopies import NullableBoolean
from WinCopies.Collections import Enumeration, Generator, IterationResult
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator
from WinCopies.Collections.Enumeration.Selection import ExcluerEnumerator, ExcluerUntilEnumerator
from WinCopies.Delegates import GetNotPredicate
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Converter, Predicate, Selector

def TryEnumerate[T](iterable: Iterable[T]|None) -> Iterable[T]:
    """Returns the given iterable, or an empty generator if None is given.

    Args:
        iterable: The iterable to check.

    Returns:
        The original iterable if not None, otherwise an empty generator.
    """
    def getEmptyGenerator(*values: T) -> Generator[T]:
        yield from values

    return getEmptyGenerator() if iterable is None else iterable

def Concatenate[T](collection: Iterable[Iterable[T]|None]|None) -> Generator[T]:
    """Concatenates multiple iterables into a single generator.

    Args:
        collection: A collection of iterables to concatenate.

    Yields:
        Items from all iterables in the collection.
    """
    for iterable in TryEnumerate(collection):
        for item in TryEnumerate(iterable):
            yield item

def Append[T](items: Iterable[T]|None, values: Iterable[T]|None) -> Generator[T]:
    """Appends values to the end of items.

    Args:
        items: The initial items.
        values: The values to append.

    Yields:
        All items followed by all values.
    """
    for item in TryEnumerate(items):
        yield item

    for value in TryEnumerate(values):
        yield value
def AppendItem[T](items: Iterable[T]|None, value: T) -> Generator[T]:
    """Appends a single item to the end of items.

    Args:
        items: The initial items.
        value: The item to append.

    Yields:
        All items followed by the value.
    """
    for item in TryEnumerate(items):
        yield item

    yield value
def AppendValues[T](items: Iterable[T]|None, *values: T) -> Generator[T]:
    """Appends variadic values to the end of items.

    Args:
        items: The initial items.
        *values: The values to append.

    Yields:
        All items followed by all values.
    """
    return Append(items, values)

def Prepend[T](items: Iterable[T]|None, values: Iterable[T]|None) -> Generator[T]:
    """Prepends values to the beginning of items.

    Args:
        items: The initial items.
        values: The values to prepend.

    Yields:
        All values followed by all items.
    """
    return Append(values, items)
def PrependItem[T](items: Iterable[T]|None, value: T) -> Generator[T]:
    """Prepends a single item to the beginning of items.

    Args:
        items: The initial items.
        value: The item to prepend.

    Yields:
        The value followed by all items.
    """
    yield value

    for item in TryEnumerate(items):
        yield item
def PrependValues[T](items: Iterable[T]|None, *values: T) -> Generator[T]:
    """Prepends variadic values to the beginning of items.

    Args:
        items: The initial items.
        *values: The values to prepend.

    Yields:
        All values followed by all items.
    """
    return Prepend(items, values)

def AppendTo[T](items: Iterable[T]|None, values: Iterable[T]|None) -> Generator[T]:
    """Appends values after each item.

    Args:
        items: The initial items.
        values: The values to append after each item.

    Yields:
        Each item followed by all values.
    """
    for item in TryEnumerate(items):
        yield item

        for value in TryEnumerate(values):
            yield value
def AppendValuesTo[T](items: Iterable[T]|None, *values: T) -> Generator[T]:
    """Appends variadic values after each item.

    Args:
        items: The initial items.
        *values: The values to append after each item.

    Yields:
        Each item followed by all values.
    """
    return AppendTo(items, values)

def PrependTo[T](items: Iterable[T]|None, values: Iterable[T]|None) -> Generator[T]:
    """Prepends values before each item.

    Args:
        items: The initial items.
        values: The values to prepend before each item.

    Yields:
        All values followed by each item.
    """
    for item in TryEnumerate(items):
        for value in TryEnumerate(values):
            yield value

        yield item
def PrependValuesTo[T](items: Iterable[T]|None, *values: T) -> Generator[T]:
    """Prepends variadic values before each item.

    Args:
        items: The initial items.
        *values: The values to prepend before each item.

    Yields:
        All values followed by each item.
    """
    return PrependTo(items, values)

def AppendItemTo[T](items: Iterable[T]|None, value: T) -> Generator[T]:
    """Appends a single item after each item.

    Args:
        items: The initial items.
        value: The item to append after each item.

    Yields:
        Each item followed by the value.
    """
    for item in TryEnumerate(items):
        yield item

        yield value
def PrependItemTo[T](items: Iterable[T]|None, value: T) -> Generator[T]:
    """Prepends a single item before each item.

    Args:
        items: The initial items.
        value: The item to prepend before each item.

    Yields:
        The value followed by each item.
    """
    for item in TryEnumerate(items):
        yield value

        yield item

def AppendIterable[T](items: Iterable[T]|None, values: Iterable[Iterable[T]|None]|None) -> Generator[T]:
    """Appends concatenated iterables to the end of items.

    Args:
        items: The initial items.
        values: A collection of iterables to concatenate and append.

    Yields:
        All items followed by all values from concatenated iterables.
    """
    return Append(items, Concatenate(values))
def AppendIterableValues[T](items: Iterable[T]|None, *values: Iterable[T]|None) -> Generator[T]:
    """Appends variadic iterables to the end of items.

    Args:
        items: The initial items.
        *values: Iterables to concatenate and append.

    Yields:
        All items followed by all values from concatenated iterables.
    """
    return AppendIterable(items, values)

def PrependIterable[T](items: Iterable[T]|None, values: Iterable[Iterable[T]|None]|None) -> Generator[T]:
    """Prepends concatenated iterables to the beginning of items.

    Args:
        items: The initial items.
        values: A collection of iterables to concatenate and prepend.

    Yields:
        All values from concatenated iterables followed by all items.
    """
    return Append(Concatenate(values), items)
def PrependIterableValues[T](items: Iterable[T]|None, *values: Iterable[T]|None) -> Generator[T]:
    """Prepends variadic iterables to the beginning of items.

    Args:
        items: The initial items.
        *values: Iterables to concatenate and prepend.

    Yields:
        All values from concatenated iterables followed by all items.
    """
    return PrependIterable(items, values)

def AppendIterableTo[T](items: Iterable[T]|None, values: Iterable[Iterable[T]|None]|None) -> Generator[T]:
    """Appends concatenated iterables after each item.

    Args:
        items: The initial items.
        values: A collection of iterables to concatenate and append after each item.

    Yields:
        Each item followed by all values from concatenated iterables.
    """
    return AppendTo(items, Concatenate(values))
def AppendIterableValuesTo[T](items: Iterable[T]|None, *values: Iterable[T]|None) -> Generator[T]:
    """Appends variadic iterables after each item.

    Args:
        items: The initial items.
        *values: Iterables to concatenate and append after each item.

    Yields:
        Each item followed by all values from concatenated iterables.
    """
    return AppendIterableTo(items, values)

def PrependIterableTo[T](items: Iterable[T]|None, values: Iterable[Iterable[T]|None]|None) -> Generator[T]:
    """Prepends concatenated iterables before each item.

    Args:
        items: The initial items.
        values: A collection of iterables to concatenate and prepend before each item.

    Yields:
        All values from concatenated iterables followed by each item.
    """
    return PrependTo(items, Concatenate(values))
def PrependIterableValuesTo[T](items: Iterable[T]|None, *values: Iterable[T]|None) -> Generator[T]:
    """Prepends variadic iterables before each item.

    Args:
        items: The initial items.
        *values: Iterables to concatenate and prepend before each item.

    Yields:
        All values from concatenated iterables followed by each item.
    """
    return PrependIterableTo(items, values)

def Select[TIn, TOut](items: Iterable[TIn]|None, converter: Converter[TIn, TOut]) -> Generator[TOut]:
    """Transforms items using a converter function.

    Args:
        items: The items to transform.
        converter: The function to transform each item.

    Yields:
        Transformed items.
    """
    return (converter(item) for item in TryEnumerate(items))
def WhereSelect[TIn, TOut](items: Iterable[TIn]|None, predicate: Predicate[TIn], converter: Converter[TIn, TOut]) -> Generator[TOut]:
    """Filters then transforms items.

    Args:
        items: The items to process.
        predicate: The filter function.
        converter: The transformation function.

    Yields:
        Transformed items that passed the filter.
    """
    return (converter(item) for item in TryEnumerate(items) if predicate(item))
def SelectWhere[TIn, TOut](items: Iterable[TIn]|None, converter: Converter[TIn, TOut], predicate: Predicate[TOut]) -> Generator[TOut]:
    """Transforms then filters items.

    Args:
        items: The items to process.
        converter: The transformation function.
        predicate: The filter function applied to transformed items.

    Yields:
        Transformed items that passed the filter.
    """
    result: TOut|None = None

    for item in TryEnumerate(items):
        if predicate(result := converter(item)):
            yield result

def Include[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    """Includes only items that match a given predicate.

    Args:
        items: The items to filter.
        predicate: The filter function.

    Yields:
        Items that match the predicate.
    """
    return (item for item in TryEnumerate(items) if predicate(item))
def Exclude[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    """Excludes items that match a given predicate.

    Args:
        items: The items to filter.
        predicate: The filter function.

    Yields:
        Items that do not match the predicate.
    """
    return Include(items, GetNotPredicate(predicate))

def IncludeWhile[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    """Includes items while they match a predicate (exclusive).

    Args:
        items: The items to process.
        predicate: The condition to continue including.

    Yields:
        Items until the first one that doesn't match the predicate.
    """
    for item in TryEnumerate(items):
        if predicate(item):
            yield item

        else:
            break
def IncludeUntil[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    """Includes items until one matches a predicate (exclusive).

    Args:
        items: The items to process.
        predicate: The condition to stop including.

    Yields:
        Items until the first one that matches the predicate.
    """
    for item in TryEnumerate(items):
        if predicate(item):
            break

        yield item

def DoIncludeUntil[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    """Includes items until one matches a predicate (inclusive).

    Args:
        items: The items to process.
        predicate: The condition to stop including.

    Yields:
        Items until and including the first one that matches the predicate.
    """
    for item in TryEnumerate(items):
        yield item

        if predicate(item):
            break
def DoIncludeWhile[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    """Includes items while they match a predicate (inclusive).

    Args:
        items: The items to process.
        predicate: The condition to continue including.

    Yields:
        Items while they match the predicate, including the first one not matching the predicate.
    """
    return DoIncludeUntil(items, GetNotPredicate(predicate))

def __Exclude[T](items: Iterable[T]|None, selector: Selector[IEnumerator[T]]) -> Generator[T]:
    def getIterator(enumerable: IEnumerable[T]|None) -> Iterator[T]|None:
        if enumerable is None:
            return None
        
        enumerator: IEnumerator[T]|None = enumerable.TryGetEnumerator()
        
        return None if enumerator is None else selector(enumerator).AsIterator()
    
    for item in TryEnumerate(getIterator(Enumeration.Iterable[T].TryCreate(items))):
        yield item

def ExcludeWhile[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    """Excludes items while they match a predicate, then includes the rest.

    Args:
        items: The items to process.
        predicate: The condition to continue excluding.

    Yields:
        Items starting from the first one that doesn't match the predicate.
    """
    return __Exclude(items, lambda enumerator: ExcluerEnumerator(enumerator, predicate))
def ExcludeUntil[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    """Excludes items until one matches a predicate, then includes the rest.

    Args:
        items: The items to process.
        predicate: The condition to stop excluding.

    Yields:
        Items starting from the first one that matches the predicate.
    """
    return __Exclude(items, lambda enumerator: ExcluerUntilEnumerator(enumerator, predicate))

def TryGetFirst[T](items: Iterable[T]|None) -> INullable[T]|None:
    """Tries to get the first item from an iterable.

    Args:
        items: The items to process.

    Returns:
        None if items is None; INullable with first item if found, or null value if empty.
    """
    if items is None:
        return None

    for item in items:
        return GetNullable(item)

    return GetNullValue()

def Any[T](items: Iterable[T]|None) -> bool|None:
    """Checks if an iterable contains any items.

    Args:
        items: The items to check.

    Returns:
        None if items is None, True if any items exist, False otherwise.
    """
    if items is None:
        return None

    for _ in items:
        return True

    return False

def ValidateOnlyOne[T](items: Iterable[T]|None, predicate: Predicate[T]) -> IterationResult:
    """Validates that exactly one or no item matches a predicate.

    Args:
        items: The items to check.
        predicate: The condition to validate.

    Returns:
        - IterationResult.Null if items is None
        - IterationResult.Empty if no items exist
        - IterationResult.Success if exactly one item matches
        - IterationResult.Error if more than one item matches
    """
    if items is None:
        return IterationResult.Null

    validator: Predicate[T]|None = None

    def validate(value: T) -> bool:
        nonlocal validator

        if predicate(value):
            validator = predicate # Stop iteration if a second item validated the given predicate.

        return False # Do not stop iteration.

    validator = validate

    enumerator: IEnumerator[T]|None = Enumeration.Iterable[T].Create(items).TryGetEnumerator()

    if enumerator is None:
        return IterationResult.Empty

    for item in enumerator.AsIterator():
        if validator(item):
            # The validator result, unlike the predicate result indicates that the validation failed because the predicate validated two items in the given iterable.
            return IterationResult.Error

    return IterationResult.Success if enumerator.HasProcessedItems() else IterationResult.Empty # Validation succeeded or iterable is empty.
def ValidateOneAndOnlyOne[T](items: Iterable[T]|None, predicate: Predicate[T]) -> bool|None:
    """Validates that exactly one item matches a predicate.

    Args:
        items: The items to check.
        predicate: The condition to validate.

    Returns:
        - None if items is None
        - True if exactly one item matches
        - False if zero or more than one item matches
    """
    match ValidateOnlyOne(items, predicate):
        case IterationResult.Success:
            return True
        case IterationResult.Null:
            return None
        case _:
            return False

def EnsureOnlyOne[T](items: Iterable[T]|None, predicate: Predicate[T], errorMessage: str|None = None) -> None:
    """Ensures exactly one item matches a predicate, ignoring null or empty cases.

    Args:
        items: The items to check.
        predicate: The condition to validate.
        errorMessage: Optional custom error message.

    Raises:
        ValueError: If more than one item matches the predicate.
    """
    if not ValidateOnlyOne(items, predicate):
        raise ValueError("More than one value validating the given predicate were found." if errorMessage is None else errorMessage)
def EnsureOneAndOnlyOne[T](items: Iterable[T]|None, predicate: Predicate[T], errorMessage: str|None = None) -> None:
    """Ensures exactly one item matches a predicate, with null-safe validation.

    Args:
        items: The items to check.
        predicate: The condition to validate.
        errorMessage: Optional custom error message.

    Raises:
        ValueError: If no iterable given, if no items are found or if zero or more than one item matches the predicate.
    """
    def raiseError(msg: str) -> None:
        raise ValueError(msg if errorMessage is None else errorMessage)

    match ValidateOnlyOne(items, predicate).ToNullableBoolean():
        case NullableBoolean.Null:
            raiseError("No item found.")
        case NullableBoolean.BoolFalse:
            raiseError("More than one value validating the given predicate were found.")
        case _:
            pass