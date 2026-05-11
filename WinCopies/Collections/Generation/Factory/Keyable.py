from __future__ import annotations

from abc import abstractmethod
from weakref import ref, ReferenceType

from WinCopies import Abstract
from WinCopies.Collections import IGetter
from WinCopies.Collections.Generation.Factory import IObjectFactory
from WinCopies.Typing.Comparison import IHashableItem, HashableComparableProtocol

def ExtractKey(item: NodeBase|object) -> object:
    return item.GetKey() if isinstance(item, NodeBase) else item
def GetKey[TKey: HashableComparableProtocol, TValue](node: Node[TKey, TValue]) -> TKey:
    return node.GetKey()

class NodeBase(Abstract):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetKey(self) -> object:
        pass
class Node[TKey: HashableComparableProtocol, TValue](NodeBase, IHashableItem["Node[TKey, TValue]|TKey"]):
    def __init__(self, key: TKey, obj: TValue) -> None:
        super().__init__()

        self.__key: TKey = key
        self.__ref: ReferenceType[TValue] = ref(obj)
    
    def TryGetValue(self) -> TValue|None:
        return self.__ref()
    
    def GetKey(self) -> TKey:
        return self.__key
    
    def Equals(self, item: Node[TKey, TValue]|TKey|object) -> bool:
        return self.GetKey() == ExtractKey(item)
    
    def Hash(self) -> int:
        return hash(self.GetKey())

class IKeyableObjectFactoryBase[TKey, TIn, TOut](IObjectFactory[TIn], IGetter[TKey, TOut]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def BisectLeft(self, key: TKey) -> int:
        pass
    @abstractmethod
    def BisectRight(self, key: TKey) -> int:
        pass
class IKeyableObjectFactory[TKey, TValue](IKeyableObjectFactoryBase[TKey, TValue, TValue]):
    def __init__(self) -> None:
        super().__init__()