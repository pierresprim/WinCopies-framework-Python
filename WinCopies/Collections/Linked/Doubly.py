from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Sized
from typing import final, Callable, Self as SelfType

from WinCopies import IInterface, Abstract
from WinCopies.Assertion import EnsureTrue
from WinCopies.Collections import Generator as GeneratorBase, EnumerationOrder
from WinCopies.Collections.Abstraction.Enumeration import CreateCountableEnumerable, TryCreateEnumerator
from WinCopies.Collections.Core import IReadOnlyCollection, ICountable, IClearable, Countable
from WinCopies.Collections.Enumeration import IEnumerable, ICountableEnumerable, IReversableEnumerable, IReversableCountableEnumerable, IEnumerator, Enumerable, CountableEnumerable, GetEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerable, IResumableCountableEnumerable, IResumableEnumerator, GetResumableEnumerator
from WinCopies.Collections.Enumeration.Resumable.Linked import TwoWayResumableNodeEnumerator
from WinCopies.Collections.Generation import IRemovable, INode as INodeBase, IIterator, Generator, ConverterBase
from WinCopies.Collections.Linked.Enumeration import TwoWayNodeEnumeratorBase, GetValueEnumeratorFromNode
from WinCopies.Collections.Linked.Node import ILinkedNode, ITwoWayLinkedNode, LinkedNode
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Method, Function, Converter, NullableSelector, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import IGenericConstraint, IGenericConstraintImplementation, GenericConstraint

class INode[T](ITwoWayLinkedNode[T], INodeBase):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetList(self) -> IReadWriteList[T]|None:
        ...
    
    @abstractmethod
    def GetPrevious(self) -> SelfType|None:
        ...
    @abstractmethod
    def GetNext(self) -> SelfType|None:
        ...
    
    @abstractmethod
    def SetPrevious(self, value: T) -> INode[T]:
        ...
    @abstractmethod
    def SetNext(self, value: T) -> INode[T]:
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
    def GetList(self) -> IList[T]|None:
        ...
    
    @abstractmethod
    def GetPrevious(self) -> IDoublyLinkedNode[T]|None:
        ...
    @abstractmethod
    def GetNext(self) -> IDoublyLinkedNode[T]|None:
        ...
    
    @abstractmethod
    def SetPrevious(self, value: T) -> IDoublyLinkedNode[T]:
        ...
    @abstractmethod
    def SetNext(self, value: T) -> IDoublyLinkedNode[T]:
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

class IReadOnlyList[T](IReadOnlyCollection):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryGetFirst(self) -> INullable[T]:
        ...
    @abstractmethod
    def TryGetLast(self) -> INullable[T]:
        ...

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
    
    @final
    def GetFirstValue(self) -> T:
        return self.TryGetFirst().GetValue()
    @final
    def GetLastValue(self) -> T:
        return self.TryGetLast().GetValue()

class _IAbstractList[TItem, TNode](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetNodeAsInterface(self, node: TNode) -> IDoublyLinkedNodeBase[TItem, TNode]:
        ...
class IAbstractNode[TNode, TNodeInterface](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetNodeAsClass(self, node: TNode) -> TNodeInterface:
        ...

class IReadWriteList[T](IReadOnlyList[T], IClearable):
    def __init__(self) -> None: super().__init__()

    @final
    def __TryGet(self, node: INode[T]|None) -> INullable[T]:
        return GetNullValue() if node is None else GetNullable(node.GetValue())
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyList[T]:
        ...
    
    @abstractmethod
    def GetFirstNode(self) -> INode[T]|None:
        ...
    @abstractmethod
    def GetLastNode(self) -> INode[T]|None:
        ...
    
    @final
    def TryGetFirst(self) -> INullable[T]:
        return self.__TryGet(self.GetFirstNode())
    @final
    def TryGetLast(self) -> INullable[T]:
        return self.__TryGet(self.GetLastNode())
    
    @abstractmethod
    def AddFirstNode(self, value: T) -> INode[T]:
        ...
    @abstractmethod
    def AddLastNode(self, value: T) -> INode[T]:
        ...

    @final
    def __AddItems(self, items: Iterable[T]|None, first: Converter[T, INode[T]]) -> bool:
        if items is None: return False
        
        node: INode[T] = None # type: ignore
        adder: Converter[T, INode[T]]|None = None

        def add(item: T) -> INode[T]:
            def add(item: T) -> INode[T]: return node.SetNext(item)

            nonlocal adder

            adder = add

            return first(item)
        
        adder = add

        for item in items: node = adder(item)
        
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
        ...
    @abstractmethod
    def TryRemoveLast(self) -> INullable[T]:
        ...
    
    @final
    def __AsGenerator(self, func: Function[INullable[T]]) -> GeneratorBase[T]:
        result: INullable[T] = func()

        while result.HasValue():
            yield result.GetValue()
            
            result = func()
    
    @final
    def AsQueuedGenerator(self) -> GeneratorBase[T]:
        return self.__AsGenerator(self.TryRemoveFirst)
    @final
    def AsStackedGenerator(self) -> GeneratorBase[T]:
        return self.__AsGenerator(self.TryRemoveLast)

class IListBase[TItem, TNode](IReadWriteList[TItem], IGenericConstraint[TNode, INode[TItem]]):
    def __init__(self) -> None: super().__init__()

    @final
    def __TryGet(self, node: TNode|None) -> INode[TItem]|None:
        return None if node is None else self._AsContainer(node)
    
    @abstractmethod
    def GetFirst(self) -> TNode|None:
        ...
    @abstractmethod
    def GetLast(self) -> TNode|None:
        ...

    @final
    def GetFirstNode(self) -> INode[TItem]|None:
        return self.__TryGet(self.GetFirst())
    @final
    def GetLastNode(self) -> INode[TItem]|None:
        return self.__TryGet(self.GetLast())
    
    @abstractmethod
    def AddFirst(self, value: TItem) -> TNode:
        ...
    @abstractmethod
    def AddLast(self, value: TItem) -> TNode:
        ...

    @final
    def AddFirstNode(self, value: TItem) -> INode[TItem]:
        return self._AsContainer(self.AddFirst(value))
    @final
    def AddLastNode(self, value: TItem) -> INode[TItem]:
        return self._AsContainer(self.AddLast(value))

class IReadOnlyEnumerableListBase[T](IReadOnlyList[T], IEnumerable[T]):
    def __init__(self) -> None: super().__init__()
class IReadOnlyEnumerableList[T](IReadOnlyEnumerableListBase[T], IReversableEnumerable[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> IReadOnlyEnumerableList[T]:
        ...

class IReadWriteEnumerableListBase[T](IReadWriteList[T], IReadOnlyEnumerableListBase[T]):
    def __init__(self) -> None: super().__init__()
class IReadWriteEnumerableList[T](IReadWriteEnumerableListBase[T], IReadOnlyEnumerableList[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyEnumerableList[T]:
        ...
    
    @abstractmethod
    def AsReversed(self) -> IReadWriteEnumerableList[T]:
        ...

class IEnumerableListBase[TItem, TNode](IListBase[TItem, TNode], IReadWriteEnumerableListBase[TItem]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryGetNodeEnumerator(self) -> IEnumerator[TNode]|None:
        ...
    @final
    def GetNodeEnumerator(self) -> IEnumerator[TNode]:
        return GetEnumerator(self.TryGetNodeEnumerator())
    
    @abstractmethod
    def TryGetResumableNodeEnumerator(self) -> IResumableEnumerator[TNode]|None:
        ...
    @final
    def GetResumableNodeEnumerator(self) -> IResumableEnumerator[TNode]:
        return GetResumableEnumerator(self.TryGetResumableNodeEnumerator())
    
    @abstractmethod
    def AsNodeEnumerable(self) -> IResumableEnumerable[TNode]:
        ...

    @abstractmethod
    def AsNodeGenerator(self) -> IIterator[TNode]:
        ...
    @abstractmethod
    def AsGenerator(self) -> IIterator[TItem]:
        ...
class IEnumerableList[TItem, TNode](IEnumerableListBase[TItem, TNode], IReadWriteEnumerableList[TItem]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> IEnumerableList[TItem, TNode]:
        ...

class IList[T](IEnumerableList[T, IDoublyLinkedNode[T]]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> IList[T]:
        ...

class ICountableLinkedListNode[T](INode[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetList(self) -> ICountableList[T]|None:
        ...

class IReadOnlyCountableList[T](IReadOnlyList[T], IReversableCountableEnumerable[T]):
    def __init__(self) -> None: super().__init__()

class IReadOnlyCountableEnumerableList[T](IReadOnlyCountableList[T], IReadOnlyEnumerableList[T], ICountableEnumerable[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> IReadOnlyCountableEnumerableList[T]:
        ...
class IReadWriteCountableEnumerableList[T](IReadOnlyCountableEnumerableList[T], IReadWriteEnumerableList[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> IReadWriteCountableEnumerableList[T]:
        ...

class ICountableList[T](IReadWriteCountableEnumerableList[T], IEnumerableList[T, ICountableLinkedListNode[T]]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsNodeEnumerable(self) -> IResumableCountableEnumerable[ICountableLinkedListNode[T]]:
        ...
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[T]:
        ...
    
    @abstractmethod
    def AsReversed(self) -> ICountableList[T]:
        ...

class _INodeBase[TNode, TList](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetListAsSpecialized(self, l: TList) -> _IListCookie[TNode]:
        ...
    
    @abstractmethod
    def _SetFirst(self, cookie: INodeCookie[TNode], items: _IListCookie[TNode], node: TNode|None) -> None:
        ...
    @abstractmethod
    def _SetLast(self, cookie: INodeCookie[TNode], items: _IListCookie[TNode], node: TNode|None) -> None:
        ...

class _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface: IClearable](NodeBase[TItem, TNode], IGenericConstraint[TList, IReadWriteList[TItem]]):
    def __init__(self, value: TItem, l: TListInterface|None, previousNode: TNode|None, nextNode: TNode|None) -> None:
        super().__init__(value, previousNode, nextNode)

        self.__list: TListInterface|None = l

    @abstractmethod
    def _AsLinkedNode(self, node: TNode) -> _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]:
        ...
    def _TryAsLinkedNode(self, node: TNode|None) -> _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None:
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
    
    def GetPrevious(self) -> _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None: return self._TryAsLinkedNode(self.GetPreviousNode())
    def GetNext(self) -> _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None: return self._TryAsLinkedNode(self.GetNextNode())
    
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
    def _RemoveFirst(self, l: TListInterface) -> None:
        ...
    @abstractmethod
    def _RemoveLast(self, l: TListInterface) -> None:
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
    
    def SetPrevious(self, value: TItem) -> _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]: return self._AsLinkedNode(self._SetPreviousNode(value))
    def SetNext(self, value: TItem) -> _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]: return self._AsLinkedNode(self._SetNextNode(value))
    
    @final
    def SetPreviousItems(self, items: Iterable[TItem]|None) -> bool:
        adder: Callable[[_DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface], TItem], TNode]|None = None

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
        
        node: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface] = self
        
        for item in items: node = node.SetNext(item)

        return True
    @final
    def SetNextValues(self, *values: TItem) -> bool: return self.SetNextItems(values)
    
    @final
    def __RemoveFirst(self, node: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface], previousNode: TNode|None) -> None:
        self._SetNext(None)

        node._SetPrevious(previousNode)
    @final
    def __RemoveLast(self, node: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface], nextNode: TNode|None) -> None:
        self._SetPrevious(None)

        node._SetNext(nextNode)
    
    def RemoveNode(self) -> TItem:
        def whenFirst(nextNode: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None) -> bool:
            l: TListInterface|None = self._GetInnerList()
            
            if nextNode is None:
                if l is not None:
                    l.Clear()

                    return False
            
            else:
                if l is not None: self._UpdateFirst(nextNode._AsNode(), l)

                self.__RemoveFirst(nextNode, None)
            
            return True
        def whenLast(previousNode: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]) -> None:
            l: TListInterface|None = self._GetInnerList()

            if l is not None: self._UpdateLast(previousNode._AsNode(), l)
            
            self.__RemoveLast(previousNode, None)
        
        previousNode: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None = self.GetPrevious()
        nextNode: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None = self.GetNext()

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
        def unregister(node: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]) -> None:
            def enumerate(node: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]) -> GeneratorBase[_DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]]:
                yield node

                _node: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None = node.GetPrevious()

                while _node is not None:
                    yield node

                    _node = self.GetPrevious()
            
            for _node in enumerate(node): _node._Unregister()

        previousNode: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None = self.GetPrevious()
        
        if previousNode is None:
            if inclusive: self.Remove()
            
            return
        
        l: TListInterface|None = self._GetInnerList()

        if inclusive:
            node: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None = self.GetNext()

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
        def unregister(node: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]) -> None:
            def enumerate(node: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]) -> GeneratorBase[_DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]]:
                yield node

                _node: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None = node.GetNext()

                while _node is not None:
                    yield node

                    _node = self.GetNext()
            
            for _node in enumerate(node): _node._Unregister()

        nextNode: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None = self.GetNext()
        
        if nextNode is None:
            if inclusive: self.Remove()
            
            return
        
        l: TListInterface|None = self._GetInnerList()

        if inclusive:
            node: _DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface]|None = self.GetPrevious()

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

class _ReadOnlyListBase[TItem, TList](Abstract, IReadOnlyEnumerableListBase[TItem], GenericConstraint[TList, IReadOnlyEnumerableListBase[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__items: TList = items
    
    @final
    def _GetContainer(self) -> TList: return self.__items
    
    @final
    def IsEmpty(self) -> bool: return self._GetInnerContainer().IsEmpty()
    
    @final
    def HasItems(self) -> bool: return super().HasItems()
    
    @final
    def TryGetFirst(self) -> INullable[TItem]: return self._GetInnerContainer().TryGetFirst()
    @final
    def TryGetLast(self) -> INullable[TItem]: return self._GetInnerContainer().TryGetLast()

class INodeCookie[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetFirst(self, items: _IListCookie[T]) -> T|None:
        ...
    @abstractmethod
    def GetLast(self, items: _IListCookie[T]) -> T|None:
        ...
    
    @abstractmethod
    def SetFirst(self, node: T|None, items: _IListCookie[T]) -> None:
        ...
    @abstractmethod
    def SetLast(self, node: T|None, items: _IListCookie[T]) -> None:
        ...

class EnumerableListNodeBase[TNode, TList](_INodeBase[TNode, TList]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _SetFirst(self, cookie: INodeCookie[TNode], items: _IListCookie[TNode], node: TNode|None) -> None:
        cookie.SetFirst(node, items)
    @final
    def _SetLast(self, cookie: INodeCookie[TNode], items: _IListCookie[TNode], node: TNode|None) -> None:
        cookie.SetLast(node, items)

@final
class _EnumerableListEnumerable[TItem, TNode: IRemovable](Enumerable[TNode], IResumableEnumerable[TNode]):
    def __init__(self, l: IEnumerableListBase[TItem, TNode]) -> None:
        super().__init__()

        self.__list: IEnumerableListBase[TItem, TNode] = l
    
    def TryGetEnumerator(self) -> IEnumerator[TNode]|None: return self.__list.TryGetNodeEnumerator()
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[TNode]|None: return self.__list.TryGetResumableNodeEnumerator()
@final
class _CountableEnumerableListEnumerable[T](Enumerable[ICountableLinkedListNode[T]], IResumableCountableEnumerable[ICountableLinkedListNode[T]]):
    def __init__(self, l: ICountableList[T]) -> None:
        super().__init__()

        self.__list: ICountableList[T] = l
    
    def GetCount(self) -> int: return self.__list.GetCount()
    
    def TryGetEnumerator(self) -> IEnumerator[ICountableLinkedListNode[T]]|None: return self.__list.TryGetNodeEnumerator()
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[ICountableLinkedListNode[T]]|None: return self.__list.TryGetResumableNodeEnumerator()
    
    def AsSized(self) -> Sized: return self.__list.AsSized()

@final
class _ReversedReadOnlyListUpdater[TItem, TNode: IRemovable](ValueFunctionUpdater[IReadOnlyEnumerableList[TItem]]):
    def __init__(self, items: IEnumerableList[TItem, TNode], updater: Method[IFunction[IReadOnlyEnumerableList[TItem]]]) -> None:
        super().__init__(updater)

        self.__items: IEnumerableList[TItem, TNode] = items
    
    def _GetValue(self) -> IReadOnlyEnumerableList[TItem]: return _ReversedReadOnlyList[TItem, TNode](self.__items)
@final
class _ReversedReadOnlyCountableListUpdater[T](ValueFunctionUpdater[IReadOnlyCountableEnumerableList[T]]):
    def __init__(self, items: ICountableList[T], updater: Method[IFunction[IReadOnlyCountableEnumerableList[T]]]) -> None:
        super().__init__(updater)

        self.__items: ICountableList[T] = items
    
    def _GetValue(self) -> IReadOnlyCountableEnumerableList[T]: return _ReversedReadOnlyCountableList[T](self.__items)

class _ReadOnlyEnumerableListAbstractAbstract[TItem, TList](_ReadOnlyListBase[TItem, TList], Enumerable[TItem], IReadOnlyEnumerableListBase[TItem]):
    def __init__(self, items: TList) -> None: super().__init__(items)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None: return TryCreateEnumerator(self._GetInnerContainer().TryGetEnumerator())

@final
class _ReadOnlyEnumerableListAbstractBase[TItem, TNode: IRemovable](_ReadOnlyEnumerableListAbstractAbstract[TItem, IReadOnlyEnumerableListBase[TItem]], IGenericConstraintImplementation[IReadOnlyEnumerableListBase[TItem]]):
    def __init__(self, items: IEnumerableListBase[TItem, TNode]) -> None: super().__init__(items)
@final
class _ReadOnlyEnumerableList[TItem, TNode: IRemovable](_ReadOnlyEnumerableListAbstractAbstract[TItem, IReadOnlyEnumerableList[TItem]], Enumerable[TItem], IReadOnlyEnumerableList[TItem], IGenericConstraintImplementation[IReadOnlyEnumerableList[TItem]]):
    def __init__(self, items: IEnumerableList[TItem, TNode]) -> None:
        def update(func: IFunction[IReadOnlyEnumerableList[TItem]]) -> None: self.__reversed = func
        
        super().__init__(items)

        self.__reversed: IFunction[IReadOnlyEnumerableList[TItem]] = _ReversedReadOnlyListUpdater[TItem, TNode](items, update) # type: ignore[no-redef]
    
    def AsReversed(self) -> IReadOnlyEnumerableList[TItem]: return self.__reversed.GetValue()

@final
class _EnumerableUpdater[TItem, TNode: IRemovable](ValueFunctionUpdater[IResumableEnumerable[TNode]]):
    def __init__(self, items: IEnumerableListBase[TItem, TNode], updater: Method[IFunction[IResumableEnumerable[TNode]]]) -> None:
        super().__init__(updater)

        self.__items: IEnumerableListBase[TItem, TNode] = items
    
    def _GetValue(self) -> IResumableEnumerable[TNode]: return _EnumerableListEnumerable[TItem, TNode](self.__items)
@final
class _CountableEnumerableUpdater[T](ValueFunctionUpdater[IResumableCountableEnumerable[ICountableLinkedListNode[T]]]):
    def __init__(self, items: ICountableList[T], updater: Method[IFunction[IResumableCountableEnumerable[ICountableLinkedListNode[T]]]]) -> None:
        super().__init__(updater)

        self.__items: ICountableList[T] = items
    
    def _GetValue(self) -> IResumableCountableEnumerable[ICountableLinkedListNode[T]]: return _CountableEnumerableListEnumerable[T](self.__items)

@final
class _ReadOnlyEnumerableUpdaterBase[TItem, TNode: IRemovable](ValueFunctionUpdater[IReadOnlyEnumerableListBase[TItem]]):
    def __init__(self, items: IEnumerableListBase[TItem, TNode], updater: Method[IFunction[IReadOnlyEnumerableListBase[TItem]]]) -> None:
        super().__init__(updater)

        self.__items: IEnumerableListBase[TItem, TNode] = items
    
    def _GetValue(self) -> IReadOnlyEnumerableListBase[TItem]: return _ReadOnlyEnumerableListAbstractBase[TItem, TNode](self.__items)
@final
class _ReadOnlyEnumerableUpdater[TItem, TNode: IRemovable](ValueFunctionUpdater[IReadOnlyEnumerableList[TItem]]):
    def __init__(self, items: IEnumerableList[TItem, TNode], updater: Method[IFunction[IReadOnlyEnumerableList[TItem]]]) -> None:
        super().__init__(updater)

        self.__items: IEnumerableList[TItem, TNode] = items
    
    def _GetValue(self) -> IReadOnlyEnumerableList[TItem]: return _ReadOnlyEnumerableList[TItem, TNode](self.__items)

class _IListCookie[T](IInterface):
    @final
    class _LinkedListCookie[_T](Abstract, INodeCookie[_T]):
        def __init__(self) -> None: super().__init__()
        
        def GetFirst(self, items: _IListCookie[_T]) -> _T|None: return items._GetFirst()
        def GetLast(self, items: _IListCookie[_T]) -> _T|None: return items._GetLast()
        
        def SetFirst(self, node: _T|None, items: _IListCookie[_T]) -> None: return items._SetFirst(node)
        def SetLast(self, node: _T|None, items: _IListCookie[_T]) -> None: return items._SetLast(node)
    
    def __init__(self) -> None: super().__init__()
    
    def _GetCookie(self) -> INodeCookie[T]:
        return _IListCookie._LinkedListCookie[T]()
    
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

class _EnumerableList[TItem, TNode](Enumerable[TItem], _IListCookie[TNode]):
    @final
    class _ListCookieUpdater[_T, _TNode](ValueFunctionUpdater[INodeCookie[_TNode]]):
        def __init__(self, items: _EnumerableList[_T, _TNode], updater: Method[IFunction[INodeCookie[_TNode]]]) -> None:
            super().__init__(updater)

            self.__items: _EnumerableList[_T, _TNode] = items
        
        def _GetValue(self) -> INodeCookie[_TNode]: return self.__items._GetListCookie()
    
    def __init__(self) -> None:
        def update(func: IFunction[INodeCookie[TNode]]) -> None: self.__cookie = func
        
        super().__init__()
        
        self.__cookie: IFunction[INodeCookie[TNode]] = _EnumerableList[TItem, TNode]._ListCookieUpdater(self, update) # type: ignore[no-redef]
    
    @final
    def _GetListCookie(self) -> INodeCookie[TNode]:
        return super()._GetCookie()
    @final
    def _GetCookie(self) -> INodeCookie[TNode]:
        return self.__cookie.GetValue()

class IValueCookie[TItem, TNode](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetItems(self) -> IEnumerableListBase[TItem, TNode]:
        ...

    @abstractmethod
    def GetValue(self, node: TNode) -> TItem:
        ...

@final
class _Generator[TItem, TNode: IRemovable](ConverterBase[TNode, TItem]):
    def __init__(self, cookie: IValueCookie[TItem, TNode]) -> None:
        super().__init__()

        self.__cookie: IValueCookie[TItem, TNode] = cookie
    
    def _GetItems(self) -> IIterator[TNode]:
        return self.__cookie.GetItems().AsNodeGenerator()
    
    def _Convert(self, item: TNode) -> TItem:
        return self.__cookie.GetValue(item)

@final
class _NodeGeneratorUpdater[TItem, TNode: IRemovable](ValueFunctionUpdater[IIterator[TNode]]):
    def __init__(self, items: IEnumerableListBase[TItem, TNode], updater: Method[IFunction[IIterator[TNode]]]) -> None:
        super().__init__(updater)

        self.__items: IEnumerableListBase[TItem, TNode] = items
    
    def _GetValue(self) -> IIterator[TNode]: return Generator[TNode](self.__items.AsNodeEnumerable().AsIterable())
@final
class _GeneratorUpdater[TItem, TNode: IRemovable](ValueFunctionUpdater[IIterator[TItem]]):
    def __init__(self, cookie: IValueCookie[TItem, TNode], updater: Method[IFunction[IIterator[TItem]]]) -> None:
        super().__init__(updater)

        self.__cookie: IValueCookie[TItem, TNode] = cookie
    
    def _GetValue(self) -> IIterator[TItem]: return _Generator[TItem, TNode](self.__cookie)

class _EnumerableListAbstract[TItem, TNode](IEnumerableListBase[TItem, TNode]):
    @final
    class _Cookie[_TItem, _TNode](Abstract, IValueCookie[_TItem, _TNode]):
        def __init__(self, items: _EnumerableListAbstract[_TItem, _TNode]) -> None:
            super().__init__()

            self.__items: _EnumerableListAbstract[_TItem, _TNode] = items
        
        def GetItems(self) -> IEnumerableListBase[_TItem, _TNode]: return self.__items
        
        def GetValue(self, node: _TNode) -> _TItem: return self.__items._GetValue(node)
    
    def __init__(self) -> None: super().__init__()
    
    @final
    def _GetValue(self, node: TNode) -> TItem:
        return self._AsContainer(node).GetValue()
    
    def _GetValueCookie(self) -> IValueCookie[TItem, TNode]:
        return _EnumerableListAbstract[TItem, TNode]._Cookie(self)

class IEnumerableListCookieAbstract[TItem, TNode, TReadOnly](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetValueCookie(self) -> IValueCookie[TItem, TNode]:
        ...
    
    @abstractmethod
    def GetNodeEnumerable(self) -> IResumableEnumerable[TNode]:
        ...
    @abstractmethod
    def GetReadOnly(self) -> TReadOnly:
        ...
    
    @abstractmethod
    def GetNodeGenerator(self) -> IIterator[TNode]:
        ...
    @abstractmethod
    def GetGenerator(self) -> IIterator[TItem]:
        ...
class ICountableEnumerableListCookieAbstract[TItem, TNode, TReadOnly](IEnumerableListCookieAbstract[TItem, TNode, TReadOnly]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetNodeEnumerable(self) -> IResumableCountableEnumerable[TNode]:
        ...

class IEnumerableListCookieBase[TItem, TNode](IEnumerableListCookieAbstract[TItem, TNode, IReadOnlyEnumerableListBase[TItem]]):
    def __init__(self) -> None: super().__init__()
class IEnumerableListCookie[TItem, TNode](IEnumerableListCookieAbstract[TItem, TNode, IReadOnlyEnumerableList[TItem]]):
    def __init__(self) -> None: super().__init__()

class ICountableEnumerableListCookie[TItem, TNode](ICountableEnumerableListCookieAbstract[TItem, TNode, IReadOnlyCountableEnumerableList[TItem]]):
    def __init__(self) -> None: super().__init__()

class _EnumerableListBase[TItem, TNode: IRemovable, TList, TReadOnly](Abstract, IEnumerableListCookieAbstract[TItem, TNode, TReadOnly]):
    def __init__(self, items: TList, cookie: IValueCookie[TItem, TNode]) -> None:
        def updateReadOnlyEnumerable(func: IFunction[TReadOnly]) -> None: self.__readOnlyEnumerable = func
        
        def updateNodeGenerator(func: IFunction[IIterator[TNode]]) -> None: self.__nodeGenerator = func
        def updateGenerator(func: IFunction[IIterator[TItem]]) -> None: self.__generator = func
        
        super().__init__()

        self.__cookie: IValueCookie[TItem, TNode] = cookie

        self.__readOnlyEnumerable: IFunction[TReadOnly] = self._CreateReadOnly(items, updateReadOnlyEnumerable) # type: ignore[no-redef]
        
        self.__nodeGenerator: IFunction[IIterator[TNode]] = _NodeGeneratorUpdater[TItem, TNode](self._AsList(items), updateNodeGenerator) # type: ignore[no-redef]
        self.__generator: IFunction[IIterator[TItem]] = _GeneratorUpdater[TItem, TNode](cookie, updateGenerator) # type: ignore[no-redef]
    
    @abstractmethod
    def _CreateReadOnly(self, items: TList, action: Method[IFunction[TReadOnly]]) -> IFunction[TReadOnly]:
        ...
    
    @abstractmethod
    def _AsList(self, items: TList) -> IEnumerableListBase[TItem, TNode]:
        ...
    
    @final
    def GetValueCookie(self) -> IValueCookie[TItem, TNode]: return self.__cookie
    
    @final
    def GetReadOnly(self) -> TReadOnly: return self.__readOnlyEnumerable.GetValue()
    
    @final
    def GetNodeGenerator(self) -> IIterator[TNode]: return self.__nodeGenerator.GetValue()
    @final
    def GetGenerator(self) -> IIterator[TItem]: return self.__generator.GetValue()

@final
class _ReadOnlyEnumerableListAbstract[TItem, TNode: IRemovable](_EnumerableListBase[TItem, TNode, IEnumerableListBase[TItem, TNode], IReadOnlyEnumerableListBase[TItem]], IEnumerableListCookieBase[TItem, TNode]):
    def __init__(self, items: IEnumerableListBase[TItem, TNode], cookie: IValueCookie[TItem, TNode]) -> None:
        def updateNodeEnumerable(func: IFunction[IResumableEnumerable[TNode]]) -> None: self.__nodeEnumerable = func
        
        super().__init__(items, cookie)

        self.__nodeEnumerable: IFunction[IResumableEnumerable[TNode]] = _EnumerableUpdater[TItem, TNode](items, updateNodeEnumerable) # type: ignore[no-redef]
    
    def _CreateReadOnly(self, items: IEnumerableListBase[TItem, TNode], action: Method[IFunction[IReadOnlyEnumerableListBase[TItem]]]) -> IFunction[IReadOnlyEnumerableListBase[TItem]]:
        return _ReadOnlyEnumerableUpdaterBase[TItem, TNode](items, action)
    
    def _AsList(self, items: IEnumerableListBase[TItem, TNode]) -> IEnumerableListBase[TItem, TNode]:
        return items
    
    def GetNodeEnumerable(self) -> IResumableEnumerable[TNode]: return self.__nodeEnumerable.GetValue()
@final
class _ReadOnlyEnumerableListBase[TItem, TNode: IRemovable](_EnumerableListBase[TItem, TNode, IEnumerableList[TItem, TNode], IReadOnlyEnumerableList[TItem]], IEnumerableListCookie[TItem, TNode]):
    def __init__(self, items: IEnumerableList[TItem, TNode], cookie: IValueCookie[TItem, TNode]) -> None:
        def updateNodeEnumerable(func: IFunction[IResumableEnumerable[TNode]]) -> None: self.__nodeEnumerable = func
        
        super().__init__(items, cookie)

        self.__nodeEnumerable: IFunction[IResumableEnumerable[TNode]] = _EnumerableUpdater[TItem, TNode](items, updateNodeEnumerable) # type: ignore[no-redef]
    
    def _CreateReadOnly(self, items: IEnumerableList[TItem, TNode], action: Method[IFunction[IReadOnlyEnumerableList[TItem]]]) -> IFunction[IReadOnlyEnumerableList[TItem]]:
        return _ReadOnlyEnumerableUpdater[TItem, TNode](items, action)
    
    def _AsList(self, items: IEnumerableList[TItem, TNode]) -> IEnumerableList[TItem, TNode]:
        return items
    
    def GetNodeEnumerable(self) -> IResumableEnumerable[TNode]: return self.__nodeEnumerable.GetValue()

class _Enumerable[TItem, TNode, TNodeInterface: IRemovable, TEnumerable, TCookie](_EnumerableList[TItem, TNode], _EnumerableListAbstract[TItem, TNodeInterface], _IAbstractList[TItem, TNode], IAbstractNode[TNode, TNodeInterface]):
    def __init__(self, items: Iterable[TItem]|None) -> None:
        super().__init__()
        
        self.__first: TNode|None = None
        self.__last: TNode|None = None

        self.__cookie: TCookie = self._CreateEnumerationCookie(super()._GetValueCookie())

        self.AddLastItems(items)
    
    @abstractmethod
    def _CreateEnumerationCookie(self, cookie: IValueCookie[TItem, TNodeInterface]) -> TCookie:
        ...

    @abstractmethod
    def _GetCookieAsEnumerationCookie(self, items: TCookie) -> IEnumerableListCookieAbstract[TItem, TNodeInterface, TEnumerable]:
        ...

    @final
    def _GetEnumerationCookie(self) -> TCookie:
        return self.__cookie
    @final
    def _GetInnerCookie(self) -> IEnumerableListCookieAbstract[TItem, TNodeInterface, TEnumerable]:
        return self._GetCookieAsEnumerationCookie(self._GetEnumerationCookie())

    @final
    def _AsReadOnly(self) -> TEnumerable:
        return self._GetInnerCookie().GetReadOnly()
    
    @abstractmethod
    def _CreateNode(self, value: TItem) -> TNode:
        pass
    
    @final
    def _GetValueCookie(self) -> IValueCookie[TItem, TNodeInterface]:
        return self._GetInnerCookie().GetValueCookie()

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
    def IsEmpty(self) -> bool: return self.__first is None
    @final
    def HasItems(self) -> bool: return super().HasItems()
    
    def _AddNode(self, value: TItem) -> TNode:
        node: TNode = self._CreateNode(value)

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
    def GetFirst(self) -> TNodeInterface|None: return self.__TryGetNodeAsClass(self._GetFirst())
    @final
    def GetLast(self) -> TNodeInterface|None: return self.__TryGetNodeAsClass(self._GetLast())
    
    @final
    def __TryRemove(self, node: TNode|None) -> INullable[TItem]:
        return GetNullValue() if node is None else GetNullable(self._GetNodeAsInterface(node).RemoveNode())
    
    @final
    def TryRemoveFirst(self) -> INullable[TItem]: return self.__TryRemove(self._GetFirst())
    @final
    def TryRemoveLast(self) -> INullable[TItem]: return self.__TryRemove(self._GetLast())
    
    @abstractmethod
    def _GetPreviousNode(self, node: TNode) -> TNode|None:
        ...
    @abstractmethod
    def _GetNextNode(self, node: TNode) -> TNode|None:
        ...

    @abstractmethod
    def _UnregisterNode(self, node: TNode) -> None:
        ...
    
    @final
    def Clear(self) -> None:
        def enumerate() -> GeneratorBase[TNode]:
            node: TNode|None = self._GetFirst()

            while node is not None:
                yield node

                node = self._GetNextNode(node)
        
        for node in enumerate(): self._UnregisterNode(node)

        self.__first = None
        self.__last = None
    
    @abstractmethod
    def _GetNodeEnumerator(self, node: TNodeInterface) -> IEnumerator[TNodeInterface]:
        ...
    @abstractmethod
    def _GetResumableNodeEnumerator(self, node: TNodeInterface) -> IResumableEnumerator[TNodeInterface]:
        ...
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None:
        first: TNode|None = self._GetFirst()

        return None if first is None else GetValueEnumeratorFromNode(self._GetNodeAsInterface(first))
    
    @final
    def TryGetNodeEnumerator(self) -> IEnumerator[TNodeInterface]|None:
        first: TNodeInterface|None = self.GetFirst()

        return None if first is None else self._GetNodeEnumerator(first)
    @final
    def TryGetResumableNodeEnumerator(self) -> IResumableEnumerator[TNodeInterface]|None:
        first: TNodeInterface|None = self.GetFirst()

        return None if first is None else self._GetResumableNodeEnumerator(first)

    @final
    def AsNodeGenerator(self) -> IIterator[TNodeInterface]: return self._GetInnerCookie().GetNodeGenerator()
    @final
    def AsGenerator(self) -> IIterator[TItem]: return self._GetInnerCookie().GetGenerator()
class EnumerableListAbstract[TItem, TNode, TNodeInterface: IRemovable, TEnumerable](_Enumerable[TItem, TNode, TNodeInterface, TEnumerable, IEnumerableListCookieAbstract[TItem, TNodeInterface, TEnumerable]]):
    def __init__(self, items: Iterable[TItem]|None = None) -> None: super().__init__(items)
    
    @final
    def _GetCookieAsEnumerationCookie(self, items: IEnumerableListCookieAbstract[TItem, TNodeInterface, TEnumerable]) -> IEnumerableListCookieAbstract[TItem, TNodeInterface, TEnumerable]:
        return items
    
    @final
    def AsNodeEnumerable(self) -> IResumableEnumerable[TNodeInterface]: return self._GetInnerCookie().GetNodeEnumerable()
class EnumerableListBase[TItem, TNode, TNodeInterface: IRemovable](EnumerableListAbstract[TItem, TNode, TNodeInterface, IReadOnlyEnumerableListBase[TItem]]):
    def __init__(self, items: Iterable[TItem]|None = None) -> None: super().__init__(items)
    
    @final
    def _CreateEnumerationCookie(self, cookie: IValueCookie[TItem, TNodeInterface]) -> IEnumerableListCookieAbstract[TItem, TNodeInterface, IReadOnlyEnumerableListBase[TItem]]:
        return _ReadOnlyEnumerableListAbstract[TItem, TNodeInterface](self, cookie)
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableListBase[TItem]: return self._AsReadOnly()
class EnumerableList[TItem, TNode, TNodeInterface: IRemovable](EnumerableListAbstract[TItem, TNode, TNodeInterface, IReadOnlyEnumerableList[TItem]], IEnumerableList[TItem, TNodeInterface]):
    def __init__(self, items: Iterable[TItem]|None) -> None: super().__init__(items)
    
    @final
    def _CreateEnumerationCookie(self, cookie: IValueCookie[TItem, TNodeInterface]) -> IEnumerableListCookieAbstract[TItem, TNodeInterface, IReadOnlyEnumerableList[TItem]]:
        return _ReadOnlyEnumerableListBase[TItem, TNodeInterface](self, cookie)
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableList[TItem]: return self._AsReadOnly()

class ListBase[TItem, TNode](EnumerableList[TItem, TNode, IDoublyLinkedNode[TItem]], IList[TItem], IGenericConstraintImplementation[IDoublyLinkedNode[TItem]]):
    def __init__(self, items: Iterable[TItem]|None) -> None: super().__init__(items)
    
    @final
    def _AddNode(self, value: TItem) -> TNode:
        return super()._AddNode(value)
    
    @final
    def _GetNodeEnumerator(self, node: IDoublyLinkedNode[TItem]) -> IEnumerator[IDoublyLinkedNode[TItem]]:
        return DoublyLinkedNodeEnumerator[TItem](node)
    @final
    def _GetResumableNodeEnumerator(self, node: IDoublyLinkedNode[TItem]) -> IResumableEnumerator[IDoublyLinkedNode[TItem]]:
        return ResumableDoublyLinkedNodeEnumerator[TItem](node)

class DoublyLinkedNodeAbstract[TItem, TNode, TNodeInterface: IRemovable, TList, TListInterface: IClearable](_DoublyLinkedNodeBase[TItem, TNode, TList, TListInterface], _INodeBase[TNode, TListInterface], IAbstractNode[TNode, TNodeInterface]):
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
    
    @final
    def TryMoveToTop(self) -> bool|None:
        _l: TListInterface|None = self._GetInnerList()

        if _l is None: return False
        
        if self.GetPrevious() is None: return None
        
        l: _IListCookie[TNode] = self._GetListAsSpecialized(_l)
        
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
        
        l: _IListCookie[TNode] = self._GetListAsSpecialized(_l)
        
        self.Remove()
        
        node: TNode|None = self._GetCookie().GetLast(l)

        if node is None: return False
        
        _node: TNode = self._AsNode()
        
        self._AsLinkedNode(node)._SetNext(_node)
        self._SetPrevious(node)

        return True

class DoublyLinkedNode[TItem, TNode, TNodeInterface: IRemovable, TList, TListInterface: IClearable](DoublyLinkedNodeAbstract[TItem, TNode, TNodeInterface, TList, TListInterface], IDoublyLinkedNode[TItem]):
    def __init__(self, value: TItem, l: TListInterface|None, cookie: INodeCookie[TNode], previousNode: TNode|None, nextNode: TNode|None) -> None:
        super().__init__(value, l, cookie, previousNode, nextNode)

    @abstractmethod
    def _AsLinkedNode(self, node: TNode) -> SelfType:
        ...
    def _TryAsLinkedNode(self, node: TNode|None) -> SelfType|None:
        return None if node is None else self._AsLinkedNode(node)
    
    @final
    def GetPrevious(self) -> SelfType|None: return self._TryAsLinkedNode(self.GetPreviousNode())
    @final
    def GetNext(self) -> SelfType|None: return self._TryAsLinkedNode(self.GetNextNode())
    
    @final
    def SetPrevious(self, value: TItem) -> SelfType: return self._AsLinkedNode(super()._SetPreviousNode(value))
    @final
    def SetNext(self, value: TItem) -> SelfType: return self._AsLinkedNode(super()._SetNextNode(value))
    
    @final
    def RemoveNode(self) -> TItem: return super().RemoveNode()

@final
class _Node[T](DoublyLinkedNode[T, "_Node[T]", IDoublyLinkedNode[T], IList[T], ListBase[T, "_Node[T]"]], EnumerableListNodeBase["_Node[T]", ListBase[T, "_Node[T]"]], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, value: T, l: ListBase[T, _Node[T]]|None, cookie: INodeCookie[_Node[T]], previousNode: SelfType|None, nextNode: SelfType|None) -> None: super().__init__(value, l, cookie, previousNode, nextNode)
    
    def _AsLinkedNode(self, node: _Node[T]) -> _Node[T]:
        return node
    
    def _GetListAsClass(self, l: ListBase[T, _Node[T]]) -> IList[T]:
        return l
    def _GetListAsSpecialized(self, l: ListBase[T, _Node[T]]) -> _IListCookie[_Node[T]]:
        return l
    
    def _GetNodeAsClass(self, node: _Node[T]) -> IDoublyLinkedNode[T]:
        return node
    
    def _AsNode(self) -> _Node[T]:
        return self
    
    def _CreateNode(self, value: T, previous: SelfType|None, next: SelfType|None) -> _Node[T]:
        return _Node[T](value, self._GetInnerList(), self._GetCookie(), previous, next)
    
    def GetList(self) -> IList[T]|None: return self._GetList()

class _ReversedReadOnlyListAbstract[TItem, TNode: IRemovable, TList](Enumerable[TItem], IReadOnlyEnumerableList[TItem]):
    def __init__(self, items: TList) -> None:
        super().__init__()
        
        self.__items: TList = items
    
    @final
    def _GetInnerList(self) -> TList:
        return self.__items
    
    @abstractmethod
    def _AsList(self, items: TList) -> IEnumerableList[TItem, TNode]:
        pass
    @final
    def _GetList(self) -> IEnumerableList[TItem, TNode]:
        return self._AsList(self._GetInnerList())
    
    @final
    def IsEmpty(self) -> bool: return self._GetList().IsEmpty()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None:
        first: INode[TItem]|None = self._GetList().GetLastNode()

        return None if first is None else GetValueEnumeratorFromNode(first, EnumerationOrder.LIFO)

class _ReversedReadOnlyListBase[TItem, TNode: IRemovable, TList](_ReversedReadOnlyListAbstract[TItem, TNode, TList]):
    def __init__(self, items: TList) -> None: super().__init__(items)
    
    @final
    def TryGetFirst(self) -> INullable[TItem]: return self._GetList().TryGetLast()
    @final
    def TryGetLast(self) -> INullable[TItem]: return self._GetList().TryGetFirst()

@final
class _ReversedReadOnlyList[TItem, TNode: IRemovable](_ReversedReadOnlyListBase[TItem, TNode, IEnumerableList[TItem, TNode]]):
    def __init__(self, items: IEnumerableList[TItem, TNode]) -> None: super().__init__(items)
    
    def _AsList(self, items: IEnumerableList[TItem, TNode]) -> IEnumerableList[TItem, TNode]:
        return items
    
    def AsReversed(self) -> IReadOnlyEnumerableList[TItem]: return self._GetInnerList()

@final
class _ReversedReadOnlyCountableListBase[T](_ReversedReadOnlyListBase[T, ICountableLinkedListNode[T], ICountableList[T]]):
    def __init__(self, items: ICountableList[T]) -> None: super().__init__(items)
    
    def GetCount(self) -> int: return self._GetInnerList().GetCount()
    
    def _AsList(self, items: ICountableList[T]) -> IEnumerableList[T, ICountableLinkedListNode[T]]:
        return items
    def _AsNode(self, node: ICountableLinkedListNode[T]) -> ILinkedNode[T]:
        return node
    
    def AsReversed(self) -> IReadOnlyCountableEnumerableList[T]: return self._GetInnerList()
    
    def AsSized(self) -> Sized: return self._GetInnerList().AsSized()
@final
class _ReversedReadOnlyCountableList[T](Countable, IReadOnlyCountableEnumerableList[T]):
    def __init__(self, items: ICountableList[T]) -> None:
        super().__init__()

        self.__items: _ReversedReadOnlyCountableListBase[T] = _ReversedReadOnlyCountableListBase[T](items)
    
    def IsEmpty(self) -> bool: return self.__items.IsEmpty()
    
    def GetCount(self) -> int: return self.__items.GetCount()
    
    def TryGetFirst(self) -> INullable[T]: return self.__items.TryGetFirst()
    def TryGetLast(self) -> INullable[T]: return self.__items.TryGetLast()
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self.__items.TryGetEnumerator()
    
    def AsIterable(self) -> Iterable[T]: return self.__items.AsIterable()
    
    def AsReversed(self) -> IReadOnlyCountableEnumerableList[T]: return self.__items.AsReversed()

class _ReversedListBase[TItem, TNode: IRemovable, TList, TReadOnly, TCookie](_ReversedReadOnlyListAbstract[TItem, TNode, TList], _EnumerableListAbstract[TItem, TNode], IEnumerableList[TItem, TNode]):
    def __init__(self, items: TList) -> None:
        super().__init__(items)

        self.__cookie: TCookie = self._CreateEnumerationCookie(super()._GetValueCookie())
    
    @abstractmethod
    def _CreateEnumerationCookie(self, cookie: IValueCookie[TItem, TNode]) -> TCookie:
        ...

    @abstractmethod
    def _GetCookieAsEnumerationCookie(self, items: TCookie) -> IEnumerableListCookieAbstract[TItem, TNode, TReadOnly]:
        ...

    @final
    def _GetEnumerationCookie(self) -> TCookie:
        return self.__cookie
    @final
    def _GetInnerCookie(self) -> IEnumerableListCookieAbstract[TItem, TNode, TReadOnly]:
        return self._GetCookieAsEnumerationCookie(self._GetEnumerationCookie())
    
    @final
    def _AsReadOnly(self) -> TReadOnly:
        return self._GetInnerCookie().GetReadOnly()
    
    @abstractmethod
    def _GetNodeEnumerator(self, first: TNode) -> IEnumerator[TNode]:
        ...
    @abstractmethod
    def _GetResumableNodeEnumerator(self, first: TNode) -> IResumableEnumerator[TNode]:
        ...
    
    @final
    def _GetValueCookie(self) -> IValueCookie[TItem, TNode]:
        return self._GetInnerCookie().GetValueCookie()
    
    @final
    def GetFirst(self) -> TNode|None: return self._GetList().GetLast()
    @final
    def GetLast(self) -> TNode|None: return self._GetList().GetFirst()
    
    @final
    def AddFirst(self, value: TItem) -> TNode: return self._GetList().AddLast(value)
    @final
    def AddLast(self, value: TItem) -> TNode: return self._GetList().AddFirst(value)
    
    @final
    def TryRemoveFirst(self) -> INullable[TItem]: return self._GetList().TryRemoveLast()
    @final
    def TryRemoveLast(self) -> INullable[TItem]: return self._GetList().TryRemoveFirst()
    
    @final
    def Clear(self) -> None: return self._GetList().Clear()
    
    @final
    def TryGetNodeEnumerator(self) -> IEnumerator[TNode]|None:
        first: TNode|None = self.GetFirst()

        return None if first is None else self._GetNodeEnumerator(first)
    @final
    def TryGetResumableNodeEnumerator(self) -> IResumableEnumerator[TNode]|None:
        first: TNode|None = self.GetFirst()

        return None if first is None else self._GetResumableNodeEnumerator(first)

    @final
    def AsNodeGenerator(self) -> IIterator[TNode]: return self._GetInnerCookie().GetNodeGenerator()
    @final
    def AsGenerator(self) -> IIterator[TItem]: return self._GetInnerCookie().GetGenerator()

@final
class _ReversedList[T](_ReversedListBase[T, IDoublyLinkedNode[T], IList[T], IReadOnlyEnumerableList[T], IEnumerableListCookieAbstract[T, IDoublyLinkedNode[T], IReadOnlyEnumerableList[T]]], IList[T], IGenericConstraintImplementation[IDoublyLinkedNode[T]]):
    def __init__(self, items: IList[T]) -> None: super().__init__(items)
    
    def _CreateEnumerationCookie(self, cookie: IValueCookie[T, IDoublyLinkedNode[T]]) -> IEnumerableListCookieAbstract[T, IDoublyLinkedNode[T], IReadOnlyEnumerableList[T]]:
        return _ReadOnlyEnumerableListBase[T, IDoublyLinkedNode[T]](self, cookie)
    
    def _GetCookieAsEnumerationCookie(self, items: IEnumerableListCookieAbstract[T, IDoublyLinkedNode[T], IReadOnlyEnumerableList[T]]) -> IEnumerableListCookieAbstract[T, IDoublyLinkedNode[T], IReadOnlyEnumerableList[T]]:
        return items
    
    def _AsList(self, items: IList[T]) -> IEnumerableList[T, IDoublyLinkedNode[T]]:
        return items
    def _AsNode(self, node: IDoublyLinkedNode[T]) -> ILinkedNode[T]:
        return node
    
    def _GetNodeEnumerator(self, first: IDoublyLinkedNode[T]) -> IEnumerator[IDoublyLinkedNode[T]]:
        return DoublyLinkedNodeEnumerator[T](first)
    def _GetResumableNodeEnumerator(self, first: IDoublyLinkedNode[T]) -> IResumableEnumerator[IDoublyLinkedNode[T]]:
        return ResumableDoublyLinkedNodeEnumerator[T](first)
    
    def AsReadOnly(self) -> IReadOnlyEnumerableList[T]: return self._AsReadOnly()
    
    def AsReversed(self) -> IList[T]: return self._GetInnerList()
    
    @final
    def AsNodeEnumerable(self) -> IResumableEnumerable[IDoublyLinkedNode[T]]: return self._GetEnumerationCookie().GetNodeEnumerable()
@final
class _ReversedCountableListBase[T](_ReversedListBase[T, ICountableLinkedListNode[T], ICountableList[T], IReadOnlyCountableEnumerableList[T], ICountableEnumerableListCookieAbstract[T, ICountableLinkedListNode[T], IReadOnlyCountableEnumerableList[T]]], IGenericConstraintImplementation[ICountableLinkedListNode[T]]):
    def __init__(self, items: ICountableList[T]) -> None: super().__init__(items)
    
    def _CreateEnumerationCookie(self, cookie: IValueCookie[T, ICountableLinkedListNode[T]]) -> ICountableEnumerableListCookieAbstract[T, ICountableLinkedListNode[T], IReadOnlyCountableEnumerableList[T]]:
        return _ReadOnlyCountableEnumerableListBase[T](self._GetInnerList(), cookie)
    
    def _GetCookieAsEnumerationCookie(self, items: ICountableEnumerableListCookieAbstract[T, ICountableLinkedListNode[T], IReadOnlyCountableEnumerableList[T]]) -> IEnumerableListCookieAbstract[T, ICountableLinkedListNode[T], IReadOnlyCountableEnumerableList[T]]:
        return items
    
    def _AsList(self, items: ICountableList[T]) -> IEnumerableList[T, ICountableLinkedListNode[T]]:
        return items
    def _AsNode(self, node: ICountableLinkedListNode[T]) -> ILinkedNode[T]:
        return node
    
    def _GetNodeEnumerator(self, first: ICountableLinkedListNode[T]) -> IEnumerator[ICountableLinkedListNode[T]]:
        return CountableLinkedListNodeEnumerator[T](first)
    def _GetResumableNodeEnumerator(self, first: ICountableLinkedListNode[T]) -> IResumableEnumerator[ICountableLinkedListNode[T]]:
        return ResumableCountableLinkedListNodeEnumerator[T](first)
    
    def GetCount(self) -> int: return self._GetInnerList().GetCount()
    
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[T]: return self._AsReadOnly()
    
    def AsReversed(self) -> ICountableList[T]: return self._GetInnerList()
    
    def AsSized(self) -> Sized: return self._GetInnerList().AsSized()
    
    @final
    def AsNodeEnumerable(self) -> IResumableCountableEnumerable[ICountableLinkedListNode[T]]: return self._GetEnumerationCookie().GetNodeEnumerable()

@final
class _ReversedUpdater[T](ValueFunctionUpdater[IList[T]]):
    def __init__(self, items: IList[T], updater: Method[IFunction[IList[T]]]) -> None:
        super().__init__(updater)

        self.__items: IList[T] = items
    
    def _GetValue(self) -> IList[T]: return _ReversedList[T](self.__items)

class List[T](ListBase[T, _Node[T]]):
    def __init__(self, items: Iterable[T]|None = None) -> None:
        def update(func: IFunction[IList[T]]) -> None: self.__reversed = func
        
        super().__init__(items)

        self.__reversed: IFunction[IList[T]] = _ReversedUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def _GetNodeAsClass(self, node: _Node[T]) -> IDoublyLinkedNode[T]:
        return node
    @final
    def _GetNodeAsInterface(self, node: _Node[T]) -> IDoublyLinkedNodeBase[T, _Node[T]]:
        return node
    
    @final
    def _CreateNode(self, value: T) -> _Node[T]:
        return _Node[T](value, self, self._GetCookie(), None, None)
    
    @final
    def _GetPreviousNode(self, node: _Node[T]) -> _Node[T]|None:
        return node.GetPreviousNode()
    @final
    def _GetNextNode(self, node: _Node[T]) -> _Node[T]|None:
        return node.GetNextNode()
    
    @final
    def _UnregisterNode(self, node: _Node[T]) -> None:
        return node._Unregister() # pyright: ignore[reportPrivateUsage]
    
    @final
    def AsReversed(self) -> IList[T]: return self.__reversed.GetValue()

class CountableListProvider[T](Abstract, IClearable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetInnerItems(self) -> _CountableInnerList[T]:
        ...

    @abstractmethod
    def GetItems(self) -> ICountableList[T]:
        ...

    @abstractmethod
    def AsSized(self) -> Sized:
        ...

    @abstractmethod
    def OnAdded(self, node: ICountableLinkedListNode[T]) -> None:
        ...
    @abstractmethod
    def OnRemoved(self, value: T) -> None:
        ...

@final
class _ReadOnlyCountableEnumerableList[T](_ReadOnlyListBase[T, IReadOnlyCountableEnumerableList[T]], IReadOnlyCountableEnumerableList[T], IGenericConstraintImplementation[IReadOnlyCountableEnumerableList[T]]):
    def __init__(self, items: ICountableList[T]) -> None:
        def update(func: IFunction[IReadOnlyCountableEnumerableList[T]]) -> None: self.__reversed = func
        
        super().__init__(items)

        self.__items: CountableEnumerable[T] = CreateCountableEnumerable(items)
        self.__reversed: IFunction[IReadOnlyCountableEnumerableList[T]] = _ReversedReadOnlyCountableListUpdater[T](items, update) # type: ignore[no-redef]
    
    def GetCount(self) -> int: return self._GetContainer().GetCount()
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self._GetContainer().TryGetEnumerator()
    
    def AsSized(self) -> Sized: return self.__items.AsSized()
    def AsIterable(self) -> Iterable[T]: return self.__items.AsIterable()
    
    def AsReversed(self) -> IReadOnlyCountableEnumerableList[T]: return self.__reversed.GetValue()

@final
class _ReadOnlyCountableUpdater[T](ValueFunctionUpdater[IReadOnlyCountableEnumerableList[T]]):
    def __init__(self, items: ICountableList[T], updater: Method[IFunction[IReadOnlyCountableEnumerableList[T]]]) -> None:
        super().__init__(updater)

        self.__items: ICountableList[T] = items
    
    def _GetValue(self) -> IReadOnlyCountableEnumerableList[T]: return _ReadOnlyCountableEnumerableList[T](self.__items)

@final
class _ReadOnlyCountableEnumerableListBase[T](_EnumerableListBase[T, ICountableLinkedListNode[T], ICountableList[T], IReadOnlyCountableEnumerableList[T]], ICountableEnumerableListCookie[T, ICountableLinkedListNode[T]]):
    def __init__(self, items: ICountableList[T], cookie: IValueCookie[T, ICountableLinkedListNode[T]]) -> None:
        def updateNodeEnumerable(func: IFunction[IResumableCountableEnumerable[ICountableLinkedListNode[T]]]) -> None: self.__nodeEnumerable = func
        
        super().__init__(items, cookie)

        self.__nodeEnumerable: IFunction[IResumableCountableEnumerable[ICountableLinkedListNode[T]]] = _CountableEnumerableUpdater[T](items, updateNodeEnumerable) # type: ignore[no-redef]
    
    def _CreateReadOnly(self, items: ICountableList[T], action: Method[IFunction[IReadOnlyCountableEnumerableList[T]]]) -> IFunction[IReadOnlyCountableEnumerableList[T]]:
        return _ReadOnlyCountableUpdater[T](items, action)
    
    def _AsList(self, items: ICountableList[T]) -> IEnumerableList[T, ICountableLinkedListNode[T]]:
        return items
    
    def GetNodeEnumerable(self) -> IResumableCountableEnumerable[ICountableLinkedListNode[T]]: return self.__nodeEnumerable.GetValue()

class CountableListBase[TItem, TNode](_Enumerable[TItem, TNode, ICountableLinkedListNode[TItem], IReadOnlyCountableEnumerableList[TItem], ICountableEnumerableListCookieAbstract[TItem, ICountableLinkedListNode[TItem], IReadOnlyCountableEnumerableList[TItem]]], ICountableList[TItem], IGenericConstraintImplementation[ICountableLinkedListNode[TItem]]):
    def __init__(self, items: Iterable[TItem]|None) -> None: super().__init__(items)
    
    @final
    def _CreateEnumerationCookie(self, cookie: IValueCookie[TItem, ICountableLinkedListNode[TItem]]) -> ICountableEnumerableListCookieAbstract[TItem, ICountableLinkedListNode[TItem], IReadOnlyCountableEnumerableList[TItem]]:
        return _ReadOnlyCountableEnumerableListBase[TItem](self, cookie)
    
    @final
    def _GetCookieAsEnumerationCookie(self, items: ICountableEnumerableListCookieAbstract[TItem, ICountableLinkedListNode[TItem], IReadOnlyCountableEnumerableList[TItem]]) -> IEnumerableListCookieAbstract[TItem, ICountableLinkedListNode[TItem], IReadOnlyCountableEnumerableList[TItem]]:
        return items
    
    @final
    def _GetNodeEnumerator(self, node: ICountableLinkedListNode[TItem]) -> IEnumerator[ICountableLinkedListNode[TItem]]:
        return CountableLinkedListNodeEnumerator[TItem](node)
    @final
    def _GetResumableNodeEnumerator(self, node: ICountableLinkedListNode[TItem]) -> IResumableEnumerator[ICountableLinkedListNode[TItem]]:
        return ResumableCountableLinkedListNodeEnumerator[TItem](node)
    
    def AsNodeEnumerable(self) -> IResumableCountableEnumerable[ICountableLinkedListNode[TItem]]: return self._GetEnumerationCookie().GetNodeEnumerable()
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[TItem]: return self._AsReadOnly()

@final
class _CountableListNode[T](DoublyLinkedNodeAbstract[T, "_CountableListNode[T]", ICountableLinkedListNode[T], ICountableList[T], CountableListProvider[T]], NodeBase[T, "_CountableListNode[T]"], EnumerableListNodeBase["_CountableListNode[T]", CountableListProvider[T]], ICountableLinkedListNode[T], IGenericConstraintImplementation[ICountableList[T]]):
    def __init__(self, value: T, l: CountableListProvider[T]|None, cookie: INodeCookie[_CountableListNode[T]], previousNode: SelfType|None, nextNode: SelfType|None) -> None:
        super().__init__(value, l, cookie, previousNode, nextNode)
    
    @final
    def _GetListAsClass(self, l: CountableListProvider[T]) -> ICountableList[T]:
        return l.GetItems()
    @final
    def _GetListAsSpecialized(self, l: CountableListProvider[T]) -> _IListCookie[_CountableListNode[T]]:
        return l.GetInnerItems()
    
    @final
    def _GetNodeAsClass(self, node: _CountableListNode[T]) -> ICountableLinkedListNode[T]:
        return node
    
    @final
    def _AsNode(self) -> SelfType:
        return self
    
    @final
    def _AsLinkedNode(self, node: _CountableListNode[T]) -> _DoublyLinkedNodeBase[T, _CountableListNode[T], ICountableList[T], CountableListProvider[T]]:
        return node
    
    @final
    def _CreateNode(self, value: T, previous: SelfType|None, next: SelfType|None) -> _CountableListNode[T]:
        return _CountableListNode[T](value, self._GetInnerList(), self._GetCookie(), previous, next)
    
    @final
    def GetList(self) -> ICountableList[T]|None: return self._GetList()
    
    @final
    def GetPrevious(self) -> _CountableListNode[T]|None: return self.GetPreviousNode()
    @final
    def GetNext(self) -> _CountableListNode[T]|None: return self.GetNextNode()
    
    @final
    def _OnAdded(self, node: ICountableLinkedListNode[T]) -> None:
        l: CountableListProvider[T]|None = self._GetInnerList()

        if l is not None: l.OnAdded(node)
    @final
    def _OnRemoved(self, l: CountableListProvider[T]|None, value: T) -> None:
        if l is not None: l.OnRemoved(value)
    
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
    def RemoveNode(self) -> T:
        l: CountableListProvider[T]|None = self._GetInnerList()

        value: T = super().RemoveNode()

        self._OnRemoved(l, value)

        return value

@final
class _ReversedCountableList[T](CountableEnumerable[T], _EnumerableListAbstract[T, ICountableLinkedListNode[T]], ICountableList[T], IGenericConstraintImplementation[ICountableLinkedListNode[T]]):
    def __init__(self, items: ICountableList[T]) -> None:
        super().__init__()

        self.__items: _ReversedCountableListBase[T] = _ReversedCountableListBase[T](items)
        self.__countable: ICountable = items
    
    def IsEmpty(self) -> bool: return self.__items.IsEmpty()
    
    def GetCount(self) -> int: return self.__countable.GetCount()
    
    def GetFirst(self) -> ICountableLinkedListNode[T]|None: return self.__items.GetFirst()
    def GetLast(self) -> ICountableLinkedListNode[T]|None: return self.__items.GetLast()
    
    def AddFirst(self, value: T) -> ICountableLinkedListNode[T]: return self.__items.AddFirst(value)
    def AddLast(self, value: T) -> ICountableLinkedListNode[T]: return self.__items.AddLast(value)
    
    def TryRemoveFirst(self) -> INullable[T]: return self.__items.TryRemoveFirst()
    def TryRemoveLast(self) -> INullable[T]: return self.__items.TryRemoveLast()
    
    def Clear(self) -> None: return self.__items.Clear()
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self.__items.TryGetEnumerator()
    
    def TryGetNodeEnumerator(self) -> IEnumerator[ICountableLinkedListNode[T]]|None: return self.__items.TryGetNodeEnumerator()
    def TryGetResumableNodeEnumerator(self) -> IResumableEnumerator[ICountableLinkedListNode[T]]|None: return self.__items.TryGetResumableNodeEnumerator()
    
    def AsReversed(self) -> ICountableList[T]: return self.__items.AsReversed()
    
    def AsNodeEnumerable(self) -> IResumableCountableEnumerable[ICountableLinkedListNode[T]]: return self.__items.AsNodeEnumerable()
    
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[T]: return self.__items.AsReadOnly()

    def AsNodeGenerator(self) -> IIterator[ICountableLinkedListNode[T]]: return self.__items.AsNodeGenerator()
    def AsGenerator(self) -> IIterator[T]: return self.__items.AsGenerator()
@final
class _ReversedCountableUpdater[T](ValueFunctionUpdater[ICountableList[T]]):
    def __init__(self, items: ICountableList[T], updater: Method[IFunction[ICountableList[T]]]) -> None:
        super().__init__(updater)

        self.__items: ICountableList[T] = items
    
    def _GetValue(self) -> ICountableList[T]: return _ReversedCountableList[T](self.__items)

@final
class _CountableInnerList[T](CountableListBase[T, _CountableListNode[T]]):
    def __init__(self, l: CountableListProvider[T], items: Iterable[T]|None) -> None:
        def update(func: IFunction[ICountableList[T]]) -> None: self.__reversed = func
        
        self.__items: CountableListProvider[T] = l
        self.__count: int = 0

        super().__init__(items)

        self.__reversed: IFunction[ICountableList[T]] = _ReversedCountableUpdater[T](self, update) # type: ignore[no-redef]
    
    def _GetNodeAsClass(self, node: _CountableListNode[T]) -> ICountableLinkedListNode[T]:
        return node
    def _GetNodeAsInterface(self, node: _CountableListNode[T]) -> IDoublyLinkedNodeBase[T, _CountableListNode[T]]:
        return node
    
    def _CreateNode(self, value: T) -> _CountableListNode[T]:
        return _CountableListNode[T](value, self.__items, self._GetCookie(), None, None)
    
    @final
    def _AddNode(self, value: T) -> _CountableListNode[T]:
        node: _CountableListNode[T] = super()._AddNode(value)

        self.Increment()

        return node
    
    def AsSized(self) -> Sized: return self.__items.AsSized()
    
    def GetCount(self) -> int: return self.__count
    
    def Increment(self) -> None: self.__count += 1
    def Decrement(self) -> None: self.__count -= 1
    
    @final
    def _GetPreviousNode(self, node: _CountableListNode[T]) -> _CountableListNode[T]|None:
        return node.GetPreviousNode()
    @final
    def _GetNextNode(self, node: _CountableListNode[T]) -> _CountableListNode[T]|None:
        return node.GetNextNode()
    
    @final
    def _UnregisterNode(self, node: _CountableListNode[T]) -> None:
        return node._Unregister() # pyright: ignore[reportPrivateUsage]
    
    @final
    def AsReversed(self) -> ICountableList[T]: return self.__reversed.GetValue()

class CountableList[T](CountableEnumerable[T], ICountableList[T], IGenericConstraintImplementation[ICountableLinkedListNode[T]]):
    @final
    class _CountableListProvider[_T](CountableListProvider[_T]):
        def __init__(self, l: CountableList[_T]) -> None:
            super().__init__()

            self.__items: CountableList[_T] = l
        
        def GetInnerItems(self) -> _CountableInnerList[_T]: return self.__items._GetItems()
        
        def GetItems(self) -> ICountableList[_T]: return self.__items
        
        def Clear(self) -> None: return self.GetItems().Clear()
        
        def AsSized(self) -> Sized: return self.GetItems().AsSized()
        
        def OnAdded(self, node: ICountableLinkedListNode[_T]) -> None: self.__items._OnAdded(node)
        def OnRemoved(self, value: _T) -> None: self.__items._OnRemoved(value)
    
    def __init__(self, items: Iterable[T]|None = None) -> None:
        super().__init__()

        self.__items: _CountableInnerList[T] = _CountableInnerList[T](CountableList[T]._CountableListProvider(self), items)
    
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
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[T]: return self._GetItems().AsReadOnly()
    
    @final
    def IsEmpty(self) -> bool: return self._GetItems().IsEmpty()
    
    @final
    def GetCount(self) -> int: return self._GetItems().GetCount()
    
    @final
    def GetFirst(self) -> ICountableLinkedListNode[T]|None: return self._GetItems().GetFirst()
    @final
    def GetLast(self) -> ICountableLinkedListNode[T]|None: return self._GetItems().GetLast()
    
    @final
    def AddFirst(self, value: T) -> ICountableLinkedListNode[T]: return self._GetItems().AddFirst(value)
    @final
    def AddLast(self, value: T) -> ICountableLinkedListNode[T]: return self._GetItems().AddLast(value)
    
    @final
    def TryRemoveFirst(self) -> INullable[T]: return self._GetItems().TryRemoveFirst()
    @final
    def TryRemoveLast(self) -> INullable[T]: return self._GetItems().TryRemoveLast()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self._GetItems().TryGetEnumerator()
    
    @final
    def TryGetNodeEnumerator(self) -> IEnumerator[ICountableLinkedListNode[T]]|None: return self._GetItems().TryGetNodeEnumerator()
    @final
    def TryGetResumableNodeEnumerator(self) -> IResumableEnumerator[ICountableLinkedListNode[T]]|None: return self._GetItems().TryGetResumableNodeEnumerator()
    
    @final
    def AsNodeEnumerable(self) -> IResumableCountableEnumerable[ICountableLinkedListNode[T]]: return self._GetItems().AsNodeEnumerable()
    
    @final
    def AsNodeGenerator(self) -> IIterator[ICountableLinkedListNode[T]]: return self._GetItems().AsNodeGenerator()
    @final
    def AsGenerator(self) -> IIterator[T]: return self._GetItems().AsGenerator()
    
    @final
    def AsReversed(self) -> ICountableList[T]: return self._GetItems().AsReversed()
    
    @final
    def Clear(self) -> None: self._GetItems().Clear()

class DoublyLinkedNodeEnumerator[T](TwoWayNodeEnumeratorBase[IDoublyLinkedNode[T]]):
    def __init__(self, node: IDoublyLinkedNode[T], order: EnumerationOrder = EnumerationOrder.FIFO) -> None: super().__init__(node, order)
    
    @final
    def _GetNodeConverter(self, order: EnumerationOrder) -> NullableSelector[IDoublyLinkedNode[T]]:
        match order:
            case EnumerationOrder.FIFO: return lambda node: node.GetNext()
            case EnumerationOrder.LIFO: return lambda node: node.GetPrevious()
            
            case _: raise ValueError()
class CountableLinkedListNodeEnumerator[T](TwoWayNodeEnumeratorBase[ICountableLinkedListNode[T]], IGenericConstraintImplementation[ICountableLinkedListNode[T]]):
    def __init__(self, node: ICountableLinkedListNode[T], order: EnumerationOrder = EnumerationOrder.FIFO) -> None: super().__init__(node, order)
    
    @final
    def _GetNodeConverter(self, order: EnumerationOrder) -> NullableSelector[ICountableLinkedListNode[T]]:
        match order:
            case EnumerationOrder.FIFO: return lambda node: node.GetNext()
            case EnumerationOrder.LIFO: return lambda node: node.GetPrevious()
            
            case _: raise ValueError()

class ResumableDoublyLinkedNodeEnumerator[T](TwoWayResumableNodeEnumerator[IDoublyLinkedNode[T]]):
    def __init__(self, node: IDoublyLinkedNode[T], order: EnumerationOrder = EnumerationOrder.FIFO) -> None: super().__init__(node, order)
    
    @final
    def _GetNodeConverter(self, order: EnumerationOrder) -> NullableSelector[IDoublyLinkedNode[T]]:
        match order:
            case EnumerationOrder.FIFO: return lambda node: node.GetNext()
            case EnumerationOrder.LIFO: return lambda node: node.GetPrevious()
            
            case _: raise ValueError()
class ResumableCountableLinkedListNodeEnumerator[T](TwoWayResumableNodeEnumerator[ICountableLinkedListNode[T]], IGenericConstraintImplementation[ICountableLinkedListNode[T]]):
    def __init__(self, node: ICountableLinkedListNode[T], order: EnumerationOrder = EnumerationOrder.FIFO) -> None: super().__init__(node, order)
    
    @final
    def _GetNodeConverter(self, order: EnumerationOrder) -> NullableSelector[ICountableLinkedListNode[T]]:
        match order:
            case EnumerationOrder.FIFO: return lambda node: node.GetNext()
            case EnumerationOrder.LIFO: return lambda node: node.GetPrevious()
            
            case _: raise ValueError()

def CreateList[T](items: Iterable[T]|None = None) -> List[T]:
    return List[T](items)
def MakeList[T](*values: T) -> List[T]:
    return CreateList(values)

def CreateCountableList[T](items: Iterable[T]|None = None) -> CountableList[T]:
    return CountableList[T](items)
def MakeCountableList[T](*values: T) -> CountableList[T]:
    return CreateCountableList(values)