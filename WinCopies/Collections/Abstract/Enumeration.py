from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import Abstract
from WinCopies.Collections import Enumeration
from WinCopies.Collections.Abstract import ConverterBase
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator
from WinCopies.Typing import INullable, GetNullable, GetNullValue

class Enumerator[TIn, TOut](Enumeration.Selector[TIn, TOut], ConverterBase[TIn, TOut]):
    def __init__(self, enumerator: IEnumerator[TIn]) -> None:
        super().__init__(enumerator)

        self.__current: INullable[TOut] = GetNullValue()
    
    def _OnEnded(self) -> None:
        self.__current = GetNullValue()
        
        super()._OnEnded()
    
    def _MoveNextOverride(self) -> bool:
        if super()._MoveNextOverride():
            self.__current = GetNullable(self._Convert(self._GetContainer().GetCurrent()))

            return True
        
        return False
    
    def _GetCurrent(self) -> TOut:
        return self.__current.GetValue()

@final
class _Enumerator[TIn, TOut](Enumerator[TIn, TOut]):
    def __init__(self, enumerable: EnumerableBase[TIn, TOut], enumerator: IEnumerator[TIn]) -> None:
        super().__init__(enumerator)

        self.__enumerable: EnumerableBase[TIn, TOut] = enumerable
    
    def _Convert(self, item: TIn) -> TOut:
        return self.__enumerable._Convert(item)

class EnumerableBase[TIn, TOut](Abstract, ConverterBase[TIn, TOut], IEnumerable[TOut]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _TryGetEnumerator(self) -> IEnumerator[TIn]|None:
        pass
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TOut]|None:
        result: IEnumerator[TIn]|None = self._TryGetEnumerator()

        return None if result is None else _Enumerator[TIn, TOut](self, result)
class Enumerable[TIn, TOut](EnumerableBase[TIn, TOut]):
    def __init__(self, enumerable: IEnumerable[TIn]) -> None:
        super().__init__()

        self.__enumerable: IEnumerable[TIn] = enumerable
    
    @final
    def _TryGetEnumerator(self) -> IEnumerator[TIn]|None:
        return self.__enumerable.TryGetEnumerator()