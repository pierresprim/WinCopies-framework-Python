
from abc import abstractmethod
from typing import final

from WinCopies.Collections.Enumeration.Core import EnumeratorBase
from WinCopies.Typing.Delegate import Function

class DelegateEnumerator[T](EnumeratorBase[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__moveNext: Function[bool]|None = None
    
    @abstractmethod
    def _OnMoveNext(self) -> Function[bool]|None:
        ...
    
    def _OnStarting(self) -> bool:
        def moveNext() -> bool:
            func: Function[bool]|None = self._OnMoveNext()

            if func is None: return False
            
            self.__moveNext = func

            return func()

        if super()._OnStarting():
            self.__moveNext = moveNext

            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        return False if self.__moveNext is None else self.__moveNext()
    
    def _OnEnded(self) -> None:
        self.__moveNext = None

        super()._OnEnded()

class IncrementalEnumerator[T](EnumeratorBase[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__i: int = self.__GetResetIndex()
    
    @final
    def __GetResetIndex(self) -> int:
        return -1
    @final
    def __Reset(self) -> None:
        self.__i = self.__GetResetIndex()
    
    @final
    def _GetValue(self) -> int:
        return self.__i
    @final
    def _SetValue(self, value: int) -> None:
        self.__i = value
    
    @abstractmethod
    def _GetMaxValue(self) -> int:
        ...
    
    def IsResetSupported(self) -> bool: return True
    
    def _MoveNextOverride(self) -> bool:
        i: int = self.__i

        i += 1

        if i < self._GetMaxValue():
            self._SetValue(i)

            return True
        
        self.__Reset()

        return False
    
    def _OnAborted(self) -> None: self.__Reset()
    
    def _ResetOverride(self) -> bool:
        self.__Reset()

        return True