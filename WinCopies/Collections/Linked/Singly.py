from abc import abstractmethod
from typing import _T, final

from .Singly import Base
from WinCopies.Collections import Collection

class IList(Collection[_T]):
    def __init__(self):
        pass

    @abstractmethod
    def Push(self, value: _T) -> None:
        pass
    
    @abstractmethod
    def TryPop(self) -> tuple[bool, _T|None]:
        pass
    @abstractmethod
    def Pop(self) -> _T:
        pass
    
    @abstractmethod
    def TryPull(self) -> tuple[bool, _T|None]:
        pass
    @abstractmethod
    def Pull(self) -> _T:
        pass
    
    @abstractmethod
    def Clear(self) -> None:
        pass

class Base(IList[_T]):
    class _Node:
        def __init__(self, value: _T, next):
            self.__value: _T = value
            self.__next = next
        
        @final
        def GetValue(self) -> _T:
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
    def _InitNode(self, value: _T) -> None:
        pass
    def _OnNodeInitialized(self) -> None:
        pass
    
    @final
    def _GetFirst(self) -> Base._Node:
        return self.__first
    @final
    def _SetFirst(self, node: Base._Node) -> None:
        self.__first = node

    def _OnRemoved(self) -> None:
        pass
    
    @final
    def _GetFirstValue(self) -> _T:
        return self.__first.GetValue()
    @final
    def _RemoveFirstValue(self) -> _T:
        node: Base._Node = self.__first
        value: _T = node.GetValue()

        self.__first = node._GetNext()
        self._OnRemoved()

        return value
    
    @final
    def Push(self, value: _T) -> None:
        if self.IsEmpty():
            self.__first = Base._Node(value, None, None)
            self._OnInitialNodeAdded()
        
        else:
            self._InitNode(value)
            self._OnNodeInitialized()
    
    @final
    def TryPop(self) -> tuple[bool, _T|None]:
        return (False, None) if self.IsEmpty() else (True, self._GetFirstValue())
    @final
    def Pop(self) -> _T:
        self.ThrowIfEmpty()
        
        return self._GetFirstValue()
    
    @final
    def TryPull(self) -> tuple[bool, _T|None]:
        return (False, None) if self.IsEmpty() else (True, self._RemoveFirstValue())
    @final
    def Pull(self) -> _T:
        self.ThrowIfEmpty()

        return self._RemoveFirstValue()
    
    @final
    def _Weld(self, last: _Node) -> None:
        last._SetNext(self.__first)
    
    @final
    def Clear(self) -> None:
        self._OnRemoved()

        self.__first = None

class Queue(Base[_T]):
    def __init__(self):
        super().__init__()
        
        self.__last: Base._Node|None = None
    
    @final
    def _GetLast(self) -> Base._Node:
        return self.__last
    @final
    def _SetLast(self, last: Base._Node) -> None:
        self.__last = last
    
    @final
    def _InitNode(self, value):
        node: Base._Node = Base._Node(value, None)

        self.__last._SetNext(node)        
        self.__last = node
    
    def _OnRemovedNode(self) -> None:
        pass
    
    def _OnRemoved(self) -> None:
        if self.IsEmpty():
            self.__last = None
        else:
            self._OnRemovedNode()
class Stack(Base[_T]):
    def __init__(self):
        super().__init__()
    
    @final
    def _InitNode(self, value) -> None:
        self._SetFirst(Base._Node(value, self._GetFirst()))

class IBuffer(IList[_T]):
    def __init__(self):
        pass

    @abstractmethod
    def _GetFirst(self) -> Base._Node:
        pass

    @final
    def _IsFirstAndLast(self) -> tuple[bool, Base._Node, Base._Node]:
        first: Base._Node = self._GetFirst()
        next: Base._Node = first._GetNext()

        return (first is next, first, next)

    @abstractmethod
    def _SetFirst(node: Base._Node) -> None:
        pass
    @abstractmethod
    def _SetLast(node: Base._Node) -> None:
        pass

    @abstractmethod
    def _Weld(self, last: Base._Node) -> None:
        pass
    
    @abstractmethod
    def _GetLast(self) -> Base._Node:
        pass
    
    def _WeldLast(self) -> None:
        self._Weld(self._GetLast())

    def _OnNodeInitialized(self) -> None:
        self._WeldLast()
    
    @final
    def Move(self) -> bool:
        result: tuple[bool, Base._Node, Base._Node] = self._IsFirstAndLast()
        
        if result[0]:
            return False
        
        self._SetFirst(result[2])
        self._SetLast(result[1])
        
        return True
class BufferedQueue(Queue[_T], IBuffer[_T]):
    def __init__(self):
        super().__init__()
    
    def _OnInitialNodeAdded(self) -> None:
        self._WeldLast()
    
    def _OnRemovedNode(self) -> None:
        self._WeldLast()
class BufferedStack(Stack[_T], IBuffer[_T]):
    def __init__(self):
        super().__init__()
        self.__last: Base._Node|None = None
    
    @final
    def _GetLast(self) -> Base._Node:
        return self.__last
    
    def _OnInitialNodeAdded(self) -> None:
        self.__last = self._GetFirst()
        self._WeldLast()
        
    def _OnRemoved(self) -> None:
        if self.IsEmpty():
            self.__last = None
        else:
            self._WeldLast()