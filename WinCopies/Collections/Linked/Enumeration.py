from abc import abstractmethod
from typing import final

from WinCopies.Collections import Generator, EnumerationOrder
from WinCopies.Collections.Enumeration import IEnumerator, Enumerator, AsEnumerator
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Linked.Node import INode, ITwoWayNode, ILinkedNode, ITwoWayLinkedNode

from WinCopies.Typing.Delegate import Function, NullableSelector

class NodeEnumeratorBase[T: INode](Enumerator[T]):
    def __init__(self, node: T) -> None:
        super().__init__()

        self.__first: T = node
        self.__moveNextFunc: Function[bool]|None = None
    
    @final
    def IsResetSupported(self) -> bool:
        return True
    
    @abstractmethod
    def _GetNextNode(self, node: T) -> T|None:
        pass
    
    @final
    def __MoveNext(self) -> bool:
        self._SetCurrent(self.__first)

        def moveNext() -> bool:
            node: T = self.GetCurrent()
            _node: T|None = None

            if (_node := self._GetNextNode(node)) is None:
                return False
            
            self._SetCurrent(_node)

            return True

        self.__moveNextFunc = moveNext

        return True
    
    def _OnStarting(self) -> bool:
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
class NodeEnumerator[T](NodeEnumeratorBase[ILinkedNode[T]]):
    def __init__(self, node: ILinkedNode[T]) -> None:
        super().__init__(node)
    
    @final
    def _GetNextNode(self, node: ILinkedNode[T]) -> ILinkedNode[T]|None:
        return node.GetNext()

class TwoWayNodeEnumeratorBase[T: ITwoWayNode](NodeEnumeratorBase[T]):
    def __init__(self, node: T, order: EnumerationOrder = EnumerationOrder.FIFO) -> None:
        super().__init__(node)
        
        self.__getNext: NullableSelector[T] = self._GetNodeConverter(order)
    
    @abstractmethod
    def _GetNodeConverter(self, order: EnumerationOrder) -> NullableSelector[T]:
        pass
    
    @final
    def _GetNextNode(self, node: T) -> T|None:
        return self.__getNext(node)
class TwoWayNodeEnumerator[T](TwoWayNodeEnumeratorBase[ITwoWayLinkedNode[T]]):
    def __init__(self, node: ITwoWayLinkedNode[T], order: EnumerationOrder = EnumerationOrder.FIFO) -> None:
        super().__init__(node, order)
    
    @final
    def _GetNodeConverter(self, order: EnumerationOrder) -> NullableSelector[ITwoWayLinkedNode[T]]:
        match order:
            case EnumerationOrder.FIFO:
                return lambda node: node.GetNext()
            case EnumerationOrder.LIFO:
                return lambda node: node.GetPrevious()
            
            case _:
                raise ValueError()

def GetValueIterator[T](nodeEnumerator: NodeEnumerator[T]) -> Generator[T]:
    return Select(nodeEnumerator, lambda node: node.GetValue())
def GetValueIteratorFromNode[T](node: ILinkedNode[T]) -> Generator[T]:
    return GetValueIterator(NodeEnumerator[T](node))

def GetValueEnumerator[T](nodeEnumerator: NodeEnumerator[T]) -> IEnumerator[T]:
    return AsEnumerator(GetValueIterator(nodeEnumerator))
def GetValueEnumeratorFromNode[T](node: ILinkedNode[T]) -> IEnumerator[T]:
    return AsEnumerator(GetValueIteratorFromNode(node))
def TryGetValueEnumeratorFromNode[T](node: ILinkedNode[T]|None) -> IEnumerator[T]|None:
    return None if node is None else GetValueEnumeratorFromNode(node)