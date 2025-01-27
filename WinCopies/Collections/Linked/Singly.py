from abc import abstractmethod
from collections.abc import Iterable, Iterator
from typing import final, Callable, Self

from WinCopies.Collections import Generator, Collection, Enumeration
from WinCopies.Collections.Linked.Enumeration import NodeEnumeratorBase, GetValueIterator
from WinCopies.Collections.Linked.Node import LinkedNode
from WinCopies.Typing.Pairing import DualResult, DualNullableValueBool
    
class SinglyLinkedNode[T](LinkedNode[Self, T]):
    def __init__(self, value: T, nextNode: Self|None):
        super().__init__(value, nextNode)

class IList[T](Collection):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Push(self, value: T) -> None:
        pass
    
    @abstractmethod
    def TryPushItems(self, items: Iterable[T]|None) -> bool:
        pass
    @abstractmethod
    def PushItems(self, items: Iterable[T]) -> None:
        pass
    
    @abstractmethod
    def PushValues(self, *values: T) -> None:
        pass
    
    @abstractmethod
    def TryPeek(self) -> DualNullableValueBool[T]:
        pass
    
    @abstractmethod
    def TryPop(self) -> DualNullableValueBool[T]:
        pass
    
    @abstractmethod
    def Clear(self) -> None:
        pass
    
    @final
    def AsIterator(self) -> Generator[T]:
        result: DualNullableValueBool[T] = self.TryPop()

        while result.GetValue():
            yield result.GetKey()
            
            result = self.TryPop()

class IIterable[T](IList[T], Enumeration.IIterable[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _GetFirst(self) -> SinglyLinkedNode[T]:
        pass
    
    @final
    def TryGetIterator(self) -> Iterator[T]|None:
        return None if self.IsEmpty() else GetValueIterator(self._GetFirst())

class List[T](IList[T]):
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
    def _GetFirst(self) -> SinglyLinkedNode[T]:
        return self.__first
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
    def __PushItems(self, items: Iterable[T]) -> None:
        for value in items:
            self.Push(value)
    
    @final
    def TryPushItems(self, items: Iterable[T]|None) -> bool:
        if items is None:
            return False
        
        self.__PushItems(items)

        return True
    @final
    def PushItems(self, items: Iterable[T]) -> None:
        if items is None:
            raise ValueError("items can not be None.")
        
        self.__PushItems(items)
    
    @final
    def PushValues(self, *values: T) -> None:
        self.__PushItems(values)
    
    @final
    def TryPeek(self) -> DualNullableValueBool[T]:
        return DualResult[T|None, bool](None, False) if self.IsEmpty() else DualResult[T|None, bool](self.__first.GetValue(), True)
    
    @final
    def TryPop(self) -> DualNullableValueBool[T]:
        result: DualNullableValueBool[T] = self.TryPeek()

        if result.GetValue():
            first: SinglyLinkedNode[T] = self.__first

            self.__first = first.GetNext()

            first._SetNext(None) # Needed in case of a running enumeration.

            self._OnRemoved()

        return result
    
    @final
    def Clear(self) -> None:
        result: DualNullableValueBool[T] = self.TryPop()

        while result.GetValue(): # Needed in case of a running enumeration.
            result = self.TryPop()

        self.__first = None

        self._OnRemoved()

class Queue[T](List[T]):
    def __init__(self, *values: T):
        super().__init__()
        
        self.__last: SinglyLinkedNode[T]|None = None
        self.__updater: Callable[[SinglyLinkedNode[T], SinglyLinkedNode[T]], None] = self.__GetUpdater()

        self.PushItems(values)
    
    @final
    def __Push(self, first: SinglyLinkedNode[T], newNode: SinglyLinkedNode[T]) -> None:
        def push(previousNode: SinglyLinkedNode[T], newNode: SinglyLinkedNode[T]) -> None:
            previousNode._SetNext(newNode)

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

class Stack[T](List[T]):
    def __init__(self, *values: T):
        super().__init__()

        self.PushItems(values)
    
    @final
    def _Push(self, value: T, first: SinglyLinkedNode[T]) -> None:
        self._SetFirst(SinglyLinkedNode[T](value, first))
    
    @final
    def _OnRemoved(self) -> None:
        pass

class SinglyLinkedNodeEnumeratorBase[TNode: SinglyLinkedNode[TItems], TItems](NodeEnumeratorBase[TNode, TItems]):
    def __init__(self, node: TNode):
        super().__init__(node)
class SinglyLinkedNodeEnumerator[T](SinglyLinkedNodeEnumeratorBase[SinglyLinkedNode[T], T]):
    def __init__(self, node: SinglyLinkedNode[T]):
        super().__init__(node)

class IterableQueue[T](Queue[T], IIterable[T]):
    def __init__(self, *values: T):
        super().__init__(*values)
class IterableStack[T](Stack[T], IIterable[T]):
    def __init__(self, *values: T):
        super().__init__(*values)