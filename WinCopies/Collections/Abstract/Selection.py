from abc import abstractmethod
from typing import final

from WinCopies import IInterface, IStringable, Abstract
from WinCopies.Typing.Generic import GenericConstraint

class ConverterBase[TIn, TOut](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _Convert(self, item: TIn) -> TOut:
        ...
class TwoWayConverterBase[TIn, TOut](ConverterBase[TIn, TOut]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _ConvertBack(self, item: TOut) -> TIn:
        ...

class SelectorBase[TIn, TOut](ConverterBase[TIn, TOut], IStringable):
    def __init__(self) -> None: super().__init__()

class StringableConverter[TIn, TOut, TSequence: IStringable, TInterface](Abstract, SelectorBase[TIn, TOut], GenericConstraint[TSequence, TInterface]):
    def __init__(self) -> None: super().__init__()
    
    def ToString(self) -> str: return self._GetContainer().ToString()
class StringableTwoWayConverter[TIn, TOut, TSequence: IStringable, TInterface](StringableConverter[TIn, TOut, TSequence, TInterface], TwoWayConverterBase[TIn, TOut]):
    def __init__(self) -> None: super().__init__()

class Converter[TIn, TOut, TSequence: IStringable, TInterface](StringableConverter[TIn, TOut, TSequence, TInterface]):
    def __init__(self, items: TSequence) -> None:
        super().__init__()

        self.__items: TSequence = items
    
    @final
    def _GetContainer(self) -> TSequence: return self.__items
class TwoWayConverter[TIn, TOut, TSequence: IStringable, TInterface](Converter[TIn, TOut, TSequence, TInterface], StringableTwoWayConverter[TIn, TOut, TSequence, TInterface]):
    def __init__(self, items: TSequence) -> None: super().__init__(items)

class ISelector[TIn, TOut, TSequence: IStringable](TwoWayConverterBase[TIn, TOut], SelectorBase[TIn, TOut]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetItems(self) -> TSequence:
        ...
    
    def ToString(self) -> str: return self._GetItems().ToString()
class Selector[TIn, TOut, TSequence: IStringable](ISelector[TIn, TOut, TSequence]):
    def __init__(self, items: TSequence) -> None:
        super().__init__()

        self.__items: TSequence = items
    
    @final
    def _GetItems(self) -> TSequence: return self.__items