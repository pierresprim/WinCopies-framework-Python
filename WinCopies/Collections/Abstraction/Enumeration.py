import collections.abc

from typing import final

from WinCopies.Collections import Generator
from WinCopies.Collections.Enumeration import IEnumerable, IEquatableEnumerable, ICountableEnumerable, IEnumerator, Enumerable as EnumerableBase, CountableEnumerable as CountableEnumerableBase, EquatableEnumerable as EquatableEnumerableBase, EnumeratorBase, AbstractEnumerator
from WinCopies.Typing import IEquatableItem
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

def GetGenerator[T](iterable: collections.abc.Iterable[T]) -> Generator[T]:
    yield from iterable
def TryGetGenerator[T](iterable: collections.abc.Iterable[T]|None) -> Generator[T]|None:
    if iterable is None:
        return None
    
    return GetGenerator(iterable)

class Enumerable[T](EnumerableBase[T]):
    def __init__(self, enumerable: IEnumerable[T]):
        EnsureDirectModuleCall()

        super().__init__()

        self.__enumerable: IEnumerable[T] = enumerable
    
    @final
    def _GetEnumerable(self) -> IEnumerable[T]:
        return self.__enumerable
    
    def TryGetEnumerator(self) -> IEnumerator[T] | None:
        return self._GetEnumerable().TryGetEnumerator()
    
    @staticmethod
    def Create(enumerable: IEnumerable[T]) -> EnumerableBase[T]:
        return enumerable if type(enumerable) == Enumerable[T] else Enumerable[T](enumerable)
    @staticmethod
    def TryCreate(enumerable: IEnumerable[T]|None) -> EnumerableBase[T]|None:
        return None if enumerable is None else Enumerable[T].Create(enumerable)

class EquatableEnumerable[T: IEquatableItem](EquatableEnumerableBase[T]):
    def __init__(self, enumerable: IEquatableEnumerable[T]):
        EnsureDirectModuleCall()

        super().__init__()

        self.__enumerable: IEquatableEnumerable[T] = enumerable
    
    @final
    def _GetEnumerable(self) -> IEquatableEnumerable[T]:
        return self.__enumerable
    
    @final
    def Equals(self, item: object) -> bool:
        return self.__enumerable.Equals(item)
    
    @final
    def Hash(self) -> int:
        return self.__enumerable.Hash()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self._GetEnumerable().TryGetEnumerator()
    
    @staticmethod
    def Create(enumerable: IEquatableEnumerable[T]) -> EquatableEnumerableBase[T]:
        return enumerable if type(enumerable) == EquatableEnumerable[T] else EquatableEnumerable[T](enumerable)
    @staticmethod
    def TryCreate(enumerable: IEquatableEnumerable[T]|None) -> EquatableEnumerableBase[T]|None:
        return None if enumerable is None else EquatableEnumerable[T].Create(enumerable)
class CountableEnumerable[T](CountableEnumerableBase[T]):
    def __init__(self, enumerable: ICountableEnumerable[T]):
        EnsureDirectModuleCall()

        super().__init__()

        self.__enumerable: ICountableEnumerable[T] = enumerable
    
    @final
    def _GetEnumerable(self) -> ICountableEnumerable[T]:
        return self.__enumerable
    
    @final
    def GetCount(self) -> int:
        return self._GetEnumerable().GetCount()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self._GetEnumerable().TryGetEnumerator()
    
    @staticmethod
    def Create(enumerable: ICountableEnumerable[T]) -> CountableEnumerableBase[T]:
        return enumerable if type(enumerable) == CountableEnumerable[T] else CountableEnumerable[T](enumerable)
    @staticmethod
    def TryCreate(enumerable: ICountableEnumerable[T]|None) -> CountableEnumerableBase[T]|None:
        return None if enumerable is None else CountableEnumerable[T].Create(enumerable)

class Enumerator[T](AbstractEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]):
        EnsureDirectModuleCall()

        super().__init__(enumerator)
    
    @staticmethod
    def Create(enumerator: IEnumerator[T]) -> EnumeratorBase[T]:
        return enumerator if type(enumerator) == Enumerator[T] else Enumerator[T](enumerator)
    @staticmethod
    def TryCreate(enumerator: IEnumerator[T]|None) -> EnumeratorBase[T]|None:
        return None if enumerator is None else Enumerator[T].Create(enumerator)