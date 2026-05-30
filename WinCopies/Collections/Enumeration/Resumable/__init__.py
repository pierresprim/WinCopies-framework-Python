from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator
from typing import final, Any

from WinCopies import IInterface, IDisposable, Abstract
from WinCopies.Collections.Core import IReadOnlyCollection
from WinCopies.Collections.Enumeration import EnumerationResult, EnumerationState, IEnumerable, ICountableEnumerable, IEnumeratorBase, IEnumerator, IDisposableEnumerator, Enumerable, CountableEnumerable, IteratorBase, EnumeratorBase, EnumeratorProvider, AbstractEnumeratorBase, DisposableEnumeratorBase, GetEmptyEnumerable, GetEmptyEnumerator, GetEnumeratorInactiveError
from WinCopies.Collections.Generation import IResumable, INode
from WinCopies.Collections.Generation.Factory import IObjectFactory
from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Delegate import Function
from WinCopies.Typing.Generic import IGenericConstraintImplementation

class ICookie[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def SetCursor(self, value: T) -> None:
        pass

class IResumableEnumerationCursor(IResumable, IDisposable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def MoveToTop(self) -> None:
        pass

class IResumableEnumerator[T](IEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def SupportsMultipleCursors(self) -> bool:
        pass
    
    @abstractmethod
    def PlaceCursor(self) -> IResumableEnumerationCursor:
        pass
    @abstractmethod
    def PlaceTopCursor(self) -> IResumableEnumerationCursor:
        pass

    @abstractmethod
    def MoveToTop(self, cursor: IResumableEnumerationCursor) -> None:
        pass

    @abstractmethod
    def Resume(self, cursor: IResumableEnumerationCursor|None = None) -> None:
        pass
class IDefaultResumableEnumerator[TItem, TCursorValue](IResumableEnumerator[TItem]):
    @final
    class _Cookie[_TItem, _TCursorValue](Abstract, ICookie[_TCursorValue]):
        def __init__(self, enumerator: IDefaultResumableEnumerator[_TItem, _TCursorValue]) -> None:
            super().__init__()

            self.__enumerator: IDefaultResumableEnumerator[_TItem, _TCursorValue] = enumerator
        
        def SetCursor(self, value: _TCursorValue) -> None:
            self.__enumerator._SetCursor(value)
    
    def __init__(self) -> None:
        super().__init__()
    
    @staticmethod
    def _GetException(msg: str) -> InvalidOperationError:
        return InvalidOperationError(f"Cannot {msg} before the enumeration has started.")
    @staticmethod
    def _GetCursorException(msg: str) -> InvalidOperationError:
        return IDefaultResumableEnumerator._GetException(f"{msg} a cursor")
    
    @abstractmethod
    def _GetFirstCursor(self) -> IResumableEnumerationCursor:
        pass

    @abstractmethod
    def _SetCursor(self, value: TCursorValue) -> None:
        pass

    @final
    def _CreateCursorCookie(self) -> ICookie[TCursorValue]:
        return IDefaultResumableEnumerator[TItem, TCursorValue]._Cookie(self)
    
    @abstractmethod
    def _PlaceCursor(self) -> IResumableEnumerationCursor:
        pass
    
    @final
    def PlaceCursor(self) -> IResumableEnumerationCursor:
        if self.IsStarted():
            return self._PlaceCursor()
        
        raise IDefaultResumableEnumerator._GetCursorException("place")
    @final
    def PlaceTopCursor(self) -> IResumableEnumerationCursor:
        cursor: IResumableEnumerationCursor = self.PlaceCursor()

        cursor.MoveToTop()

        return cursor
    
    @final
    def MoveToTop(self, cursor: IResumableEnumerationCursor) -> None:
        if self.IsStarted():
            cursor.MoveToTop()
        
        else:
            raise IDefaultResumableEnumerator._GetCursorException("move")
    
    @final
    def Resume(self, cursor: IResumableEnumerationCursor|None = None) -> None:
        if self.IsStarted():
            (self._GetFirstCursor() if cursor is None else cursor).Resume()
        
        else:
            raise IDefaultResumableEnumerator._GetException("resume")

class IResumableEnumerable[T](IEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]|None:
        pass
    @final
    def GetResumableEnumerator(self) -> IResumableEnumerator[T]:
        return GetResumableEnumerator(self.TryGetResumableEnumerator())

class IResumableCountableEnumerable[T](IResumableEnumerable[T], ICountableEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
class ResumableCountableEnumerable[T](CountableEnumerable[T], IResumableCountableEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()

class ResumableEnumeratorBase[T](EnumeratorBase[T], IResumableEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()
class ResumableEnumerator[T](ResumableEnumeratorBase[T]):
    def __init__(self) -> None:
        super().__init__()

class IResumableEnumerationCursorFactory[T: IResumableEnumerationCursor](IObjectFactory[T], IReadOnlyCollection):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def GetFirstCursor(self) -> IResumableEnumerationCursor:
        pass
class IDefaultResumableEnumerationCursorFactory[T: IResumableEnumerationCursor](IResumableEnumerationCursorFactory[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _InitializeCursor(self, cursor: T, node: INode) -> None:
        pass

class AbstractResumableEnumeratorAbstract[TIn, TOut, TEnumerator: IEnumeratorBase](AbstractEnumeratorBase[TIn, TOut, TEnumerator], IResumableEnumerator[TOut]):
    def __init__(self, enumerator: TEnumerator) -> None:
        super().__init__(enumerator)
class AbstractResumableEnumeratorBase[TItem, TEnumerator: IEnumeratorBase](AbstractResumableEnumeratorAbstract[TItem, TItem, TEnumerator]):
    def __init__(self, enumerator: TEnumerator) -> None:
        super().__init__(enumerator)
class AbstractResumableEnumerator[T](AbstractResumableEnumeratorBase[T, IResumableEnumerator[T]], IGenericConstraintImplementation[IResumableEnumerator[T]]):
    def __init__(self, enumerator: IResumableEnumerator[T]) -> None:
        super().__init__(enumerator)

class IDisposableResumableEnumerator[T](IResumableEnumerator[T], IDisposableEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()

@final
class _EmptyEnumerator[T](IteratorBase[T], IResumableEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def GetState(self) -> EnumerationState:
        return GetEmptyEnumerator().GetState()
    def GetResult(self) -> EnumerationResult:
        return GetEmptyEnumerator().GetResult()
    
    def GetCurrent(self) -> T:
        return GetEmptyEnumerator().GetCurrent() # pyright: ignore[reportUnknownVariableType]
    def MoveNext(self) -> bool:
        return GetEmptyEnumerator().MoveNext()
    def Stop(self) -> None:
        GetEmptyEnumerator().Stop()
    def TryReset(self) -> bool|None:
        return GetEmptyEnumerator().TryReset()
    def IsResetSupported(self) -> bool:
        return GetEmptyEnumerator().IsResetSupported()
    def HasProcessedItems(self) -> bool:
        return GetEmptyEnumerator().HasProcessedItems()
    def SupportsMultipleCursors(self) -> bool:
        return False
    def PlaceCursor(self) -> IResumableEnumerationCursor:
        raise GetEnumeratorInactiveError()
    def PlaceTopCursor(self) -> IResumableEnumerationCursor:
        raise GetEnumeratorInactiveError()
    def MoveToTop(self, cursor: IResumableEnumerationCursor) -> None:
        raise GetEnumeratorInactiveError()
    def Resume(self, cursor: IResumableEnumerationCursor|None = None) -> None:
        raise GetEnumeratorInactiveError()
@final
class _EmptyEnumerable[T](Iterable[T], IResumableEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return GetEmptyEnumerable().TryGetEnumerator() # pyright: ignore[reportUnknownVariableType]
    def TryGetResumableEnumerator(self) -> None:
        return None
    
    def AsIterable(self) -> Iterable[T]:
        return GetEmptyEnumerable().AsIterable() # pyright: ignore[reportUnknownVariableType]
    
    def __iter__(self) -> Iterator[T]:
        return GetEmptyEnumerator().AsIterator() # pyright: ignore[reportUnknownVariableType]

class ResumableEnumerable[T](Enumerable[T], IResumableEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()

class ResumableEnumeratorProvider[T](EnumeratorProvider[T], IResumableEnumerable[T]):
    def __init__(self, enumeratorProvider: Function[IEnumerator[T]|None]|None, resumableEnumeratorProvider: Function[IResumableEnumerator[T]|None]|None) -> None:
        super().__init__(enumeratorProvider)
        
        self.__resumableEnumeratorProvider: Function[IResumableEnumerator[T]|None]|None = resumableEnumeratorProvider
    
    @final
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]|None:
        return None if self.__resumableEnumeratorProvider is None else self.__resumableEnumeratorProvider()

@final
class _DisposedEnumerator[T](Abstract, IResumableEnumerator[T]):
    def __init__(self, enumerator: IEnumerator[T]) -> None:
        super().__init__()

        self.__enumerator: IEnumerator[T] = enumerator
    
    def GetState(self) -> EnumerationState:
        return GetEmptyEnumerator().GetState()
    def GetResult(self) -> EnumerationResult:
        return GetEmptyEnumerator().GetResult()
    
    def MoveNext(self) -> bool:
        return self.__enumerator.MoveNext()
    def Stop(self) -> None:
        return self.__enumerator.Stop()
    def TryReset(self) -> bool|None:
        return self.__enumerator.TryReset()
    def IsResetSupported(self) -> bool:
        return self.__enumerator.IsResetSupported()
    def HasProcessedItems(self) -> bool:
        return self.__enumerator.HasProcessedItems()
    def GetCurrent(self) -> T:
        return self.__enumerator.GetCurrent()
    def AsIterator(self) -> Iterator[T]:
        return self.__enumerator.AsIterator()
    def SupportsMultipleCursors(self) -> bool:
        return False
    def PlaceCursor(self) -> IResumableEnumerationCursor:
        raise InvalidOperationError()
    def PlaceTopCursor(self) -> IResumableEnumerationCursor:
        raise InvalidOperationError()
    def MoveToTop(self, cursor: IResumableEnumerationCursor) -> None:
        raise InvalidOperationError()
    def Resume(self, cursor: IResumableEnumerationCursor|None = None) -> None:
        raise InvalidOperationError()

@final
class _DisposableEnumerator[T](DisposableEnumeratorBase[T, IResumableEnumerator[T]], IDisposableResumableEnumerator[T], IGenericConstraintImplementation[IResumableEnumerator[T]]):
    def __init__(self, enumerator: IResumableEnumerator[T]) -> None:
        super().__init__(enumerator)
    
    def _GetDisposedEnumerator(self) -> IResumableEnumerator[T]:
        return _DisposedEnumerator[T](self._GetDefaultDisposedEnumerator())
    
    def SupportsMultipleCursors(self) -> bool:
        return self._GetContainer().SupportsMultipleCursors()
    
    def PlaceCursor(self) -> IResumableEnumerationCursor:
        return self._GetContainer().PlaceCursor()
    def PlaceTopCursor(self) -> IResumableEnumerationCursor:
        return self._GetContainer().PlaceTopCursor()
    
    def MoveToTop(self, cursor: IResumableEnumerationCursor) -> None:
        return self._GetContainer().MoveToTop(cursor)
    
    def Resume(self, cursor: IResumableEnumerationCursor|None = None) -> None:
        return self._GetContainer().Resume(cursor)

__emptyEnumerator = _EmptyEnumerator[Any]()
__emptyEnumerable = _EmptyEnumerable[Any]()

def TryGetResumableEnumerator[T](enumerable: IResumableEnumerable[T]|None) -> IResumableEnumerator[T]|None:
    return None if enumerable is None else enumerable.TryGetResumableEnumerator()

def GetEmptyResumableEnumerable[T]() -> IResumableEnumerable[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __emptyEnumerable
def GetEmptyResumableEnumerator[T]() -> IResumableEnumerator[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __emptyEnumerator

def GetResumableEnumerable[T](enumerable: IResumableEnumerable[T]|None) -> IResumableEnumerable[T]:
    return GetEmptyResumableEnumerable() if enumerable is None else enumerable
def GetResumableEnumerator[T](enumerator: IResumableEnumerator[T]|None) -> IResumableEnumerator[T]:
    return GetEmptyResumableEnumerator() if enumerator is None else enumerator

def CreateResumableEnumeratorProvider[T](enumeratorProvider: Function[IEnumerator[T]|None], resumableEnumeratorProvider: Function[IResumableEnumerator[T]|None]|None) -> IResumableEnumerable[T]:
    return ResumableEnumeratorProvider[T](enumeratorProvider, resumableEnumeratorProvider)
def TryCreateResumableEnumeratorProvider[T](enumeratorProvider: Function[IResumableEnumerator[T]|None]|None, resumableEnumeratorProvider: Function[IResumableEnumerator[T]|None]|None) -> IResumableEnumerable[T]|None:
    return None if enumeratorProvider is None else CreateResumableEnumeratorProvider(enumeratorProvider, resumableEnumeratorProvider)

def ToDisposableResumableEnumerator[T](enumerator: IResumableEnumerator[T]) -> IDisposableResumableEnumerator[T]:
    return enumerator if isinstance(enumerator, IDisposableResumableEnumerator) else _DisposableEnumerator[T](enumerator)