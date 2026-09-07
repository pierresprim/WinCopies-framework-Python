from __future__ import annotations

from collections.abc import Iterable, Iterator, Collection
from contextlib import AbstractContextManager

from WinCopies.Bool import BooleanableEnum, NullableBoolean
from WinCopies.Collections import Generator
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, ICountableEnumerable, TryAsIterable, AsEnumerable, AsEnumerator
from WinCopies.Collections.Enumeration.Selection import ExcluerEnumerator, ExcluerUntilEnumerator
from WinCopies.Collections.Iteration import Concatenate, TryEnumerate, Select, Include, IterateWith
from WinCopies.Collections.Util import MakeGenerator
from WinCopies.Typing.Delegate import Function, Predicate, Converter, Selector
from WinCopies.Typing.Pairing import IKeyValuePair, CreateDualResult

class IterableScanResult(BooleanableEnum):
    DoesNotExist = -2
    Empty = -1
    Success = 0
    Error = 1
    
    def Not(self) -> IterableScanResult: return (IterableScanResult.Error if self == IterableScanResult.Success else IterableScanResult.Success) if self else self
class ScanResult(BooleanableEnum):
    Error = -1
    Success = 0
    Empty = 1
    Null = 2
    
    def ToNullableBool(self) -> bool|None: return True if self == ScanResult.Success else (None if self.value > 0 else False)
    
    def ToNullableBoolean(self) -> NullableBoolean: return NullableBoolean.BoolTrue if self == ScanResult.Success else (NullableBoolean.Null if self.value > 0 else NullableBoolean.BoolFalse)

def TryAsIterables[T](collection: Iterable[IEnumerable[T]|None]|None) -> Generator[Iterable[T]|None]:
    return Select(collection, TryAsIterable)
def AsIterables[T](collection: Iterable[IEnumerable[T]]|None) -> Generator[Iterable[T]]:
    return Select(collection, lambda collection: collection.AsIterable())

def TryConcatenateItems[T](collection: Iterable[IEnumerable[T]|None]|None) -> Generator[T]:
    return Concatenate(TryAsIterables(collection))
def ConcatenateItems[T](collection: Iterable[IEnumerable[T]]|None) -> Generator[T]:
    return Concatenate(AsIterables(collection))

def TryConcatenateEnumerables[T](*collection: IEnumerable[T]|None) -> Generator[T]:
    return TryConcatenateItems(collection)
def ConcatenateEnumerables[T](*collection: IEnumerable[T]) -> Generator[T]:
    return ConcatenateItems(collection)

def __Exclude[T](items: Iterable[T]|None, selector: Selector[IEnumerator[T]]) -> Generator[T]:
    def getIterator(enumerable: IEnumerable[T]) -> Iterator[T]|None:
        enumerator: IEnumerator[T]|None = enumerable.TryGetEnumerator()
        
        return None if enumerator is None else selector(enumerator).AsIterator()
    
    for item in TryEnumerate(None if items is None else getIterator(AsEnumerable(items))): yield item

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

def Any[T](items: ICountableEnumerable[T]|Collection[T]|Iterable[T], predicate: Predicate[T]|None = None) -> bool:
    def any(length: int) -> bool: return length > 0
    
    def _any(items: ICountableEnumerable[T]) -> bool: return any(items.GetCount())
    def __any(items: Collection[T]) -> bool: return any(len(items))

    def parse(items: Iterable[T], predicate: Predicate[T]) -> bool:
        for _ in Include(items, predicate): return True

        return False

    if predicate is None:
        match items:
            case ICountableEnumerable(): return _any(items)
            case Collection(): return __any(items)
            
            case Iterable():
                for _ in items: return True

                return False
    
    else:
        match items:
            case ICountableEnumerable(): return _any(items) and parse(items.AsIterable(), predicate)
            case Collection(): return __any(items) and parse(items, predicate)
            
            case Iterable():
                return parse(items, predicate)
def CheckIfAny[T](items: Iterable[T]|None, predicate: Predicate[T]|None = None) -> bool|None:
    """Checks if an iterable contains any items.

    Args:
        items: The items to check.

    Returns:
        True if any items exist, False otherwise.
    """
    return None if items is None else Any(items, predicate)

def __Zip[T1, T2](x: Iterable[T1], y: IEnumerator[T2]) -> Generator[IKeyValuePair[T1, T2]]:
    current: T2|None = None

    for item in x:
        if y.MoveNext():
            if (current := y.GetCurrent()) is None: break
            
            yield CreateDualResult(item, current)
        
        else: break
def __TryZip[T1, T2](x: Iterable[T1], y: Iterable[T2]|IEnumerable[T2]) -> Generator[IKeyValuePair[T1, T2]]|None:
    def zip(y: IEnumerator[T2]) -> Generator[IKeyValuePair[T1, T2]]: return __Zip(x, y)
    
    match y:
        case Iterator(): return zip(AsEnumerator(y))
        case Iterable(): return zip(AsEnumerable(y).GetEnumerator())
        
        case IEnumerable():
            _y: IEnumerator[T2]|None = y.TryGetEnumerator()

            return None if _y is None else zip(_y)

def TryZip[T1, T2](x: Iterable[T1]|IEnumerable[T1], y: Iterable[T2]|IEnumerable[T2]) -> Generator[IKeyValuePair[T1, T2]]|None:
    return __TryZip(x.AsIterable() if isinstance(x, IEnumerable) else x, y)
def Zip[T1, T2](x: Iterable[T1]|IEnumerable[T1], y: Iterable[T2]|IEnumerable[T2]) -> Generator[IKeyValuePair[T1, T2]]:
    items: Generator[IKeyValuePair[T1, T2]]|None = TryZip(x, y)

    return MakeGenerator() if items is None else items

def ValidateOnlyOne[T](items: Iterable[T]|None, predicate: Predicate[T]) -> ScanResult:
    """Validates that exactly one or no item matches a predicate.

    Args:
        items: The items to check.
        predicate: The condition to validate.

    Returns:
        - ScanResult.Null if items is None
        - ScanResult.Empty if no items exist
        - ScanResult.Success if exactly one item matches
        - ScanResult.Error if more than one item matches
    """
    if items is None: return ScanResult.Null

    validator: Predicate[T]|None = None

    def validate(value: T) -> bool:
        nonlocal validator

        if predicate(value): validator = predicate # Stop iteration if a second item validated the given predicate.

        return False # Do not stop iteration.

    validator = validate

    enumerator: IEnumerator[T]|None = AsEnumerable(items).TryGetEnumerator()

    if enumerator is None: return ScanResult.Empty

    for item in enumerator.AsIterator():
        # The validator result, unlike the predicate result indicates that the validation failed because the predicate validated two items in the given iterable.
        if validator(item): return ScanResult.Error

    return ScanResult.Success if enumerator.GetStatus().HasProcessedItems() else ScanResult.Empty # Validation succeeded or iterable is empty.
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
        case ScanResult.Success: return True
        case ScanResult.Null: return None
        
        case _: return False

def EnsureOnlyOne[T](items: Iterable[T]|None, predicate: Predicate[T], errorMessage: str|None = None) -> None:
    """Ensures exactly one item matches a predicate, ignoring null or empty cases.

    Args:
        items: The items to check.
        predicate: The condition to validate.
        errorMessage: Optional custom error message.

    Raises:
        ValueError: If more than one item matches the predicate.
    """
    if not ValidateOnlyOne(items, predicate): raise ValueError("More than one value validating the given predicate were found." if errorMessage is None else errorMessage)
def EnsureOneAndOnlyOne[T](items: Iterable[T]|None, predicate: Predicate[T], errorMessage: str|None = None) -> None:
    """Ensures exactly one item matches a predicate, with null-safe validation.

    Args:
        items: The items to check.
        predicate: The condition to validate.
        errorMessage: Optional custom error message.

    Raises:
        ValueError: If no iterable given, if no items are found or if zero or more than one item matches the predicate.
    """
    def raiseError(msg: str) -> None: raise ValueError(msg if errorMessage is None else errorMessage)

    match ValidateOnlyOne(items, predicate).ToNullableBoolean():
        case NullableBoolean.Null: raiseError("No item found.")
        case NullableBoolean.BoolFalse: raiseError("More than one value validating the given predicate were found.")
        
        case _: pass

def TryIterateWith[T](checker: Function[bool], itemsProvider: Function[AbstractContextManager[Iterable[T]]], func: Converter[Iterable[T], bool|None]) -> IterableScanResult:
    if checker():
        result: bool|None = IterateWith(itemsProvider, func)

        return IterableScanResult.Empty if result == None else (IterableScanResult.Success if result else IterableScanResult.Error)
    
    return IterableScanResult.DoesNotExist
def TryIterateFrom[TIn, TOut](value: TIn, checker: Predicate[TIn], itemsProvider: Converter[TIn, AbstractContextManager[Iterable[TOut]]], func: Converter[Iterable[TOut], bool|None]) -> IterableScanResult:
    return TryIterateWith(lambda: checker(value), lambda: itemsProvider(value), func)