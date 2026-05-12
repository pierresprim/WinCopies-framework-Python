from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import IInterface, IDisposable, Abstract
from WinCopies.Collections import IReadOnlyCollection
from WinCopies.Collections.Enumeration import IEnumerable, IEnumeratorBase, IEnumerator, EnumeratorBase, AbstractEnumeratorBase
from WinCopies.Collections.Generation import IResumable, INode
from WinCopies.Collections.Generation.Factory import IObjectFactory
from WinCopies.Typing import InvalidOperationError
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

class IResumableEnumerator[T](IEnumerator[T], IDisposable):
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
    
    def Dispose(self) -> None:
        self.Stop()

class IResumableEnumerable[T](IEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]|None:
        pass

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