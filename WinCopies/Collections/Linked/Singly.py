from abc import abstractmethod
from collections.abc import Iterable, Iterator
from typing import final, Callable, Self

from WinCopies.Collections import Generator, ICountable, Collection
from WinCopies.Collections.Enumeration import IIterable, ICountableIterable
from WinCopies.Collections.Linked.Enumeration import NodeEnumeratorBase, GetValueIterator
from WinCopies.Collections.Linked.Node import ILinkedNode, LinkedNode
from WinCopies.Typing import EnsureDirectModuleCall
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
    def AsGenerator(self) -> Generator[T]:
        result: DualNullableValueBool[T] = self.TryPop()

        while result.GetValue():
            yield result.GetKey()
            
            result = self.TryPop()

class Iterable[T](IList[T], IIterable[T]):
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

class SinglyLinkedNodeEnumeratorBase[TNode: ILinkedNode[TItems], TItems](NodeEnumeratorBase[TNode, TItems]):
    def __init__(self, node: TNode):
        super().__init__(node)
class SinglyLinkedNodeEnumerator[T](SinglyLinkedNodeEnumeratorBase[SinglyLinkedNode[T], T]):
    def __init__(self, node: SinglyLinkedNode[T]):
        super().__init__(node)

class IterableQueue[T](Queue[T], Iterable[T]):
    def __init__(self, *values: T):
        super().__init__(*values)
class IterableStack[T](Stack[T], Iterable[T]):
    def __init__(self, *values: T):
        super().__init__(*values)

class CollectionBase[TList: IList[TItems], TItems](IList[TItems]):
    def __init__(self, l: TList):
        self.__list: TList = l
    
    def _GetCollection(self) -> TList:
        return self.__list

class Collection[T](CollectionBase[IList[T], T]):
    def __init__(self, l: IList[T]):
        super().__init__(l)

class CountableBase[TList: IList[TItems], TItems](CollectionBase[TList, TItems], ICountable):
    def __init__(self, l: TList):
        EnsureDirectModuleCall()

        super().__init__(l)

        self.__count: int = 0
    
    @final
    def GetCount(self) -> int:
        return self.__count
    
    @final
    def __Increment(self) -> None:
        self.__count += 1
    
    @final
    def Push(self, value: TItems) -> None:
        self._GetCollection().Push(value)

        self.__Increment()
    
    @final
    def __PushItems(self, items: Iterable[TItems]) -> None:
        def loop() -> Generator[TItems]:
            for item in items:
                yield item
                
                self.__Increment()
        
        self._GetCollection().PushItems(loop())
    
    @final
    def TryPushItems(self, items: Iterable[TItems]|None) -> bool:
        if items is None:
            return False
        
        self.__PushItems(items)

        return True
    @final
    def PushItems(self, items: Iterable[TItems]) -> None:
        if items is None:
            raise ValueError("No value provided.")
        
        self.__PushItems(items)
    
    @final
    def PushValues(self, *values: TItems) -> None:
        self.PushItems(values)
    
    @final
    def TryPeek(self) -> DualNullableValueBool[TItems]:
        self._GetCollection().TryPeek()
    
    @final
    def TryPop(self) -> DualNullableValueBool[TItems]:
        self._GetCollection().TryPop()

        self.__count -= 1
    
    @final
    def Clear(self) -> None:
        self._GetCollection().Clear()

        self.__count = 0

class Countable[T](CountableBase[IList[T], T]):
    def __init__(self, l: IList[T]):
        super().__init__(l)

class CountableQueue[T](Countable[T]):
    def __init__(self, *values: T):
        super().__init__(Queue[T]())

        self.PushItems(values)
class CountableStack[T](Countable[T]):
    def __init__(self, *values: T):
        super().__init__(Stack[T]())

        self.PushItems(values)

class CountableIterableQueue[T](CountableBase[Iterable[T], T], ICountableIterable[T]):
    def __init__(self, *values: T):
        super().__init__(IterableQueue[T]())

        self.PushItems(values)
    
    @final
    def TryGetIterator(self) -> Iterator[T]:
        return self._GetCollection().TryGetIterator()
class CountableIterableStack[T](CountableBase[Iterable[T], T], ICountableIterable[T]):
    def __init__(self, *values: T):
        super().__init__(IterableStack[T]())

        self.PushItems(values)
    
    @final
    def TryGetIterator(self) -> Iterator[T]:
        return self._GetCollection().TryGetIterator()