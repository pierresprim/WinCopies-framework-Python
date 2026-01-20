from abc import abstractmethod
from typing import final

from WinCopies import IInterface, Abstract

class ILinkedNode[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetValue(self) -> T:
        pass
    @abstractmethod
    def SetValue(self, value: T) -> None:
        pass

    @abstractmethod
    def GetNext(self) -> ILinkedNode[T]|None:
        pass

class LinkedNodeBase[T](Abstract):
    def __init__(self, value: T) -> None:
        super().__init__()
        
        self.__value: T = value
    
    @final
    def GetValue(self) -> T:
        return self.__value
    @final
    def SetValue(self, value: T) -> None:
        self.__value = value

class LinkedNode[TItem, TNode](LinkedNodeBase[TItem], ILinkedNode[TItem]):
    def __init__(self, value: TItem, nextNode: TNode|None) -> None:
        super().__init__(value)

        self.__next: TNode|None = nextNode

    @abstractmethod
    def _AsLinkedNode(self, node: TNode) -> LinkedNode[TItem, TNode]:
        pass
    def _TryAsLinkedNode(self, node: TNode|None) -> LinkedNode[TItem, TNode]|None:
        return None if node is None else self._AsLinkedNode(node)
    
    @final
    def GetNextNode(self) -> TNode|None:
        return self.__next
    def GetNext(self) -> ILinkedNode[TItem]|None:
        return self._TryAsLinkedNode(self.GetNextNode())
    
    @final
    def _SetNext(self, nextNode: TNode|None) -> None:
        self.__next = nextNode