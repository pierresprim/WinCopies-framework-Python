import collections.abc

from collections.abc import Iterator
from typing import final

from WinCopies.Collections import Enumeration, Generator
from WinCopies.Collections.Enumeration import IIterable, ICountableIterable
from WinCopies.Typing import GenericConstraint, IGenericConstraintImplementation
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

def GetGenerator[T](iterable: collections.abc.Iterable[T]) -> Generator[T]:
    yield from iterable
def TryGetGenerator[T](iterable: collections.abc.Iterable[T]|None) -> Generator[T]|None:
    if iterable is None:
        return None
    
    return GetGenerator(iterable)

class IterableBase[TItems, TIterable](IIterable[TItems], GenericConstraint[TIterable, IIterable[TItems]]):
    def __init__(self, iterable: TIterable):
        EnsureDirectModuleCall()

        super().__init__()

        self.__iterable: TIterable = iterable
    
    @final
    def _GetContainer(self) -> TIterable:
        return self.__iterable
    @final
    def _GetIterable(self) -> IIterable[TItems]:
        return self._GetInnerContainer()
    
    @final
    def TryGetIterator(self) -> Iterator[TItems]|None:
        return self._GetIterable().TryGetIterator()
class Iterable[T](IterableBase[T, IIterable[T]], IGenericConstraintImplementation[IIterable[T]]):
    def __init__(self, iterable: IIterable[T]):
        super().__init__(iterable)
    
    @staticmethod
    def Create(iterable: collections.abc.Iterable[T]) -> collections.abc.Iterable[T]:
        return iterable if type(iterable) == Iterable[T] else Iterable[T](Enumeration.Iterable[T].Create(iterable))
    @staticmethod
    def TryCreate(iterable: collections.abc.Iterable[T]|None) -> collections.abc.Iterable[T]|None:
        return None if iterable is None else Iterable[T].Create(iterable)

class CountableIterable[T](IterableBase[T, ICountableIterable[T]], ICountableIterable[T], IGenericConstraintImplementation[ICountableIterable[T]]):
    def __init__(self, collection: ICountableIterable[T]):
        super().__init__(collection)
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()

    @staticmethod
    def Create(collection: ICountableIterable[T]) -> ICountableIterable[T]:
        return collection if type(collection) == CountableIterable[T] else CountableIterable[T](collection)
    @staticmethod
    def TryCreate(collection: ICountableIterable[T]|None) -> ICountableIterable[T]|None:
        return None if collection is None else CountableIterable[T].Create(collection)