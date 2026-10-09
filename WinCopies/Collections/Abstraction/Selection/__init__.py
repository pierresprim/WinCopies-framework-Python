from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Abstract.Selection import ConverterBase as ConverterAbstract, TwoWayConverterBase
from WinCopies.Typing.Delegate import Converter as _Converter

class IConverter[TIn, TOut](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Convert(self, item: TIn) -> TOut:
        ...
class IConverters[TIn, TOut](IConverter[TIn, TOut]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def ConvertBack(self, item: TOut) -> TIn:
        ...

class Converter[TIn, TOut](Abstract, IConverter[TIn, TOut]):
    def __init__(self, converter: _Converter[TIn, TOut]) -> None:
        super().__init__()

        self.__converter: _Converter[TIn, TOut] = converter

    @final
    def Convert(self, item: TIn) -> TOut: return self.__converter(item)
class Converters[TIn, TOut](Converter[TIn, TOut], IConverters[TIn, TOut]):
    def __init__(self, converter: _Converter[TIn, TOut], backConverter: _Converter[TOut, TIn]) -> None:
        super().__init__(converter)

        self.__backConverter: _Converter[TOut, TIn] = backConverter

    @final
    def ConvertBack(self, item: TOut) -> TIn: return self.__backConverter(item)

class ConverterBase[TIn, TOut](ConverterAbstract[TIn, TOut]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetConverter(self) -> _Converter[TIn, TOut]:
        ...
    
    @final
    def _Convert(self, item: TIn) -> TOut: return self._GetConverter()(item)
class TwoWayConverter[TIn, TOut](TwoWayConverterBase[TIn, TOut]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetConverters(self) -> IConverters[TIn, TOut]:
        ...
    
    @final
    def _Convert(self, item: TIn) -> TOut: return self._GetConverters().Convert(item)
    @final
    def _ConvertBack(self, item: TOut) -> TIn: return self._GetConverters().ConvertBack(item)