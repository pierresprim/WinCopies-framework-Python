from __future__ import annotations

from abc import abstractmethod
from typing import final, cast

from WinCopies import Abstract
from WinCopies.Collections.Enumeration.Resumable import ICookie as ICookieBase, IResumableEnumerationCursor, IDefaultResumableEnumerationCursorFactory, IDefaultResumableEnumerator
from WinCopies.Collections.Generation import IRemovable, INode
from WinCopies.Collections.Generation.Factory.Keyable import IKeyableObjectFactory
from WinCopies.Collections.Generation.Factory.Mapping import KeyedDisposableObjectFactory
from WinCopies.Collections.Linked.Node import INode as ILinkedNode
from WinCopies.Collections.Linked.Enumeration import NodeEnumeratorBase
from WinCopies.Typing import GetDisposedError
from WinCopies.Typing.Comparison import IHashable

type ICookie = ICookieBase[ILinkedNode]

class _ICookie(ICookieBase[ILinkedNode], IRemovable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def MoveToTop(self) -> None:
        pass

class IResumableNodeEnumerationCursor(IResumableEnumerationCursor):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryGetNode(self) -> ILinkedNode|None:
        pass
    @final
    def GetNode(self) -> ILinkedNode:
        node: ILinkedNode|None = self.TryGetNode()

        if node is None:
            raise GetDisposedError()
        
        return node

@final
class _ResumableNodeEnumerationCursor(Abstract, IResumableNodeEnumerationCursor):
    @final
    class _Cookie(Abstract, _ICookie):
        def __init__(self, node: INode, cookie: ICookie) -> None:
            super().__init__()

            self.__node: INode = node
            self.__cookie: ICookie = cookie
        
        def SetCursor(self, value: ILinkedNode) -> None:
            return self.__cookie.SetCursor(value)
        
        def MoveToTop(self) -> None:
            self.__node.TryMoveToBottom()
        
        def Remove(self) -> None:
            self.__node.Remove()
    
    def __init__(self, node: ILinkedNode) -> None:
        super().__init__()

        self.__node: ILinkedNode|None = node
        self.__cookie: _ICookie|None = None
    
    def _InitializeCookie(self, node: INode, cookie: ICookie) -> None:
        self.__cookie = _ResumableNodeEnumerationCursor._Cookie(node, cookie)
    
    def TryGetNode(self) -> ILinkedNode|None:
        return self.__node
    
    def Resume(self) -> None:
        cookie: _ICookie|None = self.__cookie

        if cookie is None:
            raise GetDisposedError()
        
        cookie.SetCursor(self.GetNode())
    
    def MoveToTop(self) -> None:
        cookie: _ICookie|None = self.__cookie
        
        if cookie is None:
            raise GetDisposedError()
        
        cookie.MoveToTop()
    
    def Dispose(self) -> None:
        cookie: _ICookie|None = self.__cookie
    
        if cookie is not None:
            cookie.Remove()

            self.__cookie = None
            self.__node = None

@final
class _NodeKey(Abstract, IHashable["_NodeKey"]):
    def __init__(self, node: ILinkedNode) -> None:
        super().__init__()

        self.__node: ILinkedNode = node
    
    def GetNode(self) -> ILinkedNode:
        return self.__node
    
    def Equals(self, item: _NodeKey|object) -> bool:
        return isinstance(item, _NodeKey) and self.__node is item.GetNode()
    
    def Hash(self) -> int:
        return id(self.__node)

class IResumableNodeEnumerationCursorFactory[T: IResumableNodeEnumerationCursor](IKeyableObjectFactory[_NodeKey, T], IDefaultResumableEnumerationCursorFactory[T]):
    def __init__(self) -> None:
        super().__init__()
class ResumableNodeEnumerationCursorFactory[T: IResumableNodeEnumerationCursor](KeyedDisposableObjectFactory[_NodeKey, T], IResumableNodeEnumerationCursorFactory[T]):
    def __init__(self, cookie: ICookie) -> None:
        super().__init__()

        self.__cookie: ICookie = cookie
    
    @abstractmethod
    def _InitializeCursorOverride(self, cursor: T, node: INode, cookie: ICookie) -> None:
        pass
    
    @final
    def _InitializeCursor(self, cursor: T, node: INode) -> None:
        self._InitializeCursorOverride(cursor, node, self.__cookie)
    
    @final
    def _GetKey(self, item: T) -> _NodeKey:
        return _NodeKey(item.GetNode())
    
    def _Push(self, item: T) -> INode:
        node: INode = super()._Push(item)

        self._InitializeCursor(item, node)
        
        return node
    
    @final
    def GetFirstCursor(self) -> T:
        return self._GetItems().GetLastValue()

@final
class _ResumableEnumerationCursorFactory(ResumableNodeEnumerationCursorFactory[_ResumableNodeEnumerationCursor]):
    def __init__(self, cookie: ICookie) -> None:
        super().__init__(cookie)
    
    def _InitializeCursorOverride(self, cursor: _ResumableNodeEnumerationCursor, node: INode, cookie: ICookie) -> None:
        cursor._InitializeCookie(node, cookie) # pyright: ignore[reportPrivateUsage]


class ResumableNodeEnumerator[T: ILinkedNode](NodeEnumeratorBase[T], IDefaultResumableEnumerator[T, ILinkedNode]):
    def __init__(self, firstNode: T) -> None:
        super().__init__(firstNode)
        
        self.__cursors: IResumableNodeEnumerationCursorFactory[_ResumableNodeEnumerationCursor] = _ResumableEnumerationCursorFactory(self._CreateCursorCookie())
    
    @final
    def _GetFirstCursor(self) -> IResumableEnumerationCursor:
        return self.__cursors.GetFirstCursor()
    
    @final
    def _SetCursor(self, value: ILinkedNode) -> None:
        self._SetCurrent(cast(T, value))
    
    @final
    def SupportsMultipleCursors(self) -> bool:
        return True
    
    @final
    def _PlaceCursor(self) -> IResumableEnumerationCursor:
        def add(node: ILinkedNode) -> IResumableEnumerationCursor:
            cursor: _ResumableNodeEnumerationCursor = _ResumableNodeEnumerationCursor(node)

            cursors.RegisterObject(cursor)

            return cursor
        
        cursors: IResumableNodeEnumerationCursorFactory[_ResumableNodeEnumerationCursor] = self.__cursors
        node: T = self._GetCurrent()
        cursor: IResumableNodeEnumerationCursor|None = cursors.TryGetValue(_NodeKey(node)).TryGetValue()

        return add(node) if cursor is None else cursor
    
    def _OnEnded(self) -> None:
        super()._OnEnded()

        self.__cursors.InvalidateObjects()