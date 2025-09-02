from collections.abc import Iterable, Iterator

from WinCopies.Collections import Generator, Enumeration
from WinCopies.Collections.Enumeration import IEnumerator, EmptyEnumerator, AsEnumerator
from WinCopies.Collections.Enumeration.Selection import ExcluerEnumerator, ExcluerUntilEnumerator
from WinCopies.Delegates import GetNotPredicate
from WinCopies.Typing import INullable, GetNullable, GetNullValue
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

def AppendTo[T](items: Iterable[T], values: Iterable[T]) -> Generator[T]:
    for item in items:
        yield item

        for value in values:
            yield value
def AppendValuesTo[T](items: Iterable[T], *values: T) -> Generator[T]:
    return AppendTo(items, values)

def PrependTo[T](items: Iterable[T], values: Iterable[T]) -> Generator[T]:
    for item in items:
        for value in values:
            yield value
        
        yield item
def PrependValuesTo[T](items: Iterable[T], *values: T) -> Generator[T]:
    return PrependTo(items, values)

def AppendItemTo[T](items: Iterable[T], value: T) -> Generator[T]:
    for item in items:
        yield item

        yield value
def PrependItemTo[T](items: Iterable[T], value: T) -> Generator[T]:
    for item in items:
        yield value

        yield item

def Select[TIn, TOut](items: Iterable[TIn], converter: Converter[TIn, TOut]) -> Generator[TOut]:
    for item in items:
        yield converter(item)
def WhereSelect[TIn, TOut](items: Iterable[TIn], predicate: Predicate[TIn], converter: Converter[TIn, TOut]) -> Generator[TOut]:
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
    return Include(items, GetNotPredicate(predicate))

def IncludeWhile[T](items: Iterable[T], predicate: Predicate[T]) -> Generator[T]:
    for item in items:
        if predicate(item):
            yield item
        
        else:
            break
def IncludeUntil[T](items: Iterable[T], predicate: Predicate[T]) -> Generator[T]:
    for item in items:
        if predicate(item):
            break
        
        yield item

def DoIncludeUntil[T](items: Iterable[T], predicate: Predicate[T]) -> Generator[T]:
    for item in items:
        yield item

        if predicate(item):
            break
def DoIncludeWhile[T](items: Iterable[T], predicate: Predicate[T]) -> Generator[T]:
    return DoIncludeUntil(items, GetNotPredicate(predicate))

def __Exclude[T](items: Iterable[T], converter: Converter[Iterator[T], IEnumerator[T]]) -> Generator[T]:
    iterator: Iterator[T]|None = Enumeration.Iterable[T].Create(items).TryGetIterator()
    
    for item in EmptyEnumerator[T]() if iterator is None else converter(iterator):
        yield item

def ExcludeWhile[T](items: Iterable[T], predicate: Predicate[T]) -> Generator[T]:
    return __Exclude(items, lambda iterator: ExcluerEnumerator(AsEnumerator(iterator), predicate))
def ExcludeUntil[T](items: Iterable[T], predicate: Predicate[T]) -> Generator[T]:
    return __Exclude(items, lambda iterator: ExcluerUntilEnumerator(AsEnumerator(iterator), predicate))

def Concatenate[T](collection: Iterable[Iterable[T]]) -> Generator[T]:
    for iterable in collection:
        for item in iterable:
            yield item

def TryGetFirst[T](items: Iterable[T]) -> INullable[T]:
    for item in items:
        return GetNullable(item)
    
    return GetNullValue()

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
def EnsureOnlyOne[T](items: Iterable[T], predicate: Predicate[T], errorMessage: str|None = None) -> None:
    if not ValidateOnlyOne(items, predicate):
        raise ValueError("More than one value validating the given predicate were found." if errorMessage is None else errorMessage)