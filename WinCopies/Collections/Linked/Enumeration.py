from abc import abstractmethod
from typing import overload, final

from WinCopies.Collections import Generator, EnumerationOrder, ThrowInvalidEnumerationOrderError
from WinCopies.Collections.Enumeration.Abstraction import AbstractEnumeratorBase
from WinCopies.Collections.Enumeration.Core import IEnumerator, IInvalidatableEnumerator, IDefaultInvalidatableEnumerator, Enumerator
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Linked.Node import INode, ITwoWayNode, ILinkedNode, ITwoWayLinkedNode, ILinkedListCookie, ITwoWayLinkedListCookie, IEnumerableLinkedListCookie, ITwoWayEnumerableLinkedListCookie

from WinCopies.Collections.Registry import IObjectRegistrar
from WinCopies.Collections.Registry.Invalidation import IInvalidationRegistrar
from WinCopies.Delegates import BoolFalse

from WinCopies.Typing.Delegate import Function
from WinCopies.Typing.Discard import IInvalidatable
from WinCopies.Typing.Generic import IGenericConstraintImplementation

class _IEnumerator[T: INode](IEnumerator[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetFirstNode(self) -> T|None:
        ...
    @abstractmethod
    def _GetNextNode(self, node: T) -> T|None:
        ...

class NodeEnumeratorAbstract[T: INode](Enumerator[T], IDefaultInvalidatableEnumerator[T], _IEnumerator[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__moveNextFunc: Function[bool] = BoolFalse
    
    @final
    def IsResetSupported(self) -> bool: return True
    
    @final
    def __MoveNext(self) -> bool:
        first: T|None = self._GetFirstNode()

        if first is None: return False

        self._SetCurrent(first)

        def moveNext() -> bool:
            node: T = self.GetCurrent()
            _node: T|None = None

            if (_node := self._GetNextNode(node)) is None: return False
            
            self._SetCurrent(_node)

            return True

        self.__moveNextFunc = moveNext

        return True
    
    def _OnStarting(self) -> bool:
        if super()._OnStarting():
            self.__moveNextFunc = self.__MoveNext

            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool: return self.__moveNextFunc()
    
    @final
    def __OnEnded(self) -> None:
        self.__moveNextFunc = BoolFalse
    
    def _OnEnded(self) -> None:
        self.__OnEnded()

        super()._OnEnded()
    
    def _ResetOverride(self) -> bool:
        self.__OnEnded()

        return True
class NodeEnumeratorBase[T: INode](NodeEnumeratorAbstract[T]):
    def __init__(self, cookie: ILinkedListCookie[T]) -> None:
        super().__init__()

        self.__cookie: ILinkedListCookie[T] = cookie

    @final
    def _GetFirstNode(self) -> T|None: return self.__cookie.GetFirst()
class NodeEnumerator[T](NodeEnumeratorBase[ILinkedNode[T]]):
    def __init__(self, cookie: ILinkedListCookie[ILinkedNode[T]]) -> None: super().__init__(cookie)

    @final
    def _GetNextNode(self, node: ILinkedNode[T]) -> ILinkedNode[T]|None: return node.GetNext()

class ITwoWayNodeEnumerator[T: ITwoWayNode](_IEnumerator[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetEnumerationCookie(self) -> ITwoWayLinkedListCookie[T]:
        ...
    
    @abstractmethod
    def _GetPrevious(self, node: T) -> T|None:
        ...
    @abstractmethod
    def _GetNext(self, node: T) -> T|None:
        ...

    @abstractmethod
    def GetEnumerationOrder(self) -> EnumerationOrder:
        ...

    @final
    def _GetFirstNode(self) -> T|None:
        cookie: ITwoWayLinkedListCookie[T] = self._GetEnumerationCookie()
        order: EnumerationOrder = self.GetEnumerationOrder()

        match order:
            case EnumerationOrder.FIFO: return cookie.GetFirst()
            case EnumerationOrder.LIFO: return cookie.GetLast()
            
            case _: ThrowInvalidEnumerationOrderError(order)
    @final
    def _GetNextNode(self, node: T) -> T|None:
        order: EnumerationOrder = self.GetEnumerationOrder()

        match order:
            case EnumerationOrder.FIFO: return self._GetNext(node)
            case EnumerationOrder.LIFO: return self._GetPrevious(node)
            
            case _: ThrowInvalidEnumerationOrderError(order)
class ITwoWayLinkedNodeEnumerator[T](ITwoWayNodeEnumerator[ITwoWayLinkedNode[T]]):
    def __init__(self) -> None: super().__init__()

    @final
    def _GetPrevious(self, node: ITwoWayLinkedNode[T]) -> ITwoWayLinkedNode[T]|None: return node.GetPrevious()
    @final
    def _GetNext(self, node: ITwoWayLinkedNode[T]) -> ITwoWayLinkedNode[T]|None: return node.GetNext()

class TwoWayNodeEnumeratorBase[T: ITwoWayNode](NodeEnumeratorAbstract[T], ITwoWayNodeEnumerator[T]):
    def __init__(self, cookie: ITwoWayLinkedListCookie[T], order: EnumerationOrder = EnumerationOrder.FIFO) -> None:
        super().__init__()

        self.__cookie: ITwoWayLinkedListCookie[T] = cookie
        self.__enumerationOrder: EnumerationOrder = order

    @final
    def _GetEnumerationCookie(self) -> ITwoWayLinkedListCookie[T]: return self.__cookie

    @final
    def GetEnumerationOrder(self) -> EnumerationOrder: return self.__enumerationOrder
class TwoWayNodeEnumerator[T](TwoWayNodeEnumeratorBase[ITwoWayLinkedNode[T]], ITwoWayLinkedNodeEnumerator[T]):
    def __init__(self, cookie: ITwoWayLinkedListCookie[ITwoWayLinkedNode[T]], order: EnumerationOrder = EnumerationOrder.FIFO) -> None: super().__init__(cookie, order)

class ValueEnumeratorBase[TItem, TNode: INode](AbstractEnumeratorBase[TNode, TItem, IInvalidatableEnumerator[TNode]], IGenericConstraintImplementation[IInvalidatableEnumerator[TNode]]):
    def __init__(self, enumerator: IInvalidatableEnumerator[TNode]) -> None: super().__init__(enumerator)

    @abstractmethod
    def _Convert(self, node: TNode) -> TItem:
        ...

    @final
    def _GetCurrent(self) -> TItem: return self._Convert(self._GetContainer().GetCurrent())
class ValueEnumerator[T](ValueEnumeratorBase[T, ILinkedNode[T]], IInvalidatableEnumerator[T]):
    def __init__(self, enumerator: IInvalidatableEnumerator[ILinkedNode[T]]) -> None: super().__init__(enumerator)

    @final
    def _Convert(self, node: ILinkedNode[T]) -> T: return node.GetValue()

    @final
    def Register(self, registry: IObjectRegistrar[IInvalidatable]) -> None: self._GetContainer().Register(registry)
    @final
    def AddRegistrar(self, invalidationRegistrar: IInvalidationRegistrar) -> IRemovable: return self._GetContainer().AddRegistrar(invalidationRegistrar)

@overload
def GetNodeEnumerator[T](cookie: IEnumerableLinkedListCookie[T]) -> IInvalidatableEnumerator[ILinkedNode[T]]:
    ...
@overload
def GetNodeEnumerator[T](cookie: ITwoWayEnumerableLinkedListCookie[T], enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO) -> IInvalidatableEnumerator[ITwoWayLinkedNode[T]]:
    ...

def GetNodeEnumerator[T](cookie: IEnumerableLinkedListCookie[T]|ITwoWayEnumerableLinkedListCookie[T], enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO) -> IInvalidatableEnumerator[ILinkedNode[T]]|IInvalidatableEnumerator[ITwoWayLinkedNode[T]]:
    return TwoWayNodeEnumerator[T](cookie, enumerationOrder) if isinstance(cookie, ITwoWayEnumerableLinkedListCookie) and enumerationOrder != EnumerationOrder.FIFO else NodeEnumerator[T](cookie)

def GetValueEnumerator[T](nodeEnumerator: IInvalidatableEnumerator[ILinkedNode[T]]) -> IInvalidatableEnumerator[T]:
    return ValueEnumerator[T](nodeEnumerator)
def GetValueIterator[T](nodeEnumerator: IEnumerator[ILinkedNode[T]]|IEnumerator[ITwoWayLinkedNode[T]]) -> Generator[T]:
    return Select(nodeEnumerator.AsIterator(), lambda node: node.GetValue())

@overload
def GetValueEnumeratorFromNode[T](cookie: IEnumerableLinkedListCookie[T]) -> IInvalidatableEnumerator[T]:
    ...
@overload
def GetValueEnumeratorFromNode[T](cookie: ITwoWayEnumerableLinkedListCookie[T], enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO) -> IInvalidatableEnumerator[T]:
    ...

def GetValueEnumeratorFromNode[T](cookie: IEnumerableLinkedListCookie[T]|ITwoWayEnumerableLinkedListCookie[T], enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO) -> IInvalidatableEnumerator[T]:
    return GetValueEnumerator(GetNodeEnumerator(cookie, enumerationOrder)) if isinstance(cookie, ITwoWayEnumerableLinkedListCookie) and enumerationOrder != EnumerationOrder.FIFO else GetValueEnumerator(GetNodeEnumerator(cookie))
def TryGetValueEnumeratorFromNode[T](node: IEnumerableLinkedListCookie[T]|None) -> IInvalidatableEnumerator[T]|None:
    return None if node is None else GetValueEnumeratorFromNode(node)

@overload
def GetValueIteratorFromNode[T](cookie: IEnumerableLinkedListCookie[T]) -> Generator[T]:
    ...
@overload
def GetValueIteratorFromNode[T](cookie: ITwoWayEnumerableLinkedListCookie[T], enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO) -> Generator[T]:
    ...

def GetValueIteratorFromNode[T](cookie: IEnumerableLinkedListCookie[T]|ITwoWayEnumerableLinkedListCookie[T], enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO) -> Generator[T]:
    return GetValueIterator(GetNodeEnumerator(cookie, enumerationOrder)) if isinstance(cookie, ITwoWayEnumerableLinkedListCookie) else GetValueIterator(GetNodeEnumerator(cookie))