from abc import abstractmethod
from typing import final, Callable

from WinCopies.Collections import Collection
from WinCopies.Collections.Linked import SinglyLinkedNode
from WinCopies.Typing.Pairing import DualResult, DualNullableValueBool

class List[T](Collection):
    def __init__(self):
        super().__init__()
        self.__first: SinglyLinkedNode[T]|None = None

    @final
    def IsEmpty(self) -> bool:
        return self.__first is None
    @final
    def HasItems(self) -> bool:
        return super().HasItems()
    
    @final
    def _SetFirst(self, node: SinglyLinkedNode[T]) -> None:
        self.__first = node
    
    @abstractmethod
    def _OnRemoved(self) -> None:
        pass
    
    @abstractmethod
    def _Push(self, value: T, first: SinglyLinkedNode[T]) -> None:
        pass
    @final
    def Push(self, value: T) -> None:
        if self.IsEmpty():
            self.__first = SinglyLinkedNode[T](value, None)
        
        else:
            self._Push(value, self.__first)
    
    @final
    def TryPeek(self) -> DualNullableValueBool[T]:
        return DualResult[T|None, bool](None, False) if self.IsEmpty() else DualResult[T|None, bool](self.__first.GetValue(), True)
    
    @final
    def TryPop(self) -> DualNullableValueBool[T]:
        result: DualNullableValueBool[T] = self.TryPeek()

        if result.GetValue():
            self.__first = self.__first.GetNext()
            self._OnRemoved()

        return result
    
    @final
    def Clear(self) -> None:
        self._OnRemoved()

        self.__first = None

class Queue[T](List):
    def __init__(self):
        super().__init__()
        
        self.__last: SinglyLinkedNode[T]|None = None
        self.__updater: Callable[[SinglyLinkedNode[T], SinglyLinkedNode[T]], None] = self.__GetUpdater()
    
    @final
    def __Push(self, first: SinglyLinkedNode[T], newNode: SinglyLinkedNode[T]) -> None:
        def push(previousNode: SinglyLinkedNode[T], newNode: SinglyLinkedNode[T]) -> None:
            previousNode.SetNext(newNode)

            self.__last = newNode
        
        push(first, newNode)

        self.__updater = lambda first, newNode: push(self.__last, newNode)
    
    @final
    def __GetUpdater(self) -> Callable[[SinglyLinkedNode[T], SinglyLinkedNode[T]], None]:
        return lambda first, newNode: self.__Push(first, newNode)
    
    @final
    def _Push(self, value: T, first: SinglyLinkedNode[T]):
        self.__updater(first, SinglyLinkedNode[T](value, None))
    
    @final
    def _OnRemoved(self) -> None:
        if self.IsEmpty():
            self.__last = None
            self.__updater = self.__GetUpdater()

class Stack[T](List):
    def __init__(self):
        super().__init__()
    
    @final
    def _Push(self, value: T, first: SinglyLinkedNode[T]) -> None:
        self._SetFirst(SinglyLinkedNode[T](value, first))
    
    @final
    def _OnRemoved(self) -> None:
        pass