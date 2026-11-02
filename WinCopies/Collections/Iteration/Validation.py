from collections.abc import Iterable

from WinCopies.Bool import NullableBoolean
from WinCopies.Collections.Iteration.Enumeration import ScanResult
from WinCopies.Collections.Loop import ForEachItemUntil
from WinCopies.Typing.Delegate import Predicate

def ValidateOnlyOne[T](items: Iterable[T]|None, predicate: Predicate[T]) -> ScanResult:
    """Validates that exactly one or no item matches a predicate.

    Args:
        items: The items to check.
        predicate: The condition to validate.

    Returns:
        - ScanResult.Null if items is None
        - ScanResult.Empty if no items exist
        - ScanResult.Success if exactly one item matches
        - ScanResult.Error if more than one item matches"""
    
    if items is None: return ScanResult.Null

    validator: Predicate[T]|None = None

    def validate(value: T) -> bool:
        nonlocal validator

        if predicate(value): validator = predicate # Stop iteration if a second item validated the given predicate.

        return False # Do not stop iteration.

    validator = validate

    match ForEachItemUntil(items, validator):
        # The validator result, unlike the predicate result indicates that the validation failed because the predicate validated two items in the given iterable.
        case True: return ScanResult.Error
        case False: return ScanResult.Success
        
        # Validation succeeded or iterable is empty.
        case _: return ScanResult.Empty
def ValidateOneAndOnlyOne[T](items: Iterable[T]|None, predicate: Predicate[T]) -> bool|None:
    """Validates that exactly one item matches a predicate.

    Args:
        items: The items to check.
        predicate: The condition to validate.

    Returns:
        - None if items is None
        - True if exactly one item matches
        - False if zero or more than one item matches"""
    
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
        ValueError: If more than one item matches the predicate."""
    
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