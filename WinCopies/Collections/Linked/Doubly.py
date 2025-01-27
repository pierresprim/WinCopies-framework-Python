from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator
from typing import final, Self

from WinCopies.Collections import Generator, Collection, Enumeration
from WinCopies.Collections.Enumeration import EmptyEnumerator
from WinCopies.Collections.Linked.Enumeration import NodeEnumeratorBase, GetValueIterator
from WinCopies.Collections.Linked.Node import IDoublyLinkedNode, NodeBase

from WinCopies.Typing import AssertIsDirectModuleCall
from WinCopies.Typing.Delegate import Function

@final
class DoublyLinkedNode[T](NodeBase[Self, T]):
    def __init__(self, value: T, l: IList[T], previousNode: Self|None, nextNode: Self|None):
        AssertIsDirectModuleCall()

        super().__init__(value, previousNode, nextNode)

        self.__list: IList[T]|None = l
    
    def GetList(self) -> IList[T]:
        return self.__list
    
    def _OnRemoved(self) -> None:
        AssertIsDirectModuleCall()

        self.__list = None
    
    def Remove(self) -> None:
        self.GetList().Remove(self)

class IListBase[T](Collection):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AddFirst(self, value: T) -> DoublyLinkedNode[T]:
        pass
    @abstractmethod
    def AddLast(self, value: T) -> DoublyLinkedNode[T]:
        pass

    @abstractmethod
    def AddBefore(self, node: DoublyLinkedNode[T], value: T) -> DoublyLinkedNode[T]:
        pass
    @abstractmethod
    def AddAfter(self, node: DoublyLinkedNode[T], value: T) -> DoublyLinkedNode[T]:
        pass

    @final
    def __AddItems(self, items: Iterable[T]|None, first: Converter[T, DoublyLinkedNode[T]], other: Callable[[DoublyLinkedNode[T], T], None]) -> bool:
        if items is None:
            return False
        
        node: DoublyLinkedNode[T]|None = None
        adder: Method[T]|None = None

        def add(item: T) -> None:
            nonlocal node
            nonlocal adder

            node = first(item)
            
            adder = lambda item: other(node, item)
        
        adder = add

        for item in items:
            adder(item)
        
        return True

    @final
    def AddFirstItems(self, items: Iterable[T]|None) -> bool:
        return self.__AddItems(items, self.AddFirst, self.AddAfter)
    @final
    def AddFirstValues(self, *values: T) -> bool:
        return self.AddFirstItems(values)
    @final
    def AddLastItems(self, items: Iterable[T]|None) -> bool:
        return self.__AddItems(items, self.AddLast, self.AddBefore)
    @final
    def AddLastValues(self, *values: T) -> bool:
        return self.AddLastItems(values)
    
    @final
    def AddItemsBefore(self, node: DoublyLinkedNode[T], items: Iterable[T]|None) -> bool:
        if items is None:
            return False
        
        for item in items:
            self.AddBefore(node, item)

        return True
    @final
    def AddValuesBefore(self, node: DoublyLinkedNode[T], *values: T) -> bool:
        return self.AddItemsBefore(node, values)
    @final
    def AddItemsAfter(self, node: DoublyLinkedNode[T], items: Iterable[T]|None) -> bool:
        if items is None:
            return False
        
        for item in items:
            node = self.AddAfter(node, item)

        return True
    @final
    def AddValuesAfter(self, node: DoublyLinkedNode[T], *values: T) -> bool:
        return self.AddItemsAfter(node, values)
    
    @abstractmethod
    def GetFirst(self) -> DoublyLinkedNode[T]|None:
        pass
    @abstractmethod
    def GetLast(self) -> DoublyLinkedNode[T]|None:
        pass
    
    @abstractmethod
    def Remove(self, node: DoublyLinkedNode[T]) -> None:
        pass
    
    @abstractmethod
    def RemoveFirst(self) -> DoublyLinkedNode[T]|None:
        pass
    @abstractmethod
    def RemoveLast(self) -> DoublyLinkedNode[T]|None:
        pass
    
    @abstractmethod
    def Clear(self) -> None:
        pass
    
    @final
    def __AsIterator(self, func: Function[DoublyLinkedNode[T]|None]) -> Generator[DoublyLinkedNode[T]]:
        result: DoublyLinkedNode[T] = func()

        while result is not None:
            yield result
            
            result = func()
    
    @final
    def AsQueuedIterator(self) -> Generator[DoublyLinkedNode[T]]:
        return self.__AsIterator(self.RemoveFirst)
    @final
    def AsStackedIterator(self) -> Generator[DoublyLinkedNode[T]]:
        return self.__AsIterator(self.RemoveLast)

class IIterable[T](IListBase[T], Enumeration.IIterable[DoublyLinkedNode[T]]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def TryGetValueIterator(self) -> Iterator[T]|None:
        pass

class IList[T](IIterable[T]):
    def __init__(self):
        super().__init__()

class List[T](IList[T]):
    def __init__(self):
        super().__init__()
        
        self.__first: DoublyLinkedNode[T]|None = None
        self.__last: DoublyLinkedNode[T]|None = None

    @final
    def IsEmpty(self) -> bool:
        return self.__first is None
    @final
    def HasItems(self) -> bool:
        return super().HasItems()
    
    @final
    def AddFirst(self, value: T) -> DoublyLinkedNode[T]:
        first: DoublyLinkedNode[T]|None = self.__first

        self.__first = DoublyLinkedNode[T](value, self, None, first)

        if first is not None:
            first._SetPrevious(self.__first)
        
        if self.__last is None:
            self.__last = self.__first

        return self.__first
    @final
    def AddLast(self, value: T) -> DoublyLinkedNode[T]:
        last: DoublyLinkedNode[T]|None = self.__last
        
        self.__last = DoublyLinkedNode[T](value, self, last, None)
        
        if last is not None:
            last._SetNext(self.__last)
        
        if self.__first is None:
            self.__first = self.__last

        return self.__last
    
    @final
    def AddBefore(self, node: DoublyLinkedNode[T], value: T) -> DoublyLinkedNode[T]:
        previousNode: DoublyLinkedNode[T] = node.GetPrevious()
        
        newNode: DoublyLinkedNode[T] = DoublyLinkedNode[T](value, self, previousNode, node)

        previousNode._SetNext(newNode)

        node._SetPrevious(newNode)

        return newNode
    @final
    def AddAfter(self, node: DoublyLinkedNode[T], value: T) -> DoublyLinkedNode[T]:
        nextNode: DoublyLinkedNode[T] = node.GetNext()
        
        newNode: DoublyLinkedNode[T] = DoublyLinkedNode[T](value, self, node, nextNode)

        nextNode._SetPrevious(newNode)

        node._SetNext(newNode)

        return newNode
    
    @final
    def GetFirst(self) -> DoublyLinkedNode[T]|None:
        return self.__first
    @final
    def GetLast(self) -> DoublyLinkedNode[T]|None:
        return self.__last

    @final
    def __Remove(self, node: DoublyLinkedNode[T]) -> None:
        previousNode: DoublyLinkedNode[T]|None = node.GetPrevious()
        nextNode: DoublyLinkedNode[T]|None = node.GetNext()

        if previousNode is None:
            self.__first = nextNode
        
        else:
            previousNode._SetNext(nextNode)
        
        if nextNode is None:
            self.__last = previousNode
        else:
            nextNode._SetPrevious(previousNode)

        node._SetPrevious(None)
        node._SetNext(None)
    @final
    def Remove(self, node: DoublyLinkedNode[T]) -> None:
        assert(node.GetList() is not self, "Invalid operation.")

        self.__Remove(node)
    
    @final
    def RemoveFirst(self) -> DoublyLinkedNode[T]|None:
        node: DoublyLinkedNode[T]|None = self.__first

        if node is None:
            return
        
        nextNode: DoublyLinkedNode[T] = node.GetNext()
        
        self.__Remove(node)

        self.__first = nextNode

        return node
    @final
    def RemoveLast(self) -> DoublyLinkedNode[T]|None:
        node: DoublyLinkedNode[T]|None = self.__last

        if node is None:
            return
        
        previousNode: DoublyLinkedNode[T] = node.GetPrevious()
        
        self.__Remove(node)

        self.__last = previousNode

        return node
    
    @final
    def Clear(self) -> None:
        node: DoublyLinkedNode[T]|None = self.RemoveFirst()

        while node is not None:
            node = self.RemoveFirst()
    
    @final
    def TryGetIterator(self) -> Iterator[DoublyLinkedNode[T]]|None:
        return None if self.IsEmpty() else DoublyLinkedNodeEnumerator[T](self.__first)
    
    @final
    def TryGetValueIterator(self) -> Iterator[T]|None:
        return None if self.IsEmpty() else GetValueIterator(self.__first)
    @final
    def AsValueIterator(self) -> Iterator[T]:
        iterator: Iterator[T]|None = self.TryGetValueIterator()

        return EmptyEnumerator[T]() if iterator is None else iterator

class DoublyLinkedNodeEnumeratorBase[TNode: IDoublyLinkedNode[TItems], TItems](NodeEnumeratorBase[TNode, TItems]):
    def __init__(self, node: TNode):
        super().__init__(node)
class DoublyLinkedNodeEnumerator[T](DoublyLinkedNodeEnumeratorBase[DoublyLinkedNode[T], T]):
    def __init__(self, node: DoublyLinkedNode[T]):
        super().__init__(node)