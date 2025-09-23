from abc import abstractmethod
from typing import final

from WinCopies import IInterface, IStringable
from WinCopies.Typing import GenericConstraint

class ConverterBase[TIn, TOut](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _Convert(self, item: TIn) -> TOut:
        pass
class TwoWayConverterBase[TIn, TOut](ConverterBase[TIn, TOut]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _ConvertBack(self, item: TOut) -> TIn:
        pass

class SelectorBase[TIn, TOut](ConverterBase[TIn, TOut], IStringable):
    def __init__(self):
        super().__init__()

class Converter[TIn, TOut, TSequence: IStringable, TInterface](SelectorBase[TIn, TOut], GenericConstraint[TSequence, TInterface]):
    def __init__(self, items: TSequence):
        super().__init__()

        self.__items: TSequence = items
    
    @final
    def _GetContainer(self) -> TSequence:
        return self.__items
    
    def ToString(self) -> str:
        return self._GetContainer().ToString()

class Selector[TIn, TOut, TSequence: IStringable](TwoWayConverterBase[TIn, TOut], SelectorBase[TIn, TOut]):
    def __init__(self, items: TSequence):
        super().__init__()

        self.__items: TSequence = items
    
    @final
    def _GetItems(self) -> TSequence:
        return self.__items
    
    def ToString(self) -> str:
        return self._GetItems().ToString()