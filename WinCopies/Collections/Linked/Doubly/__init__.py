from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import final

from WinCopies.Collections.Core import IClearable, IReadOnlyCollection
from WinCopies.Collections.Linked.Node import IReadWriteTwoWayLinkedNode
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Converter

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
class IReadWriteList[T](IReadOnlyList[T], IClearable):
    def __init__(self) -> None: super().__init__()

    @final
    def __TryGet(self, node: IReadWriteTwoWayLinkedNode[T]|None) -> INullable[T]:
        return GetNullValue() if node is None else GetNullable(node.GetValue())
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyList[T]:
        ...
    
    @abstractmethod
    def GetFirstNode(self) -> IReadWriteTwoWayLinkedNode[T]|None:
        ...
    @abstractmethod
    def GetLastNode(self) -> IReadWriteTwoWayLinkedNode[T]|None:
        ...
    
    @final
    def TryGetFirst(self) -> INullable[T]:
        return self.__TryGet(self.GetFirstNode())
    @final
    def TryGetLast(self) -> INullable[T]:
        return self.__TryGet(self.GetLastNode())
    
    @abstractmethod
    def AddFirstNode(self, value: T) -> IReadWriteTwoWayLinkedNode[T]:
        ...
    @abstractmethod
    def AddLastNode(self, value: T) -> IReadWriteTwoWayLinkedNode[T]:
        ...

    @final
    def __AddItems(self, items: Iterable[T]|None, first: Converter[T, IReadWriteTwoWayLinkedNode[T]]) -> bool:
        if items is None: return False
        
        node: IReadWriteTwoWayLinkedNode[T] = None # type: ignore
        adder: Converter[T, IReadWriteTwoWayLinkedNode[T]]|None = None

        def add(item: T) -> IReadWriteTwoWayLinkedNode[T]:
            def add(item: T) -> IReadWriteTwoWayLinkedNode[T]: return node.SetNext(item)

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