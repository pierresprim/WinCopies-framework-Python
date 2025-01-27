from abc import ABC, abstractmethod
from typing import final, Self

from WinCopies.Typing import AssertIsDirectPackageCall

class ILinkedNode[T](ABC):
    @abstractmethod
    def GetValue(self) -> T:
        pass
    @abstractmethod
    def SetValue(self, value: T) -> None:
        pass

    @abstractmethod
    def GetNext(self) -> Self|None:
        pass
class IDoublyLinkedNode[T](ILinkedNode[T]):
    @abstractmethod
    def GetPrevious(self) -> Self|None:
        pass

class LinkedNodeBase[T]:
    def __init__(self, value: T):
        self.__value: T = value
    
    @final
    def GetValue(self) -> T:
        return self.__value
    @final
    def SetValue(self, value: T) -> None:
        self.__value = value

class LinkedNode[TNode: Self, TItems](LinkedNodeBase[TItems], ILinkedNode[TItems]):
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

class NodeBase[TNode: Self, TItems](LinkedNode[TNode, TItems], IDoublyLinkedNode[TItems]):
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