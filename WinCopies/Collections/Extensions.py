from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import Collections
from WinCopies.Collections.Enumeration import IIterable, IEnumerator, EnumeratorBase
from WinCopies.Typing.Pairing import IKeyValuePair

class IArray[T](Collections.IArray[T], IIterable[T]):
    def __init__(self):
        super().__init__()
class IList[T](Collections.IList[T], IArray[T]):
    def __init__(self):
        super().__init__()
class IDictionary[TKey, TValue](Collections.IDictionary[TKey, TValue], IIterable[IKeyValuePair[TKey, TValue]]):
    def __init__(self):
        super().__init__()

class ArrayBase[TItems, TList](Collections.Array[TItems], IArray[TItems]):
    @final
    class Enumerator(EnumeratorBase[TItems]):
        def __init__(self, items: ArrayBase[TItems, TList]):
            super().__init__()

            self.__list: ArrayBase[TItems, TList] = items
            self.__i: int = -1
        
        def _GetListAsArray(self) -> IArray[TItems]:
            return self.__list
        def _GetList(self) -> TList:
            return self.__list._AsList()
        
        def IsResetSupported(self) -> bool:
            return True
        
        def _MoveNextOverride(self) -> bool:
            self.__i += 1
            
            return self.__i < self._GetListAsArray().GetCount()
        
        def GetCurrent(self) -> TItems:
            return self._GetListAsArray().GetAt(self.__i)
        
        def _OnStopped(self) -> None:
            pass
        
        def _ResetOverride(self) -> bool:
            self.__i = -1

            return True
    
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _AsList(self) -> TList:
        pass
    
    # Not final to allow customization of the enumerator.
    def TryGetIterator(self) -> IEnumerator[TItems]:
        return ArrayBase[TItems, TList].Enumerator(self)

class Array[T](ArrayBase[T, 'Array']):
    def __init__(self):
        super().__init__()
    
    @final
    def _AsList(self) -> Array[T]:
        return self

class List[T](Collections.List[T], ArrayBase[T, 'List'], IList[T]):
    def __init__(self):
        super().__init__()
    
    @final
    def _AsList(self) -> List[T]:
        return self