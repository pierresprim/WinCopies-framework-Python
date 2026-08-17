from __future__ import annotations

from abc import abstractmethod
from typing import Callable, final

from WinCopies.Collections.Enumeration import IncrementalEnumerator
from WinCopies.Collections.Enumeration.Resumable import ICookie as ICookieBase, IResumableEnumerationCursor, IDefaultResumableEnumerationCursorFactory, IDefaultResumableEnumerator, ResumableEnumerationCursor
from WinCopies.Collections.Generation import INode
from WinCopies.Collections.Generation.Factory.Sorted import ISortedObjectFactory, SortedDisposableObjectFactory
from WinCopies.Typing.Comparison import IHashableComparableItem
from WinCopies.Typing.Object import UnderlyingValueEquals, CompareUnderlyingValue

type ICookie = ICookieBase[int]

class IResumableIncrementalEnumerationCursor(IHashableComparableItem[int], IResumableEnumerationCursor):
    def __init__(self) -> None: super().__init__()

    @final
    def _AsComparableValue(self) -> int: return self.GetIndex()
    
    @abstractmethod
    def GetIndex(self) -> int:
        ...

@final
class _ResumableIncrementalEnumerationCursor(ResumableEnumerationCursor[int], IResumableIncrementalEnumerationCursor):
    def __init__(self, index: int) -> None: super().__init__(index)
    
    def __Compare[T](self, item: IResumableIncrementalEnumerationCursor|int|object, func: Callable[[int, int|object], T]) -> T:
        return func(self.GetIndex(), item.GetIndex() if isinstance(item, IResumableIncrementalEnumerationCursor) else item)
    
    def GetIndex(self) -> int:
        return self._GetCursorValue()
    
    def Equals(self, item: IResumableIncrementalEnumerationCursor|int|object) -> bool: return self.__Compare(item, UnderlyingValueEquals)
    def Hash(self) -> int: return hash(self.GetIndex())
    
    def _CompareTo(self, item: int|object) -> bool|None: return self.__Compare(item, CompareUnderlyingValue)

    def _GetDefaultCursorValue(self) -> int: return -1

class IResumableIncrementalEnumerationCursorFactory[T: IResumableIncrementalEnumerationCursor](ISortedObjectFactory[int, T], IDefaultResumableEnumerationCursorFactory[T]):
    def __init__(self) -> None: super().__init__()
class ResumableIncrementalEnumerationCursorFactory[T: IResumableIncrementalEnumerationCursor](SortedDisposableObjectFactory[int, T], IResumableIncrementalEnumerationCursorFactory[T]):
    def __init__(self, cookie: ICookie) -> None:
        super().__init__()
        
        self.__cookie: ICookie = cookie
    
    @abstractmethod
    def _InitializeCursorOverride(self, cursor: T, node: INode, cookie: ICookie) -> None:
        ...
    
    @final
    def _InitializeCursor(self, cursor: T, node: INode) -> None:
        self._InitializeCursorOverride(cursor, node, self.__cookie)
    
    @final
    def _GetKey(self, item: T) -> int:
        return item.GetIndex()
    
    def _Push(self, item: T) -> INode:
        node: INode = super()._Push(item)

        self._InitializeCursor(item, node)

        return node
    
    @final
    def GetFirstCursor(self) -> T:
        return self._GetItems().GetLastValue()
@final
class _ResumableEnumerationCursorFactory(ResumableIncrementalEnumerationCursorFactory[_ResumableIncrementalEnumerationCursor]):
    def __init__(self, cookie: ICookie) -> None: super().__init__(cookie)
    
    def _InitializeCursorOverride(self, cursor: _ResumableIncrementalEnumerationCursor, node: INode, cookie: ICookie) -> None:
        cursor._InitializeCookie(node, cookie) # pyright: ignore[reportPrivateUsage]

class ResumableIncrementalEnumerator[T](IncrementalEnumerator[T], IDefaultResumableEnumerator[T, int]):
    def __init__(self) -> None:
        super().__init__()
        
        self.__cursors: IResumableIncrementalEnumerationCursorFactory[_ResumableIncrementalEnumerationCursor] = _ResumableEnumerationCursorFactory(self._CreateCursorCookie())
    
    @final
    def _GetFirstCursor(self) -> IResumableEnumerationCursor:
        return self.__cursors.GetFirstCursor()
    
    @final
    def _SetCursor(self, value: int) -> None:
        self._SetValue(value)
    
    @final
    def SupportsMultipleCursors(self) -> bool: return True
    
    @final
    def _PlaceCursor(self) -> IResumableEnumerationCursor:
        def add(index: int) -> IResumableEnumerationCursor:
            cursor: _ResumableIncrementalEnumerationCursor = _ResumableIncrementalEnumerationCursor(index)

            cursors.RegisterObject(cursor)

            return cursor
        
        cursors: IResumableIncrementalEnumerationCursorFactory[_ResumableIncrementalEnumerationCursor] = self.__cursors
        index: int = self._GetValue()
        cursor: IResumableIncrementalEnumerationCursor|None = cursors.TryGetValue(cursors.BisectLeft(index)).TryGetValue()

        return add(index) if cursor is None else (cursor if cursor.Equals(index) else add(index))
    
    def _OnEnded(self) -> None:
        super()._OnEnded()

        self.__cursors.InvalidateObjects()