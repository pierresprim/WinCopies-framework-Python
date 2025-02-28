from collections.abc import Iterable

from WinCopies import Delegates
from WinCopies.Collections import Generator
from WinCopies.Typing.Delegate import Converter, Predicate

def Append[T](items: Iterable[T], values: Iterable[T]) -> Generator[T]:
    for item in items:
        yield item
    
    for value in values:
        yield value
def AppendValues[T](items: Iterable[T], *values: T) -> Generator[T]:
    return Append(items, values)

def Prepend[T](items: Iterable[T], values: Iterable[T]) -> Generator[T]:
    return Append(values, items)
def PrependValues[T](items: Iterable[T], *values: T) -> Generator[T]:
    return Prepend(items, values)

def Select[TIn, TOut](items: Iterable[TIn], converter: Converter[TIn, TOut]) -> Generator[TOut]:
    for item in items:
        yield converter(item)
def WhereSelect[TIn, TOut](items: Iterable[TIn], predicate: Predicate[TIn], converter: Converter[TIn, TOut]) -> Generator[TIn]:
    for item in items:
        if predicate(item):
            yield converter(item)
def SelectWhere[TIn, TOut](items: Iterable[TIn], converter: Converter[TIn, TOut], predicate: Predicate[TOut]) -> Generator[TOut]:
    result: TOut|None = None

    for item in items:
        if predicate(result := converter(item)):
            yield result

def Include[T](items: Iterable[T], predicate: Predicate[T]) -> Generator[T]:
    for item in items:
        if predicate(item):
            yield item
def Exclude[T](items: Iterable[T], predicate: Predicate[T]) -> Generator[T]:
    return Include(items, Delegates.GetNotPredicate(predicate))

def Concatenate[T](collection: Iterable[Iterable[T]]) -> Generator[T]:
    for iterable in collection:
        for item in iterable:
            yield item

def ValidateOnlyOne[T](items: Iterable[T], predicate: Predicate[T]) -> bool:
    validator: Predicate[T]|None = None

    def validate(value: T) -> bool:
        nonlocal validator

        if predicate(value):
            validator = predicate # Stop iteration if a second item validated the given predicate.
        
        return False # Do not stop iteration.

    validator = validate

    for item in items:
        if validator(item):
            # The validator result, unlike the predicate result indicates that the validation failed because the predicate validated two items in the given iterable.
            return False
    
    return True # Validation succeeded.
def EnsureOnlyOne[T](items: Iterable[T], predicate: Predicate[T], errorMessage: str|None = None) -> bool:
    if not ValidateOnlyOne(items, predicate):
        raise ValueError("More than one value validating the given predicate were found." if errorMessage is None else errorMessage)