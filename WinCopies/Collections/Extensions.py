from __future__ import annotations

from abc import abstractmethod

from WinCopies import Collections, IStringable
from WinCopies.Collections import Enumeration
from WinCopies.Collections.Enumeration import ICountableIterable, IEquatableIterable, IEnumerator
from WinCopies.Typing import IEquatableItem, GenericConstraint, IGenericConstraintImplementation
from WinCopies.Typing.Pairing import IKeyValuePair

class ITuple[T](Collections.ITuple[T], ICountableIterable[T], IStringable):
    def __init__(self):
        super().__init__()
class IEquatableTuple[T: IEquatableItem](ITuple[T], IEquatableIterable[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def SliceAt(self, key: slice[int, int, int]) -> IEquatableTuple[T]:
        pass
class IArray[T](Collections.IArray[T], ITuple[T]):
    def __init__(self):
        super().__init__()
class IList[T](Collections.IList[T], IArray[T]):
    def __init__(self):
        super().__init__()

class IReadOnlyDictionary[TKey: IEquatableItem, TValue](Collections.IReadOnlyDictionary[TKey, TValue], ICountableIterable[IKeyValuePair[TKey, TValue]], IStringable):
    def __init__(self):
        super().__init__()
class IDictionary[TKey: IEquatableItem, TValue](Collections.IDictionary[TKey, TValue], IReadOnlyDictionary[TKey, TValue]):
    def __init__(self):
        super().__init__()

class IReadOnlySet[T: IEquatableItem](Collections.IReadOnlySet, ICountableIterable[T], IStringable):
    def __init__(self):
        super().__init__()
class ISet[T: IEquatableItem](Collections.ISet[T], IReadOnlySet[T]):
    def __init__(self):
        super().__init__()

class ArrayBase[T](Collections.Tuple[T], ITuple[T]):
    class EnumeratorBase[TList](Enumeration.EnumeratorBase[T], GenericConstraint[TList, ITuple[T]]):
        def __init__(self, items: TList):
            super().__init__()

            self.__list: TList = items
            self.__i: int = -1
        
        def _GetContainer(self) -> TList:
            return self.__list
        
        def IsResetSupported(self) -> bool:
            return True
        
        def _MoveNextOverride(self) -> bool:
            self.__i += 1
            
            return self.__i < self._GetInnerContainer().GetCount()
        
        def GetCurrent(self) -> T:
            return self._GetInnerContainer().GetAt(self.__i)
        
        def _OnStopped(self) -> None:
            pass
        
        def _ResetOverride(self) -> bool:
            self.__i = -1

            return True
    class Enumerator(EnumeratorBase[ITuple[T], T], IGenericConstraintImplementation[ITuple[T]]):
        def __init__(self, items: ITuple[T]):
            super().__init__(items)
    
    def __init__(self):
        super().__init__()
    
    # Not final to allow customization for the enumerator.
    def TryGetIterator(self) -> IEnumerator[T]:
        return ArrayBase[T].Enumerator(self)

class Tuple[T](ArrayBase[T]):
    def __init__(self):
        super().__init__()
class EquatableTuple[T: IEquatableItem](Tuple[T], IEquatableTuple[T]):
    def __init__(self):
        super().__init__()
class Array[T](Collections.Array[T], ArrayBase[T], IArray[T]):
    def __init__(self):
        super().__init__()
class List[T](Collections.List[T], ArrayBase[T], IList[T]):
    def __init__(self):
        super().__init__()