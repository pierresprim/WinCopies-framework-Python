from collections.abc import Iterable

from WinCopies.Collections import Generator
from WinCopies.Collections.Util import MakeGenerator
from WinCopies.Typing.Delegate import Action

def __DoForEach[T](items: Iterable[T], action: Action) -> Generator[T]:
    for item in items:
        action()

        yield item
def __ForEach[T](items: Iterable[T], action: Action) -> Generator[T]:
    for item in items:
        yield item

        action()
def __DoActionForEach[T](items: Iterable[T], pre: Action, post: Action) -> Generator[T]:
    for item in items:
        pre()

        yield item

        post()

def DoForEach[T](items: Iterable[T]|None, action: Action) -> Generator[T]:
    return MakeGenerator() if items is None else __DoForEach(items, action)
def TryDoForEach[T](items: Iterable[T]|None, action: Action) -> Generator[T]|None:
    return None if items is None else __DoForEach(items, action)
def DoForEachValue[T](action: Action, *values: T) -> Generator[T]:
    return __DoForEach(values, action)

def ForEach[T](items: Iterable[T]|None, action: Action) -> Generator[T]:
    return MakeGenerator() if items is None else __ForEach(items, action)
def TryForEach[T](items: Iterable[T]|None, action: Action) -> Generator[T]|None:
    return None if items is None else __ForEach(items, action)
def ForEachValue[T](action: Action, *values: T) -> Generator[T]:
    return __ForEach(values, action)

def DoActionForEach[T](items: Iterable[T]|None, pre: Action, post: Action) -> Generator[T]:
    return MakeGenerator() if items is None else __DoActionForEach(items, pre, post)
def TryDoActionForEach[T](items: Iterable[T]|None, pre: Action, post: Action) -> Generator[T]|None:
    return None if items is None else __DoActionForEach(items, pre, post)
def DoActionForEachValue[T](pre: Action, post: Action, *values: T) -> Generator[T]:
    return __DoActionForEach(values, pre, post)