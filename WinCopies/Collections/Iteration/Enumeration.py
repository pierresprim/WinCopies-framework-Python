from collections.abc import Iterable, Iterator, Collection

from WinCopies.Collections import Generator
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, ICountableEnumerable, TryAsIterable, AsEnumerable, AsEnumerator
from WinCopies.Collections.Enumeration.Selection import ExcluerEnumerator, ExcluerUntilEnumerator
from WinCopies.Collections.Iteration import Concatenate, TryEnumerate, Select, Include
from WinCopies.Collections.Util import MakeGenerator
from WinCopies.Typing.Delegate import Predicate, Selector
from WinCopies.Typing.Pairing import IKeyValuePair, CreateDualResult

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