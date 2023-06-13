# -*- coding: utf-8 -*-
"""
Created on Sun Feb  6 20:37:51 2022

@author: Pierre Sprimont
"""

from abc import ABC, abstractmethod
from typing import final #, protected

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
    
class Enumerator(IEnumerator):
    def __init__(self):
        self.__moveNext: callable = self.__GetMoveNext()
    @final
    def __GetMoveNext(self) -> callable:
        def moveNext() -> bool:
            def setCompletedMoveNext() -> callable:
                def completedMoveNext() -> bool:
                    return False
                
                self.__moveNext = completedMoveNext
            
            def moveNext() -> bool:
                if self.MoveNextOverride():
                    return True
                
                self.OnCompleted()
                setCompletedMoveNext()
                return False
            
            if self.OnStarting() and self.MoveNextOverride():
                self.__moveNext = moveNext
                return True
            
            setCompletedMoveNext()
            return False
        
        return moveNext
    #@protected
    @abstractmethod
    def MoveNextOverride(self) -> bool:
        pass
    #@protected
    @abstractmethod
    def ResetOverride(self) -> bool:
        pass
    @abstractmethod
    def GetCurrent(self):
        pass
    @abstractmethod
    def IsResetSupported(self) -> bool:
        pass
    #@protected
    def OnStarting(self) -> bool:
        return True
    #@protected
    def OnCompleted(self) -> None:
        pass
    @final
    def MoveNext(self) -> bool:
        return self.__moveNext()
    
    @final
    def Reset(self) -> bool:
        if self.IsResetSupported():
            self.ResetOverride()
            self.__moveNext = self.__GetMoveNext()
            return True
        
        return False
    
    @final
    def __next__(self):
        if self.__moveNext():
            return self.GetCurrent()
        else:
            raise StopIteration