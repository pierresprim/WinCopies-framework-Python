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