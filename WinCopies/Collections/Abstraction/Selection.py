from __future__ import annotations

from typing import final

from WinCopies.Collections.Abstract import Collection
from WinCopies.Collections.Extensions import ITuple, IEquatableTuple, IArray, IList, ISet, IDictionary
from WinCopies.Typing import IEquatableItem
from WinCopies.Typing.Delegate import Converter

class Tuple[TIn, TOut](Collection.Tuple[TIn, TOut]):
    def __init__(self, items: ITuple[TIn], converter: Converter[TIn, TOut]):
        super().__init__(items)

        self.__converter: Converter[TIn, TOut] = converter
    
    def _Clone(self, items: ITuple[TIn]) -> Tuple[TIn, TOut]:
        return Tuple[TIn, TOut](items, self.__converter)
    
    @final
    def _Convert(self, item: TIn) -> TOut:
        return self.__converter(item)
class EquatableTuple[TIn: IEquatableItem, TOut: IEquatableItem](Collection.EquatableTuple[TIn, TOut]):
    def __init__(self, items: IEquatableTuple[TIn], converter: Converter[TIn, TOut]):
        super().__init__(items)

        self.__converter: Converter[TIn, TOut] = converter
    
    def _Clone(self, items: IEquatableTuple[TIn]) -> EquatableTuple[TIn, TOut]:
        return EquatableTuple[TIn, TOut](items, self.__converter)
    
    @final
    def _Convert(self, item: TIn) -> TOut:
        return self.__converter(item)

class Array[TIn, TOut](Collection.Array[TIn, TOut]):
    def __init__(self, items: IArray[TIn], converter: Converter[TIn, TOut], backConverter: Converter[TOut, TIn]):
        super().__init__(items)

        self.__converter: Converter[TIn, TOut] = converter
        self.__backConverter: Converter[TOut, TIn] = backConverter
    
    def _Clone(self, items: IArray[TIn]) -> Array[TIn, TOut]:
        return Array[TIn, TOut](items, self.__converter, self.__backConverter)
    
    @final
    def _Convert(self, item: TIn) -> TOut:
        return self.__converter(item)
    @final
    def _ConvertBack(self, item: TOut) -> TIn:
        return self.__backConverter(item)

class List[TIn, TOut](Collection.List[TIn, TOut]):
    def __init__(self, items: IList[TIn], converter: Converter[TIn, TOut], backConverter: Converter[TOut, TIn]):
        super().__init__(items)

        self.__converter: Converter[TIn, TOut] = converter
        self.__backConverter: Converter[TOut, TIn] = backConverter
    
    def _Clone(self, items: IList[TIn]) -> List[TIn, TOut]:
        return List[TIn, TOut](items, self.__converter, self.__backConverter)
    
    @final
    def _Convert(self, item: TIn) -> TOut:
        return self.__converter(item)
    @final
    def _ConvertBack(self, item: TOut) -> TIn:
        return self.__backConverter(item)

class Set[TIn: IEquatableItem, TOut: IEquatableItem](Collection.Set[TIn, TOut]):
    def __init__(self, items: ISet[TIn], converter: Converter[TIn, TOut], backConverter: Converter[TOut, TIn]):
        super().__init__(items)

        self.__converter: Converter[TIn, TOut] = converter
        self.__backConverter: Converter[TOut, TIn] = backConverter
    
    @final
    def _Convert(self, item: TIn) -> TOut:
        return self.__converter(item)
    @final
    def _ConvertBack(self, item: TOut) -> TIn:
        return self.__backConverter(item)

class Dictionary[TKey: IEquatableItem, TValueIn, TValueOut](Collection.Dictionary[TKey, TValueIn, TValueOut]):
    def __init__(self, items: IDictionary[TKey, TValueIn], converter: Converter[TValueIn, TValueOut], backConverter: Converter[TValueOut, TValueIn]):
        super().__init__(items)

        self.__converter: Converter[TValueIn, TValueOut] = converter
        self.__backConverter: Converter[TValueOut, TValueIn] = backConverter
    
    @final
    def _Convert(self, item: TValueIn) -> TValueOut:
        return self.__converter(item)
    @final
    def _ConvertBack(self, item: TValueOut) -> TValueIn:
        return self.__backConverter(item)