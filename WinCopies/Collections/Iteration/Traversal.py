from collections.abc import Iterable, Iterator
from typing import Final

from WinCopies.Collections import Generator
from WinCopies.Collections.Iteration import PrependItem, GetFirst
from WinCopies.Typing import INullable
from WinCopies.Typing.Delegate import Action, Method, Function, Predicate
from WinCopies.Typing.Extensions import IExceptionGroupBuilder, ExceptionGroupBuilder
from WinCopies.Typing.Pairing import DualResult, CreateDualResult

_NONE: Final = object()

def Loop[T](items: Iterable[T], action: Method[T]) -> bool:
    item: object = _NONE

    for item in items: action(item)

    return item is not _NONE
def TryLoop[T](items: Iterable[T]|None, action: Method[T]) -> bool|None:
    return None if items is None else Loop(items, action)

def Enumerate[T](items: Iterable[T]) -> DualResult[Iterator[T], Function[bool]]:
    item: object = _NONE

    def loop() -> Generator[T]:
        nonlocal item

        for item in items: yield item

    return CreateDualResult(loop(), lambda: item is not _NONE)
def TryEnumerate[T](items: Iterable[T]|None) -> DualResult[Iterator[T], Function[bool]]|None:
    return None if items is None else Enumerate(items)

def Iterate[T](items: Iterable[T], action: Method[Iterable[T]], firstAction: Predicate[T]|None) -> bool:
    def enumerate() -> bool:
        item: object = _NONE

        def loop() -> Generator[T]:
            nonlocal item

            for item in items: yield item

        action(loop())

        return item is not _NONE

    def iterate(firstAction: Predicate[T]) -> bool:
        def iterate(first: T) -> bool:
            if firstAction(first):
                action(PrependItem(items, first))

                return True

            return False

        nonlocal items

        first: INullable[T] = GetFirst(items := iter(items))
        
        return first.HasValue() and iterate(first.GetValue())

    return enumerate() if firstAction is None else iterate(firstAction)
def TryIterate[T](items: Iterable[T]|None, action: Method[Iterable[T]], firstAction: Predicate[T]|None) -> bool|None:
    return None if items is None else Iterate(items, action, firstAction)

def ForEachItemUntil[T](items: Iterable[T], predicate: Predicate[T]) -> bool|None:
    """Iterates over items until the given predicate returns True.

    Args:
        items: The items to iterate over.
        predicate: A function to test each item.

    Returns:
        - None if no items processed
        - True if predicate matched
        - False if completed without match.
    """
    item: object = _NONE

    for item in items:
        if predicate(item): return True
    
    return None if item is _NONE else False

def __ProcessSafe(func: Predicate[Method[Exception]], finalizer: Method[bool]|None) -> bool:
    exceptions: IExceptionGroupBuilder = ExceptionGroupBuilder()
    
    result: bool = func(exceptions.Push)

    if finalizer is not None: finalizer(exceptions.HasItems())

    exceptions.TryThrow()

    return result

def IterateSafe(iterator: Predicate[Action], action: Action, safe: bool|Method[bool]) -> bool:
    def iterate(finalizer: Method[bool]|None = None) -> bool:
        def process(onError: Method[Exception]) -> None:
            try: action()
            except Exception as e: onError(e)
        
        return __ProcessSafe(lambda onError: iterator(lambda: process(onError)), finalizer)
    
    return (iterate() if safe else iterator(action)) if isinstance(safe, bool) else iterate(safe)
def EnumerateSafe[T](items: Iterable[T], action: Method[T], safe: bool|Method[bool]) -> bool:
    def iterate(finalizer: Method[bool]|None = None) -> bool:
        def process(item: T, onError: Method[Exception]) -> None:
            try: action(item)
            except Exception as e: onError(e)

        return __ProcessSafe(lambda onError: Loop(items, lambda item: process(item, onError)), finalizer)

    return (iterate() if safe else Loop(items, action)) if isinstance(safe, bool) else iterate(safe)