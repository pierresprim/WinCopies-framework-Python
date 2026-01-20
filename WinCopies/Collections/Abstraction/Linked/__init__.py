from abc import abstractmethod
from collections.abc import Iterable, Sized
from typing import final

from WinCopies import Abstract
from WinCopies.Collections import EnumerationOrder, ICountable, Countable as CountableBase
from WinCopies.Collections.Abstraction import Countable
from WinCopies.Collections.Abstraction.Enumeration import Enumerable, CountableEnumerable, Enumerator
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEnumerator, Enumerable as EnumerableBase, CountableEnumerable as CountableEnumerableBase
from WinCopies.Collections.Linked.Singly.Base import IReadOnlyList, IReadOnlyCountableList, IReadOnlyEnumerableList, IReadOnlyCountableEnumerableList, IList as ISinglyLinkedList, ICountableList as ICountableSinglyLinkedList, ICountableEnumerableList, IEnumerableList
from WinCopies.Collections.Linked.Singly import IReadOnlyQueue, IReadOnlyCountableQueue, IReadOnlyEnumerableQueue, IReadOnlyCountableEnumerableQueue, IReadOnlyStack, IReadOnlyCountableStack, IReadOnlyEnumerableStack, IReadOnlyCountableEnumerableStack, IQueue, ICountableQueue, IEnumerableQueue, ICountableEnumerableQueue, IStack, ICountableStack, IEnumerableStack, ICountableEnumerableStack, ReadOnlyListBase
from WinCopies.Collections.Linked.Doubly import IReadWriteList, IReadWriteEnumerableList, IReadWriteCountableEnumerableList, IList as IDoublyLinkedList, ICountableList as ICountableDoublyLinkedList, List, CountableList

from WinCopies.Typing import IGenericConstraint, GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation, INullable
from WinCopies.Typing.Delegate import IFunction, Method, ValueFunctionUpdater, SelectionUpdater

class _ReadOnlyListUpdaterBase[TIn, TOut](ValueFunctionUpdater[TOut], IGenericConstraint[TIn, TOut]):
    def __init__(self, items: TIn, updater: Method[IFunction[TOut]]) -> None:
        super().__init__(updater)

        self.__items: TIn = items
    
    @final
    def _GetValue(self) -> TOut:
        return self._AsContainer(self.__items)

class _ReadOnlyListBase[TItem, TList](ReadOnlyListBase[TItem, TList]):
    def __init__(self, items: TList) -> None:
        super().__init__(items)
    
    def GetOrder(self) -> EnumerationOrder:
        return self._GetInnerContainer().GetOrder()

@final
class _ReadOnlyLinkedListUpdaterList[T](_ReadOnlyListBase[T, ISinglyLinkedList[T]], IGenericConstraintImplementation[ISinglyLinkedList[T]]):
    def __init__(self, items: ISinglyLinkedList[T]) -> None:
        super().__init__(items)
@final
class _ReadOnlyLinkedListUpdater[T](_ReadOnlyListUpdaterBase[ISinglyLinkedList[T], IReadOnlyList[T]]):
    def __init__(self, items: ISinglyLinkedList[T], updater: Method[IFunction[IReadOnlyList[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: ISinglyLinkedList[T]) -> IReadOnlyList[T]:
        return _ReadOnlyLinkedListUpdaterList[T](container)

@final
class _ReadOnlyCountableLinkedListUpdaterList[T](_ReadOnlyListBase[T, ICountableSinglyLinkedList[T]], CountableBase, IReadOnlyCountableList[T], IGenericConstraintImplementation[ICountableSinglyLinkedList[T]]):
    def __init__(self, items: ICountableSinglyLinkedList[T]) -> None:
        super().__init__(items)
    
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()
@final
class _ReadOnlyCountableLinkedListUpdater[T](_ReadOnlyListUpdaterBase[ICountableSinglyLinkedList[T], IReadOnlyCountableList[T]]):
    def __init__(self, items: ICountableSinglyLinkedList[T], updater: Method[IFunction[IReadOnlyCountableList[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: ICountableSinglyLinkedList[T]) -> IReadOnlyCountableList[T]:
        return _ReadOnlyCountableLinkedListUpdaterList[T](container)

@final
class _ReadOnlyEnumerableLinkedListUpdaterList[T](_ReadOnlyListBase[T, IEnumerableList[T]], EnumerableBase[T], IReadOnlyEnumerableList[T], IGenericConstraintImplementation[IEnumerableList[T]]):
    def __init__(self, items: IEnumerableList[T]) -> None:
        super().__init__(items)
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
@final
class _ReadOnlyEnumerableLinkedListUpdater[T](_ReadOnlyListUpdaterBase[IEnumerableList[T], IReadOnlyEnumerableList[T]]):
    def __init__(self, items: IEnumerableList[T], updater: Method[IFunction[IReadOnlyEnumerableList[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: IEnumerableList[T]) -> IReadOnlyEnumerableList[T]:
        return _ReadOnlyEnumerableLinkedListUpdaterList[T](container)

@final
class _ReadOnlyCountableEnumerableLinkedListUpdaterList[T](_ReadOnlyListBase[T, ICountableEnumerableList[T]], CountableEnumerableBase[T], IReadOnlyCountableEnumerableList[T], IGenericConstraintImplementation[ICountableEnumerableList[T]]):
    def __init__(self, items: ICountableEnumerableList[T]) -> None:
        super().__init__(items)
    
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
@final
class _ReadOnlyCountableEnumerableLinkedListUpdater[T](_ReadOnlyListUpdaterBase[ICountableEnumerableList[T], IReadOnlyCountableEnumerableList[T]]):
    def __init__(self, items: ICountableEnumerableList[T], updater: Method[IFunction[IReadOnlyCountableEnumerableList[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: ICountableEnumerableList[T]) -> IReadOnlyCountableEnumerableList[T]:
        return _ReadOnlyCountableEnumerableLinkedListUpdaterList[T](container)

class _ReadOnlyList[T](Abstract, ISinglyLinkedList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetUpdater(self) -> IFunction[IReadOnlyList[T]]:
        pass
    
    @final
    def AsReadOnly(self) -> IReadOnlyList[T]:
        return self._GetUpdater().GetValue()
class _ReadOnlyCountableList[T](Abstract, ICountableSinglyLinkedList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetUpdater(self) -> IFunction[IReadOnlyCountableList[T]]:
        pass
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableList[T]:
        return self._GetUpdater().GetValue()
class _ReadOnlyEnumerableList[T](Abstract, IEnumerableList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetUpdater(self) -> IFunction[IReadOnlyEnumerableList[T]]:
        pass
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableList[T]:
        return self._GetUpdater().GetValue()
class _ReadOnlyCountableEnumerableList[T](Abstract, ICountableEnumerableList[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IReadOnlyCountableEnumerableList[T]]) -> None:
            self.__updater = func
        
        super().__init__()
    
        self.__updater: IFunction[IReadOnlyCountableEnumerableList[T]] = _ReadOnlyCountableEnumerableLinkedListUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[T]:
        return self.__updater.GetValue()

class LinkedListBase[TItem, TList](Abstract, ISinglyLinkedList[TItem], GenericConstraint[TList, IReadWriteList[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__list: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__list
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    
    @final
    def TryPeek(self) -> INullable[TItem]:
        return self._GetInnerContainer().TryGetFirst()
    
    @final
    def TryPop(self) -> INullable[TItem]:
        return self._GetInnerContainer().TryRemoveFirst()
    
    @final
    def Clear(self) -> None:
        self._GetInnerContainer().Clear()

class QueueBase[TItems, TList](LinkedListBase[TItems, TList], IQueue[TItems]):
    def __init__(self, l: TList) -> None:
        super().__init__(l)
    
    @final
    def Push(self, value: TItems) -> None:
        self._GetInnerContainer().AddLastNode(value)
    @final
    def PushItems(self, items: Iterable[TItems]) -> None:
        self._GetInnerContainer().AddLastItems(items)
class StackBase[TItems, TList](LinkedListBase[TItems, TList], IStack[TItems]):
    def __init__(self, l: TList) -> None:
        super().__init__(l)
    
    @final
    def Push(self, value: TItems) -> None:
        self._GetInnerContainer().AddFirstNode(value)
    @final
    def PushItems(self, items: Iterable[TItems]) -> None:
        self._GetInnerContainer().AddFirstItems(items)

def _GetRWList[T](l: IReadWriteList[T]|None) -> IReadWriteList[T]:
    return List[T]() if l is None else l
def _GetList[T](l: IDoublyLinkedList[T]|None) -> IDoublyLinkedList[T]:
    return List[T]() if l is None else l
def _GetCountableList[T](l: ICountableDoublyLinkedList[T]|None) -> ICountableDoublyLinkedList[T]:
    return CountableList[T]() if l is None else l

class AbstractReadOnlyList[T](IReadOnlyList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def GetOrder(self) -> EnumerationOrder:
        return EnumerationOrder.Both

class AbstractList[TItem, TList](LinkedListBase[TItem, TList], AbstractReadOnlyList[TItem]):
    def __init__(self, l: TList) -> None:
        super().__init__(l)
    
    @final
    def Push(self, value: TItem) -> None:
        self._GetInnerContainer().AddLastNode(value)
    @final
    def PushItems(self, items: Iterable[TItem]) -> None:
        self._GetInnerContainer().AddLastItems(items)
class AbstractCountableList[TItem, TList](AbstractList[TItem, TList], IReadOnlyCountableList[TItem], GenericSpecializedConstraint[TList, IReadWriteList[TItem], ICountableDoublyLinkedList[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__(items)
    
    @final
    def GetCount(self) -> int:
        return self._GetSpecializedContainer().GetCount()
class AbstractEnumerableList[TItem, TList](AbstractList[TItem, TList], IReadOnlyEnumerableList[TItem], GenericSpecializedConstraint[TList, IReadWriteList[TItem], IReadWriteEnumerableList[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__(items)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None:
        return self._GetSpecializedContainer().TryGetEnumerator()
class AbstractCountableEnumerableList[TItem, TList](AbstractList[TItem, TList], IReadOnlyCountableEnumerableList[TItem], GenericSpecializedConstraint[TList, IReadWriteList[TItem], IReadWriteCountableEnumerableList[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__(items)
    
    @final
    def GetCount(self) -> int:
        return self._GetSpecializedContainer().GetCount()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None:
        return self._GetSpecializedContainer().TryGetEnumerator()

class LinkedList[T](AbstractList[T, IReadWriteList[T]], _ReadOnlyList[T], IGenericConstraintImplementation[IReadWriteList[T]]):
    def __init__(self, l: IReadWriteList[T]|None = None) -> None:
        def update(func: IFunction[IReadOnlyList[T]]) -> None:
            self.__updater = func

        super().__init__(_GetRWList(l))

        self.__updater: IFunction[IReadOnlyList[T]] = _ReadOnlyLinkedListUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def _GetUpdater(self) -> IFunction[IReadOnlyList[T]]:
        return self.__updater
class CountableLinkedList[T](AbstractCountableList[T, ICountableDoublyLinkedList[T]], _ReadOnlyCountableList[T], IGenericSpecializedConstraintImplementation[IReadWriteList[T], ICountableDoublyLinkedList[T]]):
    def __init__(self, l: ICountableDoublyLinkedList[T]|None = None) -> None:
        def update(func: IFunction[IReadOnlyCountableList[T]]) -> None:
            self.__updater = func
        
        super().__init__(_GetCountableList(l))

        self.__updater: IFunction[IReadOnlyCountableList[T]] = _ReadOnlyCountableLinkedListUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def _GetUpdater(self) -> IFunction[IReadOnlyCountableList[T]]:
        return self.__updater
class EnumerableLinkedList[T](AbstractEnumerableList[T, IDoublyLinkedList[T]], _ReadOnlyEnumerableList[T], IGenericSpecializedConstraintImplementation[IReadWriteList[T], IReadWriteEnumerableList[T]]):
    def __init__(self, l: IDoublyLinkedList[T]|None = None) -> None:
        def update(func: IFunction[IReadOnlyEnumerableList[T]]) -> None:
            self.__updater = func
    
        super().__init__(_GetList(l))

        self.__updater: IFunction[IReadOnlyEnumerableList[T]] = _ReadOnlyEnumerableLinkedListUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def _GetUpdater(self) -> IFunction[IReadOnlyEnumerableList[T]]:
        return self.__updater
class CountableEnumerableLinkedList[T](AbstractCountableEnumerableList[T, ICountableDoublyLinkedList[T]], _ReadOnlyCountableEnumerableList[T], IGenericSpecializedConstraintImplementation[IReadWriteList[T], ICountableDoublyLinkedList[T]]):
    def __init__(self, l: ICountableDoublyLinkedList[T]|None = None) -> None:
        super().__init__(_GetCountableList(l))

@final
class _ReadOnlyQueueUpdaterList[T](ReadOnlyListBase[T, IQueue[T]], IReadOnlyQueue[T], IGenericConstraintImplementation[IQueue[T]]):
    def __init__(self, items: IQueue[T]) -> None:
        super().__init__(items)
@final
class _QueueUpdater[T](_ReadOnlyListUpdaterBase[IQueue[T], IReadOnlyQueue[T]]):
    def __init__(self, items: IQueue[T], updater: Method[IFunction[IReadOnlyQueue[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: IQueue[T]) -> IReadOnlyQueue[T]:
        return _ReadOnlyQueueUpdaterList[T](container)

@final
class _ReadOnlyStackUpdaterList[T](ReadOnlyListBase[T, IStack[T]], IReadOnlyStack[T], IGenericConstraintImplementation[IStack[T]]):
    def __init__(self, items: IStack[T]) -> None:
        super().__init__(items)
@final
class _StackUpdater[T](_ReadOnlyListUpdaterBase[IStack[T], IReadOnlyStack[T]]):
    def __init__(self, items: IStack[T], updater: Method[IFunction[IReadOnlyStack[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: IStack[T]) -> IReadOnlyStack[T]:
        return _ReadOnlyStackUpdaterList[T](container)

class AbstractReadOnlyCountableList[TItem, TList](ReadOnlyListBase[TItem, TList], IReadOnlyCountableList[TItem], GenericSpecializedConstraint[TList, ISinglyLinkedList[TItem], ICountableSinglyLinkedList[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__(items)
    
    @final
    def GetCount(self) -> int:
        return self._GetSpecializedContainer().GetCount()
class AbstractReadOnlyEnumerableList[TItem, TList](ReadOnlyListBase[TItem, TList], IReadOnlyEnumerableList[TItem], GenericSpecializedConstraint[TList, ISinglyLinkedList[TItem], IReadOnlyEnumerableList[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__(items)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None:
        return Enumerator[TItem].TryCreate(self._GetSpecializedContainer().TryGetEnumerator())
class AbstractReadOnlyCountableEnumerableList[TItem, TList](ReadOnlyListBase[TItem, TList], IReadOnlyCountableEnumerableList[TItem], GenericSpecializedConstraint[TList, ISinglyLinkedList[TItem], IReadOnlyCountableEnumerableList[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__(items)
    
    @final
    def GetCount(self) -> int:
        return self._GetSpecializedContainer().GetCount()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None:
        return Enumerator[TItem].TryCreate(self._GetSpecializedContainer().TryGetEnumerator())

@final
class _CountableUpdater(ValueFunctionUpdater[CountableBase]):
    def __init__(self, collection: ICountable, updater: Method[IFunction[CountableBase]]) -> None:
        super().__init__(updater)

        self.__collection: ICountable = collection
    
    def _GetValue(self) -> CountableBase:
        return Countable.Create(self.__collection)
@final
class _EnumerableUpdater[T](SelectionUpdater[IReadOnlyEnumerableList[T], Iterable[T]]):
    def __init__(self, items: IReadOnlyEnumerableList[T], updater: Method[IFunction[Iterable[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: IReadOnlyEnumerableList[T]) -> Iterable[T]:
        return Enumerable[T].Create(container)
@final
class _CountableEnumerableUpdater[T](ValueFunctionUpdater[CountableEnumerableBase[T]]):
    def __init__(self, collection: ICountableEnumerable[T], updater: Method[IFunction[CountableEnumerableBase[T]]]) -> None:
        super().__init__(updater)

        self.__collection: ICountableEnumerable[T] = collection
    
    def _GetValue(self) -> CountableEnumerableBase[T]:
        return CountableEnumerable[T].Create(self.__collection)

@final
class _ReadOnlyCountableQueueUpdaterList[T](AbstractReadOnlyCountableList[T, ICountableQueue[T]], IReadOnlyCountableQueue[T], IGenericSpecializedConstraintImplementation[ISinglyLinkedList[T], ICountableQueue[T]]):
    def __init__(self, items: ICountableQueue[T]) -> None:
        def update(func: IFunction[CountableBase]) -> None:
            self.__updater = func
        
        super().__init__(items)

        self.__updater: IFunction[CountableBase] = _CountableUpdater(self, update) # type: ignore[no-redef]
    
    def AsSized(self) -> Sized:
        return self.__updater.GetValue()
@final
class _CountableQueueUpdater[T](_ReadOnlyListUpdaterBase[ICountableQueue[T], IReadOnlyCountableQueue[T]]):
    def __init__(self, items: ICountableQueue[T], updater: Method[IFunction[IReadOnlyCountableQueue[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: ICountableQueue[T]) -> IReadOnlyCountableQueue[T]:
        return _ReadOnlyCountableQueueUpdaterList[T](container)

@final
class _ReadOnlyCountableStackUpdaterList[T](AbstractReadOnlyCountableList[T, ICountableStack[T]], IReadOnlyCountableStack[T], IGenericSpecializedConstraintImplementation[ISinglyLinkedList[T], ICountableStack[T]]):
    def __init__(self, items: ICountableStack[T]) -> None:
        def update(func: IFunction[CountableBase]) -> None:
            self.__updater = func
        
        super().__init__(items)

        self.__updater: IFunction[CountableBase] = _CountableUpdater(self, update) # type: ignore[no-redef]
    
    def AsSized(self) -> Sized:
        return self.__updater.GetValue()
@final
class _CountableStackUpdater[T](_ReadOnlyListUpdaterBase[ICountableStack[T], IReadOnlyCountableStack[T]]):
    def __init__(self, items: ICountableStack[T], updater: Method[IFunction[IReadOnlyCountableStack[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: ICountableStack[T]) -> IReadOnlyCountableStack[T]:
        return _ReadOnlyCountableStackUpdaterList[T](container)

@final
class _ReadOnlyEnumerableQueueUpdaterList[T](AbstractReadOnlyEnumerableList[T, IEnumerableQueue[T]], IReadOnlyEnumerableQueue[T], IGenericSpecializedConstraintImplementation[ISinglyLinkedList[T], IEnumerableQueue[T]]):
    def __init__(self, items: IEnumerableQueue[T]) -> None:
        def update(func: IFunction[Iterable[T]]) -> None:
            self.__updater = func
        
        super().__init__(items)

        self.__updater: IFunction[Iterable[T]] = _EnumerableUpdater[T](self, update) # type: ignore[no-redef]
    
    def AsIterable(self) -> Iterable[T]:
        return self.__updater.GetValue()
@final
class _EnumerableQueueUpdater[T](_ReadOnlyListUpdaterBase[IEnumerableQueue[T], IReadOnlyEnumerableQueue[T]]):
    def __init__(self, items: IEnumerableQueue[T], updater: Method[IFunction[IReadOnlyEnumerableQueue[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: IEnumerableQueue[T]) -> IReadOnlyEnumerableQueue[T]:
        return _ReadOnlyEnumerableQueueUpdaterList[T](container)

@final
class _ReadOnlyEnumerableStackUpdaterList[T](AbstractReadOnlyEnumerableList[T, IEnumerableStack[T]], IReadOnlyEnumerableStack[T], IGenericSpecializedConstraintImplementation[ISinglyLinkedList[T], IEnumerableStack[T]]):
    def __init__(self, items: IEnumerableStack[T]) -> None:
        def update(func: IFunction[Iterable[T]]) -> None:
            self.__updater = func
        
        super().__init__(items)

        self.__updater: IFunction[Iterable[T]] = _EnumerableUpdater[T](self, update) # type: ignore[no-redef]
    
    def AsIterable(self) -> Iterable[T]:
        return self.__updater.GetValue()
@final
class _EnumerableStackUpdater[T](_ReadOnlyListUpdaterBase[IEnumerableStack[T], IReadOnlyEnumerableStack[T]]):
    def __init__(self, items: IEnumerableStack[T], updater: Method[IFunction[IReadOnlyEnumerableStack[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: IEnumerableStack[T]) -> IReadOnlyEnumerableStack[T]:
        return _ReadOnlyEnumerableStackUpdaterList[T](container)

@final
class _ReadOnlyCountableEnumerableQueueUpdaterList[T](AbstractReadOnlyCountableEnumerableList[T, ICountableEnumerableQueue[T]], IReadOnlyCountableEnumerableQueue[T], IGenericSpecializedConstraintImplementation[ISinglyLinkedList[T], ICountableEnumerableQueue[T]]):
    def __init__(self, items: ICountableEnumerableQueue[T]) -> None:
        def update(func: IFunction[CountableEnumerableBase[T]]) -> None:
            self.__updater = func
        
        super().__init__(items)

        self.__updater: IFunction[CountableEnumerableBase[T]] = _CountableEnumerableUpdater[T](self, update) # type: ignore[no-redef]
    
    def AsSized(self) -> Sized:
        return self.__updater.GetValue().AsSized()
    
    def AsIterable(self) -> Iterable[T]:
        return self.__updater.GetValue()
@final
class _CountableEnumerableQueueUpdater[T](_ReadOnlyListUpdaterBase[ICountableEnumerableQueue[T], IReadOnlyCountableEnumerableQueue[T]]):
    def __init__(self, items: ICountableEnumerableQueue[T], updater: Method[IFunction[IReadOnlyCountableEnumerableQueue[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: ICountableEnumerableQueue[T]) -> IReadOnlyCountableEnumerableQueue[T]:
        return _ReadOnlyCountableEnumerableQueueUpdaterList[T](container)

@final
class _ReadOnlyCountableEnumerableStackUpdaterList[T](AbstractReadOnlyCountableEnumerableList[T, ICountableEnumerableStack[T]], IReadOnlyCountableEnumerableStack[T], IGenericSpecializedConstraintImplementation[ISinglyLinkedList[T], ICountableEnumerableStack[T]]):
    def __init__(self, items: ICountableEnumerableStack[T]) -> None:
        def update(func: IFunction[CountableEnumerableBase[T]]) -> None:
            self.__updater = func
        
        super().__init__(items)

        self.__updater: IFunction[CountableEnumerableBase[T]] = _CountableEnumerableUpdater[T](self, update) # type: ignore[no-redef]
    
    def AsSized(self) -> Sized:
        return self.__updater.GetValue().AsSized()
    
    def AsIterable(self) -> Iterable[T]:
        return self.__updater.GetValue()
@final
class _CountableEnumerableStackUpdater[T](_ReadOnlyListUpdaterBase[ICountableEnumerableStack[T], IReadOnlyCountableEnumerableStack[T]]):
    def __init__(self, items: ICountableEnumerableStack[T], updater: Method[IFunction[IReadOnlyCountableEnumerableStack[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: ICountableEnumerableStack[T]) -> IReadOnlyCountableEnumerableStack[T]:
        return _ReadOnlyCountableEnumerableStackUpdaterList[T](container)

class Queue[T](QueueBase[T, IReadWriteList[T]], IGenericConstraintImplementation[IReadWriteList[T]]):
    def __init__(self, l: IReadWriteList[T]|None = None) -> None:
        def update(func: IFunction[IReadOnlyQueue[T]]) -> None:
            self.__updater = func
        
        super().__init__(_GetRWList(l))
        
        self.__updater: IFunction[IReadOnlyQueue[T]] = _QueueUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyQueue[T]:
        return self.__updater.GetValue()
class Stack[T](StackBase[T, IReadWriteList[T]], IGenericConstraintImplementation[IReadWriteList[T]]):
    def __init__(self, l: IReadWriteList[T]|None = None) -> None:
        def update(func: IFunction[IReadOnlyStack[T]]) -> None:
            self.__updater = func
        
        super().__init__(_GetRWList(l))
        
        self.__updater: IFunction[IReadOnlyStack[T]] = _StackUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyStack[T]:
        return self.__updater.GetValue()

class CountableQueue[T](QueueBase[T, ICountableDoublyLinkedList[T]], ICountableQueue[T], IGenericConstraintImplementation[IReadWriteList[T]]):
    def __init__(self, l: ICountableDoublyLinkedList[T]|None = None) -> None:
        def update(func: IFunction[IReadOnlyCountableQueue[T]]) -> None:
            self.__updater = func
        
        super().__init__(_GetCountableList(l))

        self.__updater: IFunction[IReadOnlyCountableQueue[T]] = _CountableQueueUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableQueue[T]:
        return self.__updater.GetValue()
class CountableStack[T](StackBase[T, ICountableDoublyLinkedList[T]], ICountableStack[T], IGenericConstraintImplementation[IReadWriteList[T]]):
    def __init__(self, l: ICountableDoublyLinkedList[T]|None = None) -> None:
        def update(func: IFunction[IReadOnlyCountableStack[T]]) -> None:
            self.__updater = func
        
        super().__init__(_GetCountableList(l))

        self.__updater: IFunction[IReadOnlyCountableStack[T]] = _CountableStackUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableStack[T]:
        return self.__updater.GetValue()

class EnumerableQueue[T](QueueBase[T, IDoublyLinkedList[T]], IEnumerableQueue[T], IGenericConstraintImplementation[IDoublyLinkedList[T]]):
    def __init__(self, l: IDoublyLinkedList[T]|None = None) -> None:
        def updateReadOnly(func: IFunction[IReadOnlyEnumerableQueue[T]]) -> None:
            self.__readOnly = func
        def updateIterable(func: IFunction[Iterable[T]]) -> None:
            self.__iterable = func
        
        super().__init__(_GetList(l))

        self.__readOnly: IFunction[IReadOnlyEnumerableQueue[T]] = _EnumerableQueueUpdater[T](self, updateReadOnly) # type: ignore[no-redef]
        self.__iterable: IFunction[Iterable[T]] = _EnumerableUpdater[T](self, updateIterable) # type: ignore[no-redef]

    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableQueue[T]:
        return self.__readOnly.GetValue()
    
    @final
    def AsIterable(self) -> Iterable[T]:
        return self.__iterable.GetValue()
class EnumerableStack[T](StackBase[T, IDoublyLinkedList[T]], IEnumerableStack[T], IGenericConstraintImplementation[IDoublyLinkedList[T]]):
    def __init__(self, l: IDoublyLinkedList[T]|None = None) -> None:
        def update(func: IFunction[IReadOnlyEnumerableStack[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(_GetList(l))

        self.__readOnly: IFunction[IReadOnlyEnumerableStack[T]] = _EnumerableStackUpdater[T](self, update) # type: ignore[no-redef]

    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableStack[T]:
        return self.__readOnly.GetValue()

class CountableEnumerableQueue[T](QueueBase[T, ICountableDoublyLinkedList[T]], ICountableEnumerableQueue[T], IGenericConstraintImplementation[ICountableDoublyLinkedList[T]]):
    def __init__(self, l: ICountableDoublyLinkedList[T]|None = None) -> None:
        def update(func: IFunction[IReadOnlyCountableEnumerableQueue[T]]) -> None:
            self.__updater = func
        
        super().__init__(_GetCountableList(l))

        self.__updater: IFunction[IReadOnlyCountableEnumerableQueue[T]] = _CountableEnumerableQueueUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()

    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableQueue[T]:
        return self.__updater.GetValue()
class CountableEnumerableStack[T](StackBase[T, ICountableDoublyLinkedList[T]], ICountableEnumerableStack[T], IGenericConstraintImplementation[ICountableDoublyLinkedList[T]]):
    def __init__(self, l: ICountableDoublyLinkedList[T]|None = None) -> None:
        def update(func: IFunction[IReadOnlyCountableEnumerableStack[T]]) -> None:
            self.__updater = func
        
        super().__init__(_GetCountableList(l))

        self.__updater: IFunction[IReadOnlyCountableEnumerableStack[T]] = _CountableEnumerableStackUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()

    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableStack[T]:
        return self.__updater.GetValue()