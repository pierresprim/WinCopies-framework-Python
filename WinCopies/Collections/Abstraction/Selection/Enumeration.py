from typing import final

from WinCopies.Collections.Abstract.Enumeration import Enumerable as _Enumerable, ResumableEnumerable as _ResumableEnumerable, CountableEnumerable as _CountableEnumerable, ReversableCountableEnumerable as _ReversableCountableEnumerable
from WinCopies.Collections.Enumeration.Core import IEnumerable, ICountableEnumerable, IReversableCountableEnumerable, Enumerable as _EnumerableBase
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerable
from WinCopies.Typing.Delegate import Converter

class Enumerable[TIn, TOut](_Enumerable[TIn, TOut], _EnumerableBase[TOut]):
    def __init__(self, enumerable: IEnumerable[TIn], selector: Converter[TIn, TOut]) -> None:
        super().__init__(enumerable)

        self.__selector: Converter[TIn, TOut] = selector

    @final
    def _Convert(self, item: TIn) -> TOut: return self.__selector(item)
class ResumableEnumerable[TIn, TOut](_ResumableEnumerable[TIn, TOut], _EnumerableBase[TOut]):
    def __init__(self, enumerable: IResumableEnumerable[TIn], selector: Converter[TIn, TOut]) -> None:
        super().__init__(enumerable)

        self.__selector: Converter[TIn, TOut] = selector

    @final
    def _Convert(self, item: TIn) -> TOut: return self.__selector(item)

class CountableEnumerable[TIn, TOut](_CountableEnumerable[TIn, TOut], _EnumerableBase[TOut]):
    def __init__(self, enumerable: ICountableEnumerable[TIn], selector: Converter[TIn, TOut]) -> None:
        super().__init__(enumerable)

        self.__selector: Converter[TIn, TOut] = selector

    @final
    def _Convert(self, item: TIn) -> TOut: return self.__selector(item)
class ReversableCountableEnumerable[TIn, TOut](_ReversableCountableEnumerable[TIn, TOut], _EnumerableBase[TOut]):
    def __init__(self, enumerable: IReversableCountableEnumerable[TIn], selector: Converter[TIn, TOut]) -> None:
        super().__init__(enumerable)

        self.__selector: Converter[TIn, TOut] = selector

    @final
    def _Convert(self, item: TIn) -> TOut: return self.__selector(item)
    @final
    def _ConvertFromSource(self, items: IEnumerable[TIn]) -> IEnumerable[TOut]:
        return CreateEnumerable(items, self.__selector)

def CreateEnumerable[TIn, TOut](enumerable: IEnumerable[TIn], selector: Converter[TIn, TOut]) -> IEnumerable[TOut]:
    return Enumerable[TIn, TOut](enumerable, selector)
def CreateResumableEnumerable[TIn, TOut](enumerable: IResumableEnumerable[TIn], selector: Converter[TIn, TOut]) -> IResumableEnumerable[TOut]:
    return ResumableEnumerable[TIn, TOut](enumerable, selector)

def CreateCountableEnumerable[TIn, TOut](enumerable: ICountableEnumerable[TIn], selector: Converter[TIn, TOut]) -> ICountableEnumerable[TOut]:
    return CountableEnumerable[TIn, TOut](enumerable, selector)
def CreateReversableCountableEnumerable[TIn, TOut](enumerable: IReversableCountableEnumerable[TIn], selector: Converter[TIn, TOut]) -> IReversableCountableEnumerable[TOut]:
    return ReversableCountableEnumerable[TIn, TOut](enumerable, selector)