from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Sequence, MutableSequence, MutableMapping
from typing import final

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Abstract.Collection import (Tuple as _Tuple, EquatableTuple as _EquatableTuple, HashableTuple as _HashableTuple,
                                                       Array as _Array, List as _List)
from WinCopies.Collections.Abstract.Mapping import Set as _Set, Dictionary as _Dictionary
from WinCopies.Collections.Abstract.Selection import ConverterBase as ConverterAbstract, TwoWayConverterBase
from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Extensions import ITuple, IEquatableTuple, IHashableTuple, IArray, IList, ISet, IDictionary
from WinCopies.Typing.Comparison import EquatableProtocol, HashableProtocol
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

class Tuple[TIn, TOut](_Tuple[TIn, TOut], ConverterBase[TIn, TOut]):
    def __init__(self, items: ITuple[TIn]|Sequence[TIn]|Iterable[TIn], converter: _Converter[TIn, TOut]) -> None:
        super().__init__(items)

        self.__converter: _Converter[TIn, TOut] = converter
    
    @final
    def _GetConverter(self) -> _Converter[TIn, TOut]: return self.__converter
    
    def _Clone(self, items: ITuple[TIn]) -> Tuple[TIn, TOut]: return Tuple[TIn, TOut](items, self.__converter)
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
class EquatableTuple[TIn: EquatableProtocol, TOut: EquatableProtocol](_EquatableTuple[TIn, TOut], ConverterBase[TIn, TOut]):
    def __init__(self, items: IEquatableTuple[TIn]|Sequence[TIn]|Iterable[TIn], converter: _Converter[TIn, TOut]) -> None:
        super().__init__(items)

        self.__converter: _Converter[TIn, TOut] = converter
    
    @final
    def _GetConverter(self) -> _Converter[TIn, TOut]: return self.__converter
    
    def _Clone(self, items: IEquatableTuple[TIn]) -> EquatableTuple[TIn, TOut]: return EquatableTuple[TIn, TOut](items, self.__converter)
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
class HashableTuple[TIn: HashableProtocol, TOut: HashableProtocol](_HashableTuple[TIn, TOut], ConverterBase[TIn, TOut]):
    def __init__(self, items: IHashableTuple[TIn]|Sequence[TIn]|Iterable[TIn], converter: _Converter[TIn, TOut]) -> None:
        super().__init__(items)

        self.__converter: _Converter[TIn, TOut] = converter
    
    @final
    def _GetConverter(self) -> _Converter[TIn, TOut]: return self.__converter
    
    def _Clone(self, items: IHashableTuple[TIn]) -> HashableTuple[TIn, TOut]: return HashableTuple[TIn, TOut](items, self.__converter)

class Array[TIn, TOut](_Array[TIn, TOut], TwoWayConverter[TIn, TOut]):
    def __init__(self, items: IArray[TIn]|Sequence[TIn]|Iterable[TIn], converters: IConverters[TIn, TOut]) -> None:
        super().__init__(items)

        self.__converters: IConverters[TIn, TOut] = converters

    @final
    def _GetConverters(self) -> IConverters[TIn, TOut]: return self.__converters
    
    def _Clone(self, items: IArray[TIn]) -> Array[TIn, TOut]: return Array[TIn, TOut](items, self.__converters)
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.FixedSize

class List[TIn, TOut](_List[TIn, TOut], TwoWayConverter[TIn, TOut]):
    def __init__(self, items: IList[TIn]|MutableSequence[TIn]|Iterable[TIn], converters: IConverters[TIn, TOut]) -> None:
        super().__init__(items)

        self.__converters: IConverters[TIn, TOut] = converters
    
    @final
    def _GetConverters(self) -> IConverters[TIn, TOut]: return self.__converters
    
    def _Clone(self, items: IList[TIn]) -> List[TIn, TOut]: return List[TIn, TOut](items, self.__converters)
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.Mutable

class Set[TIn: HashableProtocol, TOut: HashableProtocol](_Set[TIn, TOut], TwoWayConverter[TIn, TOut]):
    def __init__(self, items: ISet[TIn]|set[TIn]|Iterable[TIn], converters: IConverters[TIn, TOut]) -> None:
        super().__init__(items)

        self.__converters: IConverters[TIn, TOut] = converters

    @final
    def _GetConverters(self) -> IConverters[TIn, TOut]: return self.__converters

class Dictionary[TKey: HashableProtocol, TValueIn, TValueOut](_Dictionary[TKey, TValueIn, TValueOut]):
    def __init__(self, items: IDictionary[TKey, TValueIn]|MutableMapping[TKey, TValueIn], converters: IConverters[TValueIn, TValueOut]) -> None:
        super().__init__(items)

        self.__converters: IConverters[TValueIn, TValueOut] = converters
    
    @final
    def _Convert(self, item: TValueIn) -> TValueOut: return self.__converters.Convert(item)
    @final
    def _ConvertBack(self, item: TValueOut) -> TValueIn: return self.__converters.ConvertBack(item)

def CreateTuple[TIn, TOut](items: ITuple[TIn]|Sequence[TIn]|Iterable[TIn], converter: _Converter[TIn, TOut]) -> ITuple[TOut]:
    return Tuple[TIn, TOut](items, converter)
def MakeTuple[TIn, TOut](converter: _Converter[TIn, TOut], *items: TIn) -> ITuple[TOut]:
    return CreateTuple(items, converter)

def CreateEquatableTuple[TIn: EquatableProtocol, TOut: EquatableProtocol](items: IEquatableTuple[TIn]|Sequence[TIn]|Iterable[TIn], converter: _Converter[TIn, TOut]) -> IEquatableTuple[TOut]:
    return EquatableTuple[TIn, TOut](items, converter)
def MakeEquatableTuple[TIn: EquatableProtocol, TOut: EquatableProtocol](converter: _Converter[TIn, TOut], *items: TIn) -> IEquatableTuple[TOut]:
    return CreateEquatableTuple(items, converter)

def CreateHashableTuple[TIn: HashableProtocol, TOut: HashableProtocol](items: IHashableTuple[TIn]|Sequence[TIn]|Iterable[TIn], converter: _Converter[TIn, TOut]) -> IHashableTuple[TOut]:
    return HashableTuple[TIn, TOut](items, converter)
def MakeHashableTuple[TIn: HashableProtocol, TOut: HashableProtocol](converter: _Converter[TIn, TOut], *items: TIn) -> IHashableTuple[TOut]:
    return CreateHashableTuple(items, converter)

def CreateArray[TIn, TOut](items: IArray[TIn]|MutableSequence[TIn]|Iterable[TIn], converters: IConverters[TIn, TOut]) -> IArray[TOut]:
    return Array[TIn, TOut](items, converters)
def MakeArray[TIn, TOut](converters: IConverters[TIn, TOut], *items: TIn) -> IArray[TOut]:
    return CreateArray(items, converters)

def CreateList[TIn, TOut](items: IList[TIn]|MutableSequence[TIn]|Iterable[TIn], converters: IConverters[TIn, TOut]) -> IList[TOut]:
    return List[TIn, TOut](items, converters)
def MakeList[TIn, TOut](converters: IConverters[TIn, TOut], *items: TIn) -> IList[TOut]:
    return CreateList(items, converters)

def CreateSet[TIn: HashableProtocol, TOut: HashableProtocol](items: ISet[TIn]|set[TIn]|Iterable[TIn], converters: IConverters[TIn, TOut]) -> ISet[TOut]:
    return Set[TIn, TOut](items, converters)
def MakeSet[TIn: HashableProtocol, TOut: HashableProtocol](converters: IConverters[TIn, TOut], *items: TIn) -> ISet[TOut]:
    return CreateSet(items, converters)

def CreateDictionary[TKey: HashableProtocol, TValueIn, TValueOut](dictionary: IDictionary[TKey, TValueIn]|MutableMapping[TKey, TValueIn], converters: IConverters[TValueIn, TValueOut]) -> IDictionary[TKey, TValueOut]:
    return Dictionary[TKey, TValueIn, TValueOut](dictionary, converters)