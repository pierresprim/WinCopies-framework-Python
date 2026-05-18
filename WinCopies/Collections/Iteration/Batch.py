from collections.abc import Iterable, Collection, Sequence
from typing import Callable

from WinCopies.Collections import Generator, IReadOnlyCountableIndexable, MakeGenerator
from WinCopies.Collections.Enumeration import IEnumerator, ICountableEnumerable, CreateIterable
from WinCopies.Typing.Delegate import Function

def Batch[T](items: IReadOnlyCountableIndexable[T]|ICountableEnumerable[T]|Sequence[T]|Collection[T]|Iterable[T], size: int, safe: bool = True) -> Generator[Generator[T]]:
    def __getRange(start: int, stop: int) -> Iterable[int]:
        return range(start, stop)
    def _getRange(start: int) -> Iterable[int]:
        return __getRange(start, start + size)
    def getRange() -> Iterable[int]:
        return _getRange(0)
    
    def batch(items: Iterable[T]) -> Generator[Generator[T]]:
        def batch(enumerator: IEnumerator[T]) -> Generator[Generator[T]]:
            def enumerate() -> Generator[T]:
                for _ in getRange():
                    if enumerator.MoveNext():
                        yield enumerator.GetCurrent()
                    
                    else:
                        break
            
            yield enumerate()

            while enumerator.IsStarted():
                yield enumerate()
        def safeBatch(enumerator: IEnumerator[T]) -> Generator[Generator[T]]:
            def enumerate() -> Generator[T]:
                def enumerate() -> Generator[T]:
                    for _ in __getRange(1, size):
                        if enumerator.MoveNext():
                            yield enumerator.GetCurrent()
                        
                        else:
                            break
                
                yield enumerator.GetCurrent()
                
                for item in enumerate():
                    yield item
            def iterate() -> Generator[T]:
                yield enumerator.GetCurrent()
            
            def getGenerator(func: Function[Generator[T]]) -> Generator[Generator[T]]:
                yield func()

                while enumerator.MoveNext():
                    yield func()
            
            return getGenerator(iterate) if size == 1 else (getGenerator(enumerate) if enumerator.MoveNext() else MakeGenerator())

        enumerator: IEnumerator[T]|None = CreateIterable(items).TryGetEnumerator()

        return MakeGenerator() if enumerator is None else (safeBatch if safe else batch)(enumerator)

    def _batch[TList](items: TList, count: int, getAt: Callable[[TList, int], T]) -> Generator[Generator[T]]:
        def _getAt(index: int) -> T:
            return getAt(items, index)
        
        def batch(length: int) -> Generator[Generator[T]]:
            def enumerate(start: int) -> Generator[T]:
                for i in _getRange(start):
                    yield _getAt(i)
            
            def enumerateRemaining() -> Generator[Generator[T]]:
                start: int = size
                count: int = length

                def decrement() -> None:
                    nonlocal count

                    count -= size
                
                def enumerateRemaining() -> Generator[T]:
                    for i in __getRange(start, length):
                        yield _getAt(i)

                decrement()
                
                while size < count:
                    yield enumerate(start)

                    start += size

                    decrement()
                
                if count > 0:
                    yield enumerateRemaining()

            yield enumerate(0)

            for batch in enumerateRemaining():
                yield batch
        
        def enumerateAll() -> Generator[Generator[T]]:
            def enumerate() -> Generator[T]:
                for i in getRange():
                    yield _getAt(i)
            
            yield enumerate()
        
        return enumerateAll() if size >= count else batch(count)

    def batchFromIndexable(items: IReadOnlyCountableIndexable[T]) -> Generator[Generator[T]]:
        return _batch(items, items.GetCount(), lambda items, index: items.GetAt(index))
    def batchFromSequence(items: Sequence[T]) -> Generator[Generator[T]]:
        return _batch(items, len(items), lambda items, index: items[index])

    def batchFromCollection(items: Iterable[T], count: int) -> Generator[Generator[T]]:
        def getIterator() -> Generator[Generator[T]]:
            def iterate() -> Generator[T]:
                for item in items:
                    yield item
            
            yield iterate()
        
        return MakeGenerator() if count < 1 else (getIterator() if size >= count else batch(items))

    def batchFromEnumerable(items: ICountableEnumerable[T]) -> Generator[Generator[T]]:
        return batchFromCollection(items.AsIterable(), items.GetCount())
    def batchFromIterable(items: Collection[T]) -> Generator[Generator[T]]:
        return batchFromCollection(items, len(items))
    
    match items:
        case IReadOnlyCountableIndexable():
            return batchFromIndexable(items)
        case Sequence():
            return batchFromSequence(items)
        
        case ICountableEnumerable():
            return batchFromEnumerable(items)
        case Collection():
            return batchFromIterable(items)
        
        case _:
            return batch(items)