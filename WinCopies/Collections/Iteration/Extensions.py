from collections.abc import Iterable

from WinCopies.Collections.Enumeration import IEnumerable, IReversableEnumerable
from WinCopies.Collections.Linked.Singly import CreateStack, CreateEnumerableStack

def GetReversed[T](items: Iterable[T]) -> IEnumerable[T]:
    def enumerate(items: IReversableEnumerable[T]) -> IEnumerable[T]:
        return items.AsReversed()
    
    return enumerate(items) if isinstance(items, IReversableEnumerable) else CreateEnumerableStack(items)
def Reverse[T](items: Iterable[T]) -> Iterable[T]:
    def enumerate(items: IReversableEnumerable[T]) -> IEnumerable[T]:
        return items.AsReversed()
    
    return enumerate(items).AsIterable() if isinstance(items, IReversableEnumerable) else CreateStack(items).AsGenerator()