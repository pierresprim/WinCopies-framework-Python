from abc import abstractmethod
from collections.abc import Iterable, Iterator
from typing import final

from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Linked.Node import IDoublyLinkedNode
from WinCopies.Collections.Linked import Singly, Doubly
from WinCopies.Collections.Linked.Doubly import List

from WinCopies.Typing import GenericConstraint, IGenericConstraintImplementation, INullable, GetNullable, GetNullValue

class LinkedListBase[TItems, TList](Singly.IList[TItems], GenericConstraint[TList, Doubly.IListBase[TItems]]):
    def __init__(self, l: TList):
        super().__init__()

        self.__list: TList = l
    
    @final
    def _GetContainer(self) -> TList:
        return self.__list
    @final
    def _GetFirst(self) -> IDoublyLinkedNode[TItems]|None: # Needed for iteration.
        return self._GetInnerContainer().GetFirst()
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    
    @abstractmethod
    def _Push(self, value: TItems) -> IDoublyLinkedNode[TItems]:
        pass
    
    @final
    def Push(self, value: TItems) -> None:
        self._Push(value)
    
    @final
    def TryPushItems(self, items: Iterable[TItems]|None) -> bool:
        return self._GetInnerContainer().AddLastItems(items)
    @final
    def PushItems(self, items: Iterable[TItems]) -> None:
        if not self.TryPushItems(items):
            raise ValueError("items can not be None.")
    
    @final
    def PushValues(self, *values: TItems) -> None:
        self.TryPushItems(values)
    
    @final
    def TryPeek(self) -> INullable[TItems]:
        first: IDoublyLinkedNode[TItems]|None = self._GetFirst()

        return GetNullValue() if first is None else GetNullable(first.GetValue())
    
    @final
    def TryPop(self) -> INullable[TItems]:
        return self._GetInnerContainer().RemoveFirst()
    
    @final
    def Clear(self) -> None:
        self._GetInnerContainer().Clear()

class QueueBase[TItems, TList](LinkedListBase[TItems, TList]):
    def __init__(self, l: TList):
        super().__init__(l)
    
    @final
    def _Push(self, value: TItems) -> IDoublyLinkedNode[TItems]:
        return self._GetInnerContainer().AddLast(value)
class StackBase[TItems, TList](LinkedListBase[TItems, TList]):
    def __init__(self, l: TList):
        super().__init__(l)
    
    @final
    def _Push(self, value: TItems) -> IDoublyLinkedNode[TItems]:
        return self._GetInnerContainer().AddFirst(value)

class LinkedList[T](LinkedListBase[T, Doubly.IListBase[T]], IGenericConstraintImplementation[Doubly.IListBase[T]]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__(LinkedList[T].GetList(l))
    
    @staticmethod
    def GetList(l: Doubly.IListBase[T]|None) -> Doubly.IListBase[T]:
        return List[T]() if l is None else l
class IterableLinkedList[T](LinkedListBase[T, Doubly.IList[T]], IGenericConstraintImplementation[Doubly.IList[T]]):
    def __init__(self, l: Doubly.IList[T]|None = None):
        super().__init__(IterableLinkedList[T].GetList(l))
    
    @staticmethod
    def GetList(l: Doubly.IList[T]|None) -> Doubly.IList[T]:
        return List[T]() if l is None else l

class Queue[T](QueueBase[T, Doubly.IListBase[T]], IGenericConstraintImplementation[Doubly.IListBase[T]]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__(LinkedList[T].GetList(l))
class Stack[T](StackBase[T, Doubly.IListBase[T]], IGenericConstraintImplementation[Doubly.IListBase[T]]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__(LinkedList[T].GetList(l))

class IIterableLinkedListBase[TItems, TList](Singly.IIterable[TItems], GenericConstraint[TList, Doubly.IList[TItems]]):
    def __init__(self) -> None:
        super().__init__()

    def TryGetIterator(self) -> Iterator[TItems]|None:
        iterable: Iterable[IDoublyLinkedNode[TItems]]|None = self._GetInnerContainer()
        
        return Select(iterable, lambda node: node.GetValue())
class IIterableLinkedList[T](IIterableLinkedListBase[T, Doubly.IList[T]]):
    def __init__(self) -> None:
        super().__init__()

class IterableQueue[T](QueueBase[T, Doubly.IList[T]], IIterableLinkedList[T], IGenericConstraintImplementation[Doubly.IList[T]]):
    def __init__(self, l: Doubly.IList[T]|None = None):
        super().__init__(IterableLinkedList[T].GetList(l))
class IterableStack[T](StackBase[T, Doubly.IList[T]], IIterableLinkedList[T], IGenericConstraintImplementation[Doubly.IList[T]]):
    def __init__(self, l: Doubly.IList[T]|None = None):
        super().__init__(IterableLinkedList[T].GetList(l))