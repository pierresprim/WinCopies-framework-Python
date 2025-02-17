from __future__ import annotations

import typing
from typing import final, Self

from WinCopies import Collections
from WinCopies.Collections import IArray
from WinCopies.Collections.Enumeration import IIterable, EnumeratorBase

class ArrayBase[TItems, TList: IArray[TItems]](Collections.Array[TItems], IIterable[TItems]):
    @final
    class Enumerator(EnumeratorBase[TItems]):
        def __init__(self, items: TList):
            super().__init__()

            self.__list: TList = items
            self.__i: int = -1
        
        def _GetList(self) -> TList:
            return self.__list
        
        def IsResetSupported(self) -> bool:
            return True
        
        def _MoveNextOverride(self) -> bool:
            if self.__i < self._GetList().GetCount():
                self.__i += 1

                return True
            
            return False
        
        def GetCurrent(self) -> TItems:
            return self._GetList().GetAt(self.__i)
        
        def _ResetOverride(self) -> bool:
            self.__i = -1

            return True
    
    def __init__(self):
        super().__init__()
    
    @final
    def TryGetIterator(self) -> Enumerator[TItems]:
        return ArrayBase.Enumerator(self)

class Array[T](ArrayBase[T, Self]):
    def __init__(self):
        super().__init__()

class List[T](Collections.List[T], ArrayBase[T, Self]):
    def __init__(self):
        super().__init__()