from typing import final

from WinCopies.Collections import Generator
from WinCopies.Collections.Enumeration import Enumerator
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Linked.Node import ILinkedNode

from WinCopies.Typing import IInvariantGenericConstraint, IInvariantGenericConstraintImplementation
from WinCopies.Typing.Delegate import Function

class NodeEnumeratorBase[TItems, TNode](Enumerator[TNode], IInvariantGenericConstraint[TNode, ILinkedNode[TItems]]):
    def __init__(self, node: TNode):
        super().__init__()

        self.__first: TNode = node
        self.__moveNextFunc: Function[bool]|None = None
    
    @final
    def IsResetSupported(self) -> bool:
        return True
    
    def __MoveNext(self) -> bool:
        self._SetCurrent(self.__first)

        def moveNext() -> bool:
            node: TNode|None = self.GetCurrent()

            if node is None or (node := self._TryAsInterface(self._AsContainer(node).GetNext())) is None:
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
        return self.__moveNextFunc() # type: ignore
    
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

class NodeEnumerator[T](NodeEnumeratorBase[T, ILinkedNode[T]], IInvariantGenericConstraintImplementation[ILinkedNode[T]]):
    def __init__(self, node: ILinkedNode[T]):
        super().__init__(node)

def GetValueIterator[T](node: ILinkedNode[T]) -> Generator[T]:
    return Select(NodeEnumerator[T](node), lambda node: node.GetValue())