from __future__ import annotations

from collections.abc import Iterable, Iterator

from abc import abstractmethod
from typing import final, Callable, Self

from WinCopies import Abstract
from WinCopies.Collections import Generator, EnumerationOrder, ICountable, IReadOnlyCollection, Countable as CountableCollectionBase
from WinCopies.Collections.Abstraction.Enumeration import Enumerator
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, ICountableEnumerable, Enumerable as EnumerableCollectionBase, CountableEnumerable as CountableEnumerableCollectionBase, IterableBase
from WinCopies.Collections.Linked.Enumeration import NodeEnumeratorBase, GetValueEnumeratorFromNode
from WinCopies.Collections.Linked.Node import LinkedNode

from WinCopies.Typing import GenericConstraint, IGenericConstraintImplementation, INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater, SelectionUpdater
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

class SinglyLinkedNode[T](LinkedNode['SinglyLinkedNode', T]):
    def __init__(self, value: T, nextNode: Self|None):
        super().__init__(value, nextNode)

class IReadOnlyList[T](IReadOnlyCollection):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetOrder(self) -> EnumerationOrder:
        pass
    
    @abstractmethod
    def TryPeek(self) -> INullable[T]:
        pass
class IList[T](IReadOnlyList[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyList[T]:
        pass
    
    @abstractmethod
    def Push(self, value: T) -> None:
        pass
    
    @abstractmethod
    def TryPushItems(self, items: Iterable[T]|None) -> bool:
        pass
    @abstractmethod
    def PushItems(self, items: Iterable[T]) -> None:
        pass
    
    @final
    def PushValues(self, *values: T) -> None:
        self.PushItems(values)
    
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

class IReadOnlyEnumerableList[T](IReadOnlyList[T], IEnumerable[T]):
    def __init__(self):
        super().__init__()
class IEnumerableList[T](IList[T], IReadOnlyEnumerableList[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyEnumerableList[T]:
        pass

@final
class _EnumerableUpdater[T](ValueFunctionUpdater[ICountableEnumerable[T]]):
    @final
    class __Enumerable(IterableBase[T], CountableCollectionBase, ICountableEnumerable[T]):
        def __init__(self, items: ICountableList[T]):
            super().__init__()

            self.__items: ICountableList[T] = items
        
        def _TryGetIterator(self) -> Iterator[T]|None:
            return self.__items.AsGenerator()
        
        def GetCount(self) -> int:
            return self.__items.GetCount()
    
    def __init__(self, items: ICountableList[T], updater: Method[IFunction[ICountableEnumerable[T]]]):
        super().__init__(updater)

        self.__items: ICountableList[T] = items
    
    def _GetValue(self) -> ICountableEnumerable[T]:
        return _EnumerableUpdater[T].__Enumerable(self.__items)

class IReadOnlyCountableList[T](IReadOnlyList[T], ICountable):
    def __init__(self):
        super().__init__()
class ICountableList[T](IList[T], IReadOnlyCountableList[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableList[T]:
        pass

class IReadOnlyCountableEnumerableList[T](IReadOnlyEnumerableList[T], IReadOnlyCountableList[T], ICountableEnumerable[T]):
    def __init__(self):
        super().__init__()
class ICountableEnumerableList[T](IEnumerableList[T], ICountableList[T], IReadOnlyCountableEnumerableList[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[T]:
        pass

class IReadOnlyQueue[T](IReadOnlyList[T]):
    def __init__(self):
        super().__init__()
    
    @final
    def GetOrder(self) -> EnumerationOrder:
        return EnumerationOrder.FIFO
class IReadOnlyStack[T](IReadOnlyList[T]):
    def __init__(self):
        super().__init__()
    
    @final
    def GetOrder(self) -> EnumerationOrder:
        return EnumerationOrder.LIFO

class IReadOnlyCountableQueue[T](IReadOnlyQueue[T], IReadOnlyCountableList[T]):
    def __init__(self):
        super().__init__()
class IReadOnlyCountableStack[T](IReadOnlyStack[T], IReadOnlyCountableList[T]):
    def __init__(self):
        super().__init__()

class IReadOnlyEnumerableQueue[T](IReadOnlyQueue[T], IReadOnlyEnumerableList[T]):
    def __init__(self):
        super().__init__()
class IReadOnlyEnumerableStack[T](IReadOnlyStack[T], IReadOnlyEnumerableList[T]):
    def __init__(self):
        super().__init__()

class IReadOnlyCountableEnumerableQueue[T](IReadOnlyCountableEnumerableList[T], IReadOnlyEnumerableQueue[T], IReadOnlyCountableQueue[T]):
    def __init__(self):
        super().__init__()
class IReadOnlyCountableEnumerableStack[T](IReadOnlyCountableEnumerableList[T], IReadOnlyEnumerableStack[T], IReadOnlyCountableStack[T]):
    def __init__(self):
        super().__init__()

class IQueue[T](IList[T], IReadOnlyQueue[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyQueue[T]:
        pass
class IStack[T](IList[T], IReadOnlyStack[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyStack[T]:
        pass

class ICountableQueue[T](ICountableList[T], IQueue[T], IReadOnlyCountableQueue[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableQueue[T]:
        pass
class ICountableStack[T](ICountableList[T], IStack[T], IReadOnlyCountableStack[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableStack[T]:
        pass

class IEnumerableQueue[T](IEnumerableList[T], IQueue[T], IReadOnlyEnumerableQueue[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyEnumerableQueue[T]:
        pass
class IEnumerableStack[T](IEnumerableList[T], IStack[T], IReadOnlyEnumerableStack[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyEnumerableStack[T]:
        pass

class ICountableEnumerableQueue[T](ICountableEnumerableList[T], ICountableQueue[T], IEnumerableQueue[T], IReadOnlyCountableEnumerableQueue[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableQueue[T]:
        pass
class ICountableEnumerableStack[T](ICountableEnumerableList[T], ICountableStack[T], IEnumerableStack[T], IReadOnlyCountableEnumerableStack[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableStack[T]:
        pass

class ReadOnlyList[TItem, TList](Abstract, IReadOnlyList[TItem], GenericConstraint[TList, IList[TItem]]):
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
    def TryPeek(self) -> INullable[TItem]:
        return self._GetInnerContainer().TryPeek()

class ListBase[T](Abstract, IList[T]):
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
    def _OnCleared(self) -> None:
        pass
    def _OnRemoved(self) -> None:
        pass

    @final
    def __OnRemoved(self) -> None:
        if self.IsEmpty():
            self._OnCleared()
        
        else:
            self._OnRemoved()
    
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
    def PushItems(self, items: Iterable[T]) -> None:
        for value in items:
            self.Push(value)
    @final
    def TryPushItems(self, items: Iterable[T]|None) -> bool:
        if items is None:
            return False
        
        self.PushItems(items)

        return True
    
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

            self.__OnRemoved()

        return result
    
    @final
    def Clear(self) -> None:
        result: INullable[T] = self.TryPop()

        while result.HasValue(): # Needed in case of a running enumeration.
            result = self.TryPop()

        self.__first = None

        self.__OnRemoved()

class List[T](ListBase[T]):
    class ReadOnlyList(ReadOnlyList[T, IList[T]], IGenericConstraintImplementation[IList[T]]):
        def __init__(self, items: IList[T]):
            super().__init__(items)
    
    def __init__(self):
        super().__init__()

class Enumerable[T](ListBase[T], EnumerableCollectionBase[T], IEnumerableList[T]):
    class ReadOnlyList(ReadOnlyList[T, IEnumerableList[T]], EnumerableCollectionBase[T], IReadOnlyEnumerableList[T], IGenericConstraintImplementation[IEnumerableList[T]]):
        def __init__(self, items: IEnumerableList[T]):
            super().__init__(items)
        
        @final
        def TryGetEnumerator(self) -> IEnumerator[T]|None:
            return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
    
    def __init__(self):
        super().__init__()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        if self.IsEmpty():
            return None
        
        first: SinglyLinkedNode[T]|None = self._GetFirst() # Should never be None here.
        
        return None if first is None else GetValueEnumeratorFromNode(first)

class QueueBase[T](ListBase[T], IQueue[T]):
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
    
    def _OnCleared(self) -> None:
        self.__last = None
        self.__updater = self.__GetUpdater()
class StackBase[T](ListBase[T], IStack[T]):
    def __init__(self, *values: T):
        super().__init__()

        self.PushItems(values)
    
    @final
    def _Push(self, value: T, first: SinglyLinkedNode[T]) -> None:
        self._SetFirst(SinglyLinkedNode[T](value, first))
    
    def _OnCleared(self) -> None:
        pass

class Queue[T](QueueBase[T], List[T]):
    class _ReadOnlyList(List[T].ReadOnlyList, IReadOnlyQueue[T]):
        def __init__(self, items: IQueue[T]):
            super().__init__(items)
    
    @final
    class __Updater(SelectionUpdater[IQueue[T], IReadOnlyQueue[T]]):
        def __init__(self, value: IQueue[T], updater: Method[IFunction[IReadOnlyQueue[T]]]):
            super().__init__(value, updater)
        
        def _AsContainer(self, container: IQueue[T]) -> IReadOnlyQueue[T]:
            return Queue[T]._ReadOnlyList(container)
    
    def __init__(self, *values: T):
        def update(func: IFunction[IReadOnlyQueue[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(*values)

        self.__readOnly: IFunction[IReadOnlyQueue[T]] = Queue[T].__Updater(self, update)
    
    @final
    def AsReadOnly(self) -> IReadOnlyQueue[T]:
        return self.__readOnly.GetValue()
class Stack[T](StackBase[T], List[T]):
    class _ReadOnlyList(List[T].ReadOnlyList, IReadOnlyStack[T]):
        def __init__(self, items: IStack[T]):
            super().__init__(items)
    
    @final
    class __Updater(SelectionUpdater[IStack[T], IReadOnlyStack[T]]):
        def __init__(self, value: IStack[T], updater: Method[IFunction[IReadOnlyStack[T]]]):
            super().__init__(value, updater)
        
        def _AsContainer(self, container: IStack[T]) -> IReadOnlyStack[T]:
            return Stack[T]._ReadOnlyList(container)
    
    def __init__(self, *values: T):
        def update(func: IFunction[IReadOnlyStack[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(*values)

        self.__readOnly: IFunction[IReadOnlyStack[T]] = Stack[T].__Updater(self, update)
    
    @final
    def AsReadOnly(self) -> IReadOnlyStack[T]:
        return self.__readOnly.GetValue()

class SinglyLinkedNodeEnumeratorBase[TItems, TNode](NodeEnumeratorBase[TItems, TNode]):
    def __init__(self, node: TNode):
        super().__init__(node)
class SinglyLinkedNodeEnumerator[T](SinglyLinkedNodeEnumeratorBase[T, SinglyLinkedNode[T]]):
    def __init__(self, node: SinglyLinkedNode[T]):
        super().__init__(node)

class EnumerableQueueBase[T](QueueBase[T], IEnumerableQueue[T]):
    class ReadOnlyList(Enumerable[T].ReadOnlyList, IReadOnlyEnumerableQueue[T]):
        def __init__(self, items: IEnumerableQueue[T]):
            super().__init__(items)
    
    def __init__(self, *values: T):
        super().__init__(*values)
class EnumerableStackBase[T](StackBase[T], IEnumerableStack[T]):
    class ReadOnlyList(Enumerable[T].ReadOnlyList, IReadOnlyEnumerableStack[T]):
        def __init__(self, items: IEnumerableStack[T]):
            super().__init__(items)
    
    def __init__(self, *values: T):
        super().__init__(*values)

class EnumerableQueue[T](EnumerableQueueBase[T], Enumerable[T]):
    @final
    class __Updater(SelectionUpdater[IEnumerableQueue[T], IReadOnlyEnumerableQueue[T]]):
        def __init__(self, value: IEnumerableQueue[T], updater: Method[IFunction[IReadOnlyEnumerableQueue[T]]]):
            super().__init__(value, updater)
        
        def _AsContainer(self, container: IEnumerableQueue[T]) -> IReadOnlyEnumerableQueue[T]:
            return EnumerableQueueBase[T].ReadOnlyList(container)
    
    def __init__(self):
        def update(func: IFunction[IReadOnlyEnumerableQueue[T]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyEnumerableQueue[T]] = EnumerableQueue[T].__Updater(self, update)
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableQueue[T]:
        return self.__readOnly.GetValue()
class EnumerableStack[T](EnumerableStackBase[T], Enumerable[T]):
    @final
    class __Updater(SelectionUpdater[IEnumerableStack[T], IReadOnlyEnumerableStack[T]]):
        def __init__(self, value: IEnumerableStack[T], updater: Method[IFunction[IReadOnlyEnumerableStack[T]]]):
            super().__init__(value, updater)
        
        def _AsContainer(self, container: IEnumerableStack[T]) -> IReadOnlyEnumerableStack[T]:
            return EnumerableStackBase[T].ReadOnlyList(container)
    
    def __init__(self):
        def update(func: IFunction[IReadOnlyEnumerableStack[T]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyEnumerableStack[T]] = EnumerableStack[T].__Updater(self, update)
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableStack[T]:
        return self.__readOnly.GetValue()

class CollectionBase[TItems, TList](Abstract, GenericConstraint[TList, IList[TItems]], IList[TItems]):
    def __init__(self, l: TList):
        super().__init__()
        
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
    
    @final
    def GetOrder(self) -> EnumerationOrder:
        return self._GetInnerContainer().GetOrder()

class Collection[T](CollectionBase[T, IList[T]], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, l: IList[T]):
        super().__init__(l)

class _CountableCollectionBase[TItems, TList](CollectionBase[TItems, TList], CountableCollectionBase, ICountableList[TItems]):
    def __init__(self, l: TList):
        def update(func: IFunction[ICountableEnumerable[TItems]]) -> None:
            self.__generator = func
        
        EnsureDirectModuleCall()

        super().__init__(l)

        self.__count: int = 0
        self.__generator: IFunction[ICountableEnumerable[TItems]] = _EnumerableUpdater[TItems](self, update)

    @final
    def AsCountableGenerator(self) -> ICountableEnumerable[TItems]:
        return self.__generator.GetValue()
    
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
    def __PushItems(self, items: Iterable[TItems]) -> None:
        def loop() -> Generator[TItems]:
            for item in items:
                yield item
                
                self.__Increment()
        
        self._GetInnerContainer().PushItems(loop())
    
    @final
    def TryPushItems(self, items: Iterable[TItems]|None) -> bool:
        if items is None:
            return False
        
        self.__PushItems(items)

        return True
    @final
    def PushItems(self, items: Iterable[TItems]) -> None:
        if items is None: # type: ignore
            raise ValueError("No value provided.")
        
        self.__PushItems(items)
    
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

class _CountableCollection[TItem, TList](_CountableCollectionBase[TItem, TList]):
    class ReadOnlyList(ReadOnlyList[TItem, ICountableList[TItem]], CountableCollectionBase, IReadOnlyCountableList[TItem], IGenericConstraintImplementation[ICountableList[TItem]]):
        def __init__(self, items: ICountableList[TItem]):
            super().__init__(items)
        
        @final
        def GetCount(self) -> int:
            return self._GetContainer().GetCount()
    
    def __init__(self, l: TList):
        super().__init__(l)
class CountableCollection[TItem, TList](_CountableCollection[TItem, TList]):
    def __init__(self, l: TList):
        super().__init__(l)

class CountableBase[T](CountableCollection[T, IList[T]], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, l: IList[T]):
        super().__init__(l)
class Countable[T](CountableBase[T]):
    def __init__(self, *values: T):
        super().__init__(self._CreateList(*values))
    
    @abstractmethod
    def _CreateList(self, *values: T) -> IList[T]:
        pass

class CountableQueue[T](Countable[T], ICountableQueue[T]):
    class _ReadOnlyList(CountableBase[T].ReadOnlyList, IReadOnlyCountableQueue[T]):
        def __init__(self, items: ICountableQueue[T]):
            super().__init__(items)
    
    @final
    class __Updater(SelectionUpdater[ICountableQueue[T], IReadOnlyCountableQueue[T]]):
        def __init__(self, items: ICountableQueue[T], updater: Method[IFunction[IReadOnlyCountableQueue[T]]]):
            super().__init__(items, updater)

        def _AsContainer(self, container: ICountableQueue[T]) -> IReadOnlyCountableQueue[T]:
            return CountableQueue[T]._ReadOnlyList(container)
    
    def __init__(self, *values: T):
        def update(func: IFunction[IReadOnlyCountableQueue[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(*values)

        self.__readOnly: IFunction[IReadOnlyCountableQueue[T]] = CountableQueue[T].__Updater(self, update)
    
    def _CreateList(self, *values: T) -> IQueue[T]:
        return Queue[T](*values)
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableQueue[T]:
        return self.__readOnly.GetValue()
class CountableStack[T](Countable[T], ICountableStack[T]):
    class _ReadOnlyList(CountableBase[T].ReadOnlyList, IReadOnlyCountableStack[T]):
        def __init__(self, items: ICountableStack[T]):
            super().__init__(items)
    
    @final
    class __Updater(SelectionUpdater[ICountableStack[T], IReadOnlyCountableStack[T]]):
        def __init__(self, items: ICountableStack[T], updater: Method[IFunction[IReadOnlyCountableStack[T]]]):
            super().__init__(items, updater)

        def _AsContainer(self, container: ICountableStack[T]) -> IReadOnlyCountableStack[T]:
            return CountableStack[T]._ReadOnlyList(container)
    
    def __init__(self, *values: T):
        def update(func: IFunction[IReadOnlyCountableStack[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(*values)

        self.__readOnly: IFunction[IReadOnlyCountableStack[T]] = CountableStack[T].__Updater(self, update)
    
    def _CreateList(self, *values: T) -> IStack[T]:
        return Stack[T](*values)
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableStack[T]:
        return self.__readOnly.GetValue()

class CountableEnumerableBase[TItems, TList](_CountableCollectionBase[TItems, TList], EnumerableCollectionBase[TItems], ICountableEnumerableList[TItems], GenericConstraint[TList, Enumerable[TItems]]):
    def __init__(self, l: TList):
        super().__init__(l)
class CountableEnumerable[T](CountableEnumerableBase[T, Enumerable[T]], IGenericConstraintImplementation[Enumerable[T]]):
    class ReadOnlyList(ReadOnlyList[T, ICountableEnumerableList[T]], CountableEnumerableCollectionBase[T], IReadOnlyCountableEnumerableList[T], IGenericConstraintImplementation[ICountableEnumerableList[T]]):
        def __init__(self, items: ICountableEnumerableList[T]):
            super().__init__(items)
        
        @final
        def GetCount(self) -> int:
            return self._GetContainer().GetCount()
        
        @final
        def TryGetEnumerator(self) -> IEnumerator[T]|None:
            return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
    
    def __init__(self, l: Enumerable[T]):
        super().__init__(l)

class CountableEnumerableQueue[T](CountableEnumerable[T], ICountableEnumerableQueue[T]):
    class _ReadOnlyList(CountableEnumerable[T].ReadOnlyList, IReadOnlyCountableEnumerableQueue[T]):
        def __init__(self, l: ICountableEnumerableQueue[T]):
            super().__init__(l)
    
    @final
    class __Updater(SelectionUpdater[ICountableEnumerableQueue[T], IReadOnlyCountableEnumerableQueue[T]]):
        def __init__(self, items: ICountableEnumerableQueue[T], updater: Method[IFunction[IReadOnlyCountableEnumerableQueue[T]]]):
            super().__init__(items, updater)
        
        def _AsContainer(self, container: ICountableEnumerableQueue[T]) -> IReadOnlyCountableEnumerableQueue[T]:
            return CountableEnumerableQueue[T]._ReadOnlyList(container)
    
    def __init__(self, *values: T):
        def update(func: IFunction[IReadOnlyCountableEnumerableQueue[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(EnumerableQueue[T](*values))

        self.__readOnly: IFunction[IReadOnlyCountableEnumerableQueue[T]] = CountableEnumerableQueue[T].__Updater(self, update)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self._GetCollection().TryGetEnumerator()
    
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableQueue[T]:
        return self.__readOnly.GetValue()
class CountableEnumerableStack[T](CountableEnumerable[T], ICountableEnumerableStack[T]):
    class _ReadOnlyList(CountableEnumerable[T].ReadOnlyList, IReadOnlyCountableEnumerableStack[T]):
        def __init__(self, l: ICountableEnumerableStack[T]):
            super().__init__(l)
    
    @final
    class __Updater(SelectionUpdater[ICountableEnumerableStack[T], IReadOnlyCountableEnumerableStack[T]]):
        def __init__(self, items: ICountableEnumerableStack[T], updater: Method[IFunction[IReadOnlyCountableEnumerableStack[T]]]):
            super().__init__(items, updater)
        
        def _AsContainer(self, container: ICountableEnumerableStack[T]) -> IReadOnlyCountableEnumerableStack[T]:
            return CountableEnumerableStack[T]._ReadOnlyList(container)
    
    def __init__(self, *values: T):
        def update(func: IFunction[IReadOnlyCountableEnumerableStack[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(EnumerableStack[T](*values))

        self.__readOnly: IFunction[IReadOnlyCountableEnumerableStack[T]] = CountableEnumerableStack[T].__Updater(self, update)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self._GetCollection().TryGetEnumerator()
    
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableStack[T]:
        return self.__readOnly.GetValue()