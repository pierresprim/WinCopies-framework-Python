from collections.abc import Iterable, Iterator

from WinCopies.Collections import Generator, Enumeration
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator
from WinCopies.Collections.Enumeration.Selection import ExcluerEnumerator, ExcluerUntilEnumerator
from WinCopies.Delegates import GetNotPredicate
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Converter, Predicate

def TryEnumerate[T](iterable: Iterable[T]|None) -> Iterable[T]:
    def getEmptyGenerator(*values: T) -> Generator[T]:
        yield from values

    return getEmptyGenerator() if iterable is None else iterable

def Concatenate[T](collection: Iterable[Iterable[T]|None]|None) -> Generator[T]:
    for iterable in TryEnumerate(collection):
        for item in TryEnumerate(iterable):
            yield item

def Append[T](items: Iterable[T]|None, values: Iterable[T]|None) -> Generator[T]:
    for item in TryEnumerate(items):
        yield item
    
    for value in TryEnumerate(values):
        yield value
def AppendItem[T](items: Iterable[T]|None, value: T) -> Generator[T]:
    for item in TryEnumerate(items):
        yield item
    
    yield value
def AppendValues[T](items: Iterable[T]|None, *values: T) -> Generator[T]:
    return Append(items, values)

def Prepend[T](items: Iterable[T]|None, values: Iterable[T]|None) -> Generator[T]:
    return Append(values, items)
def PrependItem[T](items: Iterable[T]|None, value: T) -> Generator[T]:
    yield value
    
    for item in TryEnumerate(items):
        yield item
def PrependValues[T](items: Iterable[T]|None, *values: T) -> Generator[T]:
    return Prepend(items, values)

def AppendTo[T](items: Iterable[T]|None, values: Iterable[T]|None) -> Generator[T]:
    for item in TryEnumerate(items):
        yield item

        for value in TryEnumerate(values):
            yield value
def AppendValuesTo[T](items: Iterable[T]|None, *values: T) -> Generator[T]:
    return AppendTo(items, values)

def PrependTo[T](items: Iterable[T]|None, values: Iterable[T]|None) -> Generator[T]:
    for item in TryEnumerate(items):
        for value in TryEnumerate(values):
            yield value
        
        yield item
def PrependValuesTo[T](items: Iterable[T]|None, *values: T) -> Generator[T]:
    return PrependTo(items, values)

def AppendItemTo[T](items: Iterable[T]|None, value: T) -> Generator[T]:
    for item in TryEnumerate(items):
        yield item

        yield value
def PrependItemTo[T](items: Iterable[T]|None, value: T) -> Generator[T]:
    for item in TryEnumerate(items):
        yield value

        yield item

def AppendIterable[T](items: Iterable[T]|None, values: Iterable[Iterable[T]|None]|None) -> Generator[T]:
    return Append(items, Concatenate(values))
def AppendIterableValues[T](items: Iterable[T]|None, *values: Iterable[T]|None) -> Generator[T]:
    return AppendIterable(items, values)

def PrependIterable[T](items: Iterable[T]|None, values: Iterable[Iterable[T]|None]|None) -> Generator[T]:
    return Append(Concatenate(values), items)
def PrependIterableValues[T](items: Iterable[T]|None, *values: Iterable[T]|None) -> Generator[T]:
    return PrependIterable(items, values)

def AppendIterableTo[T](items: Iterable[T]|None, values: Iterable[Iterable[T]|None]|None) -> Generator[T]:
    return AppendTo(items, Concatenate(values))
def AppendIterableValuesTo[T](items: Iterable[T]|None, *values: Iterable[T]|None) -> Generator[T]:
    return AppendIterableTo(items, values)

def PrependIterableTo[T](items: Iterable[T]|None, values: Iterable[Iterable[T]|None]|None) -> Generator[T]:
    return PrependTo(items, Concatenate(values))
def PrependIterableValuesTo[T](items: Iterable[T]|None, *values: Iterable[T]|None) -> Generator[T]:
    return PrependIterableTo(items, values)

def Select[TIn, TOut](items: Iterable[TIn]|None, converter: Converter[TIn, TOut]) -> Generator[TOut]:
    return (converter(item) for item in TryEnumerate(items))
def WhereSelect[TIn, TOut](items: Iterable[TIn]|None, predicate: Predicate[TIn], converter: Converter[TIn, TOut]) -> Generator[TOut]:
    return (converter(item) for item in TryEnumerate(items) if predicate(item))
def SelectWhere[TIn, TOut](items: Iterable[TIn]|None, converter: Converter[TIn, TOut], predicate: Predicate[TOut]) -> Generator[TOut]:
    result: TOut|None = None

    for item in TryEnumerate(items):
        if predicate(result := converter(item)):
            yield result

def Include[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    return (item for item in TryEnumerate(items) if predicate(item))
def Exclude[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    return Include(items, GetNotPredicate(predicate))

def IncludeWhile[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    for item in TryEnumerate(items):
        if predicate(item):
            yield item
        
        else:
            break
def IncludeUntil[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    for item in TryEnumerate(items):
        if predicate(item):
            break
        
        yield item

def DoIncludeUntil[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    for item in TryEnumerate(items):
        yield item

        if predicate(item):
            break
def DoIncludeWhile[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    return DoIncludeUntil(items, GetNotPredicate(predicate))

def __Exclude[T](items: Iterable[T]|None, converter: Converter[IEnumerator[T], IEnumerator[T]]) -> Generator[T]:
    def getEnumerator(enumerable: IEnumerable[T]|None) -> Iterator[T]|None:
        if enumerable is None:
            return None
        
        enumerator: IEnumerator[T]|None = enumerable.TryGetEnumerator()
        
        return None if enumerator is None else converter(enumerator).AsIterator()
    
    for item in TryEnumerate(getEnumerator(Enumeration.Iterable[T].TryCreate(items))):
        yield item

def ExcludeWhile[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    return __Exclude(items, lambda iterator: ExcluerEnumerator(iterator, predicate))
def ExcludeUntil[T](items: Iterable[T]|None, predicate: Predicate[T]) -> Generator[T]:
    return __Exclude(items, lambda iterator: ExcluerUntilEnumerator(iterator, predicate))

def TryGetFirst[T](items: Iterable[T]|None) -> INullable[T]|None:
    if items is None:
        return None
    
    for item in items:
        return GetNullable(item)
    
    return GetNullValue()

def Any[T](items: Iterable[T]|None) -> bool|None:
    if items is None:
        return None
    
    for _ in items:
        return True
    
    return False

def ValidateOnlyOne[T](items: Iterable[T]|None, predicate: Predicate[T]) -> bool|None:
    if items is None:
        return None
    
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
def EnsureOnlyOne[T](items: Iterable[T]|None, predicate: Predicate[T], errorMessage: str|None = None) -> None:
    if not ValidateOnlyOne(items, predicate):
        raise ValueError("More than one value validating the given predicate were found." if errorMessage is None else errorMessage)