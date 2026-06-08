from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import IInterface, Abstract

class INode(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetNext(self) -> INode|None:
        ...
class ITwoWayNode(INode):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetPrevious(self) -> ITwoWayNode|None:
        ...
    @abstractmethod
    def GetNext(self) -> ITwoWayNode|None:
        ...

class ILinkedNode[T](INode):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetValue(self) -> T:
        ...
    @abstractmethod
    def SetValue(self, value: T) -> None:
        ...

    @abstractmethod
    def GetNext(self) -> ILinkedNode[T]|None:
        ...
class ITwoWayLinkedNode[T](ILinkedNode[T], ITwoWayNode):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetPrevious(self) -> ITwoWayLinkedNode[T]|None:
        ...
    @abstractmethod
    def GetNext(self) -> ITwoWayLinkedNode[T]|None:
        ...

class LinkedNodeAbstract[T](Abstract, ILinkedNode[T]):
    def __init__(self, value: T) -> None:
        super().__init__()
        
        self.__value: T = value
    
    @final
    def GetValue(self) -> T:
        return self.__value
    @final
    def SetValue(self, value: T) -> None:
        self.__value = value
class LinkedNodeBase[TItem, TNode](LinkedNodeAbstract[TItem]):
    def __init__(self, value: TItem) -> None:
        super().__init__(value)

    @abstractmethod
    def _AsLinkedNode(self, node: TNode) -> LinkedNodeBase[TItem, TNode]:
        ...
    def _TryAsLinkedNode(self, node: TNode|None) -> LinkedNodeBase[TItem, TNode]|None:
        return None if node is None else self._AsLinkedNode(node)
    
    @abstractmethod
    def GetNextNode(self) -> TNode|None:
        ...
    def GetNext(self) -> ILinkedNode[TItem]|None: return self._TryAsLinkedNode(self.GetNextNode())

class LinkedNode[TItem, TNode](LinkedNodeBase[TItem, TNode]):
    def __init__(self, value: TItem, nextNode: TNode|None) -> None:
        super().__init__(value)

        self.__next: TNode|None = nextNode

    @final
    def GetNextNode(self) -> TNode|None: return self.__next
    
    @final
    def _SetNext(self, nextNode: TNode|None) -> None:
        self.__next = nextNode

    @abstractmethod
    def _AsLinkedNode(self, node: TNode) -> LinkedNode[TItem, TNode]:
        ...
    def _TryAsLinkedNode(self, node: TNode|None) -> LinkedNode[TItem, TNode]|None:
        return None if node is None else self._AsLinkedNode(node)