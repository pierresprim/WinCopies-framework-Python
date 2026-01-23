from abc import abstractmethod
from typing import final, Callable

from WinCopies import IInterface
from WinCopies.Collections.Linked.Singly.Base import IReadOnlyList, IReadOnlyCountableList, IReadOnlyEnumerableList, IReadOnlyCountableEnumerableList, IList, ICountableList, IEnumerableList, ICountableEnumerableList
from WinCopies.Collections.Linked.Singly import IReadOnlyQueue, IReadOnlyCountableQueue, IReadOnlyEnumerableQueue, IReadOnlyCountableEnumerableQueue, IReadOnlyStack, IReadOnlyCountableStack, IReadOnlyEnumerableStack, IReadOnlyCountableEnumerableStack, IQueue, ICountableQueue, IEnumerableQueue, ICountableEnumerableQueue, IStack, ICountableStack, IEnumerableStack, ICountableEnumerableStack, ReadOnlyListBase, AbstractList, AbstractQueue, QueueBase, StackBase, SinglyLinkedNode, INodeCookie
from WinCopies.Typing import IGenericConstraintImplementation
from WinCopies.Typing.Delegate import Method, IFunction, SelectionUpdater

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
    def __init__(self, *values: T) -> None:
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
    def __init__(self, *values: T) -> None:
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

class IBufferCookie[T](IInterface):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def GetFirst(self) -> INodeCookie[T]|None:
        pass
    @abstractmethod
    def SetFirst(self, node: INodeCookie[T]) -> None:
        pass

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