from abc import ABC, abstractmethod
from typing import final, Self

from WinCopies.Collections import Generator
from WinCopies.Collections.Enumeration import Enumerator
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Linked.Node import ILinkedListNode

from WinCopies.Typing.Delegate import Function

class NodeEnumeratorBase[TNode: ILinkedListNode[TItems], TItems](Enumerator[TNode]):
    def __init__(self, node: ILinkedListNode[TItems]):
        super().__init__()

        self.__first: ILinkedListNode[TItems] = node
        self.__moveNextFunc: Function[bool]|None = None
    
    @final
    def IsResetSupported(self) -> bool:
        return True
    
    def __MoveNext(self) -> bool:
        self._SetCurrent(self.__first)

        def moveNext() -> bool:
            node: ILinkedListNode[TItems] = self.GetCurrent().GetNextNode()

            if node is None:
                return False
            
            self._SetCurrent(node)

            return True

        self.__moveNextFunc = moveNext

        return True
    
    def _OnStarting(self):
        if super()._OnStarting():
            self.__moveNextFunc = self.__MoveNext

            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        return self.__moveNextFunc()
    
    @final
    def __OnEnded(self) -> None:
        self.__moveNextFunc = None
    
    def _OnEnded(self) -> None:
        self.__OnEnded()

        super()._OnEnded()
    
    def _OnStopped(self) -> None:
        pass
    
    def _ResetOverride(self) -> bool:
        self.__OnEnded()

        return True

class NodeEnumerator[T](NodeEnumeratorBase[ILinkedListNode[T], T]):
    def __init__(self, node: ILinkedListNode[T]):
        super().__init__(node)

def GetValueIterator[T](node: ILinkedListNode[T]) -> Generator[T]:
    return Select(NodeEnumerator[T](node), lambda node: node.GetValue())