from __future__ import annotations

from abc import abstractmethod
from typing import final, Self

from WinCopies.Collections.Enumeration import IEnumerator
from WinCopies.Collections.Linked.Doubly import INode, IDoublyLinkedNodeBase, IEnumerableList, DoublyLinkedNode, EnumerableList, DoublyLinkedNodeEnumeratorBase
from WinCopies.Typing import IGenericConstraintImplementation

class ITreeNode[T](INode[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetItems(self) -> ITree[T]:
        pass

class ITree[T](IEnumerableList[T, ITreeNode[T]]):
    def __init__(self):
        super().__init__()

class TreeBase[TItem, TNode](EnumerableList[TItem, TNode, ITreeNode[TItem], "TreeBase"], ITree[TItem], IGenericConstraintImplementation[ITreeNode[TItem]]):
    def __init__(self):
        super().__init__()
    
    @final
    def _GetNodeEnumerator(self, node: ITreeNode[TItem]) -> IEnumerator[ITreeNode[TItem]]:
        return TreeNodeEnumerator[TItem](node)

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