import collections.abc

from abc import abstractmethod
from collections.abc import Iterator
from typing import final, Callable, Self

from WinCopies.Collections import Generator, ICountable, IReadOnlyCollection
from WinCopies.Collections.Enumeration import IIterable, ICountableIterable
from WinCopies.Collections.Linked.Enumeration import NodeEnumeratorBase, GetValueIteratorFromNode
from WinCopies.Collections.Linked.Node import LinkedNode

from WinCopies.Typing import GenericConstraint, IGenericConstraintImplementation, INullable, GetNullable, GetNullValue, EnsureDirectModuleCall

class SinglyLinkedNode[T](LinkedNode['SinglyLinkedNode', T]):
    def __init__(self, value: T, nextNode: Self|None):
        super().__init__(value, nextNode)

class IList[T](IReadOnlyCollection):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Push(self, value: T) -> None:
        pass
    
    @abstractmethod
    def TryPushItems(self, items: collections.abc.Iterable[T]|None) -> bool:
        pass
    @abstractmethod
    def PushItems(self, items: collections.abc.Iterable[T]) -> None:
        pass
    
    @abstractmethod
    def PushValues(self, *values: T) -> None:
        pass
    
    @abstractmethod
    def TryPeek(self) -> INullable[T]:
        pass
    
    @abstractmethod
    def TryPop(self) -> INullable[T]:
        pass
    
    @abstractmethod
    def Clear(self) -> None:
        pass
    
    @final
    def AsGenerator(self) -> Generator[T]:
        result: INullable[T] = self.TryPop()

        while result.HasValue():
            yield result.GetValue()
            
            result = self.TryPop()

class Iterable[T](IList[T], IIterable[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _GetFirst(self) -> SinglyLinkedNode[T]|None:
        pass
    
    @final
    def TryGetIterator(self) -> Iterator[T]|None:
        if self.IsEmpty():
            return None
        
        first: SinglyLinkedNode[T]|None = self._GetFirst() # Should never be None here.
        
        return None if first is None else GetValueIteratorFromNode(first)

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
    def _GetFirst(self) -> SinglyLinkedNode[T]|None:
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
            self._Push(value, self.__first) # type: ignore
    
    @final
    def __PushItems(self, items: collections.abc.Iterable[T]) -> None:
        for value in items:
            self.Push(value)
    
    @final
    def TryPushItems(self, items: collections.abc.Iterable[T]|None) -> bool:
        if items is None:
            return False
        
        self.__PushItems(items)

        return True
    @final
    def PushItems(self, items: collections.abc.Iterable[T]) -> None:
        if items is None: # type: ignore
            raise ValueError("items can not be None.")
        
        self.__PushItems(items)
    
    @final
    def PushValues(self, *values: T) -> None:
        self.__PushItems(values)
    
    @final
    def TryPeek(self) -> INullable[T]:
        return GetNullValue() if self.IsEmpty() else (GetNullValue() if self.__first is None else GetNullable(self.__first.GetValue())) # self.__first should never be None if self.IsEmpty().
    
    @final
    def TryPop(self) -> INullable[T]:
        result: INullable[T] = self.TryPeek()

        if result.HasValue():
            first: SinglyLinkedNode[T]|None = self.__first

            if first is None: # Should never be None here.
                return result

            self.__first = first.GetNext()

            first._SetNext(None) # type: ignore # Needed in case of a running enumeration.

            self._OnRemoved()

        return result
    
    @final
    def Clear(self) -> None:
        result: INullable[T] = self.TryPop()

        while result.HasValue(): # Needed in case of a running enumeration.
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
            previousNode._SetNext(newNode) # type: ignore

            self.__last = newNode
        
        push(first, newNode)

        self.__updater = lambda first, newNode: push(self.__last, newNode) # type: ignore
    
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

class SinglyLinkedNodeEnumeratorBase[TItems, TNode](NodeEnumeratorBase[TItems, TNode]):
    def __init__(self, node: TNode):
        super().__init__(node)
class SinglyLinkedNodeEnumerator[T](SinglyLinkedNodeEnumeratorBase[T, SinglyLinkedNode[T]]):
    def __init__(self, node: SinglyLinkedNode[T]):
        super().__init__(node)

class IterableQueue[T](Queue[T], Iterable[T]):
    def __init__(self, *values: T):
        super().__init__(*values)
class IterableStack[T](Stack[T], Iterable[T]):
    def __init__(self, *values: T):
        super().__init__(*values)

class CollectionBase[TItems, TList](IList[TItems], GenericConstraint[TList, IList[TItems]]):
    def __init__(self, l: TList):
        self.__list: TList = l
    
    def _GetContainer(self) -> TList:
        return self.__list
    def _GetCollection(self) -> TList:
        return self._GetContainer()

    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    @final
    def HasItems(self) -> bool:
        return self._GetInnerContainer().HasItems()

class Collection[T](CollectionBase[T, IList[T]], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, l: IList[T]):
        super().__init__(l)

class CountableBase[TItems, TList](CollectionBase[TItems, TList], ICountable):
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
        self._GetInnerContainer().Push(value)

        self.__Increment()
    
    @final
    def __PushItems(self, items: collections.abc.Iterable[TItems]) -> None:
        def loop() -> Generator[TItems]:
            for item in items:
                yield item
                
                self.__Increment()
        
        self._GetInnerContainer().PushItems(loop())
    
    @final
    def TryPushItems(self, items: collections.abc.Iterable[TItems]|None) -> bool:
        if items is None:
            return False
        
        self.__PushItems(items)

        return True
    @final
    def PushItems(self, items: collections.abc.Iterable[TItems]) -> None:
        if items is None: # type: ignore
            raise ValueError("No value provided.")
        
        self.__PushItems(items)
    
    @final
    def PushValues(self, *values: TItems) -> None:
        self.PushItems(values)
    
    @final
    def TryPeek(self) -> INullable[TItems]:
        return self._GetInnerContainer().TryPeek()
    
    @final
    def TryPop(self) ->  INullable[TItems]:
        result: INullable[TItems] = self._GetInnerContainer().TryPop()

        if result.HasValue():
            self.__count -= 1
        
        return result
    
    @final
    def Clear(self) -> None:
        self._GetInnerContainer().Clear()

        self.__count = 0

class Countable[T](CountableBase[T, IList[T]], IGenericConstraintImplementation[IList[T]]):
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

class CountableIterableBase[TItems, TList](CountableBase[TItems, TList], ICountableIterable[TItems], GenericConstraint[TList, Iterable[TItems]]):
    def __init__(self, l: TList):
        super().__init__(l)
class CountableIterable[T](CountableIterableBase[T, Iterable[T]], IGenericConstraintImplementation[Iterable[T]]):
    def __init__(self, l: Iterable[T]):
        super().__init__(l)

class CountableIterableQueue[T](CountableIterable[T]):
    def __init__(self, *values: T):
        super().__init__(IterableQueue[T]())

        self.PushItems(values)
    
    @final
    def TryGetIterator(self) -> Iterator[T]|None:
        return self._GetCollection().TryGetIterator()
class CountableIterableStack[T](CountableIterable[T]):
    def __init__(self, *values: T):
        super().__init__(IterableStack[T]())

        self.PushItems(values)
    
    @final
    def TryGetIterator(self) -> Iterator[T]|None:
        return self._GetCollection().TryGetIterator()