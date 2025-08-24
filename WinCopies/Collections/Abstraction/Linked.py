from abc import abstractmethod
from collections.abc import Iterable
from typing import final

from WinCopies.Collections.Linked.Node import IDoublyLinkedNode
from WinCopies.Collections.Linked import Singly, Doubly
from WinCopies.Collections.Linked.Doubly import List

from WinCopies.Typing import INullable, GetNullable, GetNullValue

class LinkedList[T](Singly.IList[T]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__()

        self.__list: Doubly.IListBase[T] = List[T]() if l is None else l
    
    @final
    def _GetList(self) -> Doubly.IListBase[T]:
        return self.__list
    @final
    def _GetFirst(self) -> IDoublyLinkedNode[T]|None: # Needed for iteration.
        return self._GetList().GetFirst()
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetList().IsEmpty()
    
    @abstractmethod
    def _Push(self, value: T) -> IDoublyLinkedNode[T]:
        pass
    
    @final
    def Push(self, value: T) -> None:
        self._Push(value)
    
    @final
    def TryPushItems(self, items: Iterable[T]|None) -> bool:
        return self._GetList().AddLastItems(items)
    @final
    def PushItems(self, items: Iterable[T]) -> None:
        if not self.TryPushItems(items):
            raise ValueError("items can not be None.")
    
    @final
    def PushValues(self, *values: T) -> None:
        self.TryPushItems(values)
    
    @final
    def TryPeek(self) -> INullable[T]:
        first: IDoublyLinkedNode[T]|None = self._GetFirst()

        return GetNullValue() if first is None else GetNullable(first.GetValue())
    
    @final
    def TryPop(self) -> INullable[T]:
        return self._GetList().RemoveFirst()
    
    @final
    def Clear(self) -> None:
        self._GetList().Clear()

class Queue[T](LinkedList[T]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__(l)
    
    @final
    def _Push(self, value: T) -> IDoublyLinkedNode[T]:
        return self._GetList().AddLast(value)
class Stack[T](LinkedList[T]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__(l)
    
    @final
    def _Push(self, value: T) -> IDoublyLinkedNode[T]:
        return self._GetList().AddFirst(value)

class IterableQueue[T](Queue[T], Singly.IIterable[T]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__(l)
class IterableStack[T](Stack[T], Singly.IIterable[T]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__(l)