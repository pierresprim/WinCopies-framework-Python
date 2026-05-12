from __future__ import annotations

from abc import abstractmethod
from weakref import ref, ReferenceType

from WinCopies import IInterface, Abstract
from WinCopies.Collections import IGetter
from WinCopies.Collections.Generation.Factory import IObjectFactory
from WinCopies.Typing.Comparison import IHashableItem, HashableProtocol, HashableComparableProtocol

def ExtractKey(item: INodeBase|object) -> object:
    return item.GetKey() if isinstance(item, INodeBase) else item
def GetKey[TKey: HashableComparableProtocol, TValue](node: INode[TKey, TValue]) -> TKey:
    return node.GetKey()

class INodeBase(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetKey(self) -> object:
        pass
class INode[TKey, TValue](INodeBase, IHashableItem["INode[TKey, TValue]|TKey"]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetKey(self) -> TKey:
        pass
    
    @abstractmethod
    def TryGetValue(self) -> TValue|None:
        pass

class Node[TKey: HashableProtocol, TValue](Abstract, INode[TKey, TValue]):
    def __init__(self, key: TKey, obj: TValue) -> None:
        super().__init__()

        self.__key: TKey = key
        self.__ref: ReferenceType[TValue] = ref(obj)
    
    def GetKey(self) -> TKey:
        return self.__key
    
    def TryGetValue(self) -> TValue|None:
        return self.__ref()
    
    def Equals(self, item: INode[TKey, TValue]|TKey|object) -> bool:
        return self.GetKey() == ExtractKey(item)
    
    def Hash(self) -> int:
        return hash(self.GetKey())

class IKeyableObjectFactoryBase[TKey, TIn, TOut](IObjectFactory[TIn], IGetter[TKey, TOut]):
    def __init__(self) -> None:
        super().__init__()
class IKeyableObjectFactory[TKey, TValue](IKeyableObjectFactoryBase[TKey, TValue, TValue]):
    def __init__(self) -> None:
        super().__init__()