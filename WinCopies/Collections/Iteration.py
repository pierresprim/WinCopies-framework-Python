from typing import Iterable

def Append[T](items: Iterable[T], values: Iterable[T]) -> Iterable[T]:
    for item in items:
        yield item
    
    for value in values:
        yield value
def AppendValues[T](items: Iterable[T], *values: T) -> Iterable[T]:
    return Append(items, values)

def Prepend[T](items: Iterable[T], values: Iterable[T]) -> Iterable[T]:
    return Append(values, items)
def PrependValues[T](items: Iterable[T], *values: T) -> Iterable[T]:
    return Prepend(items, values)