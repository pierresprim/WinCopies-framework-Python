from abc import ABC, abstractmethod
from typing import final, Self

from WinCopies.Typing import AssertIsDirectPackageCall

class ILinkedListNode[T](ABC):
    @abstractmethod
    def GetValue(self) -> T:
        pass
    @abstractmethod
    def SetValue(self, value: T) -> None:
        pass

    @abstractmethod
    def GetNextNode(self) -> Self|None:
        pass

class LinkedListNodeBase[T]:
    def __init__(self, value: T):
        self.__value: T = value
    
    @final
    def GetValue(self) -> T:
        return self.__value
    
    @final
    def SetValue(self, value: T) -> None:
        self.__value = value

class LinkedListNode[TNode: Self, TItems](LinkedListNodeBase[TItems], ILinkedListNode[TItems]):
    def __init__(self, value: TItems, nextNode: TNode|None):
        super().__init__(value)

        self.__next: TNode|None = nextNode
    
    @final
    def GetNext(self) -> TNode|None:
        return self.__next
    @final
    def _SetNext(self, nextNode: TNode|None) -> None:
        AssertIsDirectPackageCall()

        self.__next = nextNode
    
    @final
    def GetNextNode(self) -> ILinkedListNode[TItems]:
        return self.GetNext()

class NodeBase[TNode: Self, TItems](LinkedListNode[TNode, TItems]):
    def __init__(self, value: TItems, previousNode: TNode|None, nextNode: TNode|None):
        super().__init__(value, nextNode)

        self.__previous: TNode = previousNode
    
    @final
    def GetPrevious(self) -> TNode|None:
        return self.__previous
    @final
    def _SetPrevious(self, previous: TNode|None) -> None:
        AssertIsDirectPackageCall()
        
        self.__previous = previous