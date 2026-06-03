from collections.abc import Iterable

from WinCopies.Collections import Generator
from WinCopies.Collections.Util import MakeGenerator
from WinCopies.Typing.Delegate import Action, Method

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



def __DoForEachItem[T](items: Iterable[T], action: Method[T]) -> Generator[T]:
    for item in items:
        action(item)

        yield item
def __ForEachItem[T](items: Iterable[T], action: Method[T]) -> Generator[T]:
    for item in items:
        yield item

        action(item)
def __DoActionForEachItem[T](items: Iterable[T], pre: Method[T], post: Method[T]) -> Generator[T]:
    for item in items:
        pre(item)

        yield item

        post(item)

def DoForEachItem[T](items: Iterable[T]|None, action: Method[T]) -> Generator[T]:
    return MakeGenerator() if items is None else __DoForEachItem(items, action)
def TryDoForEachItem[T](items: Iterable[T]|None, action: Method[T]) -> Generator[T]|None:
    return None if items is None else __DoForEachItem(items, action)
def DoForEachItemValue[T](action: Method[T], *values: T) -> Generator[T]:
    return __DoForEachItem(values, action)

def ForEachItem[T](items: Iterable[T]|None, action: Method[T]) -> Generator[T]:
    return MakeGenerator() if items is None else __ForEachItem(items, action)
def TryForEachItem[T](items: Iterable[T]|None, action: Method[T]) -> Generator[T]|None:
    return None if items is None else __ForEachItem(items, action)
def ForEachValueItem[T](action: Method[T], *values: T) -> Generator[T]:
    return __ForEachItem(values, action)

def DoActionForEachItem[T](items: Iterable[T]|None, pre: Method[T], post: Method[T]) -> Generator[T]:
    return MakeGenerator() if items is None else __DoActionForEachItem(items, pre, post)
def TryDoActionForEachItem[T](items: Iterable[T]|None, pre: Method[T], post: Method[T]) -> Generator[T]|None:
    return None if items is None else __DoActionForEachItem(items, pre, post)
def DoActionForEachValueItem[T](pre: Method[T], post: Method[T], *values: T) -> Generator[T]:
    return __DoActionForEachItem(values, pre, post)