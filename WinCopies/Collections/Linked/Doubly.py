from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator
from typing import final, Callable

from WinCopies.Assertion import EnsureTrue, GetAssertionError
from WinCopies.Delegates import Self
from WinCopies.Collections import Generator, IReadOnlyCollection, Enumeration
from WinCopies.Collections.Enumeration import IEnumerator, Iterator, Accessor, AsIterator
from WinCopies.Collections.Linked.Enumeration import NodeEnumeratorBase, GetValueIteratorFromNode
from WinCopies.Collections.Linked.Node import IDoublyLinkedNode, NodeBase
from WinCopies.Typing import InvalidOperationError, IGenericConstraint, IGenericConstraintImplementation, INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Function, Converter
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

@final
class DoublyLinkedNode[T](NodeBase['DoublyLinkedNode', T]):
    def __init__(self, value: T, l: IList[T], previousNode: DoublyLinkedNode[T]|None, nextNode: DoublyLinkedNode[T]|None):
        EnsureDirectModuleCall()

        super().__init__(value, previousNode, nextNode)

        self.__list: IList[T]|None = l
    
    def GetList(self) -> IList[T]|None:
        return self.__list
    
    def _OnRemoved(self) -> None:
        EnsureDirectModuleCall()

        self.__list = None
    
    def Remove(self) -> None:
        l: IList[T]|None = self.GetList()

        if l is None:
            raise InvalidOperationError()
        
        l.Remove(self)
    
    def Check(self, l: IList[T]) -> bool:
        return self.GetList() is l
    def Ensure(self, l: IList[T]) -> None:
        EnsureTrue(self.Check(l))

class IListBase[T](IReadOnlyCollection):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AddFirst(self, value: T) -> IDoublyLinkedNode[T]:
        pass
    @abstractmethod
    def AddLast(self, value: T) -> IDoublyLinkedNode[T]:
        pass

    @abstractmethod
    def AddBefore(self, node: IDoublyLinkedNode[T], value: T) -> IDoublyLinkedNode[T]:
        pass
    @abstractmethod
    def AddAfter(self, node: IDoublyLinkedNode[T], value: T) -> IDoublyLinkedNode[T]:
        pass

    @final
    def __AddItems(self, items: Iterable[T]|None, first: Converter[T, IDoublyLinkedNode[T]], other: Callable[[IDoublyLinkedNode[T], T], IDoublyLinkedNode[T]]) -> bool:
        if items is None:
            return False
        
        node: IDoublyLinkedNode[T]
        adder: Converter[T, IDoublyLinkedNode[T]]|None = None

        def add(item: T) -> IDoublyLinkedNode[T]:
            nonlocal adder

            adder = lambda item: other(node, item)

            return first(item)
        
        adder = add

        for item in items:
            node = adder(item)
        
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
    def AddItemsBefore(self, node: IDoublyLinkedNode[T], items: Iterable[T]|None) -> bool:
        if items is None:
            return False
        
        for item in items:
            self.AddBefore(node, item)

        return True
    @final
    def AddValuesBefore(self, node: IDoublyLinkedNode[T], *values: T) -> bool:
        return self.AddItemsBefore(node, values)
    @final
    def AddItemsAfter(self, node: IDoublyLinkedNode[T], items: Iterable[T]|None) -> bool:
        if items is None:
            return False
        
        for item in items:
            node = self.AddAfter(node, item)

        return True
    @final
    def AddValuesAfter(self, node: IDoublyLinkedNode[T], *values: T) -> bool:
        return self.AddItemsAfter(node, values)
    
    @abstractmethod
    def GetFirst(self) -> IDoublyLinkedNode[T]|None:
        pass
    @abstractmethod
    def GetLast(self) -> IDoublyLinkedNode[T]|None:
        pass
    
    @final
    def __TryGetValue[TDefault](self, default: TDefault, item: INullable[T]) -> T|TDefault:
        return item.GetValue() if item.HasValue() else default
    
    @final
    def TryGetFirstValue[TDefault](self, default: TDefault) -> T|TDefault:
        return self.__TryGetValue(default, self.TryGetFirst())
    @final
    def TryGetLastValue[TDefault](self, default: TDefault) -> T|TDefault:
        return self.__TryGetValue(default, self.TryGetLast())
    
    @final
    def TryGetFirstValueOrNone(self) -> T|None:
        return self.TryGetFirstValue(None)
    @final
    def TryGetLastValueOrNone(self) -> T|None:
        return self.TryGetLastValue(None)

    @final
    def __TryGet(self, node: IDoublyLinkedNode[T]|None) -> INullable[T]:
        return GetNullValue() if node is None else GetNullable(node.GetValue())
    
    @final
    def TryGetFirst(self) -> INullable[T]:
        return self.__TryGet(self.GetFirst())
    @final
    def TryGetLast(self) -> INullable[T]:
        return self.__TryGet(self.GetLast())
    
    @abstractmethod
    def Remove(self, node: IDoublyLinkedNode[T]) -> None:
        pass
    
    @abstractmethod
    def RemoveFirst(self) -> INullable[T]:
        pass
    @abstractmethod
    def RemoveLast(self) -> INullable[T]:
        pass
    
    @abstractmethod
    def Clear(self) -> None:
        pass
    
    @final
    def __AsItemEnumerator[TOut](self, func: Function[INullable[T]], converter: Converter[INullable[T], TOut]) -> IEnumerator[TOut]:
        def enumerate() -> Generator[TOut]:
            result: INullable[T] = func()

            while result.HasValue():
                yield converter(result)
                
                result = func()
        
        return Accessor(lambda: Iterator(enumerate()))
    
    @final
    def __AsEnumerator(self, func: Function[INullable[T]]) -> IEnumerator[INullable[T]]:
        return self.__AsItemEnumerator(func, Self)
    @final
    def __AsValueEnumerator(self, func: Function[INullable[T]]) -> IEnumerator[T]:
        return self.__AsItemEnumerator(func, lambda item: item.GetValue())
    
    @final
    def AsQueuedEnumerator(self) -> IEnumerator[INullable[T]]:
        return self.__AsEnumerator(self.RemoveFirst)
    @final
    def AsStackedEnumerator(self) -> IEnumerator[INullable[T]]:
        return self.__AsEnumerator(self.RemoveLast)
    
    @final
    def AsQueuedValueEnumerator(self) -> IEnumerator[T]:
        return self.__AsValueEnumerator(self.RemoveFirst)
    @final
    def AsStackedValueEnumerator(self) -> IEnumerator[T]:
        return self.__AsValueEnumerator(self.RemoveLast)

class IIterable[T](Enumeration.IIterable[T]):
    @final
    class __Iterable(Enumeration.IIterable[IDoublyLinkedNode[T]]):
        def __init__(self, l: IIterable[T]):
            super().__init__()

            self.__list: IIterable[T] = l
        
        def TryGetIterator(self) -> Iterator[IDoublyLinkedNode[T]]|None:
            return self.__list.TryGetNodeIterator()
    
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def TryGetNodeIterator(self) -> Iterator[IDoublyLinkedNode[T]]|None:
        pass
    
    @final
    def AsNodeIterable(self) -> Enumeration.IIterable[IDoublyLinkedNode[T]]:
        return IIterable[T].__Iterable(self)

class IList[T](IListBase[T], IIterable[T]):
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
            first._SetPrevious(self.__first) # type: ignore
        
        if self.__last is None:
            self.__last = self.__first

        return self.__first
    @final
    def AddLast(self, value: T) -> DoublyLinkedNode[T]:
        last: DoublyLinkedNode[T]|None = self.__last
        
        self.__last = DoublyLinkedNode[T](value, self, last, None)
        
        if last is not None:
            last._SetNext(self.__last) # type: ignore
        
        if self.__first is None:
            self.__first = self.__last

        return self.__last
    
    @final
    def AddBefore(self, node: IDoublyLinkedNode[T], value: T) -> DoublyLinkedNode[T]:
        if node is self.GetFirst():
            return self.AddFirst(value)
        
        if not isinstance(node, DoublyLinkedNode):
            raise GetAssertionError()
        
        node.Ensure(self)
        
        previousNode: DoublyLinkedNode[T]|None = node.GetPrevious()
        newNode: DoublyLinkedNode[T] = DoublyLinkedNode[T](value, self, previousNode, node)

        previousNode._SetNext(newNode) # type: ignore
        node._SetPrevious(newNode) # type: ignore

        return newNode
    @final
    def AddAfter(self, node: IDoublyLinkedNode[T], value: T) -> DoublyLinkedNode[T]:
        if node is self.GetLast():
            return self.AddLast(value)
        
        if not isinstance(node, DoublyLinkedNode):
            raise GetAssertionError()
        
        node.Ensure(self)

        nextNode: DoublyLinkedNode[T]|None = node.GetNext()
        newNode: DoublyLinkedNode[T] = DoublyLinkedNode[T](value, self, node, nextNode)

        nextNode._SetPrevious(newNode) # type: ignore
        node._SetNext(newNode) # type: ignore

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
            previousNode._SetNext(nextNode) # type: ignore
        
        if nextNode is None:
            self.__last = previousNode
        else:
            nextNode._SetPrevious(previousNode) # type: ignore

        node._SetPrevious(None) # type: ignore
        node._SetNext(None) # type: ignore
    @final
    def Remove(self, node: IDoublyLinkedNode[T]) -> None:
        if not isinstance(node, DoublyLinkedNode):
            raise GetAssertionError()
        
        node.Ensure(self)

        self.__Remove(node)
    
    @final
    def RemoveFirst(self) -> INullable[T]:
        node: DoublyLinkedNode[T]|None = self.__first

        if node is None:
            return GetNullValue()
        
        nextNode: DoublyLinkedNode[T]|None = node.GetNext()
        
        self.__Remove(node)

        self.__first = nextNode

        return GetNullable(node.GetValue())
    @final
    def RemoveLast(self) -> INullable[T]:
        node: DoublyLinkedNode[T]|None = self.__last

        if node is None:
            return GetNullValue()
        
        previousNode: DoublyLinkedNode[T]|None = node.GetPrevious()
        
        self.__Remove(node)

        self.__last = previousNode

        return GetNullable(node.GetValue())
    
    @final
    def Clear(self) -> None:
        node: INullable[T] = self.RemoveFirst()

        while node.HasValue():
            node = self.RemoveFirst()
    
    @final
    def TryGetIterator(self) -> Iterator[T]|None:
        return None if self.IsEmpty() or self.__first is None else GetValueIteratorFromNode(self.__first) # self.__first should not be None if self.IsEmpty().
    
    @final
    def TryGetNodeIterator(self) -> Iterator[IDoublyLinkedNode[T]]|None:
        return None if self.IsEmpty() or self.__first is None else DoublyLinkedNodeEnumerator[T](self.__first) # self.__first should not be None if self.IsEmpty().
    @final
    def GetNodeIterator(self) -> Iterator[IDoublyLinkedNode[T]]:
        iterator: Iterator[IDoublyLinkedNode[T]]|None = self.TryGetNodeIterator()

        return AsIterator(iterator)

class DoublyLinkedNodeEnumeratorBase[TItems, TNode](NodeEnumeratorBase[TItems, TNode], IGenericConstraint[TNode, IDoublyLinkedNode[TItems]]):
    def __init__(self, node: TNode):
        super().__init__(node)
class DoublyLinkedNodeEnumerator[T](DoublyLinkedNodeEnumeratorBase[T, IDoublyLinkedNode[T]], IGenericConstraintImplementation[IDoublyLinkedNode[T]]):
    def __init__(self, node: IDoublyLinkedNode[T]):
        super().__init__(node)

    def _GetNextNode(self, node: IDoublyLinkedNode[T]) -> IDoublyLinkedNode[T]|None:
        return node.GetNext()