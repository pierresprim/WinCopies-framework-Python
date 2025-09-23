from collections.abc import Iterable
from typing import final

from WinCopies.Collections.Abstract import TwoWayConverterBase
from WinCopies.Collections.Abstract.Enumeration import IterableBase
from WinCopies.Collections.Enumeration import IEnumerator
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Linked import Singly
from WinCopies.Collections.Linked.Singly import IIterableList, ICountableList, ICountableIterableList

from WinCopies.Typing import GenericConstraint, IGenericConstraintImplementation, INullable

class SinglyLinkedListBase[TIn, TOut, TList](TwoWayConverterBase[TIn, TOut], Singly.IList[TOut], GenericConstraint[TList, Singly.IList[TIn]]):
    def __init__(self, items: TList):
        super().__init__()

        self.__items: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__items
    
    @final
    def Push(self, value: TOut) -> None:
        return self._GetInnerContainer().Push(self._ConvertBack(value))
    
    @final
    def PushItems(self, items: Iterable[TOut]) -> None:
        self._GetInnerContainer().PushItems(Select(items, self._ConvertBack))
    @final
    def TryPushItems(self, items: Iterable[TOut]|None) -> bool:
        if items is None:
            return False
        
        self.PushItems(items)

        return True
    
    @final
    def TryPeek(self) -> INullable[TOut]:
        return self._GetInnerContainer().TryPeek().TryConvertToNullable(self._Convert)
    
    @final
    def TryPop(self) -> INullable[TOut]:
        return self._GetInnerContainer().TryPop().TryConvertToNullable(self._Convert)
    
    @final
    def Clear(self) -> None:
        return self._GetInnerContainer().Clear()

class SinglyLinkedList[TIn, TOut](SinglyLinkedListBase[TIn, TOut, Singly.IList[TIn]], Singly.IList[TOut], IGenericConstraintImplementation[Singly.IList[TIn]]):
    def __init__(self, items: Singly.IList[TIn]):
        super().__init__(items)

class IterableSinglyLinkedList[TIn, TOut](SinglyLinkedListBase[TIn, TOut, IIterableList[TIn]], IterableBase[TIn, TOut], IIterableList[TOut], IGenericConstraintImplementation[IIterableList[TIn]]):
    def __init__(self, items: IIterableList[TIn]):
        super().__init__(items)
    
    @final
    def _TryGetEnumerator(self) -> IEnumerator[TIn]|None:
        return self._GetContainer().TryGetEnumerator()
class CountableSinglyLinkedList[TIn, TOut](SinglyLinkedListBase[TIn, TOut, ICountableList[TIn]], ICountableList[TOut], IGenericConstraintImplementation[ICountableList[TIn]]):
    def __init__(self, items: ICountableList[TIn]):
        super().__init__(items)
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()

class CountableIterableSinglyLinkedList[TIn, TOut](SinglyLinkedListBase[TIn, TOut, ICountableIterableList[TIn]], IterableBase[TIn, TOut], ICountableIterableList[TOut], IGenericConstraintImplementation[ICountableIterableList[TIn]]):
    def __init__(self, items: ICountableIterableList[TIn]):
        super().__init__(items)
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()
    
    @final
    def _TryGetEnumerator(self) -> IEnumerator[TIn]|None:
        return self._GetContainer().TryGetEnumerator()