from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator, Sized
from typing import final, Callable, Self as SelfType

from WinCopies import IInterface, Abstract
from WinCopies.Assertion import EnsureTrue
from WinCopies.Collections import Generator, IReadOnlyCollection, ICountable
from WinCopies.Collections.Abstraction.Enumeration import Enumerator
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, Enumerable, CountableEnumerable, Iterator, Accessor, GetEnumerator
from WinCopies.Collections.Linked.Enumeration import NodeEnumeratorBase, GetValueEnumeratorFromNode
from WinCopies.Collections.Linked.Node import ILinkedNode, LinkedNode
from WinCopies.Typing import IGenericConstraint, IGenericConstraintImplementation, GenericConstraint, INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Method, Function, Converter, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

class INode[T](ILinkedNode[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetList(self) -> IReadWriteList[T]|None:
        pass
    
    @abstractmethod
    def GetPrevious(self) -> SelfType|None:
        pass
    
    @abstractmethod
    def SetPrevious(self, value: T) -> SelfType:
        pass
    @abstractmethod
    def SetNext(self, value: T) -> SelfType:
        pass
    
    @abstractmethod
    def Remove(self) -> T:
        pass
class IDoublyLinkedNode[T](INode[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetList(self) -> IList[T]|None:
        pass
class IDoublyLinkedNodeBase[TItem, TNode](INode[TItem]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _AsNode(self) -> TNode:
        pass
    
    @final
    def SetPreviousNode(self, value: TItem) -> TNode:
        return self.SetPrevious(value)._AsNode()
    @final
    def SetNextNode(self, value: TItem) -> TNode:
        return self.SetNext(value)._AsNode()

class NodeBase[TItem, TNode: 'NodeBase'](LinkedNode[TNode, TItem], IDoublyLinkedNodeBase[TItem, TNode]):
    def __init__(self, value: TItem, previousNode: TNode|None, nextNode: TNode|None):
        super().__init__(value, nextNode)

        self.__previous: TNode|None = previousNode
    
    @final
    def GetPrevious(self) -> TNode|None:
        return self.__previous
    @final
    def _SetPrevious(self, previous: TNode|None) -> None:
        self.__previous = previous

class IReadOnlyList[T](IReadOnlyCollection):
    def __init__(self):
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

class __IAbstractList[TItem, TNode](IInterface):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def _GetNodeAsInterface(self, node: TNode) -> IDoublyLinkedNodeBase[TItem, TNode]:
        pass
class IAbstractNode[TNode, TNodeInterface](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _GetNodeAsClass(self, node: TNode) -> TNodeInterface:
        pass

class IReadWriteList[T](IReadOnlyList[T]):
    def __init__(self):
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
    def __AddItems(self, items: Iterable[T]|None, first: Converter[T, INode[T]], other: Converter[INode[T], Converter[T, INode[T]]]) -> bool:
        if items is None:
            return False
        
        node: INode[T] = None # type: ignore
        adder: Converter[T, INode[T]]|None = None

        def add(item: T) -> INode[T]:
            def add(item: T) -> INode[T]:
                return other(node)(item)

            nonlocal adder

            adder = add

            return first(item)
        
        adder = add

        for item in items:
            node = adder(item)
        
        return True

    @final
    def AddFirstItems(self, items: Iterable[T]|None) -> bool:
        return self.__AddItems(items, self.AddFirstNode, lambda node: node.SetNext)
    @final
    def AddFirstValues(self, *values: T) -> bool:
        return self.AddFirstItems(values)
    @final
    def AddLastItems(self, items: Iterable[T]|None) -> bool:
        return self.__AddItems(items, self.AddLastNode, lambda node: node.SetPrevious)
    @final
    def AddLastValues(self, *values: T) -> bool:
        return self.AddLastItems(values)
    
    @abstractmethod
    def RemoveFirst(self) -> INullable[T]:
        pass
    @abstractmethod
    def RemoveLast(self) -> INullable[T]:
        pass
    
    @abstractmethod
    def Clear(self) -> None:
        pass
    
    @final
    def __AsEnumerator(self, func: Function[INullable[T]]) -> IEnumerator[T]:
        def enumerate() -> Generator[T]:
            result: INullable[T] = func()

            while result.HasValue():
                yield result.GetValue()
                
                result = func()
        
        return Accessor(lambda: Iterator(enumerate()))
    
    @final
    def AsQueuedEnumerator(self) -> IEnumerator[T]:
        return self.__AsEnumerator(self.RemoveFirst)
    @final
    def AsStackedEnumerator(self) -> IEnumerator[T]:
        return self.__AsEnumerator(self.RemoveLast)

class IListBase[TItem, TNode](IReadWriteList[TItem], IGenericConstraint[TNode, INode[TItem]]):
    def __init__(self):
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
    def __init__(self):
        super().__init__()
class IReadWriteEnumerableList[T](IReadWriteList[T], IReadOnlyEnumerableList[T]):
    def __init__(self):
        super().__init__()

class IEnumerableList[TItem, TNode](IListBase[TItem, TNode], IReadWriteEnumerableList[TItem]):
    def __init__(self):
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
    def __init__(self):
        super().__init__()

class _INodeBase[TItem, TNode, TNodeInterface, TList](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _GetListAsSpecialized(self, l: TList) -> EnumerableList[TItem, TNode, TNodeInterface, TList]:
        pass
    
    @abstractmethod
    def _SetFirst(self, l: TList, node: TNodeInterface|None) -> None:
        pass
    @abstractmethod
    def _SetLast(self, l: TList, node: TNodeInterface|None) -> None:
        pass

class DoublyLinkedNodeBase[TItem, TNode: "DoublyLinkedNodeBase", TList, TListInterface](NodeBase[TItem, TNode], IGenericConstraint[TList, IReadWriteList[TItem]]):
    def __init__(self, value: TItem, l: TListInterface|None, previousNode: TNode|None, nextNode: TNode|None):
        EnsureDirectModuleCall()

        super().__init__(value, previousNode, nextNode)

        self.__list: TListInterface|None = l
    
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
    
    def SetPrevious(self, value: TItem) -> SelfType:
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

        previousNode: TNode|None = self.GetPrevious()
        newNode: TNode|None = tryAddFirst()
        
        if newNode is None:
            newNode = getNode(previousNode)

        if previousNode is not None:
            previousNode._SetNext(newNode)
        
        self._SetPrevious(newNode)

        return newNode._AsNode()
    def SetNext(self, value: TItem) -> SelfType:
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
        
        nextNode: TNode|None = self.GetNext()
        newNode: TNode|None = tryAddLast()
        
        if newNode is None:
            newNode = getNode(nextNode)

        if nextNode is not None:
            nextNode._SetPrevious(newNode)
        
        self._SetNext(newNode)

        return newNode._AsNode()
    
    @final
    def SetPreviousItems(self, items: Iterable[TItem]|None) -> bool:
        def add(node: DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface], item: TItem) -> TNode:
            nonlocal adder

            adder = lambda node, item: node.SetNextNode(item)

            return node.SetPreviousNode(item)

        if items is None:
            return False
        
        adder: Callable[[DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface], TItem], TNode] = add
        node: DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface] = self
        
        for item in items:
            node = adder(node, item)

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

            node._SetPrevious(previousNode)
        def removeLast(node: TNode, nextNode: TNode|None) -> None:
            self._SetPrevious(None)

            node._SetNext(nextNode)
        
        previousNode: TNode|None = self.GetPrevious()
        nextNode: TNode|None = self.GetNext()

        if previousNode is None:
            l: TListInterface|None = self._GetInnerList()
            
            if nextNode is None:
                if l is not None:
                    self._RemoveFirst(l)
                    self._RemoveLast(l)
            
            else:
                if l is not None:
                    self._UpdateFirst(nextNode, l)

                removeFirst(nextNode, None)

        elif nextNode is None:
            l: TListInterface|None = self._GetInnerList()

            if l is not None:
                self._UpdateLast(previousNode, l)
            
            removeLast(previousNode, None)
        
        else:
            removeFirst(nextNode, previousNode)
            removeLast(previousNode, nextNode)

        return self.GetValue()
    
    def Check(self, l: TList) -> bool:
        return self._GetList() is l
    def Ensure(self, l: TList) -> None:
        EnsureTrue(self.Check(l))

class _ReadOnlyListBase[TItem, TList](IReadOnlyList[TItem], GenericConstraint[TList, IReadOnlyList[TItem]]):
    def __init__(self, items: TList):
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

class EnumerableList[TItem, TNode, TNodeInterface, TList](Enumerable[TItem], IEnumerableList[TItem, TNodeInterface], __IAbstractList[TItem, TNode], IAbstractNode[TNode, TNodeInterface]):
    class NodeBase(_INodeBase[TItem, TNode, TNodeInterface, TList]):
        def __init__(self):
            super().__init__()
        
        @final
        def _SetFirst(self, l: TList, node: TNode|None) -> None:
            self._GetListAsSpecialized(l)._SetFirst(node)
        @final
        def _SetLast(self, l: TList, node: TNode|None) -> None:
            self._GetListAsSpecialized(l)._SetLast(node)
    @final
    class __Enumerable(Enumerable[TNodeInterface]):
        def __init__(self, l: EnumerableList[TItem, TNode, TNodeInterface, TList]):
            super().__init__()

            self.__list: EnumerableList[TItem, TNode, TNodeInterface, TList] = l
        
        def TryGetEnumerator(self) -> IEnumerator[TNodeInterface]|None:
            return self.__list.TryGetNodeEnumerator()
    
    class _ReadOnlyList(_ReadOnlyListBase[TItem, IReadOnlyList[TItem]], IGenericConstraintImplementation[IReadOnlyList[TItem]]):
        def __init__(self, items: IReadOnlyList[TItem]):
            super().__init__(items)
    class _ReadOnlyEnumerableList(_ReadOnlyListBase[TItem, IReadOnlyEnumerableList[TItem]], IReadOnlyEnumerableList[TItem], IGenericConstraintImplementation[IReadOnlyEnumerableList[TItem]]):
        def __init__(self, items: IReadOnlyEnumerableList[TItem]):
            super().__init__(items)
        
        @final
        def TryGetEnumerator(self) -> IEnumerator[TItem]|None:
            return Enumerator[TItem].TryCreate(self._GetContainer().TryGetEnumerator())
    
    @final
    class __EnumerableUpdater(ValueFunctionUpdater[IEnumerable[TNodeInterface]]):
        def __init__(self, items: EnumerableList[TItem, TNode, TNodeInterface, TList], updater: Method[IFunction[IEnumerable[TNodeInterface]]]):
            super().__init__(updater)

            self.__items: EnumerableList[TItem, TNode, TNodeInterface, TList] = items
        
        def _GetValue(self) -> IEnumerable[TNodeInterface]:
            return EnumerableList[TItem, TNode, TNodeInterface, TList].__Enumerable(self.__items)
    
    @final
    class __ReadOnlyUpdater(ValueFunctionUpdater[IReadOnlyList[TItem]]):
        def __init__(self, items: EnumerableList[TItem, TNode, TNodeInterface, TList], updater: Method[IFunction[IReadOnlyList[TItem]]]):
            super().__init__(updater)

            self.__items: EnumerableList[TItem, TNode, TNodeInterface, TList] = items
        
        def _GetValue(self) -> IReadOnlyList[TItem]:
            return self.__items._AsReadOnly()
    @final
    class __ReadOnlyEnumerableUpdater(ValueFunctionUpdater[IReadOnlyEnumerableList[TItem]]):
        def __init__(self, items: EnumerableList[TItem, TNode, TNodeInterface, TList], updater: Method[IFunction[IReadOnlyEnumerableList[TItem]]]):
            super().__init__(updater)

            self.__items: EnumerableList[TItem, TNode, TNodeInterface, TList] = items
        
        def _GetValue(self) -> IReadOnlyEnumerableList[TItem]:
            return self.__items._AsReadOnlyEnumerable()
    
    def __init__(self):
        def updateNodeEnumerable(func: IFunction[IEnumerable[TNodeInterface]]) -> None:
            self.__nodeEnumerable = func
        def updateReadOnly(func: IFunction[IReadOnlyList[TItem]]) -> None:
            self.__readOnly = func
        def updateReadOnlyEnumerable(func: IFunction[IReadOnlyEnumerableList[TItem]]) -> None:
            self.__readOnlyEnumerable = func
        
        super().__init__()
        
        self.__first: TNode|None = None
        self.__last: TNode|None = None

        self.__nodeEnumerable: IFunction[IEnumerable[TNodeInterface]] = EnumerableList[TItem, TNode, TNodeInterface, TList].__EnumerableUpdater(self, updateNodeEnumerable)
        self.__readOnly: IFunction[IReadOnlyList[TItem]] = EnumerableList[TItem, TNode, TNodeInterface, TList].__ReadOnlyUpdater(self, updateReadOnly)
        self.__readOnlyEnumerable: IFunction[IReadOnlyEnumerableList[TItem]] = EnumerableList[TItem, TNode, TNodeInterface, TList].__ReadOnlyEnumerableUpdater(self, updateReadOnlyEnumerable)
    
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
        EnsureDirectModuleCall()

        self.__first = node
    @final
    def _SetLast(self, node: TNode|None) -> None:
        EnsureDirectModuleCall()

        self.__last = node
    
    @final
    def __TryGetNodeAsClass(self, node: TNode|None) -> TNodeInterface|None:
        return None if node is None else self._GetNodeAsClass(node)
    
    def _AsReadOnly(self) -> IReadOnlyList[TItem]:
        return EnumerableList[TItem, TNode, TNodeInterface, TList]._ReadOnlyList(self)
    @final
    def AsReadOnly(self) -> IReadOnlyList[TItem]:
        return self.__readOnly.GetValue()
    
    def _AsReadOnlyEnumerable(self) -> IReadOnlyEnumerableList[TItem]:
        return EnumerableList[TItem, TNode, TNodeInterface, TList]._ReadOnlyEnumerableList(self)
    @final
    def AsReadOnlyEnumerable(self) -> IReadOnlyEnumerableList[TItem]:
        return self.__readOnlyEnumerable.GetValue()

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
    def RemoveFirst(self) -> INullable[TItem]:
        node: TNode|None = self._GetFirst()

        return GetNullValue() if node is None else GetNullable(self._GetNodeAsInterface(node).Remove())
    @final
    def RemoveLast(self) -> INullable[TItem]:
        node: TNode|None = self._GetLast()

        return GetNullValue() if node is None else GetNullable(self._GetNodeAsInterface(node).Remove())
    
    @final
    def Clear(self) -> None:
        node: INullable[TItem] = self.RemoveFirst()

        while node.HasValue():
            node = self.RemoveFirst()
    
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
        enumerator: IEnumerator[TNodeInterface]|None = self.TryGetNodeEnumerator()

        return GetEnumerator(enumerator)
    
    @final
    def AsNodeEnumerable(self) -> IEnumerable[TNodeInterface]:
        return self.__nodeEnumerable.GetValue()

class ListBase[TItem, TNode](EnumerableList[TItem, TNode, IDoublyLinkedNode[TItem], "ListBase"], IList[TItem], IGenericConstraintImplementation[IDoublyLinkedNode[TItem]]):
    def __init__(self):
        super().__init__()
    
    @final
    def _AddNode(self, value: TItem) -> TNode:
        return super()._AddNode(value)
    
    @final
    def _GetNodeEnumerator(self, node: IDoublyLinkedNode[TItem]) -> IEnumerator[IDoublyLinkedNode[TItem]]:
        return DoublyLinkedNodeEnumerator[TItem](node)

class _DoublyLinkedNode[TItem, TNode: "_DoublyLinkedNode", TNodeInterface, TList, TListInterface](DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface], _INodeBase[TItem, TNode, TNodeInterface, TListInterface], IAbstractNode[TNode, TNodeInterface]):
    def __init__(self, value: TItem, l: TListInterface|None, previousNode: TNode|None, nextNode: TNode|None):
        super().__init__(value, l, previousNode, nextNode)
    
    @final
    def _AddFirst(self, node: TNode, l: TListInterface) -> None:
        self._SetFirst(l, self._GetNodeAsClass(node))
    @final
    def _AddLast(self, node: TNode, l: TListInterface) -> None:
        self._SetLast(l, self._GetNodeAsClass(node))
    
    @final
    def _UpdateFirst(self, node: TNode, l: TListInterface) -> None:
        self._AddFirst(node, l)
    @final
    def _UpdateLast(self, node: TNode, l: TListInterface) -> None:
        self._AddLast(node, l)
    
    @final
    def _RemoveFirst(self, l: TListInterface) -> None:
        self._SetFirst(l, None)
    @final
    def _RemoveLast(self, l: TListInterface) -> None:
        self._SetLast(l, None)

class DoublyLinkedNode[TItem, TNode: "DoublyLinkedNode", TNodeInterface, TList, TListInterface](_DoublyLinkedNode[TItem, TNode, TNodeInterface, TList, TListInterface]):
    def __init__(self, value: TItem, l: TListInterface|None, previousNode: TNode|None, nextNode: TNode|None):
        super().__init__(value, l, previousNode, nextNode)
    
    @final
    def SetPrevious(self, value: TItem) -> SelfType:
        return super().SetPrevious(value)
    
    @final
    def SetNext(self, value: TItem) -> SelfType:
        return super().SetNext(value)
    
    @final
    def Remove(self) -> TItem:
        return super().Remove()

@final
class _Node[T](DoublyLinkedNode[T, "_Node", IDoublyLinkedNode[T], IList[T], ListBase[T, "_Node"]], EnumerableList[T, "_Node", IDoublyLinkedNode[T], ListBase[T, "_Node"]].NodeBase, IDoublyLinkedNode[T], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, value: T, l: ListBase[T, _Node[T]]|None, previousNode: SelfType|None, nextNode: SelfType|None):
        super().__init__(value, l, previousNode, nextNode)
    
    @final
    def _GetListAsClass(self, l: ListBase[T, _Node[T]]) -> IList[T]:
        return l
    @final
    def _GetListAsSpecialized(self, l: ListBase[T, _Node[T]]) -> EnumerableList[T, _Node[T], IDoublyLinkedNode[T], ListBase[T, _Node[T]]]:
        return l
    
    @final
    def _GetNodeAsClass(self, node: _Node[T]) -> IDoublyLinkedNode[T]:
        return node
    
    @final
    def _AsNode(self) -> _Node[T]:
        return self
    
    @final
    def _GetNode(self, value: T, previous: SelfType|None, next: SelfType|None) -> _Node[T]:
        return _Node[T](value, self._GetInnerList(), previous, next)
    
    @final
    def GetList(self) -> IList[T]|None:
        return self._GetList()

class List[T](ListBase[T, _Node[T]]):
    def __init__(self):
        super().__init__()
    
    @final
    def _GetNodeAsClass(self, node: _Node[T]) -> IDoublyLinkedNode[T]:
        return node
    @final
    def _GetNodeAsInterface(self, node: _Node[T]) -> IDoublyLinkedNodeBase[T, _Node[T]]:
        return node
    
    @final
    def _GetNode(self, value: T) -> _Node[T]:
        return _Node[T](value, self, None, None)

class ICountableLinkedListNode[T](INode[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetList(self) -> ICountableList[T]|None:
        pass

class CountableListProvider[T](Abstract):
    def __init__(self):
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

class ICountableList[T](IEnumerableList[T, ICountableLinkedListNode[T]], ICountable):
    def __init__(self):
        super().__init__()

class CountableListBase[TItem, TNode](EnumerableList[TItem, TNode, ICountableLinkedListNode[TItem], CountableListProvider[TItem]], ICountableList[TItem], IGenericConstraintImplementation[ICountableLinkedListNode[TItem]]):
    def __init__(self):
        super().__init__()
    
    @final
    def _GetNodeEnumerator(self, node: ICountableLinkedListNode[TItem]) -> IEnumerator[ICountableLinkedListNode[TItem]]:
        return CountableLinkedListNodeEnumerator[TItem](node)

@final
class _CountableListNode[T](_DoublyLinkedNode[T, "_CountableListNode", ICountableLinkedListNode[T], ICountableList[T], CountableListProvider[T]], EnumerableList[T, "_CountableListNode", ICountableLinkedListNode[T], CountableListProvider[T]].NodeBase, ICountableLinkedListNode[T], IGenericConstraintImplementation[ICountableList[T]]):
    def __init__(self, value: T, l: CountableListProvider[T]|None, previousNode: SelfType|None, nextNode: SelfType|None):
        super().__init__(value, l, previousNode, nextNode)
    
    @final
    def _GetListAsClass(self, l: CountableListProvider[T]) -> ICountableList[T]:
        return l.GetItems()
    @final
    def _GetListAsSpecialized(self, l: CountableListProvider[T]) -> EnumerableList[T, _CountableListNode[T], ICountableLinkedListNode[T], CountableListProvider[T]]:
        return l.GetInnerItems()
    
    @final
    def _GetNodeAsClass(self, node: _CountableListNode[T]) -> ICountableLinkedListNode[T]:
        return node
    
    @final
    def _AsNode(self) -> SelfType:
        return self
    
    @final
    def _GetNode(self, value: T, previous: SelfType|None, next: SelfType|None) -> _CountableListNode[T]:
        return _CountableListNode[T](value, self._GetInnerList(), previous, next)
    
    @final
    def GetList(self) -> ICountableList[T]|None:
        return self._GetList()
    
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
        node: _CountableListNode[T] = super().SetPrevious(value)

        self._OnAdded(node)

        return node
    @final
    def SetNext(self, value: T) -> _CountableListNode[T]:
        node: _CountableListNode[T] = super().SetNext(value)

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
    def __init__(self, l: CountableListProvider[T]):
        super().__init__()

        self.__items: CountableListProvider[T] = l
        self.__count: int = 0
    
    def _GetNodeAsClass(self, node: _CountableListNode[T]) -> ICountableLinkedListNode[T]:
        return node
    def _GetNodeAsInterface(self, node: _CountableListNode[T]) -> IDoublyLinkedNodeBase[T, _CountableListNode[T]]:
        return node
    
    def _GetNode(self, value: T) -> _CountableListNode[T]:
        return _CountableListNode[T](value, self.__items, None, None)
    
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

class CountableList[T](CountableEnumerable[T], ICountableList[T], IGenericConstraintImplementation[ICountableLinkedListNode[T]]):
    @final
    class __CountableListProvider(CountableListProvider[T]):
        def __init__(self, l: CountableList[T]):
            super().__init__()

            self.__items: CountableList[T] = l
        
        def GetInnerItems(self) -> _CountableInnerList[T]:
            return self.__items._GetItems()
        
        def GetItems(self) -> ICountableList[T]:
            return self.__items
        
        def AsSized(self) -> Sized:
            return self.GetItems().AsSized()
        
        def OnAdded(self, node: ICountableLinkedListNode[T]) -> None:
            self.__items._OnAdded(node)
        def OnRemoved(self, value: T) -> None:
            self.__items._OnRemoved(value)
    
    def __init__(self):
        super().__init__()

        self.__items: _CountableInnerList[T] = _CountableInnerList[T](CountableList[T].__CountableListProvider(self))
    
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
    def AsReadOnly(self) -> IReadOnlyList[T]:
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
    def RemoveFirst(self) -> INullable[T]:
        return self._GetItems().RemoveFirst()
    @final
    def RemoveLast(self) -> INullable[T]:
        return self._GetItems().RemoveLast()
    
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
    def __init__(self, node: TNode):
        super().__init__(node)

class DoublyLinkedNodeEnumerator[T](DoublyLinkedNodeEnumeratorBase[T, IDoublyLinkedNode[T]], IGenericConstraintImplementation[IDoublyLinkedNode[T]]):
    def __init__(self, node: IDoublyLinkedNode[T]):
        super().__init__(node)

    def _GetNextNode(self, node: IDoublyLinkedNode[T]) -> IDoublyLinkedNode[T]|None:
        return self._AsContainer(node).GetNext()
class CountableLinkedListNodeEnumerator[T](DoublyLinkedNodeEnumeratorBase[T, ICountableLinkedListNode[T]], IGenericConstraintImplementation[ICountableLinkedListNode[T]]):
    def __init__(self, node: ICountableLinkedListNode[T]):
        super().__init__(node)

    def _GetNextNode(self, node: ICountableLinkedListNode[T]) -> ICountableLinkedListNode[T]|None:
        return self._AsContainer(node).GetNext()