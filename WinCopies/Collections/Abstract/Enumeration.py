from abc import abstractmethod
from typing import final

from WinCopies.Collections import Enumeration
from WinCopies.Collections.Abstract import ConverterBase
from WinCopies.Collections.Enumeration import IIterable, IEnumerator
from WinCopies.Delegates import FuncNone
from WinCopies.Typing.Delegate import Function, ValueFunction

class Enumerator[TIn, TOut](Enumeration.Selector[TIn, TOut], ConverterBase[TIn, TOut]):
    def __init__(self, enumerator: IEnumerator[TIn]):
        super().__init__(enumerator)

        self.__getCurrent: Function[TOut|None] = FuncNone
    
    @final
    def __GetCurrent(self) -> Function[TOut|None]:
        current: TIn|None = self._GetEnumerator().GetCurrent()

        return FuncNone if current is None else ValueFunction(self._Convert(current))
    
    def _MoveNextOverride(self) -> bool:
        if super()._MoveNextOverride() and self.__getCurrent is FuncNone:
            self.__getCurrent = self.__GetCurrent()

            return True
        
        self.__getCurrent = FuncNone

        return False
    
    def GetCurrent(self) -> TOut|None:
        return self.__getCurrent()

class IterableBase[TIn, TOut](ConverterBase[TIn, TOut], IIterable[TOut]):
    @final
    class __Enumerator(Enumerator[TIn, TOut]):
        def __init__(self, iterable: IterableBase[TIn, TOut], enumerator: IEnumerator[TIn]):
            super().__init__(enumerator)

            self.__iterable: IterableBase[TIn, TOut] = iterable
        
        def _Convert(self, item: TIn) -> TOut:
            return self.__iterable._Convert(item)
    
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _TryGetEnumerator(self) -> IEnumerator[TIn]|None:
        pass
    
    @final
    def TryGetIterator(self) -> IEnumerator[TOut]|None:
        result: IEnumerator[TIn]|None = self._TryGetEnumerator()

        return None if result is None else IterableBase[TIn, TOut].__Enumerator(self, result)
class Iterable[TIn, TOut](IterableBase[TIn, TOut]):
    def __init__(self, iterable: IIterable[TIn]):
        super().__init__()

        self.__iterable: IIterable[TIn] = iterable
    
    @final
    def _TryGetEnumerator(self) -> IEnumerator[TIn]|None:
        return self.__iterable.TryGetEnumerator()