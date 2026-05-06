import collections.abc

from typing import final

from WinCopies.Collections import Generator
from WinCopies.Collections.Enumeration import IEnumerable, IEquatableEnumerable, IHashableEnumerable, ICountableEnumerable, IEnumerator, Enumerable, CountableEnumerable, EquatableEnumerable, EnumeratorBase, AbstractEnumeratorBase, AbstractEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator, IResumableEnumerationCursor
from WinCopies.Typing.Comparison import IEquatableItem

def GetGenerator[T](iterable: collections.abc.Iterable[T]) -> Generator[T]:
    yield from iterable
def TryGetGenerator[T](iterable: collections.abc.Iterable[T]|None) -> Generator[T]|None:
    if iterable is None:
        return None
    
    return GetGenerator(iterable)

class _Enumerable[T](Enumerable[T]):
    def __init__(self, enumerable: IEnumerable[T]) -> None:
        super().__init__()

        self.__enumerable: IEnumerable[T] = enumerable
    
    @final
    def _GetEnumerable(self) -> IEnumerable[T]:
        return self.__enumerable
    
    def TryGetEnumerator(self) -> IEnumerator[T] | None:
        return self._GetEnumerable().TryGetEnumerator()

class _EquatableEnumerable[T: IEquatableItem](EquatableEnumerable[T]):
    def __init__(self, enumerable: IEquatableEnumerable[T]) -> None:
        super().__init__()

        self.__enumerable: IEquatableEnumerable[T] = enumerable
    
    @final
    def _GetEnumerable(self) -> IEquatableEnumerable[T]:
        return self.__enumerable
    
    @final
    def Equals(self, item: object) -> bool:
        return self.__enumerable.Equals(item)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self._GetEnumerable().TryGetEnumerator()
class _HashableEnumerable[T: IEquatableItem](EquatableEnumerable[T], IHashableEnumerable[T]):
    def __init__(self, enumerable: IHashableEnumerable[T]) -> None:
        super().__init__()

        self.__enumerable: IHashableEnumerable[T] = enumerable
    
    @final
    def _GetEnumerable(self) -> IHashableEnumerable[T]:
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

class _CountableEnumerable[T](CountableEnumerable[T]):
    def __init__(self, enumerable: ICountableEnumerable[T]) -> None:
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

class _Enumerator[T](AbstractEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]) -> None:
        super().__init__(enumerator)
class _ResumableEnumerator[T](AbstractEnumeratorBase[T, T, IResumableEnumerator[T]], IResumableEnumerator[T]):
    def __init__(self, enumerator: IResumableEnumerator[T]) -> None:
        super().__init__(enumerator)
    
    @final
    def _AsContainer(self, container: IResumableEnumerator[T]) -> IEnumerator[T]:
        return container
    
    @final
    def _GetCurrent(self) -> T:
        return self._GetContainer().GetCurrent()
    
    @final
    def SupportsMultipleCursors(self) -> bool:
        return self._GetContainer().SupportsMultipleCursors()
    
    @final
    def PlaceCursor(self) -> IResumableEnumerationCursor:
        return self._GetContainer().PlaceCursor()
    @final
    def PlaceTopCursor(self) -> IResumableEnumerationCursor:
        return self._GetContainer().PlaceTopCursor()
    
    @final
    def MoveToTop(self, cursor: IResumableEnumerationCursor) -> None:
        return self._GetContainer().MoveToTop(cursor)
    
    @final
    def Resume(self, cursor: IResumableEnumerationCursor|None = None) -> None:
        return self._GetContainer().Resume(cursor)
    
    @final
    def Dispose(self) -> None:
        return self._GetContainer().Dispose()

def CreateEnumerable[T](enumerable: IEnumerable[T]) -> Enumerable[T]:
    return enumerable if type(enumerable) == _Enumerable[T] else _Enumerable[T](enumerable)
def TryCreateEnumerable[T](enumerable: IEnumerable[T]|None) -> Enumerable[T]|None:
    return None if enumerable is None else CreateEnumerable(enumerable)

def CreateEquatableEnumerable[T: IEquatableItem](enumerable: IEquatableEnumerable[T]) -> EquatableEnumerable[T]:
    return enumerable if type(enumerable) == _EquatableEnumerable[T] else _EquatableEnumerable[T](enumerable)
def TryCreateEquatableEnumerable[T: IEquatableItem](enumerable: IEquatableEnumerable[T]|None) -> EquatableEnumerable[T]|None:
    return None if enumerable is None else CreateEquatableEnumerable(enumerable)

def CreateHashableEnumerable[T: IEquatableItem](enumerable: IHashableEnumerable[T]) -> EquatableEnumerable[T]:
    return enumerable if type(enumerable) == _HashableEnumerable[T] else _HashableEnumerable[T](enumerable)
def TryCreateHashableEnumerable[T: IEquatableItem](enumerable: IEquatableEnumerable[T]|None) -> EquatableEnumerable[T]|None:
    return None if enumerable is None else CreateEquatableEnumerable(enumerable)

def CreateCountableEnumerable[T](enumerable: ICountableEnumerable[T]) -> CountableEnumerable[T]:
    return enumerable if type(enumerable) == _CountableEnumerable[T] else _CountableEnumerable[T](enumerable)
def TryCreateCountableEnumerable[T](enumerable: ICountableEnumerable[T]|None) -> CountableEnumerable[T]|None:
    return None if enumerable is None else CreateCountableEnumerable(enumerable)

def CreateEnumerator[T](enumerator: IEnumerator[T]) -> EnumeratorBase[T]:
    return enumerator if type(enumerator) == _Enumerator[T] else _Enumerator[T](enumerator)
def TryCreateEnumerator[T](enumerator: IEnumerator[T]|None) -> EnumeratorBase[T]|None:
    return None if enumerator is None else CreateEnumerator(enumerator)

def CreateResumableEnumerator[T](enumerator: IResumableEnumerator[T]) -> IResumableEnumerator[T]:
    return enumerator if type(enumerator) == _ResumableEnumerator[T] else _ResumableEnumerator[T](enumerator)
def TryCreateResumableEnumerator[T](enumerator: IResumableEnumerator[T]|None) -> IResumableEnumerator[T]|None:
    return None if enumerator is None else CreateResumableEnumerator(enumerator)