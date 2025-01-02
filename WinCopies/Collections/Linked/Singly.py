from abc import abstractmethod
from typing import final

from WinCopies.Collections import Collection

class Base(Collection):
    class _Node:
        def __init__(self, value, next):
            self.__value = value
            self.__next = next
        
        @final
        def GetValue(self):
            return self.__value
        
        @final
        def _GetNext(self):
            return self.__next
        @final
        def _SetNext(self, next):
            self.__next = next
    
    def __init__(self):
        self.__first: Base._Node|None = None

    @final
    def IsEmpty(self) -> bool:
        return self.__first is None
    @final
    def HasItems(self) -> bool:
        return super().HasItems(self)
    
    @abstractmethod
    def _InitFirstNode(self, value) -> None:
        pass
    @final
    def _GetFirst(self):
        return self.__first
    @final
    def _SetFirstNode(self, node) -> None:
        self.__first = node

    def _OnRemoved(self) -> None:
        pass
    
    @final
    def Push(self, value) -> None:
        if self.IsEmpty():
            self.__first = Base._Node(value, None, None)
        
        else:
            self._InitFirstNode(value)
    
    @final
    def Pop(self):
        self.ThrowIfEmpty()
        
        return self.__first.GetValue()
    
    @final
    def Pull(self):
        self.ThrowIfEmpty()

        value = self.__first.GetValue()

        node: Base._Node = self.__first
        self.__first = node._GetNext()
        self._OnRemoved()

        return value
    
    @final
    def Clear(self) -> None:
        self._OnRemoved()

        self.__first = None

class Queue(Base):
    def __init__(self):
        super().__init__()
        
        self.__last: Base._Node|None = None
    
    @final
    def _InitFirstNode(self, value):
        node: Base._Node = Base._Node(value, None)

        if self.HasItems():
            self.__last._SetNext(node)
        
        self.__last = node
    
    @final
    def _OnRemoved(self) -> None:
        if self.IsEmpty():
            self.__last = None

class Stack(Base):
    def __init__(self):
        super().__init__()
    
    @final
    def _InitFirstNode(self, value) -> None:
        self._SetFirstNode(Base._Node(value, self._GetFirst()))