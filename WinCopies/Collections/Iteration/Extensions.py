from collections.abc import Iterable, Collection
from typing import overload

from WinCopies.Collections.Enumeration.Core import IEnumerable, ICountableEnumerable, IReversableEnumerable
from WinCopies.Collections.Extensions import TryCountFromContainer
from WinCopies.Collections.Linked.Singly import CreateStack, CreateCountableQueue, CreateEnumerableStack, CreateCountableEnumerableQueue

@overload
def Count[T](items: ICountableEnumerable[T], makeGenerator: bool = False) -> tuple[ICountableEnumerable[T], int]: ...
@overload
def Count[T](items: Collection[T], makeGenerator: bool = False) -> tuple[Collection[T], int]: ... # type: ignore[overload-overlap]
@overload
def Count[T](items: Iterable[T], makeGenerator: bool = False) -> tuple[ICountableEnumerable[T], int]: ...
@overload
def Count(items: None, makeGenerator: bool = False) -> None: ...

def Count[T](items: ICountableEnumerable[T]|Collection[T]|Iterable[T]|None, makeGenerator: bool = False) -> tuple[Collection[T]|ICountableEnumerable[T], int]|None:
    def count(items: ICountableEnumerable[T]) -> tuple[ICountableEnumerable[T], int]: return (items, items.GetCount())

    return TryCountFromContainer(items, False, lambda items: count(CreateCountableQueue(items).AsCountableGenerator() if makeGenerator else CreateCountableEnumerableQueue(items)))

@overload
def CountAsIterable[T](items: ICountableEnumerable[T], makeGenerator: bool = False) -> tuple[Iterable[T], int]: ...
@overload
def CountAsIterable[T](items: Collection[T], makeGenerator: bool = False) -> tuple[Collection[T], int]: ...
@overload
def CountAsIterable[T](items: Iterable[T], makeGenerator: bool = False) -> tuple[Iterable[T], int]: ...
@overload
def CountAsIterable(items: None, makeGenerator: bool = False) -> None: ...

def CountAsIterable[T](items: ICountableEnumerable[T]|Collection[T]|Iterable[T]|None, makeGenerator: bool = False) -> tuple[Collection[T]|Iterable[T], int]|None:
    def count(items: ICountableEnumerable[T]) -> tuple[Iterable[T], int]: return (items.AsIterable(), items.GetCount())

    return TryCountFromContainer(items, True, lambda items: count(CreateCountableQueue(items).AsCountableGenerator() if makeGenerator else CreateCountableEnumerableQueue(items)))

def GetReversed[T](items: Iterable[T]) -> IEnumerable[T]:
    def enumerate(items: IReversableEnumerable[T]) -> IEnumerable[T]: return items.AsReversed()
    
    return enumerate(items) if isinstance(items, IReversableEnumerable) else CreateEnumerableStack(items)
def Reverse[T](items: Iterable[T]) -> Iterable[T]:
    def enumerate(items: IReversableEnumerable[T]) -> IEnumerable[T]: return items.AsReversed()
    
    return enumerate(items).AsIterable() if isinstance(items, IReversableEnumerable) else CreateStack(items).AsGenerator()