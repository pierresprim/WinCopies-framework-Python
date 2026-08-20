from abc import abstractmethod
from weakref import ref, ReferenceType

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Core import IGetter
from WinCopies.Collections.Generation.Factory import IObjectRegistry
from WinCopies.Typing.Comparison import IHashableItem, HashableProtocol

class INodeBase(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetKey(self) -> object:
        ...
class INode[TKey, TValue](INodeBase, IHashableItem[TKey]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetKey(self) -> TKey:
        ...
    
    @abstractmethod
    def TryGetValue(self) -> TValue|None:
        ...

def ExtractKey(item: INodeBase|object) -> object:
    return item.GetKey() if isinstance(item, INodeBase) else item
def GetKey[TKey: HashableProtocol, TValue](node: INode[TKey, TValue]) -> TKey:
    return node.GetKey()

class Node[TKey: HashableProtocol, TValue](Abstract, INode[TKey, TValue]):
    def __init__(self, key: TKey, obj: TValue) -> None:
        super().__init__()

        self.__key: TKey = key
        self.__ref: ReferenceType[TValue] = ref(obj)
    
    def GetKey(self) -> TKey: return self.__key
    
    def TryGetValue(self) -> TValue|None: return self.__ref()
    
    def Equals(self, item: INode[TKey, TValue]|TKey|object) -> bool: return self.GetKey() == ExtractKey(item)
    def Hash(self) -> int: return hash(self.GetKey())

class IKeyableObjectRegistryBase[TKey, TIn, TOut](IObjectRegistry[TIn], IGetter[TKey, TOut]):
    def __init__(self) -> None: super().__init__()
class IKeyableObjectRegistry[TKey, TValue](IKeyableObjectRegistryBase[TKey, TValue, TValue]):
    def __init__(self) -> None: super().__init__()