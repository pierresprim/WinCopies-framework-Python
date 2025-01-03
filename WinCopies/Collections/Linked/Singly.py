from abc import abstractmethod
from typing import final

from WinCopies.Collections import Collection
from WinCopies.Typing.Pairing import DualNullableValueBool

class Base[T](Collection):
    @final
    class _Node[T]:
        def __init__(self, value: T, next):
            self.__value: T = value
            self.__next: Base._Node[T] = next
        
        @final
        def GetValue(self) -> T:
            return self.__value
        
        @final
        def _GetNext(self):
            return self.__next
        @final
        def _SetNext(self, next):
            self.__next = next
    
    def __init__(self):
        super().__init__()
        self.__first: Base._Node[T]|None = None

    @final
    def IsEmpty(self) -> bool:
        return self.__first is None
    @final
    def HasItems(self) -> bool:
        return super().HasItems(self)
    
    @abstractmethod
    def _InitFirstNode(self, value: T) -> None:
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
    def Push(self, value: T) -> None:
        if self.IsEmpty():
            self.__first = Base._Node(value, None)
        
        else:
            self._InitFirstNode(value)
    
    @final
    def TryPop(self) -> DualNullableValueBool[T]:
        return DualNullableValueBool[T](None, False) if self.IsEmpty() else DualNullableValueBool[T](self.__first.GetValue(), True)
    
    @final
    def Pull(self) -> DualNullableValueBool[T]:
        if self.IsEmpty():
            return DualNullableValueBool[T](None, False)
        
        value: T = self.__first.GetValue()

        node: Base._Node = self.__first
        self.__first = node._GetNext()
        self._OnRemoved()

        return value
    
    @final
    def Clear(self) -> None:
        self._OnRemoved()

        self.__first = None

class Queue[T](Base):
    def __init__(self):
        super().__init__()
        
        self.__last: Base._Node[T]|None = None
    
    @final
    def _InitFirstNode(self, value: T):
        node = Base._Node[T](value, None)

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