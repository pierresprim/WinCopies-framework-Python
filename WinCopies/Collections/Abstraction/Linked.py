from abc import abstractmethod
from collections.abc import Iterable
from typing import final

from WinCopies.Collections.Abstraction.Enumeration import Enumerator
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator
from WinCopies.Collections.Linked import Singly, Doubly
from WinCopies.Collections.Linked.Doubly import INode, List

from WinCopies.Typing import GenericConstraint, IGenericConstraintImplementation, INullable

class LinkedListBase[TItems, TList](Singly.IList[TItems], GenericConstraint[TList, Doubly.IReadWriteList[TItems]]):
    def __init__(self, l: TList):
        super().__init__()

        self.__list: TList = l
    
    @final
    def _GetContainer(self) -> TList:
        return self.__list
    @final
    def _GetFirst(self) -> INode[TItems]|None: # Needed for iteration.
        return self._GetInnerContainer().GetFirstNode()
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    
    @abstractmethod
    def _Push(self, value: TItems) -> INode[TItems]:
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
        return self._GetInnerContainer().TryGetFirst()
    
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
    def _Push(self, value: TItems) -> INode[TItems]:
        return self._GetInnerContainer().AddLastNode(value)
class StackBase[TItems, TList](LinkedListBase[TItems, TList]):
    def __init__(self, l: TList):
        super().__init__(l)
    
    @final
    def _Push(self, value: TItems) -> INode[TItems]:
        return self._GetInnerContainer().AddFirstNode(value)

class LinkedList[T](LinkedListBase[T, Doubly.IReadWriteList[T]], IGenericConstraintImplementation[Doubly.IReadWriteList[T]]):
    def __init__(self, l: Doubly.IReadWriteList[T]|None = None):
        super().__init__(LinkedList[T].GetList(l))
    
    @staticmethod
    def GetList(l: Doubly.IReadWriteList[T]|None) -> Doubly.IReadWriteList[T]:
        return List[T]() if l is None else l
class EnumerableLinkedList[T](LinkedListBase[T, Doubly.IList[T]], IGenericConstraintImplementation[Doubly.IList[T]]):
    def __init__(self, l: Doubly.IList[T]|None = None):
        super().__init__(EnumerableLinkedList[T].GetList(l))
    
    @staticmethod
    def GetList(l: Doubly.IList[T]|None) -> Doubly.IList[T]:
        return List[T]() if l is None else l

class Queue[T](QueueBase[T, Doubly.IReadWriteList[T]], IGenericConstraintImplementation[Doubly.IReadWriteList[T]]):
    def __init__(self, l: Doubly.IReadWriteList[T]|None = None):
        super().__init__(LinkedList[T].GetList(l))
class Stack[T](StackBase[T, Doubly.IReadWriteList[T]], IGenericConstraintImplementation[Doubly.IReadWriteList[T]]):
    def __init__(self, l: Doubly.IReadWriteList[T]|None = None):
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