from abc import abstractmethod
from collections.abc import Iterable
from typing import final

from WinCopies.Collections import Generator
from WinCopies.Collections.Enumeration.Abstraction import AbstractEnumeratorBase, AbstractEnumerator
from WinCopies.Collections.Enumeration.Core import IEnumerable, IEquatableEnumerable, IHashableEnumerable, ICountableEnumerable, IEnumerator, Enumerable, CountableEnumerable, EquatableEnumerable, HashableEnumerable, EnumeratorBase
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator, IResumableEnumerationCursor
from WinCopies.Typing.Comparison import EquatableProtocol, HashableProtocol

def GetGenerator[T](iterable: Iterable[T]) -> Generator[T]:
    yield from iterable
def TryGetGenerator[T](iterable: Iterable[T]|None) -> Generator[T]|None:
    return None if iterable is None else GetGenerator(iterable)

class _IEnumerable[T](IEnumerable[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetEnumerable(self) -> IEnumerable[T]:
        ...
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self._GetEnumerable().TryGetEnumerator()
class _IEquatableEnumerable[T](_IEnumerable[T], IEquatableEnumerable[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetEnumerable(self) -> IEquatableEnumerable[T]:
        ...
    
    @final
    def Equals(self, item: object) -> bool: return self._GetEnumerable().Equals(item)

class _Enumerable[T](Enumerable[T], _IEnumerable[T]):
    def __init__(self, enumerable: IEnumerable[T]) -> None:
        super().__init__()

        self.__enumerable: IEnumerable[T] = enumerable
    
    @final
    def _GetEnumerable(self) -> IEnumerable[T]: return self.__enumerable

class _EquatableEnumerable[T: EquatableProtocol](EquatableEnumerable[T], _IEquatableEnumerable[T]):
    def __init__(self, enumerable: IEquatableEnumerable[T]) -> None:
        super().__init__()

        self.__enumerable: IEquatableEnumerable[T] = enumerable
    
    @final
    def _GetEnumerable(self) -> IEquatableEnumerable[T]: return self.__enumerable
class _HashableEnumerable[T: HashableProtocol](HashableEnumerable[T], _IEquatableEnumerable[T]):
    def __init__(self, enumerable: IHashableEnumerable[T]) -> None:
        super().__init__()

        self.__enumerable: IHashableEnumerable[T] = enumerable
    
    @final
    def _GetEnumerable(self) -> IHashableEnumerable[T]: return self.__enumerable
    
    @final
    def Hash(self) -> int: return self._GetEnumerable().Hash()

class _CountableEnumerable[T](CountableEnumerable[T], _IEnumerable[T]):
    def __init__(self, enumerable: ICountableEnumerable[T]) -> None:
        super().__init__()

        self.__enumerable: ICountableEnumerable[T] = enumerable
    
    @final
    def _GetEnumerable(self) -> ICountableEnumerable[T]: return self.__enumerable
    
    @final
    def GetCount(self) -> int: return self._GetEnumerable().GetCount()

class _Enumerator[T](AbstractEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]) -> None: super().__init__(enumerator)
class _ResumableEnumerator[T](AbstractEnumeratorBase[T, T, IResumableEnumerator[T]], IResumableEnumerator[T]):
    def __init__(self, enumerator: IResumableEnumerator[T]) -> None: super().__init__(enumerator)
    
    @final
    def _AsContainer(self, container: IResumableEnumerator[T]) -> IEnumerator[T]: return container
    
    @final
    def _GetCurrent(self) -> T: return self._GetContainer().GetCurrent()
    
    @final
    def SupportsMultipleCursors(self) -> bool: return self._GetContainer().SupportsMultipleCursors()
    
    @final
    def PlaceCursor(self) -> IResumableEnumerationCursor: return self._GetContainer().PlaceCursor()
    @final
    def PlaceTopCursor(self) -> IResumableEnumerationCursor: return self._GetContainer().PlaceTopCursor()
    
    @final
    def MoveToTop(self, cursor: IResumableEnumerationCursor) -> None: return self._GetContainer().MoveToTop(cursor)
    
    @final
    def Resume(self, cursor: IResumableEnumerationCursor|None = None) -> None: return self._GetContainer().Resume(cursor)

def CreateEnumerable[T](enumerable: IEnumerable[T]) -> Enumerable[T]:
    return enumerable if type(enumerable) == _Enumerable[T] else _Enumerable[T](enumerable)
def TryCreateEnumerable[T](enumerable: IEnumerable[T]|None) -> Enumerable[T]|None:
    return None if enumerable is None else CreateEnumerable(enumerable)

def CreateEquatableEnumerable[T: EquatableProtocol](enumerable: IEquatableEnumerable[T]) -> EquatableEnumerable[T]:
    return enumerable if type(enumerable) == _EquatableEnumerable[T] else _EquatableEnumerable[T](enumerable)
def TryCreateEquatableEnumerable[T: EquatableProtocol](enumerable: IEquatableEnumerable[T]|None) -> EquatableEnumerable[T]|None:
    return None if enumerable is None else CreateEquatableEnumerable(enumerable)

def CreateHashableEnumerable[T: HashableProtocol](enumerable: IHashableEnumerable[T]) -> HashableEnumerable[T]:
    return enumerable if type(enumerable) == _HashableEnumerable[T] else _HashableEnumerable[T](enumerable)
def TryCreateHashableEnumerable[T: HashableProtocol](enumerable: IHashableEnumerable[T]|None) -> HashableEnumerable[T]|None:
    return None if enumerable is None else CreateHashableEnumerable(enumerable)

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