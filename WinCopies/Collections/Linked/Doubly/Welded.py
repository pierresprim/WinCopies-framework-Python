from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Sized
from typing import final, Self as SelfType

from WinCopies import IInterface, Abstract
from WinCopies.Collections import EnumerationOrder, GetInvalidEnumerationOrderError
from WinCopies.Collections.Abstraction.Enumeration import CreateCountableEnumerable, TryCreateEnumerator
from WinCopies.Collections.Core import ICountable, IClearable, Countable
from WinCopies.Collections.Enumeration import IEnumerable, ICountableEnumerable, IReversableEnumerable, IReversableCountableEnumerable, IEnumerator, Enumerable, CountableEnumerable, GetEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerable, IResumableCountableEnumerable, IResumableEnumerator, ResumableEnumerable, GetResumableEnumerator
from WinCopies.Collections.Enumeration.Resumable.Linked import TwoWayResumableNodeEnumerator
from WinCopies.Collections.Generation import IRemovable, IIterator, GeneratorAbstract, ConverterBase
from WinCopies.Collections.Linked.Doubly import IReadOnlyList
from WinCopies.Collections.Linked.Doubly.Core import IReadWriteList, IListBase, ListNodeBase, ListBase as ListAbstract
from WinCopies.Collections.Linked.Doubly.Node import INodeCookie, INode, IDoublyLinkedNode as IDoublyLinkedNodeAbstract, IDoublyLinkedNodeBase, IListCookie, NodeBase, DoublyLinkedNodeAbstract, DoublyLinkedNodeBase, DoublyLinkedNode
from WinCopies.Collections.Linked.Enumeration import TwoWayNodeEnumeratorBase, GetValueEnumeratorFromNode
from WinCopies.Collections.Linked.Node import ILinkedNode
from WinCopies.Typing import INullable
from WinCopies.Typing.Delegate import Method, NullableSelector, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import IGenericConstraintImplementation, GenericConstraint

class IDoublyLinkedNode[T](IDoublyLinkedNodeAbstract[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetList(self) -> IList[T]|None:
        ...

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

    @abstractmethod
    def AsNodeGenerator(self, order: EnumerationOrder = EnumerationOrder.FIFO) -> IIterator[TNode]:
        ...
    @abstractmethod
    def AsGenerator(self, order: EnumerationOrder = EnumerationOrder.FIFO) -> IIterator[TItem]:
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

@final
class _EnumerableListEnumerable[TItem, TNode: IRemovable](ResumableEnumerable[TNode]):
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

class IValueCookie[TItem, TNode](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetItems(self) -> IEnumerableListBase[TItem, TNode]:
        ...
    
    @abstractmethod
    def GetNextNode(self, node: TNode) -> TNode|None:
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
class _NodeGenerator[TItem, TNode: IRemovable](GeneratorAbstract[TNode]):
    def __init__(self, cookie: IValueCookie[TItem, TNode]) -> None:
        super().__init__()

        self.__cookie: IValueCookie[TItem, TNode] = cookie
    
    @final
    def _GetItems(self) -> Iterable[TNode]:
        # TODO: should throw if the list is modified during enumeration

        current: TNode|None = self.__cookie.GetItems().GetFirst()

        while current is not None:
            next: TNode|None = self.__cookie.GetNextNode(current)
            
            yield current
            
            current = next
    
    @final
    def _OnItemProcessed(self, item: TNode) -> bool: return False

@final
class _NodeGeneratorUpdater[TItem, TNode: IRemovable](ValueFunctionUpdater[IIterator[TNode]]):
    def __init__(self, cookie: IValueCookie[TItem, TNode], updater: Method[IFunction[IIterator[TNode]]]) -> None:
        super().__init__(updater)

        self.__cookie: IValueCookie[TItem, TNode] = cookie
    
    def _GetValue(self) -> IIterator[TNode]: return _NodeGenerator[TItem, TNode](self.__cookie)
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

        def GetNextNode(self, node: _TNode) -> _TNode|None: return self.__items._GetNextNode(node)
        
        def GetValue(self, node: _TNode) -> _TItem: return self.__items._GetValue(node)
    
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetNextNode(self, node: TNode) -> TNode|None:
        ...
    
    @final
    def _GetValue(self, node: TNode) -> TItem:
        return self._AsContainer(node).GetValue()
    
    def _GetValueCookie(self) -> IValueCookie[TItem, TNode]:
        return _EnumerableListAbstract[TItem, TNode]._Cookie(self)

class IEnumerableListCookieAbstractBase[TItem, TNode](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetNodeGenerator(self) -> IIterator[TNode]:
        ...
    @abstractmethod
    def GetGenerator(self) -> IIterator[TItem]:
        ...
class IEnumerableListCookieAbstract[TItem, TNode, TReadOnly](IEnumerableListCookieAbstractBase[TItem, TNode]):
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
        
        self.__nodeGenerator: IFunction[IIterator[TNode]] = _NodeGeneratorUpdater[TItem, TNode](cookie, updateNodeGenerator) # type: ignore[no-redef]
        self.__generator: IFunction[IIterator[TItem]] = _GeneratorUpdater[TItem, TNode](cookie, updateGenerator) # type: ignore[no-redef]
    
    @abstractmethod
    def _CreateReadOnly(self, items: TList, action: Method[IFunction[TReadOnly]]) -> IFunction[TReadOnly]:
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
    
    def GetNodeEnumerable(self) -> IResumableEnumerable[TNode]: return self.__nodeEnumerable.GetValue()
@final
class _ReadOnlyEnumerableListBase[TItem, TNode: IRemovable](_EnumerableListBase[TItem, TNode, IEnumerableList[TItem, TNode], IReadOnlyEnumerableList[TItem]], IEnumerableListCookie[TItem, TNode]):
    def __init__(self, items: IEnumerableList[TItem, TNode], cookie: IValueCookie[TItem, TNode]) -> None:
        def updateNodeEnumerable(func: IFunction[IResumableEnumerable[TNode]]) -> None: self.__nodeEnumerable = func
        
        super().__init__(items, cookie)

        self.__nodeEnumerable: IFunction[IResumableEnumerable[TNode]] = _EnumerableUpdater[TItem, TNode](items, updateNodeEnumerable) # type: ignore[no-redef]
    
    def _CreateReadOnly(self, items: IEnumerableList[TItem, TNode], action: Method[IFunction[IReadOnlyEnumerableList[TItem]]]) -> IFunction[IReadOnlyEnumerableList[TItem]]:
        return _ReadOnlyEnumerableUpdater[TItem, TNode](items, action)
    
    def GetNodeEnumerable(self) -> IResumableEnumerable[TNode]: return self.__nodeEnumerable.GetValue()

class _Enumerable[TItem, TNode, TNodeInterface: IRemovable, TEnumerable, TList, TCookie](Enumerable[TItem], _EnumerableListAbstract[TItem, TNodeInterface]):
    def __init__(self, items: Iterable[TItem]|None) -> None:
        super().__init__()

        # Build the backing list empty first so __items and __cookie are both in place before any
        # population: the welded add path consults the owner list (GetLast -> _GetItems), so
        # populating during construction would read __items before it is assigned.
        self.__items: TList = self._CreateList()
        self.__cookie: TCookie = self._CreateEnumerationCookie(super()._GetValueCookie())

        self.AddLastItems(items)
    
    @abstractmethod
    def _CreateList(self) -> TList:
        ...
    
    @final
    def _GetItems(self) -> TList:
        return self.__items
    
    @abstractmethod
    def _GetItemsAsClass(self, items: TList) -> ListAbstract[TItem, TNode, TNodeInterface]:
        ...
    @final
    def _GetInnerList(self) -> ListAbstract[TItem, TNode, TNodeInterface]:
        return self._GetItemsAsClass(self._GetItems())
    
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
    
    @final
    def _GetValueCookie(self) -> IValueCookie[TItem, TNodeInterface]:
        return self._GetInnerCookie().GetValueCookie()

    @final
    def IsEmpty(self) -> bool: return self._GetInnerList().IsEmpty()
    @final
    def HasItems(self) -> bool: return self._GetInnerList().HasItems()
    
    @final
    def AddFirst(self, value: TItem) -> TNodeInterface:
        return self._GetInnerList().AddFirst(value)
    @final
    def AddLast(self, value: TItem) -> TNodeInterface:
        return self._GetInnerList().AddLast(value)
    
    @final
    def GetFirst(self) -> TNodeInterface|None: return self._GetInnerList().GetFirst()
    @final
    def GetLast(self) -> TNodeInterface|None: return self._GetInnerList().GetLast()
    
    @final
    def TryRemoveFirst(self) -> INullable[TItem]: return self._GetInnerList().TryRemoveFirst()
    @final
    def TryRemoveLast(self) -> INullable[TItem]: return self._GetInnerList().TryRemoveLast()
    
    def Clear(self) -> None: self._GetInnerList().Clear()
    
    @abstractmethod
    def _GetNodeEnumerator(self, node: TNodeInterface) -> IEnumerator[TNodeInterface]:
        ...
    @abstractmethod
    def _GetResumableNodeEnumerator(self, node: TNodeInterface) -> IResumableEnumerator[TNodeInterface]:
        ...
    
    @abstractmethod
    def _GetNodeAsInterface(self, node: TNodeInterface) -> ILinkedNode[TItem]:
        ...
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None:
        node: TNodeInterface|None = self._GetInnerList().GetFirst()

        return None if node is None else GetValueEnumeratorFromNode(self._GetNodeAsInterface(node))
    
    @final
    def TryGetNodeEnumerator(self) -> IEnumerator[TNodeInterface]|None:
        first: TNodeInterface|None = self.GetFirst()

        return None if first is None else self._GetNodeEnumerator(first)
    @final
    def TryGetResumableNodeEnumerator(self) -> IResumableEnumerator[TNodeInterface]|None:
        first: TNodeInterface|None = self.GetFirst()

        return None if first is None else self._GetResumableNodeEnumerator(first)
class EnumerableListAbstract[TItem, TNode, TNodeInterface: IRemovable, TEnumerable, TList](_Enumerable[TItem, TNode, TNodeInterface, TEnumerable, TList, IEnumerableListCookieAbstract[TItem, TNodeInterface, TEnumerable]]):
    def __init__(self, items: Iterable[TItem]|None = None) -> None: super().__init__(items)
    
    @final
    def _GetCookieAsEnumerationCookie(self, items: IEnumerableListCookieAbstract[TItem, TNodeInterface, TEnumerable]) -> IEnumerableListCookieAbstract[TItem, TNodeInterface, TEnumerable]:
        return items
    
    @final
    def AsNodeEnumerable(self) -> IResumableEnumerable[TNodeInterface]: return self._GetInnerCookie().GetNodeEnumerable()

    @final
    def Clear(self) -> None: return super().Clear()
class EnumerableListBase[TItem, TNode, TNodeInterface: IRemovable, TList](EnumerableListAbstract[TItem, TNode, TNodeInterface, IReadOnlyEnumerableListBase[TItem], TList]):
    def __init__(self, items: Iterable[TItem]|None = None) -> None: super().__init__(items)
    
    @final
    def _CreateEnumerationCookie(self, cookie: IValueCookie[TItem, TNodeInterface]) -> IEnumerableListCookieAbstract[TItem, TNodeInterface, IReadOnlyEnumerableListBase[TItem]]:
        return _ReadOnlyEnumerableListAbstract[TItem, TNodeInterface](self, cookie)

    @final
    def AsNodeGenerator(self) -> IIterator[TNodeInterface]: return self._GetInnerCookie().GetNodeGenerator()
    @final
    def AsGenerator(self) -> IIterator[TItem]: return self._GetInnerCookie().GetGenerator()
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableListBase[TItem]: return self._AsReadOnly()
class EnumerableList[TItem, TNode, TNodeInterface: IRemovable, TList](EnumerableListAbstract[TItem, TNode, TNodeInterface, IReadOnlyEnumerableList[TItem], TList], IEnumerableList[TItem, TNodeInterface]):
    def __init__(self, items: Iterable[TItem]|None) -> None: super().__init__(items)
    
    @final
    def _CreateEnumerationCookie(self, cookie: IValueCookie[TItem, TNodeInterface]) -> IEnumerableListCookieAbstract[TItem, TNodeInterface, IReadOnlyEnumerableList[TItem]]:
        return _ReadOnlyEnumerableListBase[TItem, TNodeInterface](self, cookie)
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableList[TItem]: return self._AsReadOnly()

    @final
    def AsNodeGenerator(self, order: EnumerationOrder = EnumerationOrder.FIFO) -> IIterator[TNodeInterface]:
        match order:
            case EnumerationOrder.FIFO: return self._GetInnerCookie().GetNodeGenerator()
            case EnumerationOrder.LIFO: return self.AsReversed().AsNodeGenerator()

            case _: raise GetInvalidEnumerationOrderError(order)
    @final
    def AsGenerator(self, order: EnumerationOrder = EnumerationOrder.FIFO) -> IIterator[TItem]:
        match order:
            case EnumerationOrder.FIFO: return self._GetInnerCookie().GetGenerator()
            case EnumerationOrder.LIFO: return self.AsReversed().AsGenerator()

            case _: raise GetInvalidEnumerationOrderError(order)

class ListBase[TItem, TNode](EnumerableList[TItem, TNode, IDoublyLinkedNode[TItem], ListAbstract[TItem, TNode, IDoublyLinkedNode[TItem]]], IList[TItem], IGenericConstraintImplementation[IDoublyLinkedNode[TItem]]):
    def __init__(self, items: Iterable[TItem]|None) -> None: super().__init__(items)

    @final
    def _GetItemsAsClass(self, items: ListAbstract[TItem, TNode, IDoublyLinkedNode[TItem]]) -> ListAbstract[TItem, TNode, IDoublyLinkedNode[TItem]]: return items
    
    def _GetNextNode(self, node: IDoublyLinkedNode[TItem]) -> IDoublyLinkedNode[TItem]|None: return node.GetNext()
    
    @final
    def _GetNodeEnumerator(self, node: IDoublyLinkedNode[TItem]) -> IEnumerator[IDoublyLinkedNode[TItem]]:
        return DoublyLinkedNodeEnumerator[TItem](node)
    @final
    def _GetResumableNodeEnumerator(self, node: IDoublyLinkedNode[TItem]) -> IResumableEnumerator[IDoublyLinkedNode[TItem]]:
        return ResumableDoublyLinkedNodeEnumerator[TItem](node)

@final
class _Node[T](DoublyLinkedNode[T, "_Node[T]", IList[T], ListBase[T, "_Node[T]"]], ListNodeBase["_Node[T]"], IDoublyLinkedNode[T], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, value: T, l: ListBase[T, _Node[T]]|None, itemCookie: IListCookie[_Node[T]], cookie: INodeCookie[_Node[T]], previousNode: SelfType|None, nextNode: SelfType|None) -> None: super().__init__(value, l, itemCookie, cookie, previousNode, nextNode)
    
    def _AsLinkedNode(self, node: _Node[T]) -> _Node[T]:
        return node
    
    def _GetListAsClass(self, l: ListBase[T, _Node[T]]) -> IList[T]:
        return l
    
    def _AsNode(self) -> _Node[T]:
        return self
    
    def _CreateNode(self, value: T, previous: SelfType|None, next: SelfType|None) -> _Node[T]:
        return _Node[T](value, self._GetInnerList(), self._GetItemCookie(), self._GetCookie(), previous, next)
    
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
    def AsNodeGenerator(self, order: EnumerationOrder = EnumerationOrder.FIFO) -> IIterator[TNode]:
        match order:
            case EnumerationOrder.FIFO: return self._GetInnerCookie().GetNodeGenerator()
            case EnumerationOrder.LIFO: return self.AsReversed().AsNodeGenerator()
        
            case _: raise GetInvalidEnumerationOrderError(order)
    @final
    def AsGenerator(self, order: EnumerationOrder = EnumerationOrder.FIFO) -> IIterator[TItem]:
        match order:
            case EnumerationOrder.FIFO: return self._GetInnerCookie().GetGenerator()
            case EnumerationOrder.LIFO: return self.AsReversed().AsGenerator()
        
            case _: raise GetInvalidEnumerationOrderError(order)

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
    
    def _GetNextNode(self, node: IDoublyLinkedNode[T]) -> IDoublyLinkedNode[T]|None: return node.GetNext()
    
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
    
    def _GetNextNode(self, node: ICountableLinkedListNode[T]) -> ICountableLinkedListNode[T]|None: return node.GetNext()
    
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

@final
class _List[T](ListAbstract[T, _Node[T], IDoublyLinkedNode[T]], IGenericConstraintImplementation[IDoublyLinkedNode[T]]):
    def __init__(self, items: List[T]) -> None:
        # __items must exist before super().__init__ populates the list, since _CreateNode reads it.
        self.__items: List[T] = items

        super().__init__()

    def _CreateNode(self, value: T) -> _Node[T]:
        return _Node[T](value, self.__items, self, self._GetCookie(), None, None)
    
    def _GetPreviousNode(self, node: _Node[T]) -> _Node[T]|None:
        return node.GetPreviousNode()
    def _GetNextNode(self, node: _Node[T]) -> _Node[T]|None:
        return node.GetNextNode()
    
    def _AddNode(self, value: T) -> _Node[T]:
        return super()._AddNode(value)
    
    def _GetNodeAsClass(self, node: _Node[T]) -> IDoublyLinkedNode[T]:
        return node
    def _GetNodeAsInterface(self, node: _Node[T]) -> IDoublyLinkedNodeBase[T, _Node[T]]:
        return node
    
    def _UnregisterNode(self, node: _Node[T]) -> None:
        return node._Unregister() # pyright: ignore[reportPrivateUsage]
    
    def AsReadOnly(self) -> IReadOnlyList[T]:
        return self.__items.AsReadOnly()

class List[T](ListBase[T, _Node[T]]):
    def __init__(self, items: Iterable[T]|None = None) -> None:
        def update(func: IFunction[IList[T]]) -> None: self.__reversed = func
        
        super().__init__(items)

        self.__reversed: IFunction[IList[T]] = _ReversedUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def _CreateList(self) -> ListAbstract[T, _Node[T], IDoublyLinkedNode[T]]:
        return _List[T](self)
    
    @final
    def _GetNodeAsInterface(self, node: IDoublyLinkedNode[T]) -> ILinkedNode[T]:
        return node
    
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
    
    def GetNodeEnumerable(self) -> IResumableCountableEnumerable[ICountableLinkedListNode[T]]: return self.__nodeEnumerable.GetValue()

@final
class _CountableListNode[T](DoublyLinkedNodeBase[T, "_CountableListNode[T]", ICountableList[T], CountableListProvider[T]], NodeBase[T, "_CountableListNode[T]"], ListNodeBase["_CountableListNode[T]"], ICountableLinkedListNode[T], IGenericConstraintImplementation[ICountableList[T]]):
    def __init__(self, value: T, l: CountableListProvider[T]|None, itemCookie: IListCookie[_CountableListNode[T]], cookie: INodeCookie[_CountableListNode[T]], previousNode: SelfType|None, nextNode: SelfType|None) -> None:
        super().__init__(value, l, itemCookie, cookie, previousNode, nextNode)
    
    def _GetListAsClass(self, l: CountableListProvider[T]) -> ICountableList[T]:
        return l.GetItems()
    
    def _GetNodeAsClass(self, node: _CountableListNode[T]) -> ICountableLinkedListNode[T]:
        return node
    
    def _AsNode(self) -> SelfType:
        return self
    
    def _AsLinkedNode(self, node: _CountableListNode[T]) -> DoublyLinkedNodeAbstract[T, _CountableListNode[T], ICountableList[T], CountableListProvider[T]]:
        return node
    
    def _CreateNode(self, value: T, previous: SelfType|None, next: SelfType|None) -> _CountableListNode[T]:
        return _CountableListNode[T](value, self._GetInnerList(), self._GetItemCookie(), self._GetCookie(), previous, next)
    
    def GetList(self) -> ICountableList[T]|None: return self._GetList()
    
    def GetPrevious(self) -> _CountableListNode[T]|None: return self.GetPreviousNode()
    def GetNext(self) -> _CountableListNode[T]|None: return self.GetNextNode()
    
    def _OnAdded(self, node: ICountableLinkedListNode[T]) -> None:
        l: CountableListProvider[T]|None = self._GetInnerList()

        if l is not None: l.OnAdded(node)
    def _OnRemoved(self, l: CountableListProvider[T]|None, value: T) -> None:
        if l is not None: l.OnRemoved(value)
    
    def SetPrevious(self, value: T) -> _CountableListNode[T]:
        node: _CountableListNode[T] = self._SetPreviousNode(value)

        self._OnAdded(node)

        return node
    def SetNext(self, value: T) -> _CountableListNode[T]:
        node: _CountableListNode[T] = self._SetNextNode(value)

        self._OnAdded(node)

        return node
    
    def RemoveNode(self) -> T:
        l: CountableListProvider[T]|None = self._GetInnerList()

        value: T = super().RemoveNode()

        self._OnRemoved(l, value)

        return value

@final
class _CountableInnerListBase[T](ListAbstract[T, _CountableListNode[T], ICountableLinkedListNode[T]], IGenericConstraintImplementation[ICountableLinkedListNode[T]]):
    def __init__(self, items: CountableList[T], l: CountableListProvider[T]) -> None:
        self.__items: CountableList[T] = items
        self.__cookie: CountableListProvider[T] = l
        self.__count: int = 0

        super().__init__()
    
    def _GetNodeAsClass(self, node: _CountableListNode[T]) -> ICountableLinkedListNode[T]:
        return node
    def _GetNodeAsInterface(self, node: _CountableListNode[T]) -> IDoublyLinkedNodeBase[T, _CountableListNode[T]]:
        return node
    
    def _CreateNode(self, value: T) -> _CountableListNode[T]:
        return _CountableListNode[T](value, self.__cookie, self, self._GetCookie(), None, None)
    
    def _AddNode(self, value: T) -> _CountableListNode[T]:
        node: _CountableListNode[T] = super()._AddNode(value)

        self.Increment()

        return node
    
    def AsSized(self) -> Sized: return self.__cookie.AsSized()
    
    def GetCount(self) -> int: return self.__count
    
    def Increment(self) -> None: self.__count += 1
    def Decrement(self) -> None: self.__count -= 1

    def Reset(self) -> None:
        self.__count = 0
    
    def _GetPreviousNode(self, node: _CountableListNode[T]) -> _CountableListNode[T]|None:
        return node.GetPreviousNode()
    def _GetNextNode(self, node: _CountableListNode[T]) -> _CountableListNode[T]|None:
        return node.GetNextNode()
    
    def _UnregisterNode(self, node: _CountableListNode[T]) -> None:
        return node._Unregister() # pyright: ignore[reportPrivateUsage]
    
    def AsReadOnly(self) -> IReadOnlyList[T]:
        return self.__items.AsReadOnly()

class CountableListBase[TItem, TNode](_Enumerable[TItem, TNode, ICountableLinkedListNode[TItem], IReadOnlyCountableEnumerableList[TItem], _CountableInnerListBase[TItem], ICountableEnumerableListCookieAbstract[TItem, ICountableLinkedListNode[TItem], IReadOnlyCountableEnumerableList[TItem]]], ICountableList[TItem], IGenericConstraintImplementation[ICountableLinkedListNode[TItem]]):
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
    
    @final
    def AsNodeEnumerable(self) -> IResumableCountableEnumerable[ICountableLinkedListNode[TItem]]: return self._GetEnumerationCookie().GetNodeEnumerable()
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[TItem]: return self._AsReadOnly()

@final
class _ReversedCountableList[T](CountableEnumerable[T], _EnumerableListAbstract[T, ICountableLinkedListNode[T]], ICountableList[T], IGenericConstraintImplementation[ICountableLinkedListNode[T]]):
    def __init__(self, items: ICountableList[T]) -> None:
        super().__init__()

        self.__items: _ReversedCountableListBase[T] = _ReversedCountableListBase[T](items)
        self.__countable: ICountable = items
    
    def _GetNextNode(self, node: ICountableLinkedListNode[T]) -> ICountableLinkedListNode[T]|None: return node.GetNext()
    
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

    def AsNodeGenerator(self, order: EnumerationOrder = EnumerationOrder.FIFO) -> IIterator[ICountableLinkedListNode[T]]: return self.__items.AsNodeGenerator(order)
    def AsGenerator(self, order: EnumerationOrder = EnumerationOrder.FIFO) -> IIterator[T]: return self.__items.AsGenerator(order)
@final
class _ReversedCountableUpdater[T](ValueFunctionUpdater[ICountableList[T]]):
    def __init__(self, items: ICountableList[T], updater: Method[IFunction[ICountableList[T]]]) -> None:
        super().__init__(updater)

        self.__items: ICountableList[T] = items
    
    def _GetValue(self) -> ICountableList[T]: return _ReversedCountableList[T](self.__items)

@final
class _CountableInnerList[T](CountableListBase[T, _CountableListNode[T]]):
    def __init__(self, items: CountableList[T], l: CountableListProvider[T], values: Iterable[T]|None) -> None:
        def update(func: IFunction[ICountableList[T]]) -> None: self.__reversed = func

        self.__items: CountableList[T] = items
        self.__cookie: CountableListProvider[T] = l
        
        super().__init__(values)

        self.__reversed: IFunction[ICountableList[T]] = _ReversedCountableUpdater[T](self, update) # type: ignore[no-redef]
    
    def _CreateList(self) -> _CountableInnerListBase[T]:
        return _CountableInnerListBase[T](self.__items, self.__cookie)
    
    def _GetItemsAsClass(self, items: _CountableInnerListBase[T]) -> ListAbstract[T, _CountableListNode[T], ICountableLinkedListNode[T]]:
        return items
    
    def _GetNodeAsInterface(self, node: ICountableLinkedListNode[T]) -> ILinkedNode[T]:
        return node
    
    def _GetNextNode(self, node: ICountableLinkedListNode[T]) -> ICountableLinkedListNode[T]|None: return node.GetNext()
    
    def GetCount(self) -> int: return self._GetItems().GetCount()
    
    def Increment(self) -> None: self._GetItems().Increment()
    def Decrement(self) -> None: self._GetItems().Decrement()

    def Clear(self) -> None:
        super().Clear()

        self._GetItems().Reset()
    
    @final
    def AsNodeGenerator(self, order: EnumerationOrder = EnumerationOrder.FIFO) -> IIterator[ICountableLinkedListNode[T]]:
        match order:
            case EnumerationOrder.FIFO: return self._GetInnerCookie().GetNodeGenerator()
            case EnumerationOrder.LIFO: return self.AsReversed().AsNodeGenerator()
        
            case _: raise GetInvalidEnumerationOrderError(order)
    @final
    def AsGenerator(self, order: EnumerationOrder = EnumerationOrder.FIFO) -> IIterator[T]:
        match order:
            case EnumerationOrder.FIFO: return self._GetInnerCookie().GetGenerator()
            case EnumerationOrder.LIFO: return self.AsReversed().AsGenerator()
        
            case _: raise GetInvalidEnumerationOrderError(order)
    
    def AsReversed(self) -> ICountableList[T]: return self.__reversed.GetValue()
    def AsSized(self) -> Sized: return self._GetItems().AsSized()

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

        self.__items: _CountableInnerList[T] = _CountableInnerList[T](self, CountableList[T]._CountableListProvider(self), items)
    
    @final
    def _OnAdded(self, node: ICountableLinkedListNode[T]) -> None:
        self._GetItems().Increment()
    
    @final
    def _OnRemoved(self, value: T) -> None:
        items: _CountableInnerList[T] = self._GetItems()

        if items.GetCount() > 0: # Needed to avoid double decrementation when removing the last node.
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
    def AsNodeGenerator(self, order: EnumerationOrder = EnumerationOrder.FIFO) -> IIterator[ICountableLinkedListNode[T]]: return self._GetItems().AsNodeGenerator(order)
    @final
    def AsGenerator(self, order: EnumerationOrder = EnumerationOrder.FIFO) -> IIterator[T]: return self._GetItems().AsGenerator(order)
    
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