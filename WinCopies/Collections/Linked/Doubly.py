from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Sized
from typing import final, Callable, Self as SelfType

from WinCopies import IInterface, Abstract
from WinCopies.Assertion import EnsureTrue
from WinCopies.Collections import Generator, IReadOnlyCollection, ICountable
from WinCopies.Collections.Abstraction.Enumeration import CountableEnumerable, Enumerator
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEnumerable, IEnumerator, CountableEnumerable as CountableEnumerableBase, Enumerable, GetEnumerator
from WinCopies.Collections.Linked.Enumeration import NodeEnumeratorBase, GetValueEnumeratorFromNode
from WinCopies.Collections.Linked.Node import ILinkedNode, LinkedNode
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Method, Function, Converter, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import IGenericConstraint, IGenericConstraintImplementation, GenericConstraint
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

class INode[T](ILinkedNode[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetList(self) -> IReadWriteList[T]|None:
        pass
    
    @abstractmethod
    def GetPrevious(self) -> SelfType|None:
        pass
    @abstractmethod
    def GetNext(self) -> SelfType|None:
        pass
    
    @abstractmethod
    def SetPrevious(self, value: T) -> INode[T]:
        pass
    @abstractmethod
    def SetNext(self, value: T) -> INode[T]:
        pass
    
    @abstractmethod
    def Remove(self) -> T:
        pass
class IDoublyLinkedNode[T](INode[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetList(self) -> IList[T]|None:
        pass
    
    @abstractmethod
    def GetPrevious(self) -> IDoublyLinkedNode[T]|None:
        pass
    @abstractmethod
    def GetNext(self) -> IDoublyLinkedNode[T]|None:
        pass
    
    @abstractmethod
    def SetPrevious(self, value: T) -> IDoublyLinkedNode[T]:
        pass
    @abstractmethod
    def SetNext(self, value: T) -> IDoublyLinkedNode[T]:
        pass
class IDoublyLinkedNodeBase[TItem, TNode](INode[TItem]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _AsNode(self) -> TNode:
        pass

    @abstractmethod
    def _AsLinkedNode(self, node: TNode) -> IDoublyLinkedNodeBase[TItem, TNode]:
        pass
    def _TryAsLinkedNode(self, node: TNode|None) -> IDoublyLinkedNodeBase[TItem, TNode]|None:
        return None if node is None else self._AsLinkedNode(node)
    
    @abstractmethod
    def GetPrevious(self) -> IDoublyLinkedNodeBase[TItem, TNode]|None:
        pass
    @abstractmethod
    def GetNext(self) -> IDoublyLinkedNodeBase[TItem, TNode]|None:
        pass
    
    @abstractmethod
    def SetPrevious(self, value: TItem) -> IDoublyLinkedNodeBase[TItem, TNode]:
        pass
    @abstractmethod
    def SetNext(self, value: TItem) -> IDoublyLinkedNodeBase[TItem, TNode]:
        pass
    
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
        pass
    def _TryAsLinkedNode(self, node: TNode|None) -> NodeBase[TItem, TNode]|None:
        return None if node is None else self._AsLinkedNode(node)
    
    @final
    def GetPreviousNode(self) -> TNode|None:
        return self.__previous
    def GetPrevious(self) -> NodeBase[TItem, TNode]|None:
        return self._TryAsLinkedNode(self.GetPreviousNode())
    
    def GetNext(self) -> NodeBase[TItem, TNode]|None:
        return self._TryAsLinkedNode(self.GetNextNode())
    
    @final
    def _SetPrevious(self, previous: TNode|None) -> None:
        self.__previous = previous

class IReadOnlyList[T](IReadOnlyCollection):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryGetFirst(self) -> INullable[T]:
        pass
    @abstractmethod
    def TryGetLast(self) -> INullable[T]:
        pass

    @final
    def __TryGetValue[TDefault](self, default: TDefault, item: INullable[T]) -> T|TDefault:
        return item.GetValue() if item.HasValue() else default
    
    @final
    def TryGetFirstValue[TDefault](self, default: TDefault) -> T|TDefault:
        return self.__TryGetValue(default, self.TryGetFirst())
    @final
    def TryGetLastValue[TDefault](self, default: TDefault) -> T|TDefault:
        return self.__TryGetValue(default, self.TryGetLast())
    
    @final
    def TryGetFirstValueOrNone(self) -> T|None:
        return self.TryGetFirstValue(None)
    @final
    def TryGetLastValueOrNone(self) -> T|None:
        return self.TryGetLastValue(None)

class _IAbstractList[TItem, TNode](IInterface):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def _GetNodeAsInterface(self, node: TNode) -> IDoublyLinkedNodeBase[TItem, TNode]:
        pass
class IAbstractNode[TNode, TNodeInterface](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetNodeAsClass(self, node: TNode) -> TNodeInterface:
        pass

class IReadWriteList[T](IReadOnlyList[T]):
    def __init__(self) -> None:
        super().__init__()

    @final
    def __TryGet(self, node: INode[T]|None) -> INullable[T]:
        return GetNullValue() if node is None else GetNullable(node.GetValue())
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyList[T]:
        pass
    
    @abstractmethod
    def GetFirstNode(self) -> INode[T]|None:
        pass
    @abstractmethod
    def GetLastNode(self) -> INode[T]|None:
        pass
    
    @final
    def TryGetFirst(self) -> INullable[T]:
        return self.__TryGet(self.GetFirstNode())
    @final
    def TryGetLast(self) -> INullable[T]:
        return self.__TryGet(self.GetLastNode())
    
    @abstractmethod
    def AddFirstNode(self, value: T) -> INode[T]:
        pass
    @abstractmethod
    def AddLastNode(self, value: T) -> INode[T]:
        pass

    @final
    def __AddItems(self, items: Iterable[T]|None, first: Converter[T, INode[T]]) -> bool:
        if items is None:
            return False
        
        node: INode[T] = None # type: ignore
        adder: Converter[T, INode[T]]|None = None

        def add(item: T) -> INode[T]:
            def add(item: T) -> INode[T]:
                return node.SetNext(item)

            nonlocal adder

            adder = add

            return first(item)
        
        adder = add

        for item in items:
            node = adder(item)
        
        return True

    @final
    def AddFirstItems(self, items: Iterable[T]|None) -> bool:
        return self.__AddItems(items, self.AddFirstNode)
    @final
    def AddFirstValues(self, *values: T) -> bool:
        return self.AddFirstItems(values)
    @final
    def AddLastItems(self, items: Iterable[T]|None) -> bool:
        return self.__AddItems(items, self.AddLastNode)
    @final
    def AddLastValues(self, *values: T) -> bool:
        return self.AddLastItems(values)
    
    @abstractmethod
    def TryRemoveFirst(self) -> INullable[T]:
        pass
    @abstractmethod
    def TryRemoveLast(self) -> INullable[T]:
        pass
    
    @abstractmethod
    def Clear(self) -> None:
        pass
    
    @final
    def __AsGenerator(self, func: Function[INullable[T]]) -> Generator[T]:
        result: INullable[T] = func()

        while result.HasValue():
            yield result.GetValue()
            
            result = func()
    
    @final
    def AsQueuedGenerator(self) -> Generator[T]:
        return self.__AsGenerator(self.TryRemoveFirst)
    @final
    def AsStackedGenerator(self) -> Generator[T]:
        return self.__AsGenerator(self.TryRemoveLast)

class IListBase[TItem, TNode](IReadWriteList[TItem], IGenericConstraint[TNode, INode[TItem]]):
    def __init__(self) -> None:
        super().__init__()

    @final
    def __TryGet(self, node: TNode|None) -> INode[TItem]|None:
        return None if node is None else self._AsContainer(node)
    
    @abstractmethod
    def GetFirst(self) -> TNode|None:
        pass
    @abstractmethod
    def GetLast(self) -> TNode|None:
        pass

    @final
    def GetFirstNode(self) -> INode[TItem]|None:
        return self.__TryGet(self.GetFirst())
    @final
    def GetLastNode(self) -> INode[TItem]|None:
        return self.__TryGet(self.GetLast())
    
    @abstractmethod
    def AddFirst(self, value: TItem) -> TNode:
        pass
    @abstractmethod
    def AddLast(self, value: TItem) -> TNode:
        pass

    @final
    def AddFirstNode(self, value: TItem) -> INode[TItem]:
        return self._AsContainer(self.AddFirst(value))
    @final
    def AddLastNode(self, value: TItem) -> INode[TItem]:
        return self._AsContainer(self.AddLast(value))

class IReadOnlyEnumerableList[T](IReadOnlyList[T], IEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
class IReadWriteEnumerableList[T](IReadWriteList[T], IReadOnlyEnumerableList[T]):
    def __init__(self) -> None:
        super().__init__()

class IEnumerableList[TItem, TNode](IListBase[TItem, TNode], IReadWriteEnumerableList[TItem]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnlyEnumerable(self) -> IReadOnlyEnumerableList[TItem]:
        pass
    
    @abstractmethod
    def TryGetNodeEnumerator(self) -> IEnumerator[TNode]|None:
        pass
    
    @abstractmethod
    def AsNodeEnumerable(self) -> IEnumerable[TNode]:
        pass

class IList[T](IEnumerableList[T, IDoublyLinkedNode[T]]):
    def __init__(self) -> None:
        super().__init__()

class _INodeBase[TItem, TNode, TNodeInterface, TList](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetListAsSpecialized(self, l: TList) -> EnumerableListBase[TItem, TNode, TNodeInterface, TList]:
        pass
    
    @abstractmethod
    def _SetFirst(self, cookie: INodeCookie[TNode], items: _IListCookie[TNode], node: TNode|None) -> None:
        pass
    @abstractmethod
    def _SetLast(self, cookie: INodeCookie[TNode], items: _IListCookie[TNode], node: TNode|None) -> None:
        pass

class DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface](NodeBase[TItem, TNode], IGenericConstraint[TList, IReadWriteList[TItem]]):
    def __init__(self, value: TItem, l: TListInterface|None, previousNode: TNode|None, nextNode: TNode|None) -> None:
        EnsureDirectModuleCall()
        
        super().__init__(value, previousNode, nextNode)

        self.__list: TListInterface|None = l

    @abstractmethod
    def _AsLinkedNode(self, node: TNode) -> DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]:
        pass
    def _TryAsLinkedNode(self, node: TNode|None) -> DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None:
        return None if node is None else self._AsLinkedNode(node)
    
    @final
    def __GetList(self, l: TListInterface) -> IReadWriteList[TItem]:
        return self._AsContainer(self._GetListAsClass(l))
    
    @abstractmethod
    def _GetNode(self, value: TItem, previous: TNode|None, next: TNode|None) -> TNode:
        pass

    @final
    def _GetInnerList(self) -> TListInterface|None:
        return self.__list
    
    @abstractmethod
    def _GetListAsClass(self, l: TListInterface) -> TList:
        pass
    
    @final
    def _GetList(self) -> TList|None:
        l: TListInterface|None = self._GetInnerList()

        return None if l is None else self._GetListAsClass(l)
    
    def GetPrevious(self) -> DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None:
        return self._TryAsLinkedNode(self.GetPreviousNode())
    def GetNext(self) -> DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None:
        return self._TryAsLinkedNode(self.GetNextNode())
    
    @abstractmethod
    def _AddFirst(self, node: TNode, l: TListInterface) -> None:
        pass
    @abstractmethod
    def _AddLast(self, node: TNode, l: TListInterface) -> None:
        pass
    
    @abstractmethod
    def _UpdateFirst(self, node: TNode, l: TListInterface) -> None:
        pass
    @abstractmethod
    def _UpdateLast(self, node: TNode, l: TListInterface) -> None:
        pass

    @abstractmethod
    def _RemoveFirst(self, l: TListInterface) -> None:
        pass
    @abstractmethod
    def _RemoveLast(self, l: TListInterface) -> None:
        pass
    
    @final
    def _SetPreviousNode(self, value: TItem) -> TNode:
        def getNode(previousNode: TNode|None) -> TNode:
            return self._GetNode(value, previousNode, self._AsNode())
        
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
        
        if newNode is None:
            newNode = getNode(previousNode)

        if previousNode is not None:
            self._AsLinkedNode(previousNode)._SetNext(newNode)
        
        self._SetPrevious(newNode)

        return newNode
    @final
    def _SetNextNode(self, value: TItem) -> TNode:
        def getNode(nextNode: TNode|None) -> TNode:
            return self._GetNode(value, self._AsNode(), nextNode)
        
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
        
        if newNode is None:
            newNode = getNode(nextNode)

        if nextNode is not None:
            self._AsLinkedNode(nextNode)._SetPrevious(newNode)
        
        self._SetNext(newNode)

        return newNode
    
    def SetPrevious(self, value: TItem) -> DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]:
        return self._AsLinkedNode(self._SetPreviousNode(value))
    def SetNext(self, value: TItem) -> DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]:
        return self._AsLinkedNode(self._SetNextNode(value))
    
    @final
    def SetPreviousItems(self, items: Iterable[TItem]|None) -> bool:
        adder: Callable[[DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface], TItem], TNode]|None = None

        def add(node: IDoublyLinkedNodeBase[TItem, TNode], item: TItem) -> TNode:
            nonlocal adder

            adder = lambda node, item: node.SetNextNode(item)

            return node.SetPreviousNode(item)

        if items is None:
            return False
        
        adder = add
        node: IDoublyLinkedNodeBase[TItem, TNode] = self
        
        for item in items:
            node = self._AsLinkedNode(adder(node, item))

        return True
    @final
    def SetPreviousValues(self, *values: TItem) -> bool:
        return self.SetPreviousItems(values)
    @final
    def SetNextItems(self, items: Iterable[TItem]|None) -> bool:
        if items is None:
            return False
        
        node: DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface] = self
        
        for item in items:
            node = node.SetNext(item)

        return True
    @final
    def SetNextValues(self, *values: TItem) -> bool:
        return self.SetNextItems(values)
    
    def Remove(self) -> TItem:
        def removeFirst(node: TNode, previousNode: TNode|None) -> None:
            self._SetNext(None)

            self._AsLinkedNode(node)._SetPrevious(previousNode)
        def removeLast(node: TNode, nextNode: TNode|None) -> None:
            self._SetPrevious(None)

            self._AsLinkedNode(node)._SetNext(nextNode)
        
        def whenFirst(nextNode: TNode|None) -> None:
            l: TListInterface|None = self._GetInnerList()
            
            if nextNode is None:
                if l is not None:
                    self._RemoveFirst(l)
                    self._RemoveLast(l)
            
            else:
                if l is not None:
                    self._UpdateFirst(nextNode, l)

                removeFirst(nextNode, None)
        def whenLast(previousNode: TNode) -> None:
            l: TListInterface|None = self._GetInnerList()

            if l is not None:
                self._UpdateLast(previousNode, l)
            
            removeLast(previousNode, None)
        
        def tryAsNode(node: DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None) -> TNode|None:
            return None if node is None else node._AsNode()
        
        previousNode: TNode|None = tryAsNode(self.GetPrevious())
        nextNode: TNode|None = tryAsNode(self.GetNext())

        if previousNode is None:
            whenFirst(nextNode)

        elif nextNode is None:
            whenLast(previousNode)
        
        else:
            removeFirst(nextNode, previousNode)
            removeLast(previousNode, nextNode)

        return self.GetValue()
    
    def Check(self, l: TList) -> bool:
        return self._GetList() is l
    def Ensure(self, l: TList) -> None:
        EnsureTrue(self.Check(l))

class _ReadOnlyListBase[TItem, TList](Abstract, IReadOnlyList[TItem], GenericConstraint[TList, IReadOnlyList[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__items: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__items
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    
    @final
    def HasItems(self) -> bool:
        return super().HasItems()
    
    @final
    def TryGetFirst(self) -> INullable[TItem]:
        return self._GetInnerContainer().TryGetFirst()
    @final
    def TryGetLast(self) -> INullable[TItem]:
        return self._GetInnerContainer().TryGetLast()

class INodeCookie[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def SetFirst(self, node: T|None, items: _IListCookie[T]) -> None:
        pass
    @abstractmethod
    def SetLast(self, node: T|None, items: _IListCookie[T]) -> None:
        pass

class EnumerableListNodeBase[TItem, TNode, TNodeInterface, TList](_INodeBase[TItem, TNode, TNodeInterface, TList]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _SetFirst(self, cookie: INodeCookie[TNode], items: _IListCookie[TNode], node: TNode|None) -> None:
        cookie.SetFirst(node, items)
    @final
    def _SetLast(self, cookie: INodeCookie[TNode], items: _IListCookie[TNode], node: TNode|None) -> None:
        cookie.SetLast(node, items)

@final
class _EnumerableListEnumerable[TItem, TNode, TNodeInterface, TList](Enumerable[TNodeInterface]):
    def __init__(self, l: EnumerableListBase[TItem, TNode, TNodeInterface, TList]) -> None:
        super().__init__()

        self.__list: EnumerableListBase[TItem, TNode, TNodeInterface, TList] = l
    
    def TryGetEnumerator(self) -> IEnumerator[TNodeInterface]|None:
        return self.__list.TryGetNodeEnumerator()

class _ReadOnlyList[T](_ReadOnlyListBase[T, IReadOnlyList[T]], IGenericConstraintImplementation[IReadOnlyList[T]]):
    def __init__(self, items: IReadOnlyList[T]) -> None:
        super().__init__(items)
class _ReadOnlyEnumerableList[T](_ReadOnlyListBase[T, IReadOnlyEnumerableList[T]], Enumerable[T], IReadOnlyEnumerableList[T], IGenericConstraintImplementation[IReadOnlyEnumerableList[T]]):
    def __init__(self, items: IReadOnlyEnumerableList[T]) -> None:
        super().__init__(items)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())

@final
class _EnumerableUpdater[TItem, TNode, TNodeInterface, TList](ValueFunctionUpdater[IEnumerable[TNodeInterface]]):
    def __init__(self, items: EnumerableListBase[TItem, TNode, TNodeInterface, TList], updater: Method[IFunction[IEnumerable[TNodeInterface]]]) -> None:
        super().__init__(updater)

        self.__items: EnumerableListBase[TItem, TNode, TNodeInterface, TList] = items
    
    def _GetValue(self) -> IEnumerable[TNodeInterface]:
        return _EnumerableListEnumerable[TItem, TNode, TNodeInterface, TList](self.__items)

@final
class _ReadOnlyUpdater[T](ValueFunctionUpdater[IReadOnlyList[T]]):
    def __init__(self, items: IReadWriteEnumerableList[T], updater: Method[IFunction[IReadOnlyList[T]]]) -> None:
        super().__init__(updater)

        self.__items: IReadWriteEnumerableList[T] = items
    
    def _GetValue(self) -> IReadOnlyList[T]:
        return _ReadOnlyList[T](self.__items)
@final
class _ReadOnlyEnumerableUpdater[T](ValueFunctionUpdater[IReadOnlyEnumerableList[T]]):
    def __init__(self, items: IReadWriteEnumerableList[T], updater: Method[IFunction[IReadOnlyEnumerableList[T]]]) -> None:
        super().__init__(updater)

        self.__items: IReadWriteEnumerableList[T] = items
    
    def _GetValue(self) -> IReadOnlyEnumerableList[T]:
        return _ReadOnlyEnumerableList[T](self.__items)

class _IListCookie[T](IInterface):
    @final
    class _LinkedListCookie[_T](Abstract, INodeCookie[_T]):
        def __init__(self) -> None:
            super().__init__()
        
        def SetFirst(self, node: _T|None, items: _IListCookie[_T]) -> None:
            return items._SetFirst(node)
        def SetLast(self, node: _T|None, items: _IListCookie[_T]) -> None:
            return items._SetLast(node)
    
    def __init__(self) -> None:
        super().__init__()
    
    def _GetCookie(self) -> INodeCookie[T]:
        return _IListCookie._LinkedListCookie[T]()
    
    @abstractmethod
    def _SetFirst(self, node: T|None) -> None:
        pass
    @abstractmethod
    def _SetLast(self, node: T|None) -> None:
        pass

class _EnumerableList[TItem, TNode](Enumerable[TItem], _IListCookie[TNode]):
    @final
    class _ListCookieUpdater[_T, _TNode](ValueFunctionUpdater[INodeCookie[_TNode]]):
        def __init__(self, items: _EnumerableList[_T, _TNode], updater: Method[IFunction[INodeCookie[_TNode]]]) -> None:
            super().__init__(updater)

            self.__items: _EnumerableList[_T, _TNode] = items
        
        def _GetValue(self) -> INodeCookie[_TNode]:
            return self.__items._GetListCookie()
    
    def __init__(self) -> None:
        def update(func: IFunction[INodeCookie[TNode]]) -> None:
            self.__updater = func
        
        super().__init__()
        
        self.__updater: IFunction[INodeCookie[TNode]] = _EnumerableList._ListCookieUpdater(self, update) # type: ignore[no-redef]
    
    @final
    def _GetListCookie(self) -> INodeCookie[TNode]:
        return super()._GetCookie()
    @final
    def _GetCookie(self) -> INodeCookie[TNode]:
        return self.__updater.GetValue()

class EnumerableListBase[TItem, TNode, TNodeInterface, TList](_EnumerableList[TItem, TNode], IEnumerableList[TItem, TNodeInterface], _IAbstractList[TItem, TNode], IAbstractNode[TNode, TNodeInterface]):
    def __init__(self) -> None:
        def updateNodeEnumerable(func: IFunction[IEnumerable[TNodeInterface]]) -> None:
            self.__nodeEnumerable = func
        def updateReadOnlyEnumerable(func: IFunction[IReadOnlyEnumerableList[TItem]]) -> None:
            self.__readOnlyEnumerable = func
        
        super().__init__()
        
        self.__first: TNode|None = None
        self.__last: TNode|None = None

        self.__nodeEnumerable: IFunction[IEnumerable[TNodeInterface]] = _EnumerableUpdater[TItem, TNode, TNodeInterface, TList](self, updateNodeEnumerable) # type: ignore[no-redef]
        self.__readOnlyEnumerable: IFunction[IReadOnlyEnumerableList[TItem]] = _ReadOnlyEnumerableUpdater[TItem](self, updateReadOnlyEnumerable) # type: ignore[no-redef]
    
    @abstractmethod
    def _GetNode(self, value: TItem) -> TNode:
        pass

    @final
    def _GetFirst(self) -> TNode|None:
        return self.__first
    @final
    def _GetLast(self) -> TNode|None:
        return self.__last
    
    @final
    def _SetFirst(self, node: TNode|None) -> None:
        self.__first = node
    @final
    def _SetLast(self, node: TNode|None) -> None:
        self.__last = node
    
    @final
    def __TryGetNodeAsClass(self, node: TNode|None) -> TNodeInterface|None:
        return None if node is None else self._GetNodeAsClass(node)

    @final
    def IsEmpty(self) -> bool:
        return self.__first is None
    @final
    def HasItems(self) -> bool:
        return super().HasItems()
    
    def _AddNode(self, value: TItem) -> TNode:
        node: TNode = self._GetNode(value)

        self._SetFirst(node)
        self._SetLast(node)
        
        return node
    
    @final
    def AddFirst(self, value: TItem) -> TNodeInterface:
        node: TNode|None = self._GetFirst()
        
        return self._GetNodeAsClass(self._AddNode(value) if node is None else self._GetNodeAsInterface(node).SetPreviousNode(value))
    @final
    def AddLast(self, value: TItem) -> TNodeInterface:
        node: TNode|None = self._GetLast()
        
        return self._GetNodeAsClass(self._AddNode(value) if node is None else self._GetNodeAsInterface(node).SetNextNode(value))
    
    @final
    def GetFirst(self) -> TNodeInterface|None:
        return self.__TryGetNodeAsClass(self._GetFirst())
    @final
    def GetLast(self) -> TNodeInterface|None:
        return self.__TryGetNodeAsClass(self._GetLast())
    
    @final
    def TryRemoveFirst(self) -> INullable[TItem]:
        node: TNode|None = self._GetFirst()

        return GetNullValue() if node is None else GetNullable(self._GetNodeAsInterface(node).Remove())
    @final
    def TryRemoveLast(self) -> INullable[TItem]:
        node: TNode|None = self._GetLast()

        return GetNullValue() if node is None else GetNullable(self._GetNodeAsInterface(node).Remove())
    
    @final
    def Clear(self) -> None:
        node: INullable[TItem] = self.TryRemoveFirst()

        while node.HasValue():
            node = self.TryRemoveFirst()
    
    @abstractmethod
    def _GetNodeEnumerator(self, node: TNodeInterface) -> IEnumerator[TNodeInterface]:
        pass
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None:
        first: TNode|None = self._GetFirst()

        return None if self.IsEmpty() or first is None else GetValueEnumeratorFromNode(self._GetNodeAsInterface(first)) # self.GetFirst() should not be None if self.IsEmpty().
    
    @final
    def TryGetNodeEnumerator(self) -> IEnumerator[TNodeInterface]|None:
        first: TNodeInterface|None = self.GetFirst()

        return None if self.IsEmpty() or first is None else self._GetNodeEnumerator(first) # self.GetFirst() should not be None if self.IsEmpty().
    @final
    def GetNodeEnumerator(self) -> IEnumerator[TNodeInterface]:
        return GetEnumerator(self.TryGetNodeEnumerator())
    
    @final
    def AsNodeEnumerable(self) -> IEnumerable[TNodeInterface]:
        return self.__nodeEnumerable.GetValue()
    
    @final
    def AsReadOnlyEnumerable(self) -> IReadOnlyEnumerableList[TItem]:
        return self.__readOnlyEnumerable.GetValue()
class EnumerableList[TItem, TNode, TNodeInterface, TList](EnumerableListBase[TItem, TNode, TNodeInterface, TList]):
    def __init__(self) -> None:
        def updateReadOnly(func: IFunction[IReadOnlyList[TItem]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyList[TItem]] = _ReadOnlyUpdater[TItem](self, updateReadOnly) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyList[TItem]:
        return self.__readOnly.GetValue()

class ListBase[TItem, TNode](EnumerableList[TItem, TNode, IDoublyLinkedNode[TItem], "ListBase[TItem, TNode]"], IList[TItem], IGenericConstraintImplementation[IDoublyLinkedNode[TItem]]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _AddNode(self, value: TItem) -> TNode:
        return super()._AddNode(value)
    
    @final
    def _GetNodeEnumerator(self, node: IDoublyLinkedNode[TItem]) -> IEnumerator[IDoublyLinkedNode[TItem]]:
        return DoublyLinkedNodeEnumerator[TItem](node)

class DoublyLinkedNodeAbstract[TItem, TNode, TNodeInterface, TList, TListInterface](DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface], _INodeBase[TItem, TNode, TNodeInterface, TListInterface], IAbstractNode[TNode, TNodeInterface]):
    def __init__(self, value: TItem, l: TListInterface|None, cookie: INodeCookie[TNode], previousNode: TNode|None, nextNode: TNode|None) -> None:
        super().__init__(value, l, previousNode, nextNode)

        self.__cookie = cookie
    
    @final
    def _GetCookie(self) -> INodeCookie[TNode]:
        return self.__cookie
    
    @final
    def _SetFirstNode(self, node: TNode|None, l: TListInterface) -> None:
        self._SetFirst(self._GetCookie(), self._GetListAsSpecialized(l), node)
    @final
    def _SetLastNode(self, node: TNode|None, l: TListInterface) -> None:
        self._SetLast(self._GetCookie(), self._GetListAsSpecialized(l), node)
    
    @final
    def _AddFirst(self, node: TNode, l: TListInterface) -> None:
        self._SetFirstNode(node, l)
    @final
    def _AddLast(self, node: TNode, l: TListInterface) -> None:
        self._SetLastNode(node, l)
    
    @final
    def _UpdateFirst(self, node: TNode, l: TListInterface) -> None:
        self._AddFirst(node, l)
    @final
    def _UpdateLast(self, node: TNode, l: TListInterface) -> None:
        self._AddLast(node, l)
    
    @final
    def _RemoveFirst(self, l: TListInterface) -> None:
        self._SetFirstNode(None, l)
    @final
    def _RemoveLast(self, l: TListInterface) -> None:
        self._SetLastNode(None, l)

class DoublyLinkedNode[TItem, TNode, TNodeInterface, TList, TListInterface](DoublyLinkedNodeAbstract[TItem, TNode, TNodeInterface, TList, TListInterface], IDoublyLinkedNode[TItem]):
    def __init__(self, value: TItem, l: TListInterface|None, cookie: INodeCookie[TNode], previousNode: TNode|None, nextNode: TNode|None) -> None:
        super().__init__(value, l, cookie, previousNode, nextNode)

    @abstractmethod
    def _AsLinkedNode(self, node: TNode) -> SelfType:
        pass
    def _TryAsLinkedNode(self, node: TNode|None) -> SelfType|None:
        return None if node is None else self._AsLinkedNode(node)
    
    @final
    def GetPrevious(self) -> SelfType|None:
        return self._TryAsLinkedNode(self.GetPreviousNode())
    @final
    def GetNext(self) -> SelfType|None:
        return self._TryAsLinkedNode(self.GetNextNode())
    
    @final
    def SetPrevious(self, value: TItem) -> SelfType:
        return self._AsLinkedNode(super()._SetPreviousNode(value))
    @final
    def SetNext(self, value: TItem) -> SelfType:
        return self._AsLinkedNode(super()._SetNextNode(value))
    
    @final
    def Remove(self) -> TItem:
        return super().Remove()

@final
class _Node[T](DoublyLinkedNode[T, "_Node[T]", IDoublyLinkedNode[T], IList[T], ListBase[T, "_Node[T]"]], EnumerableListNodeBase[T, "_Node[T]", IDoublyLinkedNode[T], ListBase[T, "_Node[T]"]], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, value: T, l: ListBase[T, _Node[T]]|None, cookie: INodeCookie[_Node[T]], previousNode: SelfType|None, nextNode: SelfType|None) -> None:
        super().__init__(value, l, cookie, previousNode, nextNode)
    
    def _AsLinkedNode(self, node: _Node[T]) -> _Node[T]:
        return node
    
    def _GetListAsClass(self, l: ListBase[T, _Node[T]]) -> IList[T]:
        return l
    def _GetListAsSpecialized(self, l: ListBase[T, _Node[T]]) -> EnumerableList[T, _Node[T], IDoublyLinkedNode[T], ListBase[T, _Node[T]]]:
        return l
    
    def _GetNodeAsClass(self, node: _Node[T]) -> IDoublyLinkedNode[T]:
        return node
    
    def _AsNode(self) -> _Node[T]:
        return self
    
    def _GetNode(self, value: T, previous: SelfType|None, next: SelfType|None) -> _Node[T]:
        return _Node[T](value, self._GetInnerList(), self._GetCookie(), previous, next)
    
    def GetList(self) -> IList[T]|None:
        return self._GetList()

class List[T](ListBase[T, _Node[T]]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _GetNodeAsClass(self, node: _Node[T]) -> IDoublyLinkedNode[T]:
        return node
    @final
    def _GetNodeAsInterface(self, node: _Node[T]) -> IDoublyLinkedNodeBase[T, _Node[T]]:
        return node
    
    @final
    def _GetNode(self, value: T) -> _Node[T]:
        return _Node[T](value, self, self._GetCookie(), None, None)

class ICountableLinkedListNode[T](INode[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetList(self) -> ICountableList[T]|None:
        pass

class CountableListProvider[T](Abstract):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetInnerItems(self) -> _CountableInnerList[T]:
        pass

    @abstractmethod
    def GetItems(self) -> ICountableList[T]:
        pass

    @abstractmethod
    def AsSized(self) -> Sized:
        pass

    @abstractmethod
    def OnAdded(self, node: ICountableLinkedListNode[T]) -> None:
        pass
    @abstractmethod
    def OnRemoved(self, value: T) -> None:
        pass

class IReadOnlyCountableList[T](IReadOnlyList[T], ICountable):
    def __init__(self) -> None:
        super().__init__()

class IReadOnlyCountableEnumerableList[T](IReadOnlyCountableList[T], IReadOnlyEnumerableList[T], ICountableEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
class IReadWriteCountableEnumerableList[T](IReadOnlyCountableEnumerableList[T], IReadWriteEnumerableList[T]):
    def __init__(self) -> None:
        super().__init__()

class ICountableList[T](IReadWriteCountableEnumerableList[T], IEnumerableList[T, ICountableLinkedListNode[T]]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[T]:
        pass

@final
class _ReadOnlyCountableEnumerableList[T](_ReadOnlyListBase[T, IReadOnlyCountableEnumerableList[T]], IReadOnlyCountableEnumerableList[T], IGenericConstraintImplementation[IReadOnlyCountableEnumerableList[T]]):
    def __init__(self, items: IReadOnlyCountableEnumerableList[T]) -> None:
        super().__init__(items)

        self.__items: CountableEnumerableBase[T] = CountableEnumerable[T].Create(items)
    
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self._GetContainer().TryGetEnumerator()
    
    def AsSized(self) -> Sized:
        return self.__items.AsSized()
    def AsIterable(self) -> Iterable[T]:
        return self.__items.AsIterable()

@final
class _ReadOnlyCountableUpdater[T](ValueFunctionUpdater[IReadOnlyCountableEnumerableList[T]]):
    def __init__(self, items: ICountableList[T], updater: Method[IFunction[IReadOnlyCountableEnumerableList[T]]]) -> None:
        super().__init__(updater)

        self.__items: ICountableList[T] = items
    
    def _GetValue(self) -> IReadOnlyCountableEnumerableList[T]:
        return _ReadOnlyCountableEnumerableList[T](self.__items)

class CountableListBase[TItem, TNode](EnumerableListBase[TItem, TNode, ICountableLinkedListNode[TItem], CountableListProvider[TItem]], ICountableList[TItem], IGenericConstraintImplementation[ICountableLinkedListNode[TItem]]):
    def __init__(self) -> None:
        def updateReadOnly(func: IFunction[IReadOnlyCountableEnumerableList[TItem]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyCountableEnumerableList[TItem]] = _ReadOnlyCountableUpdater[TItem](self, updateReadOnly) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[TItem]:
        return self.__readOnly.GetValue()
    
    @final
    def _GetNodeEnumerator(self, node: ICountableLinkedListNode[TItem]) -> IEnumerator[ICountableLinkedListNode[TItem]]:
        return CountableLinkedListNodeEnumerator[TItem](node)

@final
class _CountableListNode[T](DoublyLinkedNodeAbstract[T, "_CountableListNode[T]", ICountableLinkedListNode[T], ICountableList[T], CountableListProvider[T]], NodeBase[T, "_CountableListNode[T]"], EnumerableListNodeBase[T, "_CountableListNode[T]", ICountableLinkedListNode[T], CountableListProvider[T]], ICountableLinkedListNode[T], IGenericConstraintImplementation[ICountableList[T]]):
    def __init__(self, value: T, l: CountableListProvider[T]|None, cookie: INodeCookie[_CountableListNode[T]], previousNode: SelfType|None, nextNode: SelfType|None) -> None:
        super().__init__(value, l, cookie, previousNode, nextNode)
    
    @final
    def _GetListAsClass(self, l: CountableListProvider[T]) -> ICountableList[T]:
        return l.GetItems()
    @final
    def _GetListAsSpecialized(self, l: CountableListProvider[T]) -> EnumerableListBase[T, _CountableListNode[T], ICountableLinkedListNode[T], CountableListProvider[T]]:
        return l.GetInnerItems()
    
    @final
    def _GetNodeAsClass(self, node: _CountableListNode[T]) -> ICountableLinkedListNode[T]:
        return node
    
    @final
    def _AsNode(self) -> SelfType:
        return self
    
    @final
    def _AsLinkedNode(self, node: _CountableListNode[T]) -> DoublyLinkedNodeBase[T, _CountableListNode[T], ICountableList[T], CountableListProvider[T]]:
        return node
    
    @final
    def _GetNode(self, value: T, previous: SelfType|None, next: SelfType|None) -> _CountableListNode[T]:
        return _CountableListNode[T](value, self._GetInnerList(), self._GetCookie(), previous, next)
    
    @final
    def GetList(self) -> ICountableList[T]|None:
        return self._GetList()
    
    @final
    def GetPrevious(self) -> _CountableListNode[T]|None:
        return self.GetPreviousNode()
    @final
    def GetNext(self) -> _CountableListNode[T]|None:
        return self.GetNextNode()
    
    @final
    def _OnAdded(self, node: ICountableLinkedListNode[T]) -> None:
        l: CountableListProvider[T]|None = self._GetInnerList()

        if l is not None:
            l.OnAdded(node)
    @final
    def _OnRemoved(self, l: CountableListProvider[T]|None, value: T) -> None:
        if l is not None:
            l.OnRemoved(value)
    
    @final
    def SetPrevious(self, value: T) -> _CountableListNode[T]:
        node: _CountableListNode[T] = self._SetPreviousNode(value)

        self._OnAdded(node)

        return node
    @final
    def SetNext(self, value: T) -> _CountableListNode[T]:
        node: _CountableListNode[T] = self._SetNextNode(value)

        self._OnAdded(node)

        return node
    
    @final
    def Remove(self) -> T:
        l: CountableListProvider[T]|None = self._GetInnerList()

        value: T = super().Remove()

        self._OnRemoved(l, value)

        return value

@final
class _CountableInnerList[T](CountableListBase[T, _CountableListNode[T]]):
    def __init__(self, l: CountableListProvider[T]) -> None:
        super().__init__()

        self.__items: CountableListProvider[T] = l
        self.__count: int = 0
    
    def _GetNodeAsClass(self, node: _CountableListNode[T]) -> ICountableLinkedListNode[T]:
        return node
    def _GetNodeAsInterface(self, node: _CountableListNode[T]) -> IDoublyLinkedNodeBase[T, _CountableListNode[T]]:
        return node
    
    def _GetNode(self, value: T) -> _CountableListNode[T]:
        return _CountableListNode[T](value, self.__items, self._GetCookie(), None, None)
    
    @final
    def _AddNode(self, value: T) -> _CountableListNode[T]:
        node: _CountableListNode[T] = super()._AddNode(value)

        self.Increment()

        return node
    
    def AsSized(self) -> Sized:
        return self.__items.AsSized()
    
    def GetCount(self) -> int:
        return self.__count
    
    def Increment(self) -> None:
        self.__count += 1
    def Decrement(self) -> None:
        self.__count -= 1

class CountableList[T](CountableEnumerableBase[T], ICountableList[T], IGenericConstraintImplementation[ICountableLinkedListNode[T]]):
    @final
    class _CountableListProvider[_T](CountableListProvider[_T]):
        def __init__(self, l: CountableList[_T]) -> None:
            super().__init__()

            self.__items: CountableList[_T] = l
        
        def GetInnerItems(self) -> _CountableInnerList[_T]:
            return self.__items._GetItems()
        
        def GetItems(self) -> ICountableList[_T]:
            return self.__items
        
        def AsSized(self) -> Sized:
            return self.GetItems().AsSized()
        
        def OnAdded(self, node: ICountableLinkedListNode[_T]) -> None:
            self.__items._OnAdded(node)
        def OnRemoved(self, value: _T) -> None:
            self.__items._OnRemoved(value)
    
    def __init__(self) -> None:
        super().__init__()

        self.__items: _CountableInnerList[T] = _CountableInnerList[T](CountableList[T]._CountableListProvider(self))
    
    @final
    def _OnAdded(self, node: ICountableLinkedListNode[T]) -> None:
        self._GetItems().Increment()
    
    @final
    def _OnRemoved(self, value: T) -> None:
        self._GetItems().Decrement()
    
    @final
    def _GetItems(self) -> _CountableInnerList[T]:
        return self.__items
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[T]:
        return self._GetItems().AsReadOnly()
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetItems().IsEmpty()
    
    @final
    def GetCount(self) -> int:
        return self._GetItems().GetCount()
    
    @final
    def GetFirst(self) -> ICountableLinkedListNode[T]|None:
        return self._GetItems().GetFirst()
    @final
    def GetLast(self) -> ICountableLinkedListNode[T]|None:
        return self._GetItems().GetLast()
    
    @final
    def AddFirst(self, value: T) -> ICountableLinkedListNode[T]:
        return self._GetItems().AddFirst(value)
    @final
    def AddLast(self, value: T) -> ICountableLinkedListNode[T]:
        return self._GetItems().AddLast(value)
    
    @final
    def TryRemoveFirst(self) -> INullable[T]:
        return self._GetItems().TryRemoveFirst()
    @final
    def TryRemoveLast(self) -> INullable[T]:
        return self._GetItems().TryRemoveLast()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self._GetItems().TryGetEnumerator()
    @final
    def TryGetNodeEnumerator(self) -> IEnumerator[ICountableLinkedListNode[T]]|None:
        return self._GetItems().TryGetNodeEnumerator()
    
    @final
    def AsReadOnlyEnumerable(self) -> IReadOnlyEnumerableList[T]:
        return self._GetItems().AsReadOnlyEnumerable()
    
    @final
    def AsNodeEnumerable(self) -> IEnumerable[ICountableLinkedListNode[T]]:
        return self._GetItems().AsNodeEnumerable()
    
    @final
    def Clear(self) -> None:
        self._GetItems().Clear()

class DoublyLinkedNodeEnumeratorBase[TItems, TNode](NodeEnumeratorBase[TItems, TNode]):
    def __init__(self, node: TNode) -> None:
        super().__init__(node)

class DoublyLinkedNodeEnumerator[T](DoublyLinkedNodeEnumeratorBase[T, IDoublyLinkedNode[T]], IGenericConstraintImplementation[IDoublyLinkedNode[T]]):
    def __init__(self, node: IDoublyLinkedNode[T]) -> None:
        super().__init__(node)

    def _GetNextNode(self, node: IDoublyLinkedNode[T]) -> IDoublyLinkedNode[T]|None:
        return self._AsContainer(node).GetNext()
class CountableLinkedListNodeEnumerator[T](DoublyLinkedNodeEnumeratorBase[T, ICountableLinkedListNode[T]], IGenericConstraintImplementation[ICountableLinkedListNode[T]]):
    def __init__(self, node: ICountableLinkedListNode[T]) -> None:
        super().__init__(node)

    def _GetNextNode(self, node: ICountableLinkedListNode[T]) -> ICountableLinkedListNode[T]|None:
        return self._AsContainer(node).GetNext()