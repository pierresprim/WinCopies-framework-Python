from typing import final, Self

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