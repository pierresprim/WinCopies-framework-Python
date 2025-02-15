from __future__ import annotations

import typing
from typing import final

from WinCopies import Collections
from WinCopies.Collections.Enumeration import IIterable, IEnumerator, EnumeratorBase

class List[T](Collections.List[T], IIterable[T]):
    @final
    class Enumerator(EnumeratorBase[T]):
        def __init__(self, items: List[T]):
            super().__init__()

            self.__list: List[T] = items
            self.__i: int = -1
        
        def _GetList(self) -> List[T]:
            return self.__list
        
        def IsResetSupported(self) -> bool:
            return True
        
        def _MoveNextOverride(self) -> bool:
            if self.__i < self._GetList().GetCount():
                self.__i += 1

                return True
            
            return False
        
        def GetCurrent(self) -> T:
            return self._GetList().GetAt(self.__i)
        
        def _ResetOverride(self) -> bool:
            self.__i = -1

            return True
    
    def __init__(self):
        super().__init__()
    
    @final
    def TryGetIterator(self) -> IEnumerator[T]:
        return List.Enumerator(self)