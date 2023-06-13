from typing import final #, protected
from math import log10

from WinCopies.Collections import Enumeration

@final
class _Enumerator(Enumeration.Enumerator):
    def __init__(self, sequenceGenerator):
        self.__sequenceGenerator = sequenceGenerator
        
        count: int = self.__sequenceGenerator.GetCount()
        
        if count > 0:
            self.__i = self.__sequenceGenerator.GetStart() - 1
            self.__count = self.__i + count
        
        else:
            self.__i = 0
            self.__count = 0
        
        self.__current: int|None = None
        self.__currentProvider: callable|None = None
        
        super().__init__()
    
    def OnStarting(self) -> bool:
        def setCurrent() -> None:
            currentProvider: callable

            (self.__current, currentProvider) = self.__sequenceGenerator._GetData().RenderFirst(self.__i, int(log10(self.__count)) - int(log10(self.__i)))
            
            def setCurrent() -> None:
                self.__current = currentProvider(self.__i)
                
            self.__currentProvider = setCurrent
        
        self.__currentProvider = setCurrent
        
        return True
    
    #@protected    
    def MoveNextOverride(self) -> bool:
        if self.__i < self.__count:
            self.__i += 1
            self.__currentProvider()
            return True
        
        self.__current = None
        self.__currentProvider = None
        return False
    
    def IsResetSupported(self) -> bool:
        return True
    #@protected
    def ResetOverride(self) -> bool:
        self.__i = 0
        return True
    
    def GetCurrent(self):
        return self.__current