from abc import abstractmethod
from collections.abc import Iterable, Iterator, Collection
from typing import final, Callable, Type

from WinCopies import NullableBoolean, IInterface, Abstract
from WinCopies.Collections import Generator, IterationResult, MakeGenerator
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, ICountableEnumerable, CreateIterable, TryCreateIterable, AsEnumerator
from WinCopies.Collections.Enumeration.Selection import ExcluerEnumerator, ExcluerUntilEnumerator
from WinCopies.Delegates import BoolFalse, GetNotPredicate
from WinCopies.Typing import INullable, GetNullable, GetNullValue, InvalidOperationError
from WinCopies.Typing.Delegate import Function, Converter, NullableConverter, Predicate, Selector
from WinCopies.Typing.Pairing import IKeyValuePair, CreateDualResult

class IAdaptiveRefinement(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def IsRefining(self) -> bool:
        pass
    @abstractmethod
    def IsTrueSize(self) -> bool:
        pass
    
    @final
    def GetSizeState(self) -> bool|None:
        return True if self.IsTrueSize() else (None if self.IsRefining() else False)
    
    @final
    def GetDiscoveredSize(self) -> int|None:
        low: int = self.GetLow()
        
        return None if low == 0 else low
    @final
    def TryGetDiscoveredSize(self) -> int|None:
        return self.GetLow() if self.IsTrueSize() else None
    
    @abstractmethod
    def CanSignalSuccess(self) -> bool:
        pass
    @abstractmethod
    def CanSignalError(self) -> bool:
        pass

    @abstractmethod
    def GetCurrent(self) -> int:
        pass

    @abstractmethod
    def GetLow(self) -> int:
        pass
    @abstractmethod
    def GetHigh(self) -> int|None:
        pass
    
    @abstractmethod
    def Reset(self) -> None:
        pass
    @abstractmethod
    def ResetTo(self, hint: int, refine: bool) -> None:
        pass

    @abstractmethod
    def TryOnSuccess(self) -> bool:
        pass
    @abstractmethod
    def TryOnError(self) -> bool|None:
        pass

    @final
    def OnSuccess(self) -> None:
        if not self.TryOnSuccess():
            raise InvalidOperationError()
    @final
    def OnError(self) -> None:
        if self.TryOnError() is not True:
            raise InvalidOperationError()

    @final
    def Update(self, success: bool) -> None:
        if success:
            self.OnSuccess()
        
        else:
            self.OnError()
@final
class _AdaptiveRefinement(Abstract, IAdaptiveRefinement):
    def __init__(self, current: int|None, refine: bool) -> None:
        super().__init__()

        self.__low: int = 0
        self.__high: int|None = None
        self.__delta: int = 1
        self.__current: int = 1 if current is None or current == 0 else current
        self.__refine: bool|None = refine
        self.__tryOnSuccess: Function[bool] = self.__TryOnSuccess
        self.__tryOnError: Function[bool|None] = self.__TryOnError
    
    def __TryOnSuccess(self) -> bool:
        current: int = self.__current
        high: int|None = self.GetHigh()
        
        self.__low = current

        if high is None:
            if self.__refine:
                self.__current = 2 * current
        
        else:
            delta: int = 2 * self.__delta

            self.__delta = delta
            low: int = self.GetLow()
            current = min(low + delta, high - 1)
            self.__current = current

            if current == low:
                self.__refine = None

                self.__tryOnSuccess = BoolFalse
                self.__tryOnError = BoolFalse
        
        return True
    def __TryOnError(self) -> bool|None:
        low: int = self.GetLow()
        current: int = self.__current

        if low == current:
            return None

        self.__refine = True

        if low == 0:
            self.__Reset(1)

        else:
            self.__ResetDelta()
            
            self.__high = current
            self.__current = low + 1
        
        return True
    
    def __ResetDelegates(self) -> None:
        self.__tryOnSuccess = self.__TryOnSuccess
        self.__tryOnError = self.__TryOnError
    def __ResetDelta(self) -> None:
        self.__delta = 1
    def __Reset(self, current: int) -> None:
        self.__ResetDelta()

        self.__current = current
    
    def CanSignalSuccess(self) -> bool:
        return not self.IsTrueSize()
    def CanSignalError(self) -> bool:
        return self.CanSignalSuccess()
    
    def GetCurrent(self) -> int:
        return self.__current
    
    def GetLow(self) -> int:
        return self.__low
    def GetHigh(self) -> int|None:
        return self.__high
    
    def TryOnSuccess(self) -> bool:
        return self.__tryOnSuccess()
    def TryOnError(self) -> bool|None:
        return self.__tryOnError()
    
    def __ResetTo(self, hint: int, refine: bool) -> None:
        self.__Reset(hint)
        self.__ResetDelegates()

        self.__low = 0
        self.__high = None
        self.__refine = refine
    
    def Reset(self) -> None:
        self.__ResetTo(1, True)
    def ResetTo(self, hint: int, refine: bool) -> None:
        if hint == 0:
            if refine:
                hint = 1
            
            else:
                raise ValueError()
        
        self.__ResetTo(hint, refine)
    
    def IsRefining(self) -> bool:
        return self.__refine is True
    
    def IsTrueSize(self) -> bool:
        return self.__refine is None

def CreateAdaptiveRefinement() -> IAdaptiveRefinement:
    return _AdaptiveRefinement(None, True)
def CreateFineRefinement(hint: int|None, refine: bool) -> IAdaptiveRefinement:
    if hint is None or hint == 0:
        if refine:
            return CreateAdaptiveRefinement()
        
        raise ValueError()
    
    if hint < 0:
        raise ValueError()
    
    return _AdaptiveRefinement(hint, refine)

def TryEnumerate[T](items: Iterable[T]|None) -> Iterable[T]:
    """Returns the given iterable, or an empty generator if None is given.

    Args:
        iterable: The iterable to check.

    Returns:
        The original iterable if not None, otherwise an empty generator.
    """

    return MakeGenerator() if items is None else items
def TryGenerate[T](items: Generator[T]|None) -> Generator[T]:
    return MakeGenerator() if items is None else items

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
def ConcatenateValues[T](*collection: Iterable[T]|None) -> Generator[T]:
    return Concatenate(collection)

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

def Expand[T](items: Iterable[Iterable[T]]) -> Generator[T]:
    for item in items:
        for _item in item:
            yield _item
def ExpandItems[TIn, TOut](items: Iterable[TIn], converter: Converter[TIn, Iterable[TOut]]) -> Generator[TOut]:
    for item in items:
        for _item in converter(item):
            yield _item

def Select[TIn, TOut](items: Iterable[TIn]|None, converter: Converter[TIn, TOut]) -> Generator[TOut]:
    """Transforms items using a converter function.

    Args:
        items: The items to transform.
        converter: The function to transform each item.

    Yields:
        Transformed items.
    """
    return (converter(item) for item in TryEnumerate(items))

def SelectMany[TIn1, TIn2, TOut](items: Iterable[TIn1], converter: Converter[TIn1, Iterable[TIn2]], selector: Converter[TIn2, TOut]) -> Generator[TOut]:
    for item in items:
        for _item in converter(item):
            yield selector(_item)
def SelectManyItems[TIn1, TIn2, TOut](items: Iterable[TIn1], converter: Converter[TIn1, Iterable[TIn2]], selector: Callable[[TIn1, TIn2], TOut]) -> Generator[TOut]:
    for item in items:
        for _item in converter(item):
            yield selector(item, _item)

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

def WhereNotNone[T](items: Iterable[T|None]|None) -> Generator[T]:
    return (item for item in TryEnumerate(items) if item is not None)

def SelectWhereNotNone[TIn, TOut](items: Iterable[TIn]|None, converter: NullableConverter[TIn, TOut]) -> Generator[TOut]:
    return (item for item in Select(items, converter) if item is not None)
def WhereNotNoneSelect[TIn, TOut](items: Iterable[TIn|None]|None, converter: Converter[TIn, TOut]) -> Generator[TOut]:
    return (converter(item) for item in TryEnumerate(items) if item is not None)

def WhereOfType[T](t: Type[T], items: Iterable[object]) -> Generator[T]:
    for item in items:
        if isinstance(item, t):
            yield item

def WhereOfTypeSelect[TIn, TOut](t: Type[TIn], items: Iterable[object], converter: Converter[TIn, TOut]) -> Generator[TOut]:
    for item in items:
        if isinstance(item, t):
            yield converter(item)

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
    
    for item in TryEnumerate(getIterator(TryCreateIterable(items))):
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

def GetFirst[T](items: Iterable[T]) -> INullable[T]:
    """Tries to get the first item from an iterable.

    Args:
        items: The items to process.

    Returns:
        INullable with first item if found or null value if empty.
    """
    for item in items:
        return GetNullable(item)

    return GetNullValue()
def TryGetFirst[T](items: Iterable[T]|None) -> INullable[T]|None:
    """Tries to get the first item from an iterable.

    Args:
        items: The items to process.

    Returns:
        None if items is None; INullable with first item if found, or null value if empty.
    """
    return None if items is None else GetFirst(items)

def GetFirstItem[T](items: Iterable[T], predicate: Predicate[T]) -> INullable[T]:
    for item in Include(items, predicate):
        return GetNullable(item)
    
    return GetNullValue()
def TryGetFirstItem[T](items: Iterable[T]|None, predicate: Predicate[T]) -> INullable[T]|None:
    return None if items is None else GetFirstItem(items, predicate)

def GetFirstItemExclusive[T](items: Iterable[T], predicate: Predicate[T]) -> INullable[T]:
    for item in Exclude(items, predicate):
        return GetNullable(item)
    
    return GetNullValue()
def TryGetFirstItemExclusive[T](items: Iterable[T]|None, predicate: Predicate[T]) -> INullable[T]|None:
    return None if items is None else GetFirstItemExclusive(items, predicate)

def Any[T](items: ICountableEnumerable[T]|Collection[T]|Iterable[T]) -> bool:
    """Checks if an iterable contains any items.

    Args:
        items: The items to check.

    Returns:
        None if items is None, True if any items exist, False otherwise.
    """
    def any(length: int) -> bool:
        return length > 0
    
    match items:
        case ICountableEnumerable():
            return any(items.GetCount())
        
        case Collection():
            return any(len(items))
        
        case Iterable():
            for _ in items:
                return True

            return False
def CheckIfAny[T](items: Iterable[T]|None) -> bool|None:
    """Checks if an iterable contains any items.

    Args:
        items: The items to check.

    Returns:
        True if any items exist, False otherwise.
    """
    return None if items is None else Any(items)

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

    enumerator: IEnumerator[T]|None = CreateIterable(items).TryGetEnumerator()

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

def __Zip[T1, T2](x: Iterable[T1], y: IEnumerator[T2]) -> Generator[IKeyValuePair[T1, T2]]:
    current: T2|None = None

    for item in x:
        if y.MoveNext():
            if (current := y.GetCurrent()) is None:
                break
            
            yield CreateDualResult(item, current)
        
        else:
            break
def __TryZip[T1, T2](x: Iterable[T1], y: Iterable[T2]|IEnumerable[T2]) -> Generator[IKeyValuePair[T1, T2]]|None:
    def zip(y: IEnumerator[T2]) -> Generator[IKeyValuePair[T1, T2]]:
        return __Zip(x, y)
    
    match y:
        case Iterator():
            return zip(AsEnumerator(y))
        
        case Iterable():
            return zip(CreateIterable(y).GetEnumerator())
        
        case IEnumerable():
            _y: IEnumerator[T2]|None = y.TryGetEnumerator()

            return None if _y is None else zip(_y)

def TryZip[T1, T2](x: Iterable[T1]|IEnumerable[T1], y: Iterable[T2]|IEnumerable[T2]) -> Generator[IKeyValuePair[T1, T2]]|None:
    return __TryZip(x.AsIterable() if isinstance(x, IEnumerable) else x, y)
def Zip[T1, T2](x: Iterable[T1]|IEnumerable[T1], y: Iterable[T2]|IEnumerable[T2]) -> Generator[IKeyValuePair[T1, T2]]:
    items: Generator[IKeyValuePair[T1, T2]]|None = TryZip(x, y)

    return MakeGenerator() if items is None else items