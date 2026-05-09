from __future__ import annotations

from abc import abstractmethod
from typing import Callable, final

from WinCopies import IInterface, IDisposable, Abstract
from WinCopies.Collections import IReadOnlyCollection, IGetter
from WinCopies.Collections.Abstraction.Collection import SortedList
from WinCopies.Collections.Enumeration import IEnumerable, IEnumeratorBase, IEnumerator, EnumeratorBase, AbstractEnumeratorBase, IncrementalEnumerator
from WinCopies.Collections.Extensions import ISortedList
from WinCopies.Collections.Generation import IResumable, IRemovable, INode
from WinCopies.Collections.Generation.Factory import IObjectFactory, DisposableObjectFactory
from WinCopies.Typing import INullable, InvalidOperationError, GetDisposedError
from WinCopies.Typing.Comparison import IExtendedComparable
from WinCopies.Typing.Generic import IGenericConstraintImplementation
from WinCopies.Typing.Object import UnderlyingValueEquals, CompareUnderlyingValue

class IResumableEnumerationCursor(IResumable, IDisposable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def MoveToTop(self) -> None:
        pass
class IResumableIncrementalEnumerationCursor(IExtendedComparable["IResumableIncrementalEnumerationCursor|int"], IResumableEnumerationCursor):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetIndex(self) -> int:
        pass

class IResumableEnumerable[T](IEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]|None:
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

class ResumableEnumeratorBase[T](EnumeratorBase[T], IResumableEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()
class ResumableEnumerator[T](ResumableEnumeratorBase[T]):
    def __init__(self) -> None:
        super().__init__()

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

class IResumableEnumerationCursorFactory(IObjectFactory[IResumableIncrementalEnumerationCursor], IGetter[int, IResumableIncrementalEnumerationCursor], IReadOnlyCollection):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def GetLastCursor(self) -> IResumableIncrementalEnumerationCursor:
        pass
    
    @abstractmethod
    def BisectLeft(self, index: int) -> int:
        pass
class ResumableEnumerationCursorFactory[T: IResumableIncrementalEnumerationCursor](DisposableObjectFactory[T], IResumableEnumerationCursorFactory):
    def __init__(self, cookie: ICookie) -> None:
        super().__init__()
        
        self.__cookie: ICookie = cookie
        self.__cursors: ISortedList[IResumableIncrementalEnumerationCursor] = SortedList[IResumableIncrementalEnumerationCursor]()
    
    @abstractmethod
    def _InitializeCursor(self, cursor: T, node: INode, cookie: ICookie) -> None:
        pass
    
    def _Push(self, item: T) -> INode:
        node: INode = super()._Push(item)

        self._InitializeCursor(item, node, self.__cookie)

        self.__cursors.Add(item)

        return node
    
    def InvalidateObjects(self) -> None:
        super().InvalidateObjects()

        self.__cursors.Clear()
    
    @final
    def _GetSortedItems(self) -> ISortedList[IResumableIncrementalEnumerationCursor]:
        return self.__cursors
    
    @final
    def IsEmpty(self) -> bool:
        return self.__cursors.IsEmpty()
    
    @final
    def ContainsKey(self, key: int) -> bool:
        return self.__cursors.ContainsKey(key)
    
    @final
    def TryGetValue(self, key: int) -> INullable[IResumableIncrementalEnumerationCursor]:
        return self.__cursors.TryGetValue(key)
    
    @final
    def GetLastCursor(self) -> IResumableIncrementalEnumerationCursor:
        return self._GetItems().GetLastValue()
    
    @final
    def BisectLeft(self, index: int) -> int:
        return self.__cursors.BisectLeft(index, lambda cursor: cursor.GetIndex())
@final
class _ResumableEnumerationCursorFactory(ResumableEnumerationCursorFactory[_ResumableIncrementalEnumerationCursor]):
    def __init__(self, cookie: ICookie) -> None:
        super().__init__(cookie)
    
    def _InitializeCursor(self, cursor: _ResumableIncrementalEnumerationCursor, node: INode, cookie: ICookie) -> None:
        cursor._InitializeCookie(node, cookie) # pyright: ignore[reportPrivateUsage]

class AbstractResumableEnumeratorAbstract[TIn, TOut, TEnumerator: IEnumeratorBase](AbstractEnumeratorBase[TIn, TOut, TEnumerator], IResumableEnumerator[TOut]):
    def __init__(self, enumerator: TEnumerator) -> None:
        super().__init__(enumerator)
class AbstractResumableEnumeratorBase[TItem, TEnumerator: IEnumeratorBase](AbstractResumableEnumeratorAbstract[TItem, TItem, TEnumerator]):
    def __init__(self, enumerator: TEnumerator) -> None:
        super().__init__(enumerator)
class AbstractResumableEnumerator[T](AbstractResumableEnumeratorBase[T, IResumableEnumerator[T]], IGenericConstraintImplementation[IResumableEnumerator[T]]):
    def __init__(self, enumerator: IResumableEnumerator[T]) -> None:
        super().__init__(enumerator)

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
        
        self.__cursors: IResumableEnumerationCursorFactory = _ResumableEnumerationCursorFactory(ResumableIncrementalEnumerator[T]._Cookie(self))
    
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
            cursor: IResumableIncrementalEnumerationCursor = _ResumableIncrementalEnumerationCursor(index)

            cursors.RegisterObject(cursor)

            return cursor
        
        if self.IsStarted():
            cursors: IResumableEnumerationCursorFactory = self.__cursors
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