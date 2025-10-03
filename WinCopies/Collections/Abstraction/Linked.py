from abc import abstractmethod
from collections.abc import Iterable
from typing import final

from WinCopies.Collections.Abstraction.Enumeration import Enumerator
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator
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
class EnumerableLinkedList[T](LinkedListBase[T, Doubly.IList[T]], IGenericConstraintImplementation[Doubly.IList[T]]):
    def __init__(self, l: Doubly.IList[T]|None = None):
        super().__init__(EnumerableLinkedList[T].GetList(l))
    
    @staticmethod
    def GetList(l: Doubly.IList[T]|None) -> Doubly.IList[T]:
        return List[T]() if l is None else l

class Queue[T](QueueBase[T, Doubly.IListBase[T]], IGenericConstraintImplementation[Doubly.IListBase[T]]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__(LinkedList[T].GetList(l))
class Stack[T](StackBase[T, Doubly.IListBase[T]], IGenericConstraintImplementation[Doubly.IListBase[T]]):
    def __init__(self, l: Doubly.IListBase[T]|None = None):
        super().__init__(LinkedList[T].GetList(l))

class IEnumerableLinkedListBase[TItems, TList](Singly.IEnumerable[TItems], GenericConstraint[TList, Doubly.IList[TItems]]):
    def __init__(self):
        super().__init__()

    def TryGetEnumerator(self) -> IEnumerator[TItems]|None:
        enumerable: IEnumerable[TItems]|None = self._GetInnerContainer()
        
        return Enumerator[TItems].TryCreate(enumerable.TryGetEnumerator())
class IEnumerableLinkedList[T](IEnumerableLinkedListBase[T, Doubly.IList[T]]):
    def __init__(self):
        super().__init__()

class EnumerableQueue[T](QueueBase[T, Doubly.IList[T]], IEnumerableLinkedList[T], IGenericConstraintImplementation[Doubly.IList[T]]):
    def __init__(self, l: Doubly.IList[T]|None = None):
        super().__init__(EnumerableLinkedList[T].GetList(l))
class EnumerableStack[T](StackBase[T, Doubly.IList[T]], IEnumerableLinkedList[T], IGenericConstraintImplementation[Doubly.IList[T]]):
    def __init__(self, l: Doubly.IList[T]|None = None):
        super().__init__(EnumerableLinkedList[T].GetList(l))