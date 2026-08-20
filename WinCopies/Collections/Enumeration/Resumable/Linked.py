from __future__ import annotations

from abc import abstractmethod
from typing import final, cast

from WinCopies import Abstract
from WinCopies.Collections import EnumerationOrder
from WinCopies.Collections.Enumeration.Resumable import ICookie as ICookieBase, IResumableEnumerationCursor, IDefaultResumableEnumerationCursorRegistry, IDefaultResumableEnumerator, NullableResumableEnumerationCursor
from WinCopies.Collections.Generation import INode
from WinCopies.Collections.Generation.Registry.Keyable import IKeyableObjectRegistry
from WinCopies.Collections.Generation.Registry.Mapping import KeyedDisposableObjectRegistry
from WinCopies.Collections.Linked.Node import INode as ILinkedNode, ITwoWayNode as ITwoWayLinkedNode
from WinCopies.Collections.Linked.Enumeration import NodeEnumeratorBase, TwoWayNodeEnumeratorBase
from WinCopies.Typing.Comparison import IHashableValue
from WinCopies.Typing.Discard import GetDiscardedError

type ICookie = ICookieBase[ILinkedNode]

class IResumableNodeEnumerationCursor(IResumableEnumerationCursor):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryGetNode(self) -> ILinkedNode|None:
        ...
    @final
    def GetNode(self) -> ILinkedNode:
        node: ILinkedNode|None = self.TryGetNode()

        if node is None: raise GetDiscardedError()
        
        return node

@final
class _ResumableNodeEnumerationCursor(NullableResumableEnumerationCursor[ILinkedNode], IResumableNodeEnumerationCursor):
    def __init__(self, node: ILinkedNode) -> None: super().__init__(node)

    def _GetCursorValue(self) -> ILinkedNode: return self.GetNode()
    
    def TryGetNode(self) -> ILinkedNode|None: return self._GetCursorItem()

@final
class _NodeKey(Abstract, IHashableValue):
    def __init__(self, node: ILinkedNode) -> None:
        super().__init__()

        self.__node: ILinkedNode = node
    
    def GetNode(self) -> ILinkedNode: return self.__node
    
    def Equals(self, item: _NodeKey|object) -> bool: return isinstance(item, _NodeKey) and self.__node is item.GetNode()
    def Hash(self) -> int: return id(self.__node)

class IResumableNodeEnumerationCursorRegistry[T: IResumableNodeEnumerationCursor](IKeyableObjectRegistry[_NodeKey, T], IDefaultResumableEnumerationCursorRegistry[T]):
    def __init__(self) -> None: super().__init__()
class ResumableNodeEnumerationCursorRegistry[T: IResumableNodeEnumerationCursor](KeyedDisposableObjectRegistry[_NodeKey, T], IResumableNodeEnumerationCursorRegistry[T]):
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
    def _GetKey(self, item: T) -> _NodeKey:
        return _NodeKey(item.GetNode())
    
    def _Push(self, item: T) -> INode:
        node: INode = super()._Push(item)

        self._InitializeCursor(item, node)
        
        return node
    
    @final
    def GetFirstCursor(self) -> T: return self._GetItems().GetLastValue()

@final
class _ResumableEnumerationCursorRegistry(ResumableNodeEnumerationCursorRegistry[_ResumableNodeEnumerationCursor]):
    def __init__(self, cookie: ICookie) -> None: super().__init__(cookie)
    
    def _InitializeCursorOverride(self, cursor: _ResumableNodeEnumerationCursor, node: INode, cookie: ICookie) -> None:
        cursor._InitializeCookie(node, cookie) # pyright: ignore[reportPrivateUsage]

class IDefaultResumableNodeEnumerator[T: ILinkedNode](IDefaultResumableEnumerator[T, ILinkedNode]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _CreateCursorRegistry(self) -> IResumableNodeEnumerationCursorRegistry[_ResumableNodeEnumerationCursor]:
        return _ResumableEnumerationCursorRegistry(self._CreateCursorCookie())

    @abstractmethod
    def _GetCursors(self) -> IResumableNodeEnumerationCursorRegistry[_ResumableNodeEnumerationCursor]:
        ...
    
    @abstractmethod
    def _GetCurrentNode(self) -> T:
        ...
    @abstractmethod
    def _SetCurrentNode(self, node: T) -> None:
        ...
    
    @final
    def _GetFirstCursor(self) -> IResumableEnumerationCursor:
        return self._GetCursors().GetFirstCursor()
    
    @final
    def _SetCursor(self, value: ILinkedNode) -> None:
        self._SetCurrentNode(cast(T, value))
    
    @final
    def SupportsMultipleCursors(self) -> bool:
        return True
    
    @final
    def _PlaceCursor(self) -> IResumableEnumerationCursor:
        def add(node: ILinkedNode) -> IResumableEnumerationCursor:
            cursor: _ResumableNodeEnumerationCursor = _ResumableNodeEnumerationCursor(node)

            cursors.RegisterObject(cursor)

            return cursor
        
        cursors: IResumableNodeEnumerationCursorRegistry[_ResumableNodeEnumerationCursor] = self._GetCursors()
        node: T = self._GetCurrentNode()
        cursor: IResumableNodeEnumerationCursor|None = cursors.TryGetValue(_NodeKey(node)).TryGetValue()

        return add(node) if cursor is None else cursor

class ResumableNodeEnumerator[T: ILinkedNode](NodeEnumeratorBase[T], IDefaultResumableNodeEnumerator[T]):
    def __init__(self, firstNode: T) -> None:
        super().__init__(firstNode)
        
        self.__cursors: IResumableNodeEnumerationCursorRegistry[_ResumableNodeEnumerationCursor] = self._CreateCursorRegistry()
    
    @final
    def _GetCursors(self) -> IResumableNodeEnumerationCursorRegistry[_ResumableNodeEnumerationCursor]:
        return self.__cursors
    
    @final
    def _GetCurrentNode(self) -> T:
        return self._GetCurrent()
    @final
    def _SetCurrentNode(self, node: T) -> None:
        return self._SetCurrent(node)
    
    def _OnEnded(self) -> None:
        super()._OnEnded()

        self._GetCursors().InvalidateObjects()
class TwoWayResumableNodeEnumerator[T: ITwoWayLinkedNode](TwoWayNodeEnumeratorBase[T], IDefaultResumableNodeEnumerator[T]):
    def __init__(self, firstNode: T, order: EnumerationOrder) -> None:
        super().__init__(firstNode, order)
        
        self.__cursors: IResumableNodeEnumerationCursorRegistry[_ResumableNodeEnumerationCursor] = self._CreateCursorRegistry()
    
    @final
    def _GetCursors(self) -> IResumableNodeEnumerationCursorRegistry[_ResumableNodeEnumerationCursor]:
        return self.__cursors
    
    @final
    def _GetCurrentNode(self) -> T:
        return self._GetCurrent()
    @final
    def _SetCurrentNode(self, node: T) -> None:
        return self._SetCurrent(node)
    
    def _OnEnded(self) -> None:
        super()._OnEnded()

        self._GetCursors().InvalidateObjects()