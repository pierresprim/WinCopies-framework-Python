from __future__ import annotations

from abc import abstractmethod
from typing import final, Self

from WinCopies.Collections.Enumeration import GetIterator, IEnumerable, IEnumerator, ConverterEnumerator, IteratorProvider
from WinCopies.Collections.Enumeration.Extensions import IRecursivelyEnumerable, IRecursiveEnumerationHandler, IRecursiveStackedEnumerationHandler, RecursiveEnumerationHandlerConverter, RecursiveStackedEnumerationHandlerConverter, RecursivelyEnumerable
from WinCopies.Collections.Linked.Doubly import INode, IDoublyLinkedNodeBase, IEnumerableList, DoublyLinkedNode, EnumerableList, DoublyLinkedNodeEnumeratorBase
from WinCopies.Typing import IGenericConstraintImplementation
from WinCopies.Typing.Delegate import IFunction, Method, ValueFunctionUpdater

class ITreeNode[T](INode[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetItems(self) -> ITree[T]:
        pass

class ITree[T](IEnumerableList[T, ITreeNode[T]], IRecursivelyEnumerable[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsNodeRecursivelyEnumerable(self) -> IRecursivelyEnumerable[ITreeNode[T]]:
        pass

class TreeBase[TItem, TNode](EnumerableList[TItem, TNode, ITreeNode[TItem], "TreeBase"], ITree[TItem], IGenericConstraintImplementation[ITreeNode[TItem]]):
    @final
    class __RecursivelyEnumerable(RecursivelyEnumerable[ITreeNode[TItem]]):
        def __init__(self, tree: ITree[TItem]):
            super().__init__()

            self.__tree: ITree[TItem] = tree
        
        def _AsRecursivelyEnumerable(self, container: ITreeNode[TItem]) -> IEnumerable[ITreeNode[TItem]]:
            return container.GetItems().AsNodeEnumerable()
        
        def TryGetEnumerator(self) -> IEnumerator[ITreeNode[TItem]]|None:
            return self.__tree.TryGetNodeEnumerator()
    
    @final
    class __RecursiveUpdater(ValueFunctionUpdater[IEnumerable[TItem]]):
        def __init__(self, tree: ITree[TItem], updater: Method[IFunction[IEnumerable[TItem]]]):
            super().__init__(updater)

            self.__tree: ITree[TItem] = tree
        
        def _GetValue(self) -> IEnumerable[TItem]:
            return IteratorProvider[TItem](lambda: GetIterator(self.__tree.TryGetRecursiveEnumerator())) # type: ignore
    @final
    class __NodeRecursiveUpdater(ValueFunctionUpdater[IRecursivelyEnumerable[ITreeNode[TItem]]]):
        def __init__(self, tree: ITree[TItem], updater: Method[IFunction[IRecursivelyEnumerable[ITreeNode[TItem]]]]):
            super().__init__(updater)

            self.__tree: ITree[TItem] = tree
        
        def _GetValue(self) -> IRecursivelyEnumerable[ITreeNode[TItem]]:
            return TreeBase[TItem, TNode].__RecursivelyEnumerable(self.__tree)
    
    def __init__(self):
        def updateRecursive(func: IFunction[IEnumerable[TItem]]) -> None:
            self.__recursive = func
        def updateNodeRecursive(func: IFunction[IRecursivelyEnumerable[ITreeNode[TItem]]]) -> None:
            self.__nodeRecursive = func
        
        super().__init__()
    
        self.__recursive: IFunction[IEnumerable[TItem]] = TreeBase[TItem, TNode].__RecursiveUpdater(self, updateRecursive)
        self.__nodeRecursive: IFunction[IRecursivelyEnumerable[ITreeNode[TItem]]] = TreeBase[TItem, TNode].__NodeRecursiveUpdater(self, updateNodeRecursive)
    
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
    def TryGetRecursiveEnumerator(self, handler: IRecursiveEnumerationHandler[TItem]|None = None) -> IEnumerator[TItem]|None:
        return self.__TryGetRecursiveEnumerator(self.AsNodeRecursivelyEnumerable().TryGetRecursiveEnumerator(None if handler is None else RecursiveEnumerationHandlerConverter[ITreeNode[TItem], TItem](handler, lambda item: item.GetValue())))
    @final
    def TryGetRecursiveStackedEnumerator(self, handler: IRecursiveStackedEnumerationHandler[TItem]|None = None) -> IEnumerator[TItem]|None:
        return self.__TryGetRecursiveEnumerator(self.AsNodeRecursivelyEnumerable().TryGetRecursiveStackedEnumerator(None if handler is None else RecursiveStackedEnumerationHandlerConverter[ITreeNode[TItem], TItem](handler, lambda node: node.GetValue())))

@final
class __TreeNode[T](DoublyLinkedNode[T, "__TreeNode", ITreeNode[T], TreeBase[T, "__TreeNode"], TreeBase[T, "__TreeNode"]], EnumerableList[T, "__TreeNode", ITreeNode[T], TreeBase[T, "__TreeNode"]].NodeBase, ITreeNode[T], IGenericConstraintImplementation[IEnumerableList[T, ITreeNode[T]]]):
    def __init__(self, value: T, l: TreeBase[T, __TreeNode[T]]|None, previousNode: __TreeNode[T]|None, nextNode: __TreeNode[T]|None):
        super().__init__(value, l, previousNode, nextNode)

        self.__items: ITree[T] = Tree[T]()
    
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
        return __TreeNode[T](value, self._GetList(), previous, next)
    
    @final
    def GetItems(self) -> ITree[T]:
        return self.__items
    
    @final
    def GetList(self) -> ITree[T]|None:
        return self._GetList()

class Tree[T](TreeBase[T, __TreeNode[T]]):
    def __init__(self):
        super().__init__()
    
    @final
    def _GetNodeAsClass(self, node: __TreeNode[T]) -> ITreeNode[T]:
        return node
    @final
    def _GetNodeAsInterface(self, node: __TreeNode[T]) -> IDoublyLinkedNodeBase[T, __TreeNode[T]]:
        return node
    
    @final
    def _GetNode(self, value: T) -> __TreeNode[T]:
        return __TreeNode[T](value, self, None, None)

class TreeNodeEnumerator[T](DoublyLinkedNodeEnumeratorBase[T, ITreeNode[T]], IGenericConstraintImplementation[ITreeNode[T]]):
    def __init__(self, node: ITreeNode[T]):
        super().__init__(node)

    def _GetNextNode(self, node: ITreeNode[T]) -> ITreeNode[T]|None:
        return self._AsContainer(node).GetNext()