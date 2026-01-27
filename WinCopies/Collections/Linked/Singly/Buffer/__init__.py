from abc import abstractmethod
from collections.abc import Iterable
from typing import final

from WinCopies.Collections import Countable as CountableCollection
from WinCopies.Collections.Abstraction.Enumeration import Enumerable, Enumerator
from WinCopies.Collections.Enumeration import Enumerable as EnumerableCollection, IEnumerator
from WinCopies.Collections.Linked.Singly import IList, INodeCookie, ReadOnlyListBase, CountableCollectionAbstract, EnumerableQueueBase, EnumerableStackBase, SinglyLinkedNode
from WinCopies.Collections.Linked.Singly.Buffer.Base import IReadOnlyCountableBuffer, IReadOnlyEnumerableBuffer, ICountableBuffer, IEnumerableBuffer, IReadOnlyCountableBufferedQueue, IReadOnlyEnumerableBufferedQueue, IReadOnlyCountableBufferedStack, IReadOnlyEnumerableBufferedStack, IBufferedQueue, ICountableBufferedQueue, IEnumerableBufferedQueue, IBufferedStack, ICountableBufferedStack, IEnumerableBufferedStack, IBufferedList, IBufferedQueueList, IBufferCookie, IBufferedQueueCookie, BufferBase, AbstractBufferedQueue, AbstractBufferedStack, BufferedStack
from WinCopies.Collections.Linked.Singly.Buffer._Cookie import BufferedList, CookieBufferedQueue
from WinCopies.Typing import GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation
from WinCopies.Typing.Delegate import Method, IFunction, SelectionUpdater

class _IBufferedQueue[T](IBufferedQueue[T], IBufferedQueueList[T]):
    def __init__(self) -> None:
        super().__init__()
class _IBufferedStack[T](IBufferedStack[T], IBufferedList[T]):
    def __init__(self) -> None:
        super().__init__()

class _ReadOnlyCountableBuffer[T](ReadOnlyListBase[T, ICountableBuffer[T]], CountableCollection, IReadOnlyCountableBuffer[T], IGenericConstraintImplementation[ICountableBuffer[T]]):
    def __init__(self, items: ICountableBuffer[T]) -> None:
        super().__init__(items)
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()
    
    @final
    def Move(self) -> bool|None:
        return self._GetContainer().Move()

class _CountableBufferBase[TItem, TList](CountableCollectionAbstract[TItem, TList], BufferBase[TItem], ICountableBuffer[TItem], GenericSpecializedConstraint[TList, IList[TItem], IBufferedList[TItem]]):
    def __init__(self, *values: TItem) -> None:
        super().__init__(self._CreateBuffer(*values))
    
    @abstractmethod
    def _CreateBuffer(self, *values: TItem) -> TList:
        pass

    @final
    def _GetCookie(self) -> IBufferCookie[TItem]:
        return self._GetSpecializedContainer().GetCookie()
    
    @final
    def _GetFirstCookie(self) -> INodeCookie[TItem]|None:
        return self._GetCookie().GetFirst()
    @final
    def _SetFirst(self, node: INodeCookie[TItem]) -> None:
        self._GetCookie().SetFirst(node)
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableBuffer[TItem]:
        pass

@final
class _ReadOnlyCountableBufferedQueue[T](_ReadOnlyCountableBuffer[T], IReadOnlyCountableBufferedQueue[T]):
    def __init__(self, items: ICountableBuffer[T]) -> None:
        super().__init__(items)
@final
class _CountableBufferedQueueBuffer[T](CookieBufferedQueue[T], _IBufferedQueue[T]):
    def __init__(self, *values: T) -> None:
        def update(func: IFunction[IBufferCookie[T]]) -> None:
            self.__cookie = func
        def updateQueueCookie(func: IFunction[IBufferedQueueCookie[T]]) -> None:
            self.__queueCookie = func
        
        super().__init__(*values)
        
        self.__cookie: IFunction[IBufferCookie[T]] = self._CreateCookieUpdater(update) # type: ignore[no-redef]
        self.__queueCookie: IFunction[IBufferedQueueCookie[T]] = self._CreateQueueCookieUpdater(updateQueueCookie) # type: ignore[no-redef]

    @final
    def GetCookie(self) -> IBufferCookie[T]:
        return self.__cookie.GetValue()
    @final
    def GetQueueCookie(self) -> IBufferedQueueCookie[T]:
        return self.__queueCookie.GetValue()
@final
class _ReadOnlyCountableBufferedQueueUpdater[T](SelectionUpdater[ICountableBufferedQueue[T], IReadOnlyCountableBufferedQueue[T]]):
    def __init__(self, items: ICountableBufferedQueue[T], updater: Method[IFunction[IReadOnlyCountableBufferedQueue[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: ICountableBufferedQueue[T]) -> IReadOnlyCountableBufferedQueue[T]:
        return _ReadOnlyCountableBufferedQueue[T](container)

@final
class _ReadOnlyCountableBufferedStack[T](_ReadOnlyCountableBuffer[T], IReadOnlyCountableBufferedStack[T]):
    def __init__(self, items: ICountableBuffer[T]) -> None:
        super().__init__(items)
@final
class _CountableBufferedStackBuffer[T](BufferedStack[T], BufferedList[T], _IBufferedStack[T]):
    def __init__(self, *values: T) -> None:
        def update(func: IFunction[IBufferCookie[T]]) -> None:
            self.__cookie = func
        
        super().__init__(*values)
        
        self.__cookie: IFunction[IBufferCookie[T]] = self._CreateCookieUpdater(update) # type: ignore[no-redef]

    @final
    def GetCookie(self) -> IBufferCookie[T]:
        return self.__cookie.GetValue()
@final
class _ReadOnlyCountableBufferedStackUpdater[T](SelectionUpdater[ICountableBufferedStack[T], IReadOnlyCountableBufferedStack[T]]):
    def __init__(self, items: ICountableBufferedStack[T], updater: Method[IFunction[IReadOnlyCountableBufferedStack[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: ICountableBufferedStack[T]) -> IReadOnlyCountableBufferedStack[T]:
        return _ReadOnlyCountableBufferedStack[T](container)

class CountableBufferedQueue[T](_CountableBufferBase[T, IBufferedQueueList[T]], AbstractBufferedQueue[T], ICountableBufferedQueue[T], IGenericSpecializedConstraintImplementation[IList[T], IBufferedQueueList[T]]):
    def __init__(self, *values: T) -> None:
        def update(func: IFunction[IReadOnlyCountableBufferedQueue[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(*values)

        self.__readOnly: IFunction[IReadOnlyCountableBufferedQueue[T]] = _ReadOnlyCountableBufferedQueueUpdater[T](self, update) # type: ignore[no-redef]
    
    def _CreateBuffer(self, *values: T) -> _IBufferedQueue[T]:
        return _CountableBufferedQueueBuffer[T](*values)
    
    @final
    def _GetQueueCookie(self) -> IBufferedQueueCookie[T]:
        return self._GetContainer().GetQueueCookie()
    
    @final
    def _GetLast(self) -> SinglyLinkedNode[T]|None:
        return self._GetQueueCookie().GetLast()
    @final
    def _SetLast(self, node: SinglyLinkedNode[T]) -> None:
        self._GetQueueCookie().SetLast(node)
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableBufferedQueue[T]:
        return self.__readOnly.GetValue()
class CountableBufferedStack[T](_CountableBufferBase[T, IBufferedList[T]], AbstractBufferedStack[T], ICountableBufferedStack[T], IGenericSpecializedConstraintImplementation[IList[T], IBufferedList[T]]):
    def __init__(self, *values: T) -> None:
        def update(func: IFunction[IReadOnlyCountableBufferedStack[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(*values)

        self.__readOnly: IFunction[IReadOnlyCountableBufferedStack[T]] = _ReadOnlyCountableBufferedStackUpdater[T](self, update) # type: ignore[no-redef]
    
    def _CreateBuffer(self, *values: T) -> _IBufferedStack[T]:
        return _CountableBufferedStackBuffer[T](*values)
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableBufferedStack[T]:
        return self.__readOnly.GetValue()

@final
class _IterableEnumerableBufferUpdater[T](SelectionUpdater[IReadOnlyEnumerableBuffer[T], Iterable[T]]):
    def __init__(self, value: IReadOnlyEnumerableBuffer[T], updater: Method[IFunction[Iterable[T]]]) -> None:
        super().__init__(value, updater)
    
    def _AsContainer(self, container: IReadOnlyEnumerableBuffer[T]) -> Iterable[T]:
        return Enumerable[T].Create(container)

class ReadOnlyEnumerableBuffer[T](ReadOnlyListBase[T, IEnumerableBuffer[T]], IReadOnlyEnumerableBuffer[T], IGenericConstraintImplementation[IEnumerableBuffer[T]]):
    def __init__(self, items: IEnumerableBuffer[T]) -> None:
        def update(func: IFunction[Iterable[T]]) -> None:
            self.__iterable = func
        
        super().__init__(items)

        self.__iterable: IFunction[Iterable[T]] = _IterableEnumerableBufferUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def Move(self) -> bool|None:
        return self._GetContainer().Move()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
    
    @final
    def AsIterable(self) -> Iterable[T]:
        return self.__iterable.GetValue()

class EnumerableBuffer[T](EnumerableCollection[T], BufferBase[T], IEnumerableBuffer[T]):
    def __init__(self) -> None:
        super().__init__()

@final
class _ReadOnlyEnumerableBufferedQueue[T](ReadOnlyEnumerableBuffer[T], IReadOnlyEnumerableBufferedQueue[T]):
    def __init__(self, items: IEnumerableBufferedQueue[T]) -> None:
        super().__init__(items)
@final
class _ReadOnlyEnumerableBufferedQueueUpdater[T](SelectionUpdater[IEnumerableBufferedQueue[T], IReadOnlyEnumerableBufferedQueue[T]]):
    def __init__(self, items: IEnumerableBufferedQueue[T], updater: Method[IFunction[IReadOnlyEnumerableBufferedQueue[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: IEnumerableBufferedQueue[T]) -> IReadOnlyEnumerableBufferedQueue[T]:
        return _ReadOnlyEnumerableBufferedQueue[T](container)

@final
class _ReadOnlyEnumerableBufferedStack[T](ReadOnlyEnumerableBuffer[T], IReadOnlyEnumerableBufferedStack[T]):
    def __init__(self, items: IEnumerableBufferedStack[T]) -> None:
        super().__init__(items)
@final
class _ReadOnlyEnumerableBufferedStackUpdater[T](SelectionUpdater[IEnumerableBufferedStack[T], IReadOnlyEnumerableBufferedStack[T]]):
    def __init__(self, items: IEnumerableBufferedStack[T], updater: Method[IFunction[IReadOnlyEnumerableBufferedStack[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: IEnumerableBufferedStack[T]) -> IReadOnlyEnumerableBufferedStack[T]:
        return _ReadOnlyEnumerableBufferedStack[T](container)

class EnumerableBufferedQueue[T](EnumerableQueueBase[T], EnumerableBuffer[T], AbstractBufferedQueue[T], IEnumerableBufferedQueue[T]):
    def __init__(self, *values: T) -> None:
        def update(func: IFunction[IReadOnlyEnumerableBufferedQueue[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(*values)

        self.__readOnly: IFunction[IReadOnlyEnumerableBufferedQueue[T]] = _ReadOnlyEnumerableBufferedQueueUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableBufferedQueue[T]:
        return self.__readOnly.GetValue()
class EnumerableBufferedStack[T](EnumerableStackBase[T], EnumerableBuffer[T], AbstractBufferedStack[T], IEnumerableBufferedStack[T]):
    def __init__(self, *values: T) -> None:
        def update(func: IFunction[IReadOnlyEnumerableBufferedStack[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(*values)

        self.__readOnly: IFunction[IReadOnlyEnumerableBufferedStack[T]] = _ReadOnlyEnumerableBufferedStackUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableBufferedStack[T]:
        return self.__readOnly.GetValue()