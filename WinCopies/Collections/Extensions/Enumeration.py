from WinCopies.Collections import Enumeration
from WinCopies.Collections.Extensions import ITuple
from WinCopies.Typing.Generic import GenericConstraint, IGenericConstraintImplementation

class TupleEnumeratorBase[TItem, TList](Enumeration.EnumeratorBase[TItem], GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self, items: TList) -> None:
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
    
    def GetCurrent(self) -> TItem:
        return self._GetInnerContainer().GetAt(self.__i)
    
    def _OnStopped(self) -> None:
        pass
    
    def _ResetOverride(self) -> bool:
        self.__i = -1

        return True
class TupleEnumerator[T](TupleEnumeratorBase[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None:
        super().__init__(items)