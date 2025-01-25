from abc import abstractmethod
from collections.abc import Iterable
from typing import final

from WinCopies.Collections.Linked.Node import ILinkedListNode
from WinCopies.Collections.Linked import Singly, Doubly
from WinCopies.Collections.Linked.Singly import Queue
from WinCopies.Collections.Linked.Doubly import DoublyLinkedNode, List

from WinCopies.Typing.Pairing import DualNullableValueBool

class LinkedList[T](Singly.IList[T]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__()

        self.__list: Doubly.IListBase[T] = List[T]() if l is None else l
    
    @final
    def _GetList(self) -> Doubly.IListBase[T]:
        return self.__list
    @final
    def _GetFirst(self) -> Doubly.IListBase[T]: # Needed for iteration.
        return self._GetList().GetFirst()
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetList().IsEmpty()
    
    @abstractmethod
    def _Push(self, value: T) -> DoublyLinkedNode[T]:
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
    def __GetResult(result: ILinkedListNode[T]|None):
        def getResult(result: T, info: bool) -> DualNullableValueBool[T]:
            return DualNullableValueBool[T](result, info)
        
        return getResult(None, False) if result is None else result.GetValue()
    
    @final
    def TryPeek(self) -> DualNullableValueBool[T]:
        return self.__GetResult(self._GetFirst())
    
    @final
    def TryPop(self) -> DualNullableValueBool[T]:
        return self.__GetResult(self._GetList().RemoveFirst())
    
    @final
    def Clear(self) -> None:
        self._GetList().Clear()

class Queue[T](LinkedList[T]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__(l)
    
    @final
    def _Push(self, value: T) -> DoublyLinkedNode[T]:
        return self._GetList().AddLast(value)
class Stack[T](LinkedList[T]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__(l)
    
    @final
    def _Push(self, value: T) -> DoublyLinkedNode[T]:
        return self._GetList().AddFirst(value)

class IterableQueue[T](Queue[T], Singly.IIterable[T]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__(l)
class IterableStack[T](Stack[T], Singly.IIterable[T]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__(l)