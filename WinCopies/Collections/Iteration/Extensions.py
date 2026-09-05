from __future__ import annotations

from collections.abc import Iterable
from contextlib import AbstractContextManager

from WinCopies.Bool import BooleanableEnum, NullableBoolean
from WinCopies.Collections.Enumeration import IEnumerable, IReversableEnumerable, IEnumerator, AsEnumerable
from WinCopies.Collections.Iteration import IterateWith
from WinCopies.Collections.Linked.Singly import CreateStack, CreateEnumerableStack
from WinCopies.Typing.Delegate import Function, Predicate, Converter

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

def GetReversed[T](items: Iterable[T]) -> IEnumerable[T]:
    def enumerate(items: IReversableEnumerable[T]) -> IEnumerable[T]: return items.AsReversed()
    
    return enumerate(items) if isinstance(items, IReversableEnumerable) else CreateEnumerableStack(items)
def Reverse[T](items: Iterable[T]) -> Iterable[T]:
    def enumerate(items: IReversableEnumerable[T]) -> IEnumerable[T]: return items.AsReversed()
    
    return enumerate(items).AsIterable() if isinstance(items, IReversableEnumerable) else CreateStack(items).AsGenerator()