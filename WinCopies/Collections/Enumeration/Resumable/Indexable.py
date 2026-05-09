from __future__ import annotations

from abc import abstractmethod
from typing import Callable, final

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Abstraction.Collection import SortedList
from WinCopies.Collections.Enumeration import IncrementalEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerationCursor, IResumableEnumerationCursorFactory, IResumableEnumerator, ResumableEnumerationCursorFactory
from WinCopies.Collections.Extensions import ISortedList
from WinCopies.Collections.Generation import IRemovable, INode
from WinCopies.Typing import INullable, InvalidOperationError, GetDisposedError
from WinCopies.Typing.Comparison import IExtendedComparable
from WinCopies.Typing.Object import UnderlyingValueEquals, CompareUnderlyingValue

class IResumableIncrementalEnumerationCursor(IExtendedComparable["IResumableIncrementalEnumerationCursor|int"], IResumableEnumerationCursor):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetIndex(self) -> int:
        pass

class ICookie(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def SetIndex(self, index: int) -> None:
        pass

class _ICookie(ICookie, IRemovable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def MoveToTop(self) -> None:
        pass

@final
class _ResumableIncrementalEnumerationCursor(Abstract, IResumableIncrementalEnumerationCursor):
    @final
    class _Cookie(Abstract, _ICookie):
        def __init__(self, node: INode, cookie: ICookie) -> None:
            super().__init__()
            
            self.__node: INode = node
            self.__cookie: ICookie = cookie
        
        def SetIndex(self, index: int) -> None:
            return self.__cookie.SetIndex(index)
        
        def MoveToTop(self) -> None:
            self.__node.TryMoveToTop()
        
        def Remove(self) -> None:
            self.__node.Remove()
    
    def __init__(self, index: int) -> None:
        super().__init__()

        self.__index: int = index
        self.__cookie: _ICookie|None = None
    
    def _InitializeCookie(self, node: INode, cookie: ICookie) -> None:
        self.__cookie = _ResumableIncrementalEnumerationCursor._Cookie(node, cookie)
    
    def __Compare[T](self, item: IResumableIncrementalEnumerationCursor|int|object, func: Callable[[int, int|object], T]) -> T:
        return func(self.GetIndex(), item.GetIndex() if isinstance(item, IResumableIncrementalEnumerationCursor) else item)
    
    def GetIndex(self) -> int:
        return self.__index
    
    def Resume(self) -> None:
        cookie: _ICookie|None = self.__cookie

        if cookie is None:
            raise GetDisposedError()

        cookie.SetIndex(self.__index)
    
    def MoveToTop(self) -> None:
        cookie: _ICookie|None = self.__cookie

        if cookie is None:
            raise GetDisposedError()
        
        cookie.MoveToTop()
    
    def Equals(self, item: IResumableIncrementalEnumerationCursor|int|object) -> bool:
        return self.__Compare(item, UnderlyingValueEquals)
    
    def CompareTo(self, item: IResumableIncrementalEnumerationCursor|int|object) -> bool|None:
        return self.__Compare(item, CompareUnderlyingValue)
    
    def Hash(self) -> int:
        return hash(self.GetIndex())
    
    def Dispose(self) -> None:
        cookie: _ICookie|None = self.__cookie

        if cookie is not None:
            cookie.Remove()
            self.__index = -1

            self.__cookie = None

class IResumableIncrementalEnumerationCursorFactory[T: IResumableIncrementalEnumerationCursor](IResumableEnumerationCursorFactory[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def BisectLeft(self, index: int) -> int:
        pass
class ResumableIncrementalEnumerationCursorFactory[T: IResumableIncrementalEnumerationCursor](ResumableEnumerationCursorFactory[T], IResumableIncrementalEnumerationCursorFactory[T]):
    def __init__(self, cookie: ICookie) -> None:
        super().__init__()
        
        self.__cookie: ICookie = cookie
        self.__cursors: ISortedList[T] = SortedList[T]()
    
    @abstractmethod
    def _InitializeCursorOverride(self, cursor: T, node: INode, cookie: ICookie) -> None:
        pass
    
    @final
    def _InitializeCursor(self, cursor: T, node: INode) -> None:
        self._InitializeCursorOverride(cursor, node, self.__cookie)
    
    @final
    def _AddItem(self, item: T) -> None:
        self.__cursors.Add(item)
    
    @final
    def _Clear(self) -> None:
        self.__cursors.Clear()
    
    @final
    def _GetSortedItems(self) -> ISortedList[T]:
        return self.__cursors
    
    @final
    def IsEmpty(self) -> bool:
        return self.__cursors.IsEmpty()
    
    @final
    def ContainsKey(self, key: int) -> bool:
        return self.__cursors.ContainsKey(key)
    
    @final
    def TryGetValue(self, key: int) -> INullable[T]:
        return self.__cursors.TryGetValue(key)
    
    @final
    def BisectLeft(self, index: int) -> int:
        return self.__cursors.BisectLeft(index, lambda cursor: cursor.GetIndex())
@final
class _ResumableEnumerationCursorFactory(ResumableIncrementalEnumerationCursorFactory[_ResumableIncrementalEnumerationCursor]):
    def __init__(self, cookie: ICookie) -> None:
        super().__init__(cookie)
    
    def _InitializeCursorOverride(self, cursor: _ResumableIncrementalEnumerationCursor, node: INode, cookie: ICookie) -> None:
        cursor._InitializeCookie(node, cookie) # pyright: ignore[reportPrivateUsage]

class ResumableIncrementalEnumerator[T](IncrementalEnumerator[T], IResumableEnumerator[T]):
    @final
    class _Cookie[_T](Abstract, ICookie):
        def __init__(self, enumerator: ResumableIncrementalEnumerator[_T]) -> None:
            super().__init__()

            self.__enumerator: ResumableIncrementalEnumerator[_T] = enumerator
        
        def SetIndex(self, index: int) -> None:
            self.__enumerator._SetIndex(index)
    
    def __init__(self) -> None:
        super().__init__()
        
        self.__cursors: IResumableIncrementalEnumerationCursorFactory[_ResumableIncrementalEnumerationCursor] = _ResumableEnumerationCursorFactory(ResumableIncrementalEnumerator[T]._Cookie(self))
    
    @staticmethod
    def __GetException(msg: str) -> InvalidOperationError:
        return InvalidOperationError(f"Cannot {msg} before the enumeration has started.")
    @staticmethod
    def __GetCursorException(msg: str) -> InvalidOperationError:
        return ResumableIncrementalEnumerator.__GetException(f"{msg} a cursor")
    
    @final
    def _SetIndex(self, index: int) -> None:
        self._SetValue(index)
    
    @final
    def SupportsMultipleCursors(self) -> bool:
        return True
    
    @final
    def PlaceCursor(self) -> IResumableEnumerationCursor:
        def add(index: int) -> IResumableEnumerationCursor:
            cursor: _ResumableIncrementalEnumerationCursor = _ResumableIncrementalEnumerationCursor(index)

            cursors.RegisterObject(cursor)

            return cursor
        
        if self.IsStarted():
            cursors: IResumableIncrementalEnumerationCursorFactory[_ResumableIncrementalEnumerationCursor] = self.__cursors
            index: int = self._GetValue()
            cursor: IResumableIncrementalEnumerationCursor|None = cursors.TryGetValue(cursors.BisectLeft(index)).TryGetValue()

            return add(index) if cursor is None else (cursor if cursor.Equals(index) else add(index))
        
        raise ResumableIncrementalEnumerator.__GetCursorException("place")
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
            raise ResumableIncrementalEnumerator.__GetCursorException("move")
    
    @final
    def Resume(self, cursor: IResumableEnumerationCursor|None = None) -> None:
        if self.IsStarted():
            (self.__cursors.GetLastCursor() if cursor is None else cursor).Resume()
        
        else:
            raise ResumableIncrementalEnumerator.__GetException("resume")
    
    def _OnEnded(self) -> None:
        super()._OnEnded()

        self.__cursors.InvalidateObjects()
    
    def Dispose(self) -> None:
        self.__cursors.InvalidateObjects()