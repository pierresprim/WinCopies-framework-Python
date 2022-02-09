# -*- coding: utf-8 -*-
"""
Created on Sun Feb  6 20:37:51 2022

@author: Pierre Sprimont
"""

from typing import final, protected

class IEnumerator:
    def GetCurrent(self):
        pass
    def MoveNext(self) -> bool:
        pass
    def Reset(self) -> bool:
        pass
    def IsResetSupported(self) -> bool:
        pass
    
class Enumerator(IEnumerator):
    def __init__(self):
        self._enumerationCompleted : bool = False
    def GetCurrent(self):
        pass
    @protected
    def MoveNextOverride(self) -> bool:
        pass
    @final
    def MoveNext(self) -> bool:
        if self._enumerationCompleted:
            return False
        if self.MoveNextOverride():
            return True
        self._enumerationCompleted = True
        return False
    def IsResetSupported(self) -> bool:
        pass
    @protected
    def ResetOverride(self) -> bool:
        pass
    def Reset(self) -> bool:
        if self.IsResetSupported():
            self.ResetOverride()
            return True
        return False
    def __next__(self):
        if self.MoveNext():
            return self.GetCurrent()
        return StopIteration()