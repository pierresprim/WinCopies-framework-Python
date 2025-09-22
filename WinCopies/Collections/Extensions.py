from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import Collections, IStringable
from WinCopies.Collections.Enumeration import IIterable, IEquatableIterable, IEnumerator, EnumeratorBase
from WinCopies.Typing import IEquatableItem
from WinCopies.Typing.Pairing import IKeyValuePair

class ITuple[T](Collections.ITuple[T], IIterable[T], IStringable):
    def __init__(self):
        super().__init__()
class IEquatableTuple[T: IEquatableItem](ITuple[T], IEquatableIterable[T]):
    def __init__(self):
        super().__init__()
class IArray[T](Collections.IArray[T], ITuple[T]):
    def __init__(self):
        super().__init__()
class IList[T](Collections.IList[T], IArray[T]):
    def __init__(self):
        super().__init__()

class IReadOnlyDictionary[TKey: IEquatableItem, TValue](Collections.IReadOnlyDictionary[TKey, TValue], IIterable[IKeyValuePair[TKey, TValue]], IStringable):
    def __init__(self):
        super().__init__()
class IDictionary[TKey: IEquatableItem, TValue](Collections.IDictionary[TKey, TValue], IReadOnlyDictionary[TKey, TValue]):
    def __init__(self):
        super().__init__()

class IReadOnlySet[T: IEquatableItem](Collections.IReadOnlySet, IIterable[T], IStringable):
    def __init__(self):
        super().__init__()
class ISet[T: IEquatableItem](Collections.ISet[T], IReadOnlySet[T]):
    def __init__(self):
        super().__init__()

class ArrayBase[TItems, TList](Collections.Tuple[TItems], ITuple[TItems]):
    @final
    class Enumerator(EnumeratorBase[TItems]):
        def __init__(self, items: ArrayBase[TItems, TList]):
            super().__init__()

            self.__list: ArrayBase[TItems, TList] = items
            self.__i: int = -1
        
        def _GetListAsArray(self) -> ITuple[TItems]:
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
    
    # Not final to allow customization for the enumerator.
    def TryGetIterator(self) -> IEnumerator[TItems]:
        return ArrayBase[TItems, TList].Enumerator(self)

class Tuple[T](ArrayBase[T, 'Tuple']):
    def __init__(self):
        super().__init__()
class EquatableTuple[T: IEquatableItem](Tuple[T], IEquatableTuple[T]):
    def __init__(self):
        super().__init__()
class Array[T](Collections.Array[T], ArrayBase[T, 'Array'], IArray[T]):
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