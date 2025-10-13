from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator
from typing import final, Callable, Self as SelfType

from WinCopies.Assertion import EnsureTrue, GetAssertionError
from WinCopies.Delegates import Self
from WinCopies.Collections import Enumeration, Generator, IReadOnlyCollection, ICountable
from WinCopies.Collections.Abstraction.Enumeration import Enumerator
from WinCopies.Collections.Enumeration import IEnumerator, Enumerable, CountableEnumerable, Iterator, Accessor, GetEnumerator
from WinCopies.Collections.Linked.Enumeration import NodeEnumeratorBase, GetValueEnumeratorFromNode
from WinCopies.Collections.Linked.Node import ILinkedNode, LinkedNode
from WinCopies.Typing import InvalidOperationError, IGenericConstraint, IGenericConstraintImplementation, GenericConstraint, INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Method, Function, Converter, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

class IDoublyLinkedNode[T](ILinkedNode[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetPrevious(self) -> SelfType|None:
        pass

class NodeBase[TNode: 'NodeBase', TItems](LinkedNode[TNode, TItems], IDoublyLinkedNode[TItems]):
    def __init__(self, value: TItems, previousNode: TNode|None, nextNode: TNode|None):
        super().__init__(value, nextNode)

        self.__previous: TNode|None = previousNode
    
    @final
    def GetPrevious(self) -> TNode|None:
        return self.__previous
    @final
    def _SetPrevious(self, previous: TNode|None) -> None:
        self.__previous = previous

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

class IReadOnlyList[T](IReadOnlyCollection):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def TryGetFirst(self) -> INullable[T]:
        pass
    @abstractmethod
    def TryGetLast(self) -> INullable[T]:
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

class IListBase[T](IReadOnlyList[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyList[T]:
        pass
    
    @abstractmethod
    def GetFirst(self) -> IDoublyLinkedNode[T]|None:
        pass
    @abstractmethod
    def GetLast(self) -> IDoublyLinkedNode[T]|None:
        pass

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

class IReadOnlyEnumerableList[T](IReadOnlyList[T], Enumeration.IEnumerable[T]):
    def __init__(self):
        super().__init__()

class IEnumerable[T](Enumeration.IEnumerable[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def TryGetNodeEnumerator(self) -> IEnumerator[IDoublyLinkedNode[T]]|None:
        pass
    
    @abstractmethod
    def AsNodeEnumerable(self) -> Enumeration.IEnumerable[IDoublyLinkedNode[T]]:
        pass

class IList[T](IListBase[T], IReadOnlyEnumerableList[T], IEnumerable[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnlyEnumerable(self) -> IReadOnlyEnumerableList[T]:
        pass

class _ReadOnlyListBase[TItem, TList](IReadOnlyList[TItem], GenericConstraint[TList, IReadOnlyList[TItem]]):
    def __init__(self, items: TList):
        super().__init__()

        self.__items: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__items
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    
    @final
    def HasItems(self) -> bool:
        return super().HasItems()
    
    @final
    def TryGetFirst(self) -> INullable[TItem]:
        return self._GetInnerContainer().TryGetFirst()
    @final
    def TryGetLast(self) -> INullable[TItem]:
        return self._GetInnerContainer().TryGetLast()

class ListBase[T](Enumerable[T], IList[T]):
    @final
    class __Enumerable(Enumerable[IDoublyLinkedNode[T]]):
        def __init__(self, l: IList[T]):
            super().__init__()

            self.__list: IList[T] = l
        
        def TryGetEnumerator(self) -> IEnumerator[IDoublyLinkedNode[T]]|None:
            return self.__list.TryGetNodeEnumerator()
    
    class _ReadOnlyList(_ReadOnlyListBase[T, IReadOnlyList[T]], IGenericConstraintImplementation[IReadOnlyList[T]]):
        def __init__(self, items: IReadOnlyList[T]):
            super().__init__(items)
    class _ReadOnlyEnumerableList(_ReadOnlyListBase[T, IReadOnlyEnumerableList[T]], IReadOnlyEnumerableList[T], IGenericConstraintImplementation[IReadOnlyEnumerableList[T]]):
        def __init__(self, items: IReadOnlyEnumerableList[T]):
            super().__init__(items)
        
        @final
        def TryGetEnumerator(self) -> IEnumerator[T]|None:
            return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
    
    @final
    class __EnumerableUpdater(ValueFunctionUpdater[Enumeration.IEnumerable[IDoublyLinkedNode[T]]]):
        def __init__(self, items: ListBase[T], updater: Method[IFunction[Enumeration.IEnumerable[IDoublyLinkedNode[T]]]]):
            super().__init__(updater)

            self.__items: ListBase[T] = items
        
        def _GetValue(self) -> Enumeration.IEnumerable[IDoublyLinkedNode[T]]:
            return ListBase[T].__Enumerable(self.__items)
    
    @final
    class __ReadOnlyUpdater(ValueFunctionUpdater[IReadOnlyList[T]]):
        def __init__(self, items: ListBase[T], updater: Method[IFunction[IReadOnlyList[T]]]):
            super().__init__(updater)

            self.__items: ListBase[T] = items
        
        def _GetValue(self) -> IReadOnlyList[T]:
            return self.__items._AsReadOnly()
    @final
    class __ReadOnlyEnumerableUpdater(ValueFunctionUpdater[IReadOnlyEnumerableList[T]]):
        def __init__(self, items: ListBase[T], updater: Method[IFunction[IReadOnlyEnumerableList[T]]]):
            super().__init__(updater)

            self.__items: ListBase[T] = items
        
        def _GetValue(self) -> IReadOnlyEnumerableList[T]:
            return self.__items._AsReadOnlyEnumerable()
    
    def __init__(self):
        def updateNodeEnumerable(func: IFunction[Enumeration.IEnumerable[IDoublyLinkedNode[T]]]) -> None:
            self.__nodeEnumerable = func
        def updateReadOnly(func: IFunction[IReadOnlyList[T]]) -> None:
            self.__readOnly = func
        def updateReadOnlyEnumerable(func: IFunction[IReadOnlyEnumerableList[T]]) -> None:
            self.__readOnlyEnumerable = func
        
        super().__init__()
        
        self.__first: DoublyLinkedNode[T]|None = None
        self.__last: DoublyLinkedNode[T]|None = None

        self.__nodeEnumerable: IFunction[Enumeration.IEnumerable[IDoublyLinkedNode[T]]] = ListBase[T].__EnumerableUpdater(self, updateNodeEnumerable)
        self.__readOnly: IFunction[IReadOnlyList[T]] = ListBase[T].__ReadOnlyUpdater(self, updateReadOnly)
        self.__readOnlyEnumerable: IFunction[IReadOnlyEnumerableList[T]] = ListBase[T].__ReadOnlyEnumerableUpdater(self, updateReadOnlyEnumerable)
    
    def _AsReadOnly(self) -> IReadOnlyList[T]:
        return ListBase[T]._ReadOnlyList(self)
    @final
    def AsReadOnly(self) -> IReadOnlyList[T]:
        return self.__readOnly.GetValue()
    
    def _AsReadOnlyEnumerable(self) -> IReadOnlyEnumerableList[T]:
        return ListBase[T]._ReadOnlyEnumerableList(self)
    @final
    def AsReadOnlyEnumerable(self) -> IReadOnlyEnumerableList[T]:
        return self.__readOnlyEnumerable.GetValue()

    @final
    def IsEmpty(self) -> bool:
        return self.__first is None
    @final
    def HasItems(self) -> bool:
        return super().HasItems()
    
    @abstractmethod
    def _GetNode(self, value: T, previous: DoublyLinkedNode[T]|None, next: DoublyLinkedNode[T]|None) -> DoublyLinkedNode[T]:
        pass
    
    @final
    def AddFirst(self, value: T) -> DoublyLinkedNode[T]:
        first: DoublyLinkedNode[T]|None = self.__first

        self.__first = self._GetNode(value, None, first)

        if first is not None:
            first._SetPrevious(self.__first) # type: ignore
        
        if self.__last is None:
            self.__last = self.__first

        return self.__first
    @final
    def AddLast(self, value: T) -> DoublyLinkedNode[T]:
        last: DoublyLinkedNode[T]|None = self.__last
        
        self.__last = self._GetNode(value, last, None)
        
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
        newNode: DoublyLinkedNode[T] = self._GetNode(value, previousNode, node)

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
        newNode: DoublyLinkedNode[T] = self._GetNode(value, node, nextNode)

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

        node._OnRemoved() # type: ignore
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
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return None if self.IsEmpty() or self.__first is None else GetValueEnumeratorFromNode(self.__first) # self.__first should not be None if self.IsEmpty().
    
    @final
    def TryGetNodeEnumerator(self) -> IEnumerator[IDoublyLinkedNode[T]]|None:
        return None if self.IsEmpty() or self.__first is None else DoublyLinkedNodeEnumerator[T](self.__first) # self.__first should not be None if self.IsEmpty().
    @final
    def GetNodeEnumerator(self) -> IEnumerator[IDoublyLinkedNode[T]]:
        enumerator: IEnumerator[IDoublyLinkedNode[T]]|None = self.TryGetNodeEnumerator()

        return GetEnumerator(enumerator)
    
    @final
    def AsNodeEnumerable(self) -> Enumeration.IEnumerable[IDoublyLinkedNode[T]]:
        return self.__nodeEnumerable.GetValue()
class List[T](ListBase[T]):
    def __init__(self):
        super().__init__()
    
    @final
    def _GetNode(self, value: T, previous: DoublyLinkedNode[T]|None, next: DoublyLinkedNode[T]|None) -> DoublyLinkedNode[T]:
        return DoublyLinkedNode[T](value, self, previous, next)

class ICountableList[T](IList[T], ICountable):
    def __init__(self):
        super().__init__()
class CountableList[T](CountableEnumerable[T], ICountableList[T]):
    @final
    class __List(ListBase[T]):
        def __init__(self, l: CountableList[T]):
            super().__init__()

            self.__items: CountableList[T] = l
        
        def _GetNode(self, value: T, previous: DoublyLinkedNode[T]|None, next: DoublyLinkedNode[T]|None) -> DoublyLinkedNode[T]:
            return DoublyLinkedNode[T](value, self.__items, previous, next)
    
    def __init__(self):
        super().__init__()

        self.__items: IList[T] = CountableList[T].__List(self)
        self.__count: int = 0
    
    @final
    def __OnAdded(self, node: IDoublyLinkedNode[T]) -> IDoublyLinkedNode[T]:
        self.__count += 1

        return node
    
    @final
    def __OnRemovedItem(self) -> None:
        self.__count -= 1
    @final
    def __OnRemoved(self, value: INullable[T]) -> INullable[T]:
        self.__OnRemovedItem()

        return value
    
    @final
    def _GetItems(self) -> IList[T]:
        return self.__items
    
    @final
    def AsReadOnly(self) -> IReadOnlyList[T]:
        return self._GetItems().AsReadOnly()
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetItems().IsEmpty()
    
    @final
    def GetCount(self) -> int:
        return self.__count
    
    @final
    def GetFirst(self) -> IDoublyLinkedNode[T]|None:
        return self._GetItems().GetFirst()
    @final
    def GetLast(self) -> IDoublyLinkedNode[T]|None:
        return self._GetItems().GetLast()
    
    @final
    def AddFirst(self, value: T) -> IDoublyLinkedNode[T]:
        return self.__OnAdded(self._GetItems().AddFirst(value))
    @final
    def AddLast(self, value: T) -> IDoublyLinkedNode[T]:
        return self.__OnAdded(self._GetItems().AddLast(value))
    
    @final
    def AddBefore(self, node: IDoublyLinkedNode[T], value: T) -> IDoublyLinkedNode[T]:
        return self.__OnAdded(self._GetItems().AddBefore(node, value))
    @final
    def AddAfter(self, node: IDoublyLinkedNode[T], value: T) -> IDoublyLinkedNode[T]:
        return self.__OnAdded(self._GetItems().AddAfter(node, value))
    
    @final
    def Remove(self, node: IDoublyLinkedNode[T]) -> None:
        self._GetItems().Remove(node)

        self.__OnRemovedItem()
    
    @final
    def RemoveFirst(self) -> INullable[T]:
        return self.__OnRemoved(self._GetItems().RemoveFirst())
    @final
    def RemoveLast(self) -> INullable[T]:
        return self.__OnRemoved(self._GetItems().RemoveLast())
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self._GetItems().TryGetEnumerator()
    @final
    def TryGetNodeEnumerator(self) -> IEnumerator[IDoublyLinkedNode[T]]|None:
        return self._GetItems().TryGetNodeEnumerator()
    
    @final
    def AsReadOnlyEnumerable(self) -> IReadOnlyEnumerableList[T]:
        return self._GetItems().AsReadOnlyEnumerable()
    
    @final
    def AsNodeEnumerable(self) -> Enumeration.IEnumerable[IDoublyLinkedNode[T]]:
        return self._GetItems().AsNodeEnumerable()
    
    @final
    def Clear(self) -> None:
        self._GetItems().Clear()

class DoublyLinkedNodeEnumeratorBase[TItems, TNode](NodeEnumeratorBase[TItems, TNode], IGenericConstraint[TNode, IDoublyLinkedNode[TItems]]):
    def __init__(self, node: TNode):
        super().__init__(node)
class DoublyLinkedNodeEnumerator[T](DoublyLinkedNodeEnumeratorBase[T, IDoublyLinkedNode[T]], IGenericConstraintImplementation[IDoublyLinkedNode[T]]):
    def __init__(self, node: IDoublyLinkedNode[T]):
        super().__init__(node)

    def _GetNextNode(self, node: IDoublyLinkedNode[T]) -> IDoublyLinkedNode[T]|None:
        return node.GetNext()