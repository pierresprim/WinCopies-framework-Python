from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import final, Callable

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Abstraction.Enumeration import CreateEnumerable, TryCreateEnumerator
from WinCopies.Collections.Core import Countable as CountableCollection
from WinCopies.Collections.Enumeration import IEnumerator, Enumerable as EnumerableCollection, CountableEnumerable as CountableEnumerableCollectionBase
from WinCopies.Collections.Linked.Enumeration import TryGetValueEnumeratorFromNode
from WinCopies.Collections.Linked.Singly import IReadOnlyList, IReadOnlyCountableList, IReadOnlyEnumerableList, IReadOnlyCountableEnumerableList, IList, ICountableList, IEnumerableList, ICountableEnumerableList, IReadOnlyQueue, IReadOnlyCountableQueue, IReadOnlyEnumerableQueue, IReadOnlyCountableEnumerableQueue, IReadOnlyStack, IReadOnlyCountableStack, IReadOnlyEnumerableStack, IReadOnlyCountableEnumerableStack, IQueue, ICountableQueue, IEnumerableQueue, ICountableEnumerableQueue, IStack, ICountableStack, IEnumerableStack, ICountableEnumerableStack, INodeCookie, ReadOnlyListBase, AbstractList, CountableCollectionAbstract, CountableEnumerableBase, CountableEnumerableList, AbstractQueue, QueueBase, EnumerableQueueBase, EnumerableStackBase, StackBase, SinglyLinkedNode
from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater, SelectionUpdater
from WinCopies.Typing.Generic import GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation

class IBufferBase(IInterface):
    def __init__(self) -> None:
        pass
    
    @abstractmethod
    def Move(self) -> bool|None:
        pass

class IReadOnlyBuffer[T](IReadOnlyList[T], IBufferBase):
    def __init__(self) -> None:
        super().__init__()
class IBuffer[T](IList[T], IBufferBase):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyBuffer[T]:
        pass

class IBufferCookie[T](IInterface):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def GetFirst(self) -> INodeCookie[T]|None:
        pass
    @abstractmethod
    def SetFirst(self, node: INodeCookie[T]) -> None:
        pass

class IBufferedList[T](IBuffer[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetCookie(self) -> IBufferCookie[T]:
        pass

class IReadOnlyCountableBuffer[T](IReadOnlyBuffer[T], IReadOnlyCountableList[T]):
    def __init__(self) -> None:
        super().__init__()
class ICountableBuffer[T](IBuffer[T], ICountableList[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableBuffer[T]:
        pass

class IReadOnlyEnumerableBuffer[T](IReadOnlyBuffer[T], IReadOnlyEnumerableList[T]):
    def __init__(self) -> None:
        super().__init__()
class IEnumerableBuffer[T](IBuffer[T], IEnumerableList[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyEnumerableBuffer[T]:
        pass

class IReadOnlyCountableEnumerableBuffer[T](IReadOnlyCountableBuffer[T], IReadOnlyEnumerableBuffer[T], IReadOnlyCountableEnumerableList[T]):
    def __init__(self) -> None:
        super().__init__()
class ICountableEnumerableBuffer[T](ICountableBuffer[T], IEnumerableBuffer[T], ICountableEnumerableList[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableBuffer[T]:
        pass

class IReadOnlyBufferedQueue[T](IReadOnlyBuffer[T], IReadOnlyQueue[T]):
    def __init__(self) -> None:
        super().__init__()
class IReadOnlyBufferedStack[T](IReadOnlyBuffer[T], IReadOnlyStack[T]):
    def __init__(self) -> None:
        super().__init__()

class IReadOnlyCountableBufferedQueue[T](IReadOnlyCountableBuffer[T], IReadOnlyBufferedQueue[T], IReadOnlyCountableQueue[T]):
    def __init__(self) -> None:
        super().__init__()
class IReadOnlyCountableBufferedStack[T](IReadOnlyCountableBuffer[T], IReadOnlyBufferedStack[T], IReadOnlyCountableStack[T]):
    def __init__(self) -> None:
        super().__init__()

class IReadOnlyEnumerableBufferedQueue[T](IReadOnlyEnumerableBuffer[T], IReadOnlyBufferedQueue[T], IReadOnlyEnumerableQueue[T]):
    def __init__(self) -> None:
        super().__init__()
class IReadOnlyEnumerableBufferedStack[T](IReadOnlyEnumerableBuffer[T], IReadOnlyBufferedStack[T], IReadOnlyEnumerableStack[T]):
    def __init__(self) -> None:
        super().__init__()

class IReadOnlyCountableEnumerableBufferedQueue[T](IReadOnlyCountableEnumerableBuffer[T], IReadOnlyCountableBufferedQueue[T], IReadOnlyEnumerableBufferedQueue[T], IReadOnlyCountableEnumerableQueue[T]):
    def __init__(self) -> None:
        super().__init__()
class IReadOnlyCountableEnumerableBufferedStack[T](IReadOnlyCountableEnumerableBuffer[T], IReadOnlyCountableBufferedStack[T], IReadOnlyEnumerableBufferedStack[T], IReadOnlyCountableEnumerableStack[T]):
    def __init__(self) -> None:
        super().__init__()

class IBufferedQueue[T](IBuffer[T], IQueue[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyBufferedQueue[T]:
        pass
class IBufferedStack[T](IBuffer[T], IStack[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyBufferedStack[T]:
        pass

class ICountableBufferedQueue[T](ICountableBuffer[T], IBufferedQueue[T], ICountableQueue[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableBufferedQueue[T]:
        pass
class ICountableBufferedStack[T](ICountableBuffer[T], IBufferedStack[T], ICountableStack[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableBufferedStack[T]:
        pass

class IEnumerableBufferedQueue[T](IEnumerableBuffer[T], IBufferedQueue[T], IEnumerableQueue[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyEnumerableBufferedQueue[T]:
        pass
class IEnumerableBufferedStack[T](IEnumerableBuffer[T], IBufferedStack[T], IEnumerableStack[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyEnumerableBufferedStack[T]:
        pass

class ICountableEnumerableBufferedQueue[T](ICountableEnumerableBuffer[T], ICountableBufferedQueue[T], IEnumerableBufferedQueue[T], ICountableEnumerableQueue[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableBufferedQueue[T]:
        pass
class ICountableEnumerableBufferedStack[T](ICountableEnumerableBuffer[T], ICountableBufferedStack[T], IEnumerableBufferedStack[T], ICountableEnumerableStack[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableBufferedStack[T]:
        pass

class AbstractBuffer[T](AbstractList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _OnSetFirst(self, first: INodeCookie[T], last: SinglyLinkedNode[T]) -> None:
        pass

class ReadOnlyBuffer[T](ReadOnlyListBase[T, IBuffer[T]], IReadOnlyBuffer[T], IGenericConstraintImplementation[IBuffer[T]]):
    def __init__(self, items: IBuffer[T]) -> None:
        super().__init__(items)
    
    @final
    def Move(self) -> bool|None:
        return self._GetContainer().Move()

class BufferBase[T](AbstractBuffer[T], IBufferBase):
    def __init__(self) -> None:
        super().__init__()

    @final
    def _IsFirstAlsoLast(self) -> tuple[INodeCookie[T], INodeCookie[T]|None]|None:
        first: INodeCookie[T]|None = self._GetFirstCookie()

        if first is None:
            return None
        
        next: INodeCookie[T]|None = first.GetNext()

        return (first, next)
    
    @final
    def Move(self) -> bool|None:
        result: tuple[INodeCookie[T], INodeCookie[T]|None]|None = self._IsFirstAlsoLast()

        if result is None:
            return None
        
        if result[1] is None:
            return False
        
        self._OnSetFirst(result[1], result[0].GetNode())
        
        return True

class Buffer[T](BufferBase[T], IBuffer[T]):
    def __init__(self) -> None:
        super().__init__()

class AbstractBufferedQueue[T](AbstractBuffer[T], AbstractQueue[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def _OnSetFirst(self, first: INodeCookie[T], last: SinglyLinkedNode[T]) -> None:
        self._SetFirst(first)
        self._SetLast(last)
class AbstractBufferedStack[T](AbstractBuffer[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def _OnSetFirst(self, first: INodeCookie[T], last: SinglyLinkedNode[T]) -> None:
        self._SetFirst(first)

@final
class _ReadOnlyBufferedQueue[T](ReadOnlyBuffer[T], IReadOnlyBufferedQueue[T]):
    def __init__(self, items: IBuffer[T]) -> None:
        super().__init__(items)
@final
class _ReadOnlyBufferedQueueUpdater[T](SelectionUpdater[IBufferedQueue[T], IReadOnlyBufferedQueue[T]]):
    def __init__(self, items: IBufferedQueue[T], updater: Method[IFunction[IReadOnlyBufferedQueue[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: IBufferedQueue[T]) -> IReadOnlyBufferedQueue[T]:
        return _ReadOnlyBufferedQueue[T](container)

@final
class _ReadOnlyBufferedStack[T](ReadOnlyBuffer[T], IReadOnlyBufferedStack[T]):
    def __init__(self, items: IBuffer[T]) -> None:
        super().__init__(items)
@final
class _ReadOnlyBufferedStackUpdater[T](SelectionUpdater[IBufferedStack[T], IReadOnlyBufferedStack[T]]):
    def __init__(self, items: IBufferedStack[T], updater: Method[IFunction[IReadOnlyBufferedStack[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: IBufferedStack[T]) -> IReadOnlyBufferedStack[T]:
        return _ReadOnlyBufferedStack[T](container)

class BufferedQueue[T](QueueBase[T], Buffer[T], AbstractBufferedQueue[T], IBufferedQueue[T]):
    def __init__(self, values: Iterable[T]) -> None:
        def update(func: IFunction[IReadOnlyBufferedQueue[T]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__first: INodeCookie[T]|None = None
        self.__last: SinglyLinkedNode[T]|None = None

        self.__readOnly: IFunction[IReadOnlyBufferedQueue[T]] = _ReadOnlyBufferedQueueUpdater[T](self, update) # type: ignore[no-redef]
        self.__updater: Callable[[INodeCookie[T], INodeCookie[T]], None] = self._GetUpdater()

        self.PushItems(values)
    
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
    
    def AsReadOnly(self) -> IReadOnlyBufferedQueue[T]:
        return self.__readOnly.GetValue()
class BufferedStack[T](StackBase[T], Buffer[T], AbstractBufferedStack[T], IBufferedStack[T]):
    def __init__(self, values: Iterable[T]) -> None:
        def update(func: IFunction[IReadOnlyBufferedStack[T]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__first: INodeCookie[T]|None = None
        self.__readOnly: IFunction[IReadOnlyBufferedStack[T]] = _ReadOnlyBufferedStackUpdater[T](self, update) # type: ignore[no-redef]

        self.PushItems(values)
    
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
    def AsReadOnly(self) -> IReadOnlyBufferedStack[T]:
        return self.__readOnly.GetValue()

class IBufferedQueueCookie[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetLast(self) -> SinglyLinkedNode[T]|None:
        pass
    @abstractmethod
    def SetLast(self, node: SinglyLinkedNode[T]) -> None:
        pass

class IBufferedQueueList[T](IBufferedList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetQueueCookie(self) -> IBufferedQueueCookie[T]:
        pass

class _BufferedList[T](Buffer[T], IBufferedList[T]):
    @final
    class _Cookie[_T](IBufferCookie[_T]):
        def __init__(self, buffer: _BufferedList[_T]) -> None:
            super().__init__()

            self.__buffer: _BufferedList[_T] = buffer

        def GetFirst(self) -> INodeCookie[_T]|None:
            return self.__buffer._GetFirstNode()
        def SetFirst(self, node: INodeCookie[_T]) -> None:
            self.__buffer._SetFirstNode(node)
    
    @final
    class __Updater[_T](ValueFunctionUpdater[IBufferCookie[_T]]):
        def __init__(self, buffer: _BufferedList[_T], updater: Method[IFunction[IBufferCookie[_T]]]) -> None:
            super().__init__(updater)

            self.__buffer: _BufferedList[_T] = buffer
        
        def _GetValue(self) -> IBufferCookie[_T]:
            return _BufferedList._Cookie(self.__buffer)
    
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _CreateCookieUpdater(self, updater: Method[IFunction[IBufferCookie[T]]]) -> ValueFunctionUpdater[IBufferCookie[T]]:
        return _BufferedList[T].__Updater(self, updater)
    
    @final
    def _GetFirstNode(self) -> INodeCookie[T]|None:
        return self._GetFirstCookie()
    @final
    def _SetFirstNode(self, node: INodeCookie[T]) -> None:
        self._SetFirst(node)

class _CookieBufferedQueue[T](BufferedQueue[T], _BufferedList[T], IBufferedQueueList[T]):
    @final
    class _QueueCookie[_T](Abstract, IBufferedQueueCookie[_T]):
        def __init__(self, buffer: _CookieBufferedQueue[_T]) -> None:
            super().__init__()

            self.__buffer: _CookieBufferedQueue[_T] = buffer

        def GetLast(self) -> SinglyLinkedNode[_T]|None:
            return self.__buffer._GetLastNode()
        def SetLast(self, node: SinglyLinkedNode[_T]) -> None:
            self.__buffer._SetLastNode(node)
    
    @final
    class __Updater[_T](ValueFunctionUpdater[IBufferedQueueCookie[_T]]):
        def __init__(self, buffer: _CookieBufferedQueue[_T], updater: Method[IFunction[IBufferedQueueCookie[_T]]]) -> None:
            super().__init__(updater)

            self.__buffer: _CookieBufferedQueue[_T] = buffer
        
        def _GetValue(self) -> IBufferedQueueCookie[_T]:
            return _CookieBufferedQueue._QueueCookie(self.__buffer)
    
    def __init__(self, values: Iterable[T]) -> None:
        super().__init__(values)
    
    @final
    def _CreateQueueCookieUpdater(self, updater: Method[IFunction[IBufferedQueueCookie[T]]]) -> ValueFunctionUpdater[IBufferedQueueCookie[T]]:
        return _CookieBufferedQueue[T].__Updater(self, updater)
    
    @final
    def _SetLastNode(self, node: SinglyLinkedNode[T]) -> None:
        self._SetLast(node)
    @final
    def _GetLastNode(self) -> SinglyLinkedNode[T]|None:
        return self._GetLast()

class _IBufferedQueue[T](IBufferedQueue[T], IBufferedQueueList[T]):
    def __init__(self) -> None:
        super().__init__()
class _IBufferedStack[T](IBufferedStack[T], IBufferedList[T]):
    def __init__(self) -> None:
        super().__init__()

class ReadOnlyCountableBufferBase[TItem, TList](ReadOnlyListBase[TItem, TList], IReadOnlyCountableBuffer[TItem], GenericSpecializedConstraint[TList, ICountableList[TItem], ICountableBuffer[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__(items)
    
    @final
    def GetCount(self) -> int:
        return self._GetSpecializedContainer().GetCount()
    
    @final
    def Move(self) -> bool|None:
        return self._GetSpecializedContainer().Move()
class ReadOnlyCountableBuffer[T](ReadOnlyCountableBufferBase[T, ICountableBuffer[T]], CountableCollection, IGenericConstraintImplementation[ICountableBuffer[T]]):
    def __init__(self, items: ICountableBuffer[T]) -> None:
        super().__init__(items)
    
    @final
    def _AsSpecialized(self, container: ICountableBuffer[T]) -> ICountableBuffer[T]:
        return container
class ReadOnlyCountableEnumerableBuffer[T](ReadOnlyCountableBufferBase[T, ICountableEnumerableBuffer[T]], CountableEnumerableCollectionBase[T], IReadOnlyCountableEnumerableBuffer[T], IGenericConstraintImplementation[ICountableEnumerableBuffer[T]]):
    def __init__(self, items: ICountableEnumerableBuffer[T]) -> None:
        super().__init__(items)
    
    @final
    def _AsSpecialized(self, container: ICountableEnumerableBuffer[T]) -> ICountableBuffer[T]:
        return container
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return TryCreateEnumerator(self._GetContainer().TryGetEnumerator())

class _CountableBufferBase[TItem, TList](CountableCollectionAbstract[TItem, TList], BufferBase[TItem], ICountableBuffer[TItem], GenericSpecializedConstraint[TList, IList[TItem], IBufferedList[TItem]]):
    def __init__(self, values: Iterable[TItem]) -> None:
        super().__init__(self._CreateBuffer(values))
    
    @abstractmethod
    def _CreateBuffer(self, values: Iterable[TItem]) -> TList:
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
class _ReadOnlyCountableBufferedQueue[T](ReadOnlyCountableBuffer[T], IReadOnlyCountableBufferedQueue[T]):
    def __init__(self, items: ICountableBuffer[T]) -> None:
        super().__init__(items)
@final
class _CountableBufferedQueueBuffer[T](_CookieBufferedQueue[T], _IBufferedQueue[T]):
    def __init__(self, values: Iterable[T]) -> None:
        def update(func: IFunction[IBufferCookie[T]]) -> None:
            self.__cookie = func
        def updateQueueCookie(func: IFunction[IBufferedQueueCookie[T]]) -> None:
            self.__queueCookie = func
        
        super().__init__(values)
        
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
class _ReadOnlyCountableBufferedStack[T](ReadOnlyCountableBuffer[T], IReadOnlyCountableBufferedStack[T]):
    def __init__(self, items: ICountableBuffer[T]) -> None:
        super().__init__(items)
@final
class _CountableBufferedStackBuffer[T](BufferedStack[T], _BufferedList[T], _IBufferedStack[T]):
    def __init__(self, values: Iterable[T]) -> None:
        def update(func: IFunction[IBufferCookie[T]]) -> None:
            self.__cookie = func
        
        super().__init__(values)
        
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
    def __init__(self, values: Iterable[T]) -> None:
        def update(func: IFunction[IReadOnlyCountableBufferedQueue[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(values)

        self.__readOnly: IFunction[IReadOnlyCountableBufferedQueue[T]] = _ReadOnlyCountableBufferedQueueUpdater[T](self, update) # type: ignore[no-redef]
    
    def _CreateBuffer(self, values: Iterable[T]) -> _IBufferedQueue[T]:
        return _CountableBufferedQueueBuffer[T](values)
    
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
    def __init__(self, values: Iterable[T]) -> None:
        def update(func: IFunction[IReadOnlyCountableBufferedStack[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(values)

        self.__readOnly: IFunction[IReadOnlyCountableBufferedStack[T]] = _ReadOnlyCountableBufferedStackUpdater[T](self, update) # type: ignore[no-redef]
    
    def _CreateBuffer(self, values: Iterable[T]) -> _IBufferedStack[T]:
        return _CountableBufferedStackBuffer[T](values)
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableBufferedStack[T]:
        return self.__readOnly.GetValue()

@final
class _IterableEnumerableBufferUpdater[T](SelectionUpdater[IReadOnlyEnumerableBuffer[T], Iterable[T]]):
    def __init__(self, value: IReadOnlyEnumerableBuffer[T], updater: Method[IFunction[Iterable[T]]]) -> None:
        super().__init__(value, updater)
    
    def _AsContainer(self, container: IReadOnlyEnumerableBuffer[T]) -> Iterable[T]:
        return CreateEnumerable(container)

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
        return TryCreateEnumerator(self._GetContainer().TryGetEnumerator())
    
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

class EnumerableBufferAbstract[T](EnumerableBuffer[T], AbstractBuffer[T], IEnumerableBuffer[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return TryGetValueEnumeratorFromNode(self._GetFirst())

class EnumerableBufferedQueue[T](EnumerableQueueBase[T], EnumerableBufferAbstract[T], AbstractBufferedQueue[T], IEnumerableBufferedQueue[T]):
    def __init__(self, values: Iterable[T]) -> None:
        def update(func: IFunction[IReadOnlyEnumerableBufferedQueue[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(values)

        self.__readOnly: IFunction[IReadOnlyEnumerableBufferedQueue[T]] = _ReadOnlyEnumerableBufferedQueueUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableBufferedQueue[T]:
        return self.__readOnly.GetValue()
class EnumerableBufferedStack[T](EnumerableStackBase[T], EnumerableBufferAbstract[T], AbstractBufferedStack[T], IEnumerableBufferedStack[T]):
    def __init__(self, values: Iterable[T]) -> None:
        def update(func: IFunction[IReadOnlyEnumerableBufferedStack[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(values)

        self.__readOnly: IFunction[IReadOnlyEnumerableBufferedStack[T]] = _ReadOnlyEnumerableBufferedStackUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableBufferedStack[T]:
        return self.__readOnly.GetValue()

@final
class _ReadOnlyCountableEnumerableBufferedQueue[T](ReadOnlyCountableEnumerableBuffer[T], IReadOnlyCountableEnumerableBufferedQueue[T]):
    def __init__(self, l: ICountableEnumerableBufferedQueue[T]) -> None:
        super().__init__(l)
@final
class _ReadOnlyCountableEnumerableBufferedQueueUpdater[T](SelectionUpdater[ICountableEnumerableBufferedQueue[T], IReadOnlyCountableEnumerableBufferedQueue[T]]):
    def __init__(self, items: ICountableEnumerableBufferedQueue[T], updater: Method[IFunction[IReadOnlyCountableEnumerableBufferedQueue[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: ICountableEnumerableBufferedQueue[T]) -> IReadOnlyCountableEnumerableBufferedQueue[T]:
        return _ReadOnlyCountableEnumerableBufferedQueue[T](container)

@final
class _ReadOnlyCountableEnumerableBufferedStack[T](ReadOnlyCountableEnumerableBuffer[T], IReadOnlyCountableEnumerableBufferedStack[T]):
    def __init__(self, l: ICountableEnumerableBufferedStack[T]) -> None:
        super().__init__(l)
@final
class _ReadOnlyCountableEnumerableBufferedStackUpdater[T](SelectionUpdater[ICountableEnumerableBufferedStack[T], IReadOnlyCountableEnumerableBufferedStack[T]]):
    def __init__(self, items: ICountableEnumerableBufferedStack[T], updater: Method[IFunction[IReadOnlyCountableEnumerableBufferedStack[T]]]) -> None:
        super().__init__(items, updater)
    
    def _AsContainer(self, container: ICountableEnumerableBufferedStack[T]) -> IReadOnlyCountableEnumerableBufferedStack[T]:
        return _ReadOnlyCountableEnumerableBufferedStack[T](container)

class CountableEnumerableBufferAbstract[TItem, TList](CountableEnumerableBase[TItem, TList], ICountableEnumerableBuffer[TItem], GenericSpecializedConstraint[TList, IEnumerableList[TItem], IEnumerableBuffer[TItem]]):
    def __init__(self, l: TList) -> None:
        super().__init__(l)
class CountableEnumerableBufferBase[T](CountableEnumerableBufferAbstract[T, IEnumerableBuffer[T]], IGenericSpecializedConstraintImplementation[IEnumerableList[T], IEnumerableBuffer[T]]):
    def __init__(self, l: IEnumerableBuffer[T]) -> None:
        super().__init__(l)
    
    @final
    def Move(self) -> bool|None:
        return self._GetSpecializedContainer().Move()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self._GetContainer().TryGetEnumerator()

class CountableEnumerableBufferedQueueAbstract[T](CountableEnumerableBufferBase[T], IBufferedQueue[T]):
    def __init__(self, values: Iterable[T]) -> None:
        super().__init__(EnumerableBufferedQueue[T](values))
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableBufferedQueue[T]:
        pass
class CountableEnumerableBufferedStackAbstract[T](CountableEnumerableBufferBase[T], IBufferedStack[T]):
    def __init__(self, values: Iterable[T]) -> None:
        super().__init__(EnumerableBufferedStack[T](values))
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableBufferedStack[T]:
        pass

class _CountableEnumerableBufferedQueue[T](CountableEnumerableBufferedQueueAbstract[T]):
    def __init__(self, items: CountableEnumerableBufferedQueue[T], values: Iterable[T]) -> None:
        def update(func: IFunction[IReadOnlyCountableEnumerableBufferedQueue[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(values)

        self.__readOnly: IFunction[IReadOnlyCountableEnumerableBufferedQueue[T]] = _ReadOnlyCountableEnumerableBufferedQueueUpdater[T](items, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableBufferedQueue[T]:
        return self.__readOnly.GetValue()
class _CountableEnumerableBufferedStack[T](CountableEnumerableBufferedStackAbstract[T]):
    def __init__(self, items: CountableEnumerableBufferedStack[T], values: Iterable[T]) -> None:
        def update(func: IFunction[IReadOnlyCountableEnumerableBufferedStack[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(values)

        self.__readOnly: IFunction[IReadOnlyCountableEnumerableBufferedStack[T]] = _ReadOnlyCountableEnumerableBufferedStackUpdater[T](items, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableBufferedStack[T]:
        return self.__readOnly.GetValue()

class CountableEnumerableBuffer[TItem, TList](CountableEnumerableList[TItem, TList], ICountableEnumerableBuffer[TItem], GenericSpecializedConstraint[TList, ICountableEnumerableList[TItem], ICountableEnumerableBuffer[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__(items)

class CountableEnumerableBufferedQueue[T](CountableEnumerableBuffer[T, CountableEnumerableBufferedQueueAbstract[T]], ICountableEnumerableBufferedQueue[T], IGenericSpecializedConstraintImplementation[ICountableBuffer[T], CountableEnumerableBufferedQueueAbstract[T]]):
    def __init__(self, values: Iterable[T]) -> None:
        super().__init__(_CountableEnumerableBufferedQueue[T](self, values))
    
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableBufferedQueue[T]:
        return self._GetContainer().AsReadOnly()
    
    @final
    def Move(self) -> bool|None:
        return self._GetContainer().Move()
class CountableEnumerableBufferedStack[T](CountableEnumerableBuffer[T, CountableEnumerableBufferedStackAbstract[T]], ICountableEnumerableBufferedStack[T], IGenericSpecializedConstraintImplementation[ICountableBuffer[T], CountableEnumerableBufferedStackAbstract[T]]):
    def __init__(self, values: Iterable[T]) -> None:
        super().__init__(_CountableEnumerableBufferedStack[T](self, values))
    
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableBufferedStack[T]:
        return self._GetContainer().AsReadOnly()
    
    @final
    def Move(self) -> bool|None:
        return self._GetContainer().Move()