from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies.Collections.Linked.Doubly import IList, List
from WinCopies.Typing.Pairing import IKeyValuePair

class ITreeNode[TValue, TTree](IKeyValuePair[TValue, TTree|None]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _AsTree(self, tree: TTree) -> ITree[TValue]:
        pass

class ITree[T](IList[ITreeNode[T, 'ITree']]):
    def __init__(self):
        super().__init__()

class TreeNodeBase[T](ITreeNode[T, ITree[T]]):
    def __init__(self, value: T):
        super().__init__()

        self.__value: T = value
    
    def GetKey(self) -> T:
        return self.__value
    
    @final
    def _AsTree(self, tree: ITree[T]) -> ITree[T]:
        return tree
@final
class TreeNode[T](TreeNodeBase[T]):
    def __init__(self, value: T, items: ITree[T]):
        super().__init__(value)

        self.__items: ITree[T] = items
    
    def GetValue(self) -> ITree[T]:
        return self.__items
@final
class EmptyTreeNode[T](TreeNodeBase[T]):
    def __init__(self, value: T):
        super().__init__(value)
    
    def GetValue(self) -> None:
        return None

class Tree[T](List[ITreeNode[T, ITree[T]]], ITree[T]):
    def __init__(self):
        super().__init__()