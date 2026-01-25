from __future__ import annotations

from typing import final

from WinCopies import Abstract
from WinCopies.Collections.Linked.Singly import SinglyLinkedNode, INodeCookie
from WinCopies.Collections.Linked.Singly.Buffer.Base import IBufferedList, IBufferedQueueList, IBufferCookie, IBufferedQueueCookie, Buffer, BufferedQueue
from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater

class BufferedList[T](Buffer[T], IBufferedList[T]):
    @final
    class _Cookie[_T](IBufferCookie[_T]):
        def __init__(self, buffer: BufferedList[_T]) -> None:
            super().__init__()

            self.__buffer: BufferedList[_T] = buffer

        def GetFirst(self) -> INodeCookie[_T]|None:
            return self.__buffer._GetFirstNode()
        def SetFirst(self, node: INodeCookie[_T]) -> None:
            self.__buffer._SetFirstNode(node)
    
    @final
    class __Updater[_T](ValueFunctionUpdater[IBufferCookie[_T]]):
        def __init__(self, buffer: BufferedList[_T], updater: Method[IFunction[IBufferCookie[_T]]]) -> None:
            super().__init__(updater)

            self.__buffer: BufferedList[_T] = buffer
        
        def _GetValue(self) -> IBufferCookie[_T]:
            return BufferedList._Cookie(self.__buffer)
    
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _CreateCookieUpdater(self, updater: Method[IFunction[IBufferCookie[T]]]) -> ValueFunctionUpdater[IBufferCookie[T]]:
        return BufferedList[T].__Updater(self, updater)
    
    @final
    def _GetFirstNode(self) -> INodeCookie[T]|None:
        return self._GetFirstCookie()
    @final
    def _SetFirstNode(self, node: INodeCookie[T]) -> None:
        self._SetFirst(node)

class CookieBufferedQueue[T](BufferedQueue[T], BufferedList[T], IBufferedQueueList[T]):
    @final
    class _QueueCookie[_T](Abstract, IBufferedQueueCookie[_T]):
        def __init__(self, buffer: CookieBufferedQueue[_T]) -> None:
            super().__init__()

            self.__buffer: CookieBufferedQueue[_T] = buffer

        def GetLast(self) -> SinglyLinkedNode[_T]|None:
            return self.__buffer._GetLastNode()
        def SetLast(self, node: SinglyLinkedNode[_T]) -> None:
            self.__buffer._SetLastNode(node)
    
    @final
    class __Updater[_T](ValueFunctionUpdater[IBufferedQueueCookie[_T]]):
        def __init__(self, buffer: CookieBufferedQueue[_T], updater: Method[IFunction[IBufferedQueueCookie[_T]]]) -> None:
            super().__init__(updater)

            self.__buffer: CookieBufferedQueue[_T] = buffer
        
        def _GetValue(self) -> IBufferedQueueCookie[_T]:
            return CookieBufferedQueue._QueueCookie(self.__buffer)
    
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _CreateQueueCookieUpdater(self, updater: Method[IFunction[IBufferedQueueCookie[T]]]) -> ValueFunctionUpdater[IBufferedQueueCookie[T]]:
        return CookieBufferedQueue[T].__Updater(self, updater)
    
    @final
    def _SetLastNode(self, node: SinglyLinkedNode[T]) -> None:
        self._SetLast(node)
    @final
    def _GetLastNode(self) -> SinglyLinkedNode[T]|None:
        return self._GetLast()