from __future__ import annotations

from abc import abstractmethod
from typing import final, Self

from WinCopies.Collections import EnumerationOrder
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, ConverterEnumerator, EnumeratorProvider
from WinCopies.Collections.Enumeration.Recursive import IRecursivelyEnumerable, IRecursiveEnumerationHandler, IRecursiveStackedEnumerationHandler, RecursiveEnumerationHandlerConverter, RecursiveStackedEnumerationHandlerConverter, RecursivelyEnumerable
from WinCopies.Collections.Linked.Doubly import INode, IDoublyLinkedNodeBase, INodeCookie, IEnumerableList, NodeBase, EnumerableListNodeBase, DoublyLinkedNodeAbstract, EnumerableList, DoublyLinkedNodeEnumeratorBase
from WinCopies.Typing import IGenericConstraintImplementation
from WinCopies.Typing.Delegate import IFunction, Method, ValueFunctionUpdater

class ITreeNode[T](INode[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetItems(self) -> ITree[T]:
        pass

class ITree[T](IEnumerableList[T, ITreeNode[T]], IRecursivelyEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsNodeRecursivelyEnumerable(self) -> IRecursivelyEnumerable[ITreeNode[T]]:
        pass

@final
class _RecursivelyEnumerable[T](RecursivelyEnumerable[ITreeNode[T]]):
    def __init__(self, tree: ITree[T]) -> None:
        super().__init__()

        self.__tree: ITree[T] = tree
    
    def _AsRecursivelyEnumerable(self, container: ITreeNode[T]) -> IEnumerable[ITreeNode[T]]:
        return container.GetItems().AsNodeEnumerable()
    
    def TryGetEnumerator(self) -> IEnumerator[ITreeNode[T]]|None:
        return self.__tree.TryGetNodeEnumerator()

@final
class _RecursiveUpdater[T](ValueFunctionUpdater[IEnumerable[T]]):
    def __init__(self, tree: ITree[T], updater: Method[IFunction[IEnumerable[T]]]) -> None:
        super().__init__(updater)

        self.__tree: ITree[T] = tree
    
    def _GetValue(self) -> IEnumerable[T]:
        return EnumeratorProvider[T](lambda: self.__tree.TryGetRecursiveEnumerator())
@final
class _NodeRecursiveUpdater[T](ValueFunctionUpdater[IRecursivelyEnumerable[ITreeNode[T]]]):
    def __init__(self, tree: ITree[T], updater: Method[IFunction[IRecursivelyEnumerable[ITreeNode[T]]]]) -> None:
        super().__init__(updater)

        self.__tree: ITree[T] = tree
    
    def _GetValue(self) -> IRecursivelyEnumerable[ITreeNode[T]]:
        return _RecursivelyEnumerable[T](self.__tree)

class TreeBase[TItem, TNode](EnumerableList[TItem, TNode, ITreeNode[TItem], "TreeBase[TItem, TNode]"], ITree[TItem], IGenericConstraintImplementation[ITreeNode[TItem]]):
    def __init__(self) -> None:
        def updateRecursive(func: IFunction[IEnumerable[TItem]]) -> None:
            self.__recursive = func
        def updateNodeRecursive(func: IFunction[IRecursivelyEnumerable[ITreeNode[TItem]]]) -> None:
            self.__nodeRecursive = func
        
        super().__init__()
    
        self.__recursive: IFunction[IEnumerable[TItem]] = _RecursiveUpdater[TItem](self, updateRecursive) # type: ignore[no-redef]
        self.__nodeRecursive: IFunction[IRecursivelyEnumerable[ITreeNode[TItem]]] = _NodeRecursiveUpdater[TItem](self, updateNodeRecursive) # type: ignore[no-redef]
    
    @final
    def __TryGetRecursiveEnumerator(self, enumerator: IEnumerator[ITreeNode[TItem]]|None) -> IEnumerator[TItem]|None:
        return None if enumerator is None else ConverterEnumerator[ITreeNode[TItem], TItem](enumerator, lambda node: node.GetValue())
    
    @final
    def _GetNodeEnumerator(self, node: ITreeNode[TItem]) -> IEnumerator[ITreeNode[TItem]]:
        return TreeNodeEnumerator[TItem](node)
    
    @final
    def AsRecursivelyEnumerable(self) -> IEnumerable[TItem]:
        return self.__recursive.GetValue()
    @final
    def AsNodeRecursivelyEnumerable(self) -> IRecursivelyEnumerable[ITreeNode[TItem]]:
        return self.__nodeRecursive.GetValue()
    
    @final
    def TryGetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[TItem]|None = None) -> IEnumerator[TItem]|None:
        return self.__TryGetRecursiveEnumerator(self.AsNodeRecursivelyEnumerable().TryGetRecursiveEnumerator(enumerationOrder, None if handler is None else RecursiveEnumerationHandlerConverter[ITreeNode[TItem], TItem](handler, lambda item: item.GetValue())))
    @final
    def TryGetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[TItem]|None = None) -> IEnumerator[TItem]|None:
        return self.__TryGetRecursiveEnumerator(self.AsNodeRecursivelyEnumerable().TryGetRecursiveStackedEnumerator(enumerationOrder, None if handler is None else RecursiveStackedEnumerationHandlerConverter[ITreeNode[TItem], TItem](handler, lambda node: node.GetValue())))

@final
class __TreeNode[T](DoublyLinkedNodeAbstract[T, "__TreeNode[T]", ITreeNode[T], TreeBase[T, "__TreeNode[T]"], TreeBase[T, "__TreeNode[T]"]], NodeBase[T, "__TreeNode[T]"], ITreeNode[T], EnumerableListNodeBase[T, "__TreeNode[T]", ITreeNode[T], TreeBase[T, "__TreeNode[T]"]], IGenericConstraintImplementation[IEnumerableList[T, ITreeNode[T]]]):
    def __init__(self, value: T, l: TreeBase[T, __TreeNode[T]]|None, cookie: INodeCookie[__TreeNode[T]], previousNode: __TreeNode[T]|None, nextNode: __TreeNode[T]|None) -> None:
        super().__init__(value, l, cookie, previousNode, nextNode)

        self.__items: ITree[T] = Tree[T]()
    
    def _AsLinkedNode(self, node: __TreeNode[T]) -> __TreeNode[T]:
        return node
    
    def _GetNodeAsClass(self, node: __TreeNode[T]) -> ITreeNode[T]:
        return node
    
    @final
    def _GetListAsClass(self, l: TreeBase[T, __TreeNode[T]]) -> TreeBase[T, __TreeNode[T]]:
        return l
    @final
    def _GetListAsSpecialized(self, l: TreeBase[T, __TreeNode[T]]) -> EnumerableList[T, __TreeNode[T], ITreeNode[T], TreeBase[T, __TreeNode[T]]]:
        return l
    
    @final
    def _AsNode(self) -> __TreeNode[T]:
        return self
    
    @final
    def _GetNode(self, value: T, previous: Self|None, next: Self|None) -> __TreeNode[T]:
        return __TreeNode[T](value, self._GetList(), self._GetCookie(), previous, next)
    
    @final
    def GetItems(self) -> ITree[T]:
        return self.__items
    
    @final
    def GetList(self) -> ITree[T]|None:
        return self._GetList()

class Tree[T](TreeBase[T, __TreeNode[T]]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _GetNodeAsClass(self, node: __TreeNode[T]) -> ITreeNode[T]:
        return node
    @final
    def _GetNodeAsInterface(self, node: __TreeNode[T]) -> IDoublyLinkedNodeBase[T, __TreeNode[T]]:
        return node
    
    @final
    def _GetNode(self, value: T) -> __TreeNode[T]:
        return __TreeNode[T](value, self, self._GetCookie(), None, None)

class TreeNodeEnumerator[T](DoublyLinkedNodeEnumeratorBase[T, ITreeNode[T]], IGenericConstraintImplementation[ITreeNode[T]]):
    def __init__(self, node: ITreeNode[T]) -> None:
        super().__init__(node)

    def _GetNextNode(self, node: ITreeNode[T]) -> ITreeNode[T]|None:
        return self._AsContainer(node).GetNext()