from collections.abc import Iterable

from WinCopies.Collections import Generator

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