from typing import final, Self

from WinCopies.Collections.Enumeration import Enumerator
from WinCopies.Typing.Delegate import Function

class SinglyLinkedNode[T]:
    def __init__(self, value: T, next: Self|None):
        self.__value: T = value
        self.__next: SinglyLinkedNode[T]|None = next
    
    @final
    def GetValue(self) -> T:
        return self.__value
    
    @final
    def SetValue(self, value: T) -> None:
        self.__value = value
    
    @final
    def GetNext(self) -> Self|None:
        return self.__next
    @final
    def SetNext(self, next: Self|None) -> None:
        self.__next = next

class Node[T](SinglyLinkedNode[T]):
    def __init__(self, value: T, previous, next):
        super().__init__(value, next)

        self.__previous: Node[T] = previous
    
    @final
    def GetPrevious(self):
        return self.__previous
    @final
    def SetPrevious(self, previous) -> None:
        self.__previous = previous

class NodeEnumerator[T](Enumerator[SinglyLinkedNode[T]]):
    def __init__(self, node: SinglyLinkedNode[T]):
        super().__init__()

        self.__first: SinglyLinkedNode[T] = node
        self.__moveNextFunc: Function[bool]|None = None
    
    def __MoveNext(self) -> bool:
        self._SetCurrent(self.__first)

        def moveNext() -> bool:
            node: SinglyLinkedNode[T] = self.GetCurrent().GetNext()

            if node is None:
                return False
            
            self._SetCurrent(node)

            return True

        self.__moveNextFunc = moveNext

        return True
    
    def _OnStarting(self):
        if super()._OnStarting():
            self.__moveNextFunc = self.__MoveNext

            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNextFunc()
    
    def _OnEnded(self):
        self.__moveNextFunc = None

        super()._OnEnded()