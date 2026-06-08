from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator, Sized
from typing import final, Callable, Self

from WinCopies import IInterface, Abstract

from WinCopies.Collections import Generator, EnumerationOrder
from WinCopies.Collections.Abstraction.Enumeration import TryCreateEnumerator
from WinCopies.Collections.Core import ICountable, IReadOnlyCollection, Countable as CountableCollectionBase
from WinCopies.Collections.Enumeration import IEnumerable, ICountableEnumerable, IEnumerator, IterableBase, Enumerable as EnumerableCollectionBase, CountableEnumerable as CountableEnumerableCollectionBase
from WinCopies.Collections.Linked.Enumeration import NodeEnumeratorBase, TryGetValueEnumeratorFromNode
from WinCopies.Collections.Linked.Node import LinkedNodeBase

from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater, SelectionUpdater
from WinCopies.Typing.Generic import GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation

class IReadOnlyListBase[T](IReadOnlyCollection):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryPeek(self) -> INullable[T]:
        ...
class IReadOnlyList[T](IReadOnlyListBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetOrder(self) -> EnumerationOrder:
        ...

class IListBase[T](IReadOnlyListBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Push(self, value: T) -> None:
        ...
    
    def PushItems(self, items: Iterable[T]) -> None:
        for value in items: self.Push(value)
    @final
    def TryPushItems(self, items: Iterable[T]|None) -> bool:
        if items is None: return False
        
        self.PushItems(items)

        return True
    
    @final
    def PushValues(self, *values: T) -> None:
        self.PushItems(values)
    
    @abstractmethod
    def TryPop(self) -> INullable[T]:
        ...
    
    @abstractmethod
    def Clear(self) -> None:
        ...
    
    @final
    def AsGenerator(self) -> Generator[T]:
        result: INullable[T] = self.TryPop()

        while result.HasValue():
            yield result.GetValue()
            
            result = self.TryPop()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyList[T]:
        ...
class IList[T](IListBase[T], IReadOnlyList[T]):
    def __init__(self) -> None: super().__init__()

class IReadOnlyEnumerableListBase[T](IReadOnlyListBase[T], IEnumerable[T]):
    def __init__(self) -> None: super().__init__()
class IReadOnlyEnumerableList[T](IReadOnlyEnumerableListBase[T], IReadOnlyList[T]):
    def __init__(self) -> None: super().__init__()

class IEnumerableListBase[T](IListBase[T], IReadOnlyEnumerableListBase[T]):
    def __init__(self) -> None: super().__init__()
class IEnumerableList[T](IEnumerableListBase[T], IList[T], IReadOnlyEnumerableList[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyEnumerableList[T]:
        ...

class IReadOnlyCountableListBase[T](IReadOnlyListBase[T], ICountable):
    def __init__(self) -> None: super().__init__()
class IReadOnlyCountableList[T](IReadOnlyCountableListBase[T], IReadOnlyList[T]):
    def __init__(self) -> None: super().__init__()

class ICountableListBase[T](IListBase[T], IReadOnlyCountableListBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsCountableGenerator(self) -> ICountableEnumerable[T]:
        ...
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableList[T]:
        ...
class ICountableList[T](ICountableListBase[T], IList[T], IReadOnlyCountableList[T]):
    def __init__(self) -> None: super().__init__()

class IReadOnlyCountableEnumerableListBase[T](IReadOnlyEnumerableListBase[T], IReadOnlyCountableListBase[T], ICountableEnumerable[T]):
    def __init__(self) -> None: super().__init__()
class IReadOnlyCountableEnumerableList[T](IReadOnlyCountableEnumerableListBase[T], IReadOnlyEnumerableList[T], IReadOnlyCountableList[T]):
    def __init__(self) -> None: super().__init__()

class ICountableEnumerableListBase[T](IEnumerableListBase[T], ICountableListBase[T], IReadOnlyCountableEnumerableListBase[T]):
    def __init__(self) -> None: super().__init__()
class ICountableEnumerableList[T](ICountableEnumerableListBase[T], IEnumerableList[T], ICountableList[T], IReadOnlyCountableEnumerableList[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[T]:
        ...

class CollectionAbstract[TItems, TList](Abstract, IListBase[TItems], GenericConstraint[TList, IList[TItems]]):
    def __init__(self, l: TList) -> None:
        super().__init__()
        
        self.__list: TList = l
    
    def _GetContainer(self) -> TList: return self.__list

    @final
    def IsEmpty(self) -> bool: return self._GetInnerContainer().IsEmpty()
    @final
    def HasItems(self) -> bool: return self._GetInnerContainer().HasItems()
class CollectionBase[TItems, TList](CollectionAbstract[TItems, TList], IList[TItems]):
    def __init__(self, l: TList) -> None: super().__init__(l)

@final
class _EnumerableUpdaterEnumerable[T](IterableBase[T], CountableCollectionBase, ICountableEnumerable[T]):
    def __init__(self, items: ICountableListBase[T]) -> None:
        super().__init__()

        self.__items: ICountableListBase[T] = items
    
    def _TryGetIterator(self) -> Iterator[T]|None: return self.__items.AsGenerator()
    
    def GetCount(self) -> int: return self.__items.GetCount()
@final
class _EnumerableUpdater[T](ValueFunctionUpdater[ICountableEnumerable[T]]):
    def __init__(self, items: ICountableListBase[T], updater: Method[IFunction[ICountableEnumerable[T]]]) -> None:
        super().__init__(updater)

        self.__items: ICountableListBase[T] = items
    
    def _GetValue(self) -> ICountableEnumerable[T]: return _EnumerableUpdaterEnumerable[T](self.__items)

class _CountableCollectionAbstractBase[TItems, TList](CollectionAbstract[TItems, TList], CountableCollectionBase, ICountableListBase[TItems], GenericConstraint[TList, IList[TItems]]):
    def __init__(self, l: TList) -> None:
        def update(func: IFunction[ICountableEnumerable[TItems]]) -> None: self.__generator = func
        
        super().__init__(l)

        self.__count: int = 0
        self.__generator: IFunction[ICountableEnumerable[TItems]] = _EnumerableUpdater[TItems](self, update) # type: ignore[no-redef]
    
    @final
    def AsCountableGenerator(self) -> ICountableEnumerable[TItems]: return self.__generator.GetValue()
    
    @final
    def GetCount(self) -> int: return self.__count
    
    @final
    def __Increment(self) -> None:
        self.__count += 1
    
    @final
    def Push(self, value: TItems) -> None:
        self._GetInnerContainer().Push(value)

        self.__Increment()
    @final
    def PushItems(self, items: Iterable[TItems]) -> None:
        def loop() -> Generator[TItems]:
            for item in items:
                yield item
                
                self.__Increment()
        
        self._GetInnerContainer().PushItems(loop())
    
    @final
    def TryPeek(self) -> INullable[TItems]: return self._GetInnerContainer().TryPeek()
    
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

class CountableCollectionAbstract[TItem, TList](_CountableCollectionAbstractBase[TItem, TList]):
    def __init__(self, l: TList) -> None: super().__init__(l)

class INodeCookie[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetNode(self) -> SinglyLinkedNode[T]:
        ...
    
    @abstractmethod
    def GetNext(self) -> INodeCookie[T]|None:
        ...
    @abstractmethod
    def SetNext(self, nextNode: SinglyLinkedNode[T]|None) -> None:
        ...

class SinglyLinkedNode[T](LinkedNodeBase[T, "SinglyLinkedNode[T]"]):
    @final
    class _Cookie[U](Abstract, INodeCookie[U]):
        def __init__(self, node: SinglyLinkedNode[U]) -> None:
            super().__init__()

            self.__node: SinglyLinkedNode[U] = node
        
        def GetNode(self) -> SinglyLinkedNode[U]: return self.__node
        
        def GetNext(self) -> INodeCookie[U]|None:
            node: SinglyLinkedNode[U]|None = self.GetNode().GetNext()

            return None if node is None else SinglyLinkedNode[U]._Cookie(node)
        def SetNext(self, nextNode: SinglyLinkedNode[U]|None) -> None: self.GetNode()._SetNext(nextNode)
    
    def __init__(self, value: T, nextNode: Self|None) -> None:
        super().__init__(value)

        self.__next: SinglyLinkedNode[T]|None = nextNode
    
    @staticmethod
    def CreateCookie(value: T, nextNode: SinglyLinkedNode[T]|None) -> SinglyLinkedNode._Cookie[T]:
        return SinglyLinkedNode._Cookie[T](SinglyLinkedNode[T](value, nextNode))

    @final
    def GetNextNode(self) -> SinglyLinkedNode[T]|None: return self.__next
    
    @final
    def _SetNext(self, nextNode: SinglyLinkedNode[T]|None) -> None:
        self.__next = nextNode
    
    @final
    def GetNext(self) -> SinglyLinkedNode[T]|None: return self._TryAsLinkedNode(self.GetNextNode())
    
    @final
    def _AsLinkedNode(self, node: SinglyLinkedNode[T]) -> SinglyLinkedNode[T]:
        return node
    def _TryAsLinkedNode(self, node: SinglyLinkedNode[T]|None) -> SinglyLinkedNode[T]|None:
        return None if node is None else self._AsLinkedNode(node)

class IReadOnlyQueue[T](IReadOnlyList[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetOrder(self) -> EnumerationOrder: return EnumerationOrder.FIFO
class IReadOnlyStack[T](IReadOnlyList[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetOrder(self) -> EnumerationOrder: return EnumerationOrder.LIFO

class IReadOnlyCountableQueue[T](IReadOnlyQueue[T], IReadOnlyCountableList[T]):
    def __init__(self) -> None: super().__init__()
class IReadOnlyCountableStack[T](IReadOnlyStack[T], IReadOnlyCountableList[T]):
    def __init__(self) -> None: super().__init__()

class IReadOnlyEnumerableQueue[T](IReadOnlyQueue[T], IReadOnlyEnumerableList[T]):
    def __init__(self) -> None: super().__init__()
class IReadOnlyEnumerableStack[T](IReadOnlyStack[T], IReadOnlyEnumerableList[T]):
    def __init__(self) -> None: super().__init__()

class IReadOnlyCountableEnumerableQueue[T](IReadOnlyCountableEnumerableList[T], IReadOnlyEnumerableQueue[T], IReadOnlyCountableQueue[T]):
    def __init__(self) -> None: super().__init__()
class IReadOnlyCountableEnumerableStack[T](IReadOnlyCountableEnumerableList[T], IReadOnlyEnumerableStack[T], IReadOnlyCountableStack[T]):
    def __init__(self) -> None: super().__init__()

class IQueue[T](IList[T], IReadOnlyQueue[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyQueue[T]:
        ...
class IStack[T](IList[T], IReadOnlyStack[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyStack[T]:
        ...

class ICountableQueue[T](ICountableList[T], IQueue[T], IReadOnlyCountableQueue[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableQueue[T]:
        ...
class ICountableStack[T](ICountableList[T], IStack[T], IReadOnlyCountableStack[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableStack[T]:
        ...

class IEnumerableQueue[T](IEnumerableList[T], IQueue[T], IReadOnlyEnumerableQueue[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyEnumerableQueue[T]:
        ...
class IEnumerableStack[T](IEnumerableList[T], IStack[T], IReadOnlyEnumerableStack[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyEnumerableStack[T]:
        ...

class ICountableEnumerableQueue[T](ICountableEnumerableList[T], ICountableQueue[T], IEnumerableQueue[T], IReadOnlyCountableEnumerableQueue[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableQueue[T]:
        ...
class ICountableEnumerableStack[T](ICountableEnumerableList[T], ICountableStack[T], IEnumerableStack[T], IReadOnlyCountableEnumerableStack[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableStack[T]:
        ...

class ReadOnlyListBase[TItem, TList](Abstract, IReadOnlyList[TItem], GenericConstraint[TList, IList[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__items: TList = items
    
    @final
    def _GetContainer(self) -> TList: return self.__items
    
    @final
    def IsEmpty(self) -> bool: return self._GetInnerContainer().IsEmpty()
    @final
    def HasItems(self) -> bool: return super().HasItems()
    
    @final
    def TryPeek(self) -> INullable[TItem]: return self._GetInnerContainer().TryPeek()

class AbstractList[T](Abstract, IReadOnlyList[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetFirstCookie(self) -> INodeCookie[T]|None:
        ...
    
    @final
    def _GetFirst(self) -> SinglyLinkedNode[T]|None:
        cookie: INodeCookie[T]|None = self._GetFirstCookie()

        return None if cookie is None else cookie.GetNode()
    @abstractmethod
    def _SetFirst(self, node: INodeCookie[T]) -> None:
        ...
class AbstractQueue[T](AbstractList[T], IReadOnlyQueue[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetLast(self) -> SinglyLinkedNode[T]|None:
        ...
    @abstractmethod
    def _SetLast(self, node: SinglyLinkedNode[T]) -> None:
        ...

class ListBase[T](AbstractList[T], IList[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def IsEmpty(self) -> bool: return self._GetFirstCookie() is None
    @final
    def HasItems(self) -> bool: return super().HasItems()
    
    @abstractmethod
    def _UnsetFirst(self) -> None:
        ...
    
    @final
    def _UpdateFirst(self, node: INodeCookie[T]|None) -> None:
        if node is None: self._UnsetFirst()
        else: self._SetFirst(node)
    
    @abstractmethod
    def _OnCleared(self) -> None:
        ...
    def _OnRemoved(self) -> None:
        pass

    @final
    def __OnRemoved(self) -> None:
        if self.IsEmpty(): self._OnCleared()
        else: self._OnRemoved()
    
    @abstractmethod
    def _Push(self, value: T, first: INodeCookie[T]) -> None:
        ...
    @final
    def Push(self, value: T) -> None:
        first: INodeCookie[T]|None = self._GetFirstCookie()
        
        if first is None: self._SetFirst(SinglyLinkedNode[T].CreateCookie(value, None))
        
        else: self._Push(value, first)
    
    @final
    def TryPeek(self) -> INullable[T]:
        first: SinglyLinkedNode[T]|None = self._GetFirst()
        
        return GetNullValue() if first is None else GetNullable(first.GetValue())
    
    @final
    def TryPop(self) -> INullable[T]:
        result: INullable[T] = self.TryPeek()
        
        if result.HasValue():
            first: INodeCookie[T]|None = self._GetFirstCookie()
            
            if first is None: return result # Should never be None here.
            
            next: INodeCookie[T]|None = first.GetNext()
            
            self._UpdateFirst(next)
            
            first.SetNext(None) # Needed in case of a running enumeration.
            
            self.__OnRemoved()
        
        return result
    
    @final
    def Clear(self) -> None:
        result: INullable[T] = self.TryPop()

        # TODO: Should be improved.
        while result.HasValue(): result = self.TryPop() # Needed in case of a running enumeration.

        self.__OnRemoved()

class ReadOnlyList[T](ReadOnlyListBase[T, IList[T]], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, items: IList[T]) -> None: super().__init__(items)
class ReadOnlyEnumerableList[T](ReadOnlyListBase[T, IEnumerableList[T]], EnumerableCollectionBase[T], IReadOnlyEnumerableList[T], IGenericConstraintImplementation[IEnumerableList[T]]):
    def __init__(self, items: IEnumerableList[T]) -> None: super().__init__(items)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return TryCreateEnumerator(self._GetContainer().TryGetEnumerator())

class List[T](ListBase[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__first: INodeCookie[T]|None = None
    
    @final
    def _GetFirstCookie(self) -> INodeCookie[T]|None:
        return self.__first
    @final
    def _SetFirst(self, node: INodeCookie[T]) -> None:
        self.__first = node
    
    @final
    def _UnsetFirst(self) -> None:
        self.__first = None

class Enumerable[T](ListBase[T], EnumerableCollectionBase[T], IEnumerableList[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return TryGetValueEnumeratorFromNode(self._GetFirst())

class QueueBase[T](ListBase[T], AbstractQueue[T], IQueue[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def __Push(self, first: INodeCookie[T], newNode: INodeCookie[T]) -> None:
        def push(previousNode: INodeCookie[T], newNode: INodeCookie[T]) -> None:
            previousNode.SetNext(newNode.GetNode())

            self._SetLast(newNode.GetNode())
        
        push(first, newNode)

        self._SetUpdater(lambda first, _newNode: push(newNode, _newNode))

    @abstractmethod
    def _UnsetLast(self) -> None:
        ...
    
    @final
    def _CreateUpdater(self) -> Callable[[INodeCookie[T], INodeCookie[T]], None]:
        return lambda first, newNode: self.__Push(first, newNode)
    
    @abstractmethod
    def _GetUpdater(self) -> Callable[[INodeCookie[T], INodeCookie[T]], None]:
        ...
    @abstractmethod
    def _SetUpdater(self, updater: Callable[[INodeCookie[T], INodeCookie[T]], None]) -> None:
        ...
    
    @final
    def _Push(self, value: T, first: INodeCookie[T]) -> None:
        self._GetUpdater()(first, SinglyLinkedNode[T].CreateCookie(value, None))
    
    def _OnCleared(self) -> None:
        self._UnsetLast()
        self._SetUpdater(self._CreateUpdater())
class StackBase[T](ListBase[T], IStack[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Push(self, value: T, first: INodeCookie[T]) -> None:
        self._SetFirst(SinglyLinkedNode[T].CreateCookie(value, first.GetNode()))
    
    def _OnCleared(self) -> None:
        pass

@final
class _ReadOnlyQueue[T](ReadOnlyList[T], IReadOnlyQueue[T]):
    def __init__(self, items: IQueue[T]) -> None: super().__init__(items)
@final
class ReadOnlyQueueUpdater[T](SelectionUpdater[IQueue[T], IReadOnlyQueue[T]]):
    def __init__(self, value: IQueue[T], updater: Method[IFunction[IReadOnlyQueue[T]]]) -> None: super().__init__(value, updater)
    
    def _AsContainer(self, container: IQueue[T]) -> IReadOnlyQueue[T]: return _ReadOnlyQueue[T](container)

@final
class _ReadOnlyStack[T](ReadOnlyList[T], IReadOnlyStack[T]):
    def __init__(self, items: IStack[T]) -> None: super().__init__(items)
@final
class ReadOnlyStackUpdater[T](SelectionUpdater[IStack[T], IReadOnlyStack[T]]):
    def __init__(self, value: IStack[T], updater: Method[IFunction[IReadOnlyStack[T]]]) -> None: super().__init__(value, updater)
    
    def _AsContainer(self, container: IStack[T]) -> IReadOnlyStack[T]: return _ReadOnlyStack[T](container)

class Queue[T](List[T], QueueBase[T]):
    def __init__(self, items: Iterable[T]|None = None) -> None:
        def update(func: IFunction[IReadOnlyQueue[T]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__last: SinglyLinkedNode[T]|None = None
        self.__readOnly: IFunction[IReadOnlyQueue[T]] = ReadOnlyQueueUpdater[T](self, update) # type: ignore[no-redef]
        self.__updater: Callable[[INodeCookie[T], INodeCookie[T]], None] = self._CreateUpdater()

        self.TryPushItems(items)
    
    @final
    def _GetUpdater(self) -> Callable[[INodeCookie[T], INodeCookie[T]], None]:
        return self.__updater
    @final
    def _SetUpdater(self, updater: Callable[[INodeCookie[T], INodeCookie[T]], None]) -> None:
        self.__updater = updater
    
    @final
    def _GetLast(self) -> SinglyLinkedNode[T]|None:
        return self.__last
    @final
    def _SetLast(self, node: SinglyLinkedNode[T]) -> None:
        self.__last = node
    
    @final
    def _UnsetLast(self) -> None:
        self.__last = None
    
    @final
    def AsReadOnly(self) -> IReadOnlyQueue[T]: return self.__readOnly.GetValue()
class Stack[T](List[T], StackBase[T]):
    def __init__(self, items: Iterable[T]|None = None) -> None:
        def update(func: IFunction[IReadOnlyStack[T]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyStack[T]] = ReadOnlyStackUpdater[T](self, update) # type: ignore[no-redef]

        self.TryPushItems(items)
    
    @final
    def AsReadOnly(self) -> IReadOnlyStack[T]: return self.__readOnly.GetValue()

class SinglyLinkedNodeEnumerator[T](NodeEnumeratorBase[SinglyLinkedNode[T]]):
    def __init__(self, node: SinglyLinkedNode[T]) -> None: super().__init__(node)

class ReadOnlyEnumerableQueue[T](ReadOnlyEnumerableList[T], IReadOnlyEnumerableQueue[T]):
    def __init__(self, items: IEnumerableQueue[T]) -> None: super().__init__(items)
class ReadOnlyEnumerableStack[T](ReadOnlyEnumerableList[T], IReadOnlyEnumerableStack[T]):
    def __init__(self, items: IEnumerableStack[T]) -> None: super().__init__(items)

class EnumerableQueueBase[T](QueueBase[T], IEnumerableQueue[T]):
    def __init__(self, items: Iterable[T]|None) -> None:
        super().__init__()

        self.__first: INodeCookie[T]|None = None
        self.__last: SinglyLinkedNode[T]|None = None

        self.__updater: Callable[[INodeCookie[T], INodeCookie[T]], None] = self._CreateUpdater()

        self.TryPushItems(items)
    
    @final
    def _GetUpdater(self) -> Callable[[INodeCookie[T], INodeCookie[T]], None]:
        return self.__updater
    @final
    def _SetUpdater(self, updater: Callable[[INodeCookie[T], INodeCookie[T]], None]) -> None:
        self.__updater = updater
    
    @final
    def _GetFirstCookie(self) -> INodeCookie[T]|None:
        return self.__first
    @final
    def _SetFirst(self, node: INodeCookie[T]) -> None:
        self.__first = node
    
    @final
    def _UnsetFirst(self) -> None:
        self.__first = None
    
    @final
    def _GetLast(self) -> SinglyLinkedNode[T]|None:
        return self.__last
    @final
    def _SetLast(self, node: SinglyLinkedNode[T]) -> None:
        self.__last = node
    
    @final
    def _UnsetLast(self) -> None:
        self.__last = None
class EnumerableStackBase[T](StackBase[T], IEnumerableStack[T]):
    def __init__(self, items: Iterable[T]|None) -> None:
        super().__init__()

        self.__first: INodeCookie[T]|None = None

        self.TryPushItems(items)
    
    @final
    def _GetFirstCookie(self) -> INodeCookie[T]|None:
        return self.__first
    
    @final
    def _SetFirst(self, node: INodeCookie[T]) -> None:
        self.__first = node
    @final
    def _UnsetFirst(self) -> None:
        self.__first = None

@final
class _EnumerableQueueUpdater[T](SelectionUpdater[IEnumerableQueue[T], IReadOnlyEnumerableQueue[T]]):
    def __init__(self, value: IEnumerableQueue[T], updater: Method[IFunction[IReadOnlyEnumerableQueue[T]]]) -> None: super().__init__(value, updater)
    
    def _AsContainer(self, container: IEnumerableQueue[T]) -> IReadOnlyEnumerableQueue[T]: return ReadOnlyEnumerableQueue[T](container)
@final
class _EnumerableStackUpdater[T](SelectionUpdater[IEnumerableStack[T], IReadOnlyEnumerableStack[T]]):
    def __init__(self, value: IEnumerableStack[T], updater: Method[IFunction[IReadOnlyEnumerableStack[T]]]) -> None: super().__init__(value, updater)
    
    def _AsContainer(self, container: IEnumerableStack[T]) -> IReadOnlyEnumerableStack[T]: return ReadOnlyEnumerableStack[T](container)

class EnumerableQueue[T](EnumerableQueueBase[T], Enumerable[T]):
    def __init__(self, items: Iterable[T]|None = None) -> None:
        def update(func: IFunction[IReadOnlyEnumerableQueue[T]]) -> None: self.__readOnly = func
        
        super().__init__(items)

        self.__readOnly: IFunction[IReadOnlyEnumerableQueue[T]] = _EnumerableQueueUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableQueue[T]: return self.__readOnly.GetValue()
class EnumerableStack[T](EnumerableStackBase[T], Enumerable[T]):
    def __init__(self, items: Iterable[T]|None = None) -> None:
        def update(func: IFunction[IReadOnlyEnumerableStack[T]]) -> None: self.__readOnly = func
        
        super().__init__(items)

        self.__readOnly: IFunction[IReadOnlyEnumerableStack[T]] = _EnumerableStackUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableStack[T]: return self.__readOnly.GetValue()

class Collection[T](CollectionBase[T, IList[T]], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, l: IList[T]) -> None: super().__init__(l)

class _ReadOnlyCountableCollection[T](ReadOnlyListBase[T, ICountableList[T]], CountableCollectionBase, IReadOnlyCountableList[T], IGenericConstraintImplementation[ICountableList[T]]):
    def __init__(self, items: ICountableList[T]) -> None: super().__init__(items)
    
    @final
    def GetCount(self) -> int: return self._GetContainer().GetCount()

class _CountableCollection[TItem, TList](CountableCollectionAbstract[TItem, TList]):
    def __init__(self, l: TList) -> None: super().__init__(l)
class _CountableAbstractBase[T](_CountableCollection[T, IList[T]], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, l: IList[T]) -> None: super().__init__(l)

class _ICountableBase[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _CreateList(self, items: Iterable[T]|None) -> IList[T]:
        ...

class Countable[T](_CountableAbstractBase[T], _ICountableBase[T]):
    def __init__(self, items: Iterable[T]|None) -> None: super().__init__(self._CreateList(items))

@final
class _ReadOnlyCountableQueue[T](_ReadOnlyCountableCollection[T], IReadOnlyCountableQueue[T]):
    def __init__(self, items: ICountableQueue[T]) -> None: super().__init__(items)
@final
class _ReadOnlyCountableQueueUpdater[T](SelectionUpdater[ICountableQueue[T], IReadOnlyCountableQueue[T]]):
    def __init__(self, items: ICountableQueue[T], updater: Method[IFunction[IReadOnlyCountableQueue[T]]]) -> None: super().__init__(items, updater)

    def _AsContainer(self, container: ICountableQueue[T]) -> IReadOnlyCountableQueue[T]: return _ReadOnlyCountableQueue[T](container)

@final
class _ReadOnlyCountableStack[T](_ReadOnlyCountableCollection[T], IReadOnlyCountableStack[T]):
    def __init__(self, items: ICountableStack[T]) -> None: super().__init__(items)
@final
class _ReadOnlyCountableStackUpdater[T](SelectionUpdater[ICountableStack[T], IReadOnlyCountableStack[T]]):
    def __init__(self, items: ICountableStack[T], updater: Method[IFunction[IReadOnlyCountableStack[T]]]) -> None: super().__init__(items, updater)

    def _AsContainer(self, container: ICountableStack[T]) -> IReadOnlyCountableStack[T]: return _ReadOnlyCountableStack[T](container)

class CountableQueueAbstract[T](Countable[T]):
    def __init__(self, items: Iterable[T]|None) -> None: super().__init__(items)
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableQueue[T]:
        ...
class CountableStackAbstract[T](Countable[T]):
    def __init__(self, items: Iterable[T]|None) -> None: super().__init__(items)
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableStack[T]:
        ...

@final
class _CountableQueue[T](CountableQueueAbstract[T]):
    def __init__(self, items: CountableQueue[T], values: Iterable[T]|None) -> None:
        def update(func: IFunction[IReadOnlyCountableQueue[T]]) -> None: self.__readOnly = func
        
        super().__init__(values)

        self.__readOnly: IFunction[IReadOnlyCountableQueue[T]] = _ReadOnlyCountableQueueUpdater[T](items, update) # type: ignore[no-redef]
    
    def _CreateList(self, items: Iterable[T]|None) -> IQueue[T]:
        return Queue[T](items)
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableQueue[T]: return self.__readOnly.GetValue()
@final
class _CountableStack[T](CountableStackAbstract[T]):
    def __init__(self, items: CountableStack[T], values: Iterable[T]|None) -> None:
        def update(func: IFunction[IReadOnlyCountableStack[T]]) -> None: self.__readOnly = func
        
        super().__init__(values)

        self.__readOnly: IFunction[IReadOnlyCountableStack[T]] = _ReadOnlyCountableStackUpdater[T](items, update) # type: ignore[no-redef]
    
    def _CreateList(self, items: Iterable[T]|None) -> IStack[T]:
        return Stack[T](items)
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableStack[T]: return self.__readOnly.GetValue()

class CountableList[TItem, TList](ICountableList[TItem], GenericConstraint[TList, ICountableListBase[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__items: TList = items
    
    @final
    def _GetContainer(self) -> TList: return self.__items
    
    @final
    def IsEmpty(self) -> bool: return self._GetInnerContainer().IsEmpty()
    
    @final
    def GetCount(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def TryPeek(self) -> INullable[TItem]: return self._GetInnerContainer().TryPeek()
    
    @final
    def Push(self, value: TItem) -> None: self._GetInnerContainer().Push(value)
    @final
    def PushItems(self, items: Iterable[TItem]) -> None: self._GetInnerContainer().PushItems(items)
    
    @final
    def TryPop(self) -> INullable[TItem]: return self._GetInnerContainer().TryPop()
    
    @final
    def Clear(self) -> None: return self._GetInnerContainer().Clear()
    
    @final
    def AsCountableGenerator(self) -> ICountableEnumerable[TItem]: return self._GetInnerContainer().AsCountableGenerator()
    
    @final
    def AsSized(self) -> Sized: return self._GetInnerContainer().AsSized()

class CountableQueue[T](CountableList[T, CountableQueueAbstract[T]], ICountableQueue[T], IGenericConstraintImplementation[CountableQueueAbstract[T]]):
    def __init__(self, items: Iterable[T]|None = None) -> None: super().__init__(_CountableQueue[T](self, items))
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableQueue[T]: return self._GetContainer().AsReadOnly()
class CountableStack[T](CountableList[T, CountableStackAbstract[T]], ICountableStack[T], IGenericConstraintImplementation[CountableStackAbstract[T]]):
    def __init__(self, items: Iterable[T]|None = None) -> None: super().__init__(_CountableStack[T](self, items))
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableStack[T]: return self._GetContainer().AsReadOnly()

class ReadOnlyCountableEnumerable[T](ReadOnlyListBase[T, ICountableEnumerableList[T]], CountableEnumerableCollectionBase[T], IReadOnlyCountableEnumerableList[T], IGenericConstraintImplementation[ICountableEnumerableList[T]]):
    def __init__(self, items: ICountableEnumerableList[T]) -> None: super().__init__(items)
    
    @final
    def GetCount(self) -> int: return self._GetContainer().GetCount()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return TryCreateEnumerator(self._GetContainer().TryGetEnumerator())

class CountableEnumerableBase[TItems, TList](CountableCollectionAbstract[TItems, TList], EnumerableCollectionBase[TItems], ICountableEnumerableListBase[TItems], GenericConstraint[TList, IEnumerableList[TItems]]):
    def __init__(self, l: TList) -> None: super().__init__(l)
class CountableEnumerable[T](CountableEnumerableBase[T, IEnumerableList[T]], IGenericConstraintImplementation[IEnumerableList[T]]):
    def __init__(self, l: IEnumerableList[T]) -> None: super().__init__(l)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self._GetContainer().TryGetEnumerator()

@final
class _ReadOnlyCountableEnumerableQueue[T](ReadOnlyCountableEnumerable[T], IReadOnlyCountableEnumerableQueue[T]):
    def __init__(self, l: ICountableEnumerableQueue[T]) -> None: super().__init__(l)
@final
class _ReadOnlyCountableEnumerableQueueUpdater[T](SelectionUpdater[ICountableEnumerableQueue[T], IReadOnlyCountableEnumerableQueue[T]]):
    def __init__(self, items: ICountableEnumerableQueue[T], updater: Method[IFunction[IReadOnlyCountableEnumerableQueue[T]]]) -> None: super().__init__(items, updater)
    
    def _AsContainer(self, container: ICountableEnumerableQueue[T]) -> IReadOnlyCountableEnumerableQueue[T]: return _ReadOnlyCountableEnumerableQueue[T](container)

@final
class _ReadOnlyCountableEnumerableStack[T](ReadOnlyCountableEnumerable[T], IReadOnlyCountableEnumerableStack[T]):
    def __init__(self, l: ICountableEnumerableStack[T]) -> None: super().__init__(l)
@final
class _ReadOnlyCountableEnumerableStackUpdater[T](SelectionUpdater[ICountableEnumerableStack[T], IReadOnlyCountableEnumerableStack[T]]):
    def __init__(self, items: ICountableEnumerableStack[T], updater: Method[IFunction[IReadOnlyCountableEnumerableStack[T]]]) -> None: super().__init__(items, updater)
    
    def _AsContainer(self, container: ICountableEnumerableStack[T]) -> IReadOnlyCountableEnumerableStack[T]: return _ReadOnlyCountableEnumerableStack[T](container)

class CountableEnumerableQueueAbstract[T](CountableEnumerable[T]):
    def __init__(self, items: Iterable[T]|None) -> None: super().__init__(EnumerableQueue[T](items))
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableQueue[T]:
        ...
class CountableEnumerableStackAbstract[T](CountableEnumerable[T]):
    def __init__(self, items: Iterable[T]|None) -> None: super().__init__(EnumerableStack[T](items))
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableStack[T]:
        ...

class _CountableEnumerableQueue[T](CountableEnumerableQueueAbstract[T]):
    def __init__(self, items: CountableEnumerableQueue[T], values: Iterable[T]|None) -> None:
        def update(func: IFunction[IReadOnlyCountableEnumerableQueue[T]]) -> None: self.__readOnly = func
        
        super().__init__(values)

        self.__readOnly: IFunction[IReadOnlyCountableEnumerableQueue[T]] = _ReadOnlyCountableEnumerableQueueUpdater[T](items, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableQueue[T]: return self.__readOnly.GetValue()
class _CountableEnumerableStack[T](CountableEnumerableStackAbstract[T]):
    def __init__(self, items: CountableEnumerableStack[T], values: Iterable[T]|None) -> None:
        def update(func: IFunction[IReadOnlyCountableEnumerableStack[T]]) -> None: self.__readOnly = func
        
        super().__init__(values)

        self.__readOnly: IFunction[IReadOnlyCountableEnumerableStack[T]] = _ReadOnlyCountableEnumerableStackUpdater[T](items, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableStack[T]: return self.__readOnly.GetValue()

class CountableEnumerableList[TItem, TList](CountableList[TItem, TList], ICountableEnumerable[TItem], GenericSpecializedConstraint[TList, ICountableListBase[TItem], ICountableEnumerable[TItem]]):
    def __init__(self, items: TList) -> None: super().__init__(items)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None: return self._GetSpecializedContainer().TryGetEnumerator()
    
    @final
    def AsIterable(self) -> Iterable[TItem]: return self._GetSpecializedContainer().AsIterable()

class CountableEnumerableQueue[T](CountableEnumerableList[T, CountableEnumerableQueueAbstract[T]], ICountableEnumerableQueue[T], IGenericSpecializedConstraintImplementation[ICountableListBase[T], CountableEnumerableQueueAbstract[T]]):
    def __init__(self, items: Iterable[T]|None = None) -> None: super().__init__(_CountableEnumerableQueue[T](self, items))
    
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableQueue[T]: return self._GetContainer().AsReadOnly()
class CountableEnumerableStack[T](CountableEnumerableList[T, CountableEnumerableStackAbstract[T]], ICountableEnumerableStack[T], IGenericSpecializedConstraintImplementation[ICountableListBase[T], CountableEnumerableStackAbstract[T]]):
    def __init__(self, items: Iterable[T]|None = None) -> None: super().__init__(_CountableEnumerableStack[T](self, items))
    
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableStack[T]: return self._GetContainer().AsReadOnly()

def CreateQueue[T](items: Iterable[T]|None) -> Queue[T]:
    return Queue[T](items)
def MakeQueue[T](*values: T) -> Queue[T]:
    return CreateQueue(values)

def CreateStack[T](items: Iterable[T]|None) -> Stack[T]:
    return Stack[T](items)
def MakeStack[T](*values: T) -> Stack[T]:
    return CreateStack(values)

def CreateEnumerableQueue[T](items: Iterable[T]|None) -> EnumerableQueue[T]:
    return EnumerableQueue[T](items)
def MakeEnumerableQueue[T](*values: T) -> EnumerableQueue[T]:
    return CreateEnumerableQueue(values)

def CreateEnumerableStack[T](items: Iterable[T]|None) -> EnumerableStack[T]:
    return EnumerableStack[T](items)
def MakeEnumerableStack[T](*values: T) -> EnumerableStack[T]:
    return CreateEnumerableStack(values)

def CreateCountableQueue[T](items: Iterable[T]|None) -> CountableQueue[T]:
    return CountableQueue[T](items)
def MakeCountableQueue[T](*values: T) -> CountableQueue[T]:
    return CreateCountableQueue(values)

def CreateCountableStack[T](items: Iterable[T]|None) -> CountableStack[T]:
    return CountableStack[T](items)
def MakeCountableStack[T](*values: T) -> CountableStack[T]:
    return CreateCountableStack(values)

def CreateCountableEnumerableQueue[T](items: Iterable[T]|None) -> CountableEnumerableQueue[T]:
    return CountableEnumerableQueue[T](items)
def MakeCountableEnumerableQueue[T](*values: T) -> CountableEnumerableQueue[T]:
    return CreateCountableEnumerableQueue(values)

def CreateCountableEnumerableStack[T](items: Iterable[T]|None) -> CountableEnumerableStack[T]:
    return CountableEnumerableStack[T](items)
def MakeCountableEnumerableStack[T](*values: T) -> CountableEnumerableStack[T]:
    return CreateCountableEnumerableStack(values)