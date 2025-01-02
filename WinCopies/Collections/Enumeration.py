# -*- coding: utf-8 -*-
"""
Created on Sun Feb  6 20:37:51 2022

@author: Pierre Sprimont
"""

from abc import ABC, abstractmethod
from typing import final, Callable

from WinCopies import Delegates

class IEnumerator(ABC):
    @abstractmethod
    def GetCurrent(self):
        pass
    @abstractmethod
    def MoveNext(self) -> bool:
        pass
    @abstractmethod
    def Reset(self) -> bool:
        pass
    @abstractmethod
    def IsResetSupported(self) -> bool:
        pass
    @abstractmethod
    def HasProcessedItems(self) -> bool:
        pass
    
class EnumeratorBase(IEnumerator):
    def __init__(self):
        self.__moveNext: callable = self.__GetMoveNext()
        self.__hasProcessedItems: bool = False
    @final
    def __GetMoveNext(self) -> Callable[[], bool]:
        def moveNext() -> bool:
            def setCompletedMoveNext() -> None:
                self.__moveNext = Delegates.BoolFalse
            
            def moveNext() -> bool:
                if self._MoveNextOverride():
                    return True
                
                self._OnCompleted()

                setCompletedMoveNext()

                return False
            
            if self._OnStarting() and self._MoveNextOverride():
                self.__moveNext = moveNext

                self.__hasProcessedItems = True

                return True
            
            setCompletedMoveNext()

            return False
        
        return moveNext
    #@protected
    @abstractmethod
    def _MoveNextOverride(self) -> bool:
        pass
    #@protected
    @abstractmethod
    def _ResetOverride(self) -> bool:
        pass
    @abstractmethod
    def GetCurrent(self):
        pass
    @abstractmethod
    def IsResetSupported(self) -> bool:
        pass
    #@protected
    def _OnStarting(self) -> bool:
        return True
    #@protected
    def _OnCompleted(self) -> None:
        pass
    @final
    def MoveNext(self) -> bool:
        return self.__moveNext()
    
    @final
    def Reset(self) -> bool:
        if self.IsResetSupported():
            self._ResetOverride()
            self.__moveNext = self.__GetMoveNext()
            self.__hasProcessedItems = False

            return True
        
        return False
    
    @final
    def HasProcessedItems(self) -> bool:
        return self.__hasProcessedItems
    
    @final
    def __next__(self):
        if self.__moveNext():
            return self.GetCurrent()
        
        else:
            raise StopIteration

class Enumerator(EnumeratorBase):
    def __init__(self):
        super().__init__()
        self.__current: object|None = None
    
    def _ResetOverride(self) -> bool:
        self.__current = None
    
    def GetCurrent(self):
        return self.__current
    
    @abstractmethod
    def _SetCurrent(self, current):
        self.__current = current

class Iterator(Enumerator):
    def __init__(self, iterator):
        super().__init__()
        self.__iterator = iterator
    
    @final
    def _GetIterator(self):
        return self.__iterator
    
    def IsResetSupported(self) -> bool:
        return False
    
    def _MoveNextOverride(self) -> bool:
        try:
            self._SetCurrent(self.__next__())
            
            return True
        except StopIteration:
            return False

class Iterable:
    def __init__(self, iterable):
        self.__iterable = iterable
    
    @final
    def _GetIterable(self):
        return self.__iterable
    
    @final
    def __iter__(self):
        return Iterator(self.__iterable.__iter__())