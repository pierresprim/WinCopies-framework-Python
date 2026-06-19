from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import final, Callable, Self

from WinCopies import IInterface, Abstract
from WinCopies.Assertion import EnsureTrue
from WinCopies.Collections import Generator as GeneratorBase
from WinCopies.Collections.Core import IClearable
from WinCopies.Collections.Linked.Doubly import IReadWriteList
from WinCopies.Collections.Linked.Node import IReadWriteTwoWayLinkedNode, LinkedNode
from WinCopies.Typing.Generic import IGenericConstraint

class INodeCookie[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetFirst(self, items: IListCookie[T]) -> T|None:
        ...
    @abstractmethod
    def GetLast(self, items: IListCookie[T]) -> T|None:
        ...
    
    @abstractmethod
    def SetFirst(self, node: T|None, items: IListCookie[T]) -> None:
        ...
    @abstractmethod
    def SetLast(self, node: T|None, items: IListCookie[T]) -> None:
        ...

class IListCookie[T](IInterface):
    @final
    class __LinkedListCookie[_T](Abstract, INodeCookie[_T]):
        def __init__(self) -> None: super().__init__()
        
        def GetFirst(self, items: IListCookie[_T]) -> _T|None: return items._GetFirst()
        def GetLast(self, items: IListCookie[_T]) -> _T|None: return items._GetLast()
        
        def SetFirst(self, node: _T|None, items: IListCookie[_T]) -> None: return items._SetFirst(node)
        def SetLast(self, node: _T|None, items: IListCookie[_T]) -> None: return items._SetLast(node)
    
    def __init__(self) -> None: super().__init__()
    
    def _CreateCookie(self) -> INodeCookie[T]:
        return IListCookie.__LinkedListCookie[T]()
    @abstractmethod
    def _GetCookie(self) -> INodeCookie[T]:
        ...
    
    @abstractmethod
    def _GetFirst(self) -> T|None:
        ...
    @abstractmethod
    def _GetLast(self) -> T|None:
        ...
    
    @abstractmethod
    def _SetFirst(self, node: T|None) -> None:
        ...
    @abstractmethod
    def _SetLast(self, node: T|None) -> None:
        ...

class INode[T](IReadWriteTwoWayLinkedNode[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetList(self) -> IReadWriteList[T]|None:
        ...
    
    @abstractmethod
    def GetPrevious(self) -> Self|None:
        ...
    @abstractmethod
    def GetNext(self) -> Self|None:
        ...
    
    @abstractmethod
    def RemoveNode(self) -> T:
        ...

    @final
    def Remove(self) -> None:
        self.RemoveNode()

    @abstractmethod
    def RemoveRangeBefore(self, inclusive: bool = False) -> None:
        ...
    @abstractmethod
    def RemoveRangeAfter(self, inclusive: bool = False) -> None:
        ...

class IDoublyLinkedNode[T](INode[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def SetPrevious(self, value: T) -> Self:
        ...
    @abstractmethod
    def SetNext(self, value: T) -> Self:
        ...
class IDoublyLinkedNodeBase[TItem, TNode](INode[TItem]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _AsNode(self) -> TNode:
        ...

    @abstractmethod
    def _AsLinkedNode(self, node: TNode) -> IDoublyLinkedNodeBase[TItem, TNode]:
        ...
    def _TryAsLinkedNode(self, node: TNode|None) -> IDoublyLinkedNodeBase[TItem, TNode]|None:
        return None if node is None else self._AsLinkedNode(node)
    
    @abstractmethod
    def GetPrevious(self) -> IDoublyLinkedNodeBase[TItem, TNode]|None:
        ...
    @abstractmethod
    def GetNext(self) -> IDoublyLinkedNodeBase[TItem, TNode]|None:
        ...
    
    @abstractmethod
    def SetPrevious(self, value: TItem) -> IDoublyLinkedNodeBase[TItem, TNode]:
        ...
    @abstractmethod
    def SetNext(self, value: TItem) -> IDoublyLinkedNodeBase[TItem, TNode]:
        ...
    
    @final
    def SetPreviousNode(self, value: TItem) -> TNode:
        return self.SetPrevious(value)._AsNode()
    @final
    def SetNextNode(self, value: TItem) -> TNode:
        return self.SetNext(value)._AsNode()

class NodeBase[TItem, TNode](LinkedNode[TItem, TNode], IDoublyLinkedNodeBase[TItem, TNode]):
    def __init__(self, value: TItem, previousNode: TNode|None, nextNode: TNode|None) -> None:
        super().__init__(value, nextNode)

        self.__previous: TNode|None = previousNode

    @abstractmethod
    def _AsLinkedNode(self, node: TNode) -> NodeBase[TItem, TNode]:
        ...
    def _TryAsLinkedNode(self, node: TNode|None) -> NodeBase[TItem, TNode]|None:
        return None if node is None else self._AsLinkedNode(node)
    
    @final
    def GetPreviousNode(self) -> TNode|None: return self.__previous
    def GetPrevious(self) -> NodeBase[TItem, TNode]|None: return self._TryAsLinkedNode(self.GetPreviousNode())
    
    def GetNext(self) -> NodeBase[TItem, TNode]|None: return self._TryAsLinkedNode(self.GetNextNode())
    
    @final
    def _SetPrevious(self, previous: TNode|None) -> None:
        self.__previous = previous

class INodeBase[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _SetFirst(self, cookie: INodeCookie[T], items: IListCookie[T], node: T|None) -> None:
        ...
    @abstractmethod
    def _SetLast(self, cookie: INodeCookie[T], items: IListCookie[T], node: T|None) -> None:
        ...

class DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface: IClearable](NodeBase[TItem, TNode], IGenericConstraint[TList, IReadWriteList[TItem]]):
    def __init__(self, value: TItem, l: TListInterface|None, previousNode: TNode|None, nextNode: TNode|None) -> None:
        super().__init__(value, previousNode, nextNode)

        self.__list: TListInterface|None = l

    @abstractmethod
    def _AsLinkedNode(self, node: TNode) -> DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]:
        ...
    def _TryAsLinkedNode(self, node: TNode|None) -> DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]|None:
        return None if node is None else self._AsLinkedNode(node)
    
    @final
    def __GetList(self, l: TListInterface) -> IReadWriteList[TItem]:
        return self._AsContainer(self._GetListAsClass(l))
    
    @abstractmethod
    def _CreateNode(self, value: TItem, previous: TNode|None, next: TNode|None) -> TNode:
        ...

    @final
    def _GetInnerList(self) -> TListInterface|None:
        return self.__list
    
    @abstractmethod
    def _GetListAsClass(self, l: TListInterface) -> TList:
        ...
    
    @final
    def _GetList(self) -> TList|None:
        l: TListInterface|None = self._GetInnerList()

        return None if l is None else self._GetListAsClass(l)
    
    def GetPrevious(self) -> DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]|None: return self._TryAsLinkedNode(self.GetPreviousNode())
    def GetNext(self) -> DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]|None: return self._TryAsLinkedNode(self.GetNextNode())
    
    @abstractmethod
    def _AddFirst(self, node: TNode, l: TListInterface) -> None:
        ...
    @abstractmethod
    def _AddLast(self, node: TNode, l: TListInterface) -> None:
        ...
    
    @abstractmethod
    def _UpdateFirst(self, node: TNode, l: TListInterface) -> None:
        ...
    @abstractmethod
    def _UpdateLast(self, node: TNode, l: TListInterface) -> None:
        ...

    @abstractmethod
    def _RemoveFirst(self) -> None:
        ...
    @abstractmethod
    def _RemoveLast(self) -> None:
        ...
    
    @final
    def _SetPreviousNode(self, value: TItem) -> TNode:
        def getNode(previousNode: TNode|None) -> TNode: return self._CreateNode(value, previousNode, self._AsNode())
        
        def tryAddFirst() -> TNode|None:
            def tryAdd(l: TListInterface) -> TNode|None:
                if self is self.__GetList(l).GetFirstNode():
                    node: TNode = getNode(None)
                    
                    self._AddFirst(node, l)

                    return node
                
                return None

            l: TListInterface|None = self._GetInnerList()

            return None if l is None else tryAdd(l)

        previousNode: TNode|None = self.GetPreviousNode()
        newNode: TNode|None = tryAddFirst()
        
        if newNode is None: newNode = getNode(previousNode)
        if previousNode is not None: self._AsLinkedNode(previousNode)._SetNext(newNode)
        
        self._SetPrevious(newNode)

        return newNode
    @final
    def _SetNextNode(self, value: TItem) -> TNode:
        def getNode(nextNode: TNode|None) -> TNode: return self._CreateNode(value, self._AsNode(), nextNode)
        
        def tryAddLast() -> TNode|None:
            def tryAdd(l: TListInterface) -> TNode|None:
                if self is self.__GetList(l).GetLastNode():
                    node: TNode = getNode(None)
                    
                    self._AddLast(node, l)

                    return node
                
                return None

            l: TListInterface|None = self._GetInnerList()

            return None if l is None else tryAdd(l)
        
        nextNode: TNode|None = self.GetNextNode()
        newNode: TNode|None = tryAddLast()
        
        if newNode is None: newNode = getNode(nextNode)
        if nextNode is not None: self._AsLinkedNode(nextNode)._SetPrevious(newNode)
        
        self._SetNext(newNode)

        return newNode
    
    def SetPrevious(self, value: TItem) -> DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]: return self._AsLinkedNode(self._SetPreviousNode(value))
    def SetNext(self, value: TItem) -> DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]: return self._AsLinkedNode(self._SetNextNode(value))
    
    @final
    def SetPreviousItems(self, items: Iterable[TItem]|None) -> bool:
        adder: Callable[[DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface], TItem], TNode]|None = None

        def add(node: IDoublyLinkedNodeBase[TItem, TNode], item: TItem) -> TNode:
            nonlocal adder

            adder = lambda node, item: node.SetNextNode(item)

            return node.SetPreviousNode(item)

        if items is None: return False
        
        adder = add
        node: IDoublyLinkedNodeBase[TItem, TNode] = self
        
        for item in items: node = self._AsLinkedNode(adder(node, item))

        return True
    @final
    def SetPreviousValues(self, *values: TItem) -> bool: return self.SetPreviousItems(values)
    @final
    def SetNextItems(self, items: Iterable[TItem]|None) -> bool:
        if items is None: return False
        
        node: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface] = self
        
        for item in items: node = node.SetNext(item)

        return True
    @final
    def SetNextValues(self, *values: TItem) -> bool: return self.SetNextItems(values)
    
    @final
    def __RemoveFirst(self, node: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface], previousNode: TNode|None) -> None:
        self._SetNext(None)

        node._SetPrevious(previousNode)
    @final
    def __RemoveLast(self, node: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface], nextNode: TNode|None) -> None:
        self._SetPrevious(None)

        node._SetNext(nextNode)
    
    def RemoveNode(self) -> TItem:
        def whenFirst(nextNode: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]|None) -> bool:
            l: TListInterface|None = self._GetInnerList()
            
            if nextNode is None:
                if l is not None:
                    l.Clear()

                    return False
            
            else:
                if l is not None: self._UpdateFirst(nextNode._AsNode(), l)

                self.__RemoveFirst(nextNode, None)
            
            return True
        def whenLast(previousNode: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]) -> None:
            l: TListInterface|None = self._GetInnerList()

            if l is not None: self._UpdateLast(previousNode._AsNode(), l)
            
            self.__RemoveLast(previousNode, None)
        
        previousNode: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]|None = self.GetPrevious()
        nextNode: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]|None = self.GetNext()

        if previousNode is None:
            if whenFirst(nextNode): self._Unregister()

        else:
            if nextNode is None: whenLast(previousNode)

            else:
                self.__RemoveFirst(nextNode, previousNode._AsNode())
                self.__RemoveLast(previousNode, nextNode._AsNode())
            
            self._Unregister()

        return self.GetValue()
    
    @final
    def RemoveRangeBefore(self, inclusive: bool = False) -> None:
        def unregister(node: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]) -> None:
            def enumerate(node: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]) -> GeneratorBase[DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]]:
                yield node

                _node: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]|None = node.GetPrevious()

                while _node is not None:
                    yield node

                    _node = self.GetPrevious()
            
            for _node in enumerate(node): _node._Unregister()

        previousNode: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]|None = self.GetPrevious()
        
        if previousNode is None:
            if inclusive: self.Remove()
            
            return
        
        l: TListInterface|None = self._GetInnerList()

        if inclusive:
            node: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]|None = self.GetNext()

            if node is None:
                if l is not None: l.Clear()

                return
            
            if l is not None:
                self._Unregister()

                unregister(previousNode)

                self._UpdateFirst(node._AsNode(), l)

            self.__RemoveFirst(node, None)
            
            return
        
        if l is not None:
            unregister(previousNode)

            self._UpdateFirst(self._AsNode(), l)
        
        self.__RemoveLast(previousNode, None)
    @final
    def RemoveRangeAfter(self, inclusive: bool = False) -> None:
        def unregister(node: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]) -> None:
            def enumerate(node: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]) -> GeneratorBase[DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]]:
                yield node

                _node: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]|None = node.GetNext()

                while _node is not None:
                    yield node

                    _node = self.GetNext()
            
            for _node in enumerate(node): _node._Unregister()

        nextNode: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]|None = self.GetNext()
        
        if nextNode is None:
            if inclusive: self.Remove()
            
            return
        
        l: TListInterface|None = self._GetInnerList()

        if inclusive:
            node: DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface]|None = self.GetPrevious()

            if node is None:
                if l is not None: l.Clear()

                return
            
            if l is not None:
                self._Unregister()

                unregister(nextNode)

                self._UpdateLast(node._AsNode(), l)

            self.__RemoveLast(node, None)
            
            return
        
        if l is not None:
            unregister(nextNode)

            self._UpdateLast(self._AsNode(), l)
        
        self.__RemoveFirst(nextNode, None)
    
    @final
    def Check(self, l: TList) -> bool: return self._GetList() is l
    @final
    def Ensure(self, l: TList) -> None: EnsureTrue(self.Check(l))
    
    @final
    def _Unregister(self) -> None:
        self.__list = None

class DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface: IClearable](DoublyLinkedNodeAbstract[TItem, TNode, TList, TListInterface], INodeBase[TNode]):
    def __init__(self, value: TItem, l: TListInterface|None, itemCookie: IListCookie[TNode], cookie: INodeCookie[TNode], previousNode: TNode|None, nextNode: TNode|None) -> None:
        super().__init__(value, l, previousNode, nextNode)

        self.__itemCookie = itemCookie
        self.__cookie = cookie
    
    @final
    def _GetItemCookie(self) -> IListCookie[TNode]:
        return self.__itemCookie
    @final
    def _GetCookie(self) -> INodeCookie[TNode]:
        return self.__cookie
    
    @final
    def _SetFirstNode(self, node: TNode|None) -> None:
        self._SetFirst(self._GetCookie(), self._GetItemCookie(), node)
    @final
    def _SetLastNode(self, node: TNode|None) -> None:
        self._SetLast(self._GetCookie(), self._GetItemCookie(), node)
    
    @final
    def _AddFirst(self, node: TNode, l: TListInterface) -> None:
        self._SetFirstNode(node)
    @final
    def _AddLast(self, node: TNode, l: TListInterface) -> None:
        self._SetLastNode(node)
    
    @final
    def _UpdateFirst(self, node: TNode, l: TListInterface) -> None:
        self._AddFirst(node, l)
    @final
    def _UpdateLast(self, node: TNode, l: TListInterface) -> None:
        self._AddLast(node, l)
    
    @final
    def _RemoveFirst(self) -> None:
        self._SetFirstNode(None)
    @final
    def _RemoveLast(self) -> None:
        self._SetLastNode(None)
    
    @final
    def TryMoveToTop(self) -> bool|None:
        _l: TListInterface|None = self._GetInnerList()

        if _l is None: return False
        
        if self.GetPrevious() is None: return None
        
        l: IListCookie[TNode] = self._GetItemCookie()
        
        self.Remove()
        
        node: TNode|None = self._GetCookie().GetFirst(l)

        if node is None: return False
        
        _node: TNode = self._AsNode()

        self._AsLinkedNode(node)._SetPrevious(_node)
        self._SetNext(node)

        return True
    @final
    def TryMoveToBottom(self) -> bool|None:
        _l: TListInterface|None = self._GetInnerList()

        if _l is None: return False
        
        if self.GetNext() is None: return None
        
        l: IListCookie[TNode] = self._GetItemCookie()
        
        self.Remove()
        
        node: TNode|None = self._GetCookie().GetLast(l)

        if node is None: return False
        
        _node: TNode = self._AsNode()
        
        self._AsLinkedNode(node)._SetNext(_node)
        self._SetPrevious(node)

        return True

class DoublyLinkedNode[TItem, TNode, TList, TListInterface: IClearable](DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface], IDoublyLinkedNode[TItem]):
    def __init__(self, value: TItem, l: TListInterface|None, itemCookie: IListCookie[TNode], cookie: INodeCookie[TNode], previousNode: TNode|None, nextNode: TNode|None) -> None:
        super().__init__(value, l, itemCookie, cookie, previousNode, nextNode)

    @abstractmethod
    def _AsLinkedNode(self, node: TNode) -> Self:
        ...
    def _TryAsLinkedNode(self, node: TNode|None) -> Self|None:
        return None if node is None else self._AsLinkedNode(node)
    
    @final
    def GetPrevious(self) -> Self|None: return self._TryAsLinkedNode(self.GetPreviousNode())
    @final
    def GetNext(self) -> Self|None: return self._TryAsLinkedNode(self.GetNextNode())
    
    @final
    def SetPrevious(self, value: TItem) -> Self: return self._AsLinkedNode(super()._SetPreviousNode(value))
    @final
    def SetNext(self, value: TItem) -> Self: return self._AsLinkedNode(super()._SetNextNode(value))
    
    @final
    def RemoveNode(self) -> TItem: return super().RemoveNode()