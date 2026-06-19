from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import final

from WinCopies import IInterface, Abstract
from WinCopies.Collections import Generator as GeneratorBase
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Linked.Doubly import IReadWriteList as IReadWriteListBase
from WinCopies.Collections.Linked.Doubly.Node import INodeBase, INode, IDoublyLinkedNodeBase, INodeCookie, IListCookie
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Function
from WinCopies.Typing.Generic import IGenericConstraint

class IAbstractNode[TNode, TNodeInterface](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetNodeAsClass(self, node: TNode) -> TNodeInterface:
        ...

class _IAbstractList[TItem, TNode](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetNodeAsInterface(self, node: TNode) -> IDoublyLinkedNodeBase[TItem, TNode]:
        ...

class IReadWriteList[T](IReadWriteListBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetFirstNode(self) -> INode[T]|None:
        ...
    @abstractmethod
    def GetLastNode(self) -> INode[T]|None:
        ...
    
    @abstractmethod
    def AddFirstNode(self, value: T) -> INode[T]:
        ...
    @abstractmethod
    def AddLastNode(self, value: T) -> INode[T]:
        ...
    
    @final
    def __AsGenerator(self, func: Function[INullable[T]]) -> GeneratorBase[T]:
        result: INullable[T] = func()

        while result.HasValue():
            yield result.GetValue()
            
            result = func()
    
    @final
    def AsQueuedGenerator(self) -> GeneratorBase[T]:
        return self.__AsGenerator(self.TryRemoveFirst)
    @final
    def AsStackedGenerator(self) -> GeneratorBase[T]:
        return self.__AsGenerator(self.TryRemoveLast)

class IListBase[TItem, TNode](IReadWriteList[TItem], IGenericConstraint[TNode, INode[TItem]]):
    def __init__(self) -> None: super().__init__()

    @final
    def __TryGet(self, node: TNode|None) -> INode[TItem]|None:
        return None if node is None else self._AsContainer(node)
    
    @abstractmethod
    def GetFirst(self) -> TNode|None:
        ...
    @abstractmethod
    def GetLast(self) -> TNode|None:
        ...

    @final
    def GetFirstNode(self) -> INode[TItem]|None:
        return self.__TryGet(self.GetFirst())
    @final
    def GetLastNode(self) -> INode[TItem]|None:
        return self.__TryGet(self.GetLast())
    
    @abstractmethod
    def AddFirst(self, value: TItem) -> TNode:
        ...
    @abstractmethod
    def AddLast(self, value: TItem) -> TNode:
        ...

    @final
    def AddFirstNode(self, value: TItem) -> INode[TItem]:
        return self._AsContainer(self.AddFirst(value))
    @final
    def AddLastNode(self, value: TItem) -> INode[TItem]:
        return self._AsContainer(self.AddLast(value))

class ListNodeBase[T](INodeBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _SetFirst(self, cookie: INodeCookie[T], items: IListCookie[T], node: T|None) -> None:
        cookie.SetFirst(node, items)
    @final
    def _SetLast(self, cookie: INodeCookie[T], items: IListCookie[T], node: T|None) -> None:
        cookie.SetLast(node, items)

class ListBase[TItem, TNode, TNodeInterface: IRemovable](Abstract, IListBase[TItem, TNodeInterface], _IAbstractList[TItem, TNode], IAbstractNode[TNode, TNodeInterface], IListCookie[TNode]):
    def __init__(self, items: Iterable[TItem]|None = None) -> None:
        super().__init__()
        
        self.__first: TNode|None = None
        self.__last: TNode|None = None
        
        self.__cookie: INodeCookie[TNode] = self._CreateCookie()

        self.AddLastItems(items)
    
    @final
    def __TryGetNodeAsClass(self, node: TNode|None) -> TNodeInterface|None:
        return None if node is None else self._GetNodeAsClass(node)
    
    @final
    def _GetCookie(self) -> INodeCookie[TNode]:
        return self.__cookie
    
    @abstractmethod
    def _CreateNode(self, value: TItem) -> TNode:
        ...
    
    @abstractmethod
    def _GetPreviousNode(self, node: TNode) -> TNode|None:
        ...
    @abstractmethod
    def _GetNextNode(self, node: TNode) -> TNode|None:
        ...

    @abstractmethod
    def _UnregisterNode(self, node: TNode) -> None:
        ...
    
    def _AddNode(self, value: TItem) -> TNode:
        node: TNode = self._CreateNode(value)

        self._SetFirst(node)
        self._SetLast(node)
        
        return node

    @final
    def _GetFirst(self) -> TNode|None:
        return self.__first
    @final
    def _GetLast(self) -> TNode|None:
        return self.__last
    
    @final
    def _SetFirst(self, node: TNode|None) -> None:
        self.__first = node
    @final
    def _SetLast(self, node: TNode|None) -> None:
        self.__last = node

    @final
    def IsEmpty(self) -> bool: return self.__first is None
    @final
    def HasItems(self) -> bool: return super().HasItems()
    
    @final
    def AddFirst(self, value: TItem) -> TNodeInterface:
        node: TNode|None = self._GetFirst()
        
        return self._GetNodeAsClass(self._AddNode(value) if node is None else self._GetNodeAsInterface(node).SetPreviousNode(value))
    @final
    def AddLast(self, value: TItem) -> TNodeInterface:
        node: TNode|None = self._GetLast()
        
        return self._GetNodeAsClass(self._AddNode(value) if node is None else self._GetNodeAsInterface(node).SetNextNode(value))
    
    @final
    def GetFirst(self) -> TNodeInterface|None: return self.__TryGetNodeAsClass(self._GetFirst())
    @final
    def GetLast(self) -> TNodeInterface|None: return self.__TryGetNodeAsClass(self._GetLast())
    
    @final
    def __TryRemove(self, node: TNode|None) -> INullable[TItem]:
        return GetNullValue() if node is None else GetNullable(self._GetNodeAsInterface(node).RemoveNode())
    
    @final
    def TryRemoveFirst(self) -> INullable[TItem]: return self.__TryRemove(self._GetFirst())
    @final
    def TryRemoveLast(self) -> INullable[TItem]: return self.__TryRemove(self._GetLast())
    
    @final
    def Clear(self) -> None:
        def enumerate() -> GeneratorBase[TNode]:
            node: TNode|None = self._GetFirst()

            while node is not None:
                yield node

                node = self._GetNextNode(node)
        
        for node in enumerate(): self._UnregisterNode(node)

        self.__first = None
        self.__last = None