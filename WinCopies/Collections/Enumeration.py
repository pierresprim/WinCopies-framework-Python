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
        self._enumerationCompleted: bool = False
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
    @final
    def MoveNext(self) -> bool:
        if self._enumerationCompleted:
            return False
        
        if self.MoveNextOverride():
            return True
        
        self._enumerationCompleted = True
        return False
    
    @final
    def Reset(self) -> bool:
        if self.IsResetSupported():
            self.ResetOverride()
            self._enumerationCompleted = False
            return True
        
        return False
    
    @final
    def __next__(self):
        if self.MoveNext():
            return self.GetCurrent()
        else:
            raise StopIteration