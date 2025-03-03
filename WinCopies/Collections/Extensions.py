from __future__ import annotations

from typing import final, Self

from WinCopies import Collections
from WinCopies.Collections.Enumeration import IIterable, IEnumerator, EnumeratorBase
from WinCopies.Typing.Pairing import IKeyValuePair

class IArray[T](Collections.IArray[T], IIterable[T]):
    def __init__(self):
        super().__init__()
class IList[T](Collections.IList[T], IArray[T]):
    def __init__(self):
        super().__init__()

class ArrayBase[TItems, TList: IArray[TItems]](Collections.Array[TItems], IArray[TItems]):
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
            self.__i += 1
            
            return self.__i < self._GetList().GetCount()
        
        def GetCurrent(self) -> TItems:
            return self._GetList().GetAt(self.__i)
        
        def _OnStopped(self) -> None:
            pass
        
        def _ResetOverride(self) -> bool:
            self.__i = -1

            return True
    
    def __init__(self):
        super().__init__()
    
    @final
    def TryGetIterator(self) -> IEnumerator[TItems]:
        return ArrayBase.Enumerator(self)

class Array[T](ArrayBase[T, Self]):
    def __init__(self):
        super().__init__()

class List[T](Collections.List[T], ArrayBase[T, Self], IList[T]):
    def __init__(self):
        super().__init__()

class IDictionary[TKey, TValue](Collections.IDictionary[TKey, TValue], IIterable[IKeyValuePair[TKey, TValue]]):
    def __init__(self):
        super().__init__()