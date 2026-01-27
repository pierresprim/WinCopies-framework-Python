from collections.abc import Iterable
from typing import final

from WinCopies import Abstract
from WinCopies.Collections.Abstract import TwoWayConverterBase
from WinCopies.Collections.Abstract.Enumeration import EnumerableBase
from WinCopies.Collections.Enumeration import IEnumerator
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Linked.Singly import IList, IEnumerableList, ICountableList, ICountableEnumerableList

from WinCopies.Typing import GenericConstraint, IGenericConstraintImplementation, INullable

class SinglyLinkedListBase[TIn, TOut, TList](Abstract, TwoWayConverterBase[TIn, TOut], IList[TOut], GenericConstraint[TList, IList[TIn]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__items: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__items
    
    @final
    def Push(self, value: TOut) -> None:
        self._GetInnerContainer().Push(self._ConvertBack(value))
    
    @final
    def PushItems(self, items: Iterable[TOut]) -> None:
        self._GetInnerContainer().PushItems(Select(items, self._ConvertBack))
    
    @final
    def TryPeek(self) -> INullable[TOut]:
        return self._GetInnerContainer().TryPeek().TryConvertToNullable(self._Convert)
    
    @final
    def TryPop(self) -> INullable[TOut]:
        return self._GetInnerContainer().TryPop().TryConvertToNullable(self._Convert)
    
    @final
    def Clear(self) -> None:
        self._GetInnerContainer().Clear()

class SinglyLinkedList[TIn, TOut](SinglyLinkedListBase[TIn, TOut, IList[TIn]], IList[TOut], IGenericConstraintImplementation[IList[TIn]]):
    def __init__(self, items: IList[TIn]) -> None:
        super().__init__(items)

class EnumerableSinglyLinkedList[TIn, TOut](SinglyLinkedListBase[TIn, TOut, IEnumerableList[TIn]], EnumerableBase[TIn, TOut], IEnumerableList[TOut], IGenericConstraintImplementation[IEnumerableList[TIn]]):
    def __init__(self, items: IEnumerableList[TIn]) -> None:
        super().__init__(items)
    
    @final
    def _TryGetEnumerator(self) -> IEnumerator[TIn]|None:
        return self._GetContainer().TryGetEnumerator()
class CountableSinglyLinkedList[TIn, TOut](SinglyLinkedListBase[TIn, TOut, ICountableList[TIn]], ICountableList[TOut], IGenericConstraintImplementation[ICountableList[TIn]]):
    def __init__(self, items: ICountableList[TIn]) -> None:
        super().__init__(items)
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()

class CountableEnumerableSinglyLinkedList[TIn, TOut](SinglyLinkedListBase[TIn, TOut, ICountableEnumerableList[TIn]], EnumerableBase[TIn, TOut], ICountableEnumerableList[TOut], IGenericConstraintImplementation[ICountableEnumerableList[TIn]]):
    def __init__(self, items: ICountableEnumerableList[TIn]) -> None:
        super().__init__(items)
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()
    
    @final
    def _TryGetEnumerator(self) -> IEnumerator[TIn]|None:
        return self._GetContainer().TryGetEnumerator()