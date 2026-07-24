from __future__ import annotations

from collections.abc import Iterable, Sequence, MutableSequence, MutableMapping
from typing import final

from WinCopies.Collections.Abstract import Collection, Mapping
from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Extensions import ITuple, IEquatableTuple, IHashableTuple, IArray, IList, ISet, IDictionary
from WinCopies.Typing.Comparison import EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import Converter

class Tuple[TIn, TOut](Collection.Tuple[TIn, TOut]):
    def __init__(self, items: ITuple[TIn]|Sequence[TIn]|Iterable[TIn], converter: Converter[TIn, TOut]) -> None:
        super().__init__(items)

        self.__converter: Converter[TIn, TOut] = converter
    
    def _Clone(self, items: ITuple[TIn]) -> Tuple[TIn, TOut]:
        return Tuple[TIn, TOut](items, self.__converter)
    
    @final
    def _Convert(self, item: TIn) -> TOut:
        return self.__converter(item)
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
class EquatableTuple[TIn: EquatableProtocol, TOut: EquatableProtocol](Collection.EquatableTuple[TIn, TOut]):
    def __init__(self, items: IEquatableTuple[TIn]|Sequence[TIn]|Iterable[TIn], converter: Converter[TIn, TOut]) -> None:
        super().__init__(items)

        self.__converter: Converter[TIn, TOut] = converter
    
    def _Clone(self, items: IEquatableTuple[TIn]) -> EquatableTuple[TIn, TOut]:
        return EquatableTuple[TIn, TOut](items, self.__converter)
    
    @final
    def _Convert(self, item: TIn) -> TOut:
        return self.__converter(item)
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
class HashableTuple[TIn: HashableProtocol, TOut: HashableProtocol](Collection.HashableTuple[TIn, TOut]):
    def __init__(self, items: IHashableTuple[TIn]|Sequence[TIn]|Iterable[TIn], converter: Converter[TIn, TOut]) -> None:
        super().__init__(items)

        self.__converter: Converter[TIn, TOut] = converter
    
    def _Clone(self, items: IHashableTuple[TIn]) -> HashableTuple[TIn, TOut]:
        return HashableTuple[TIn, TOut](items, self.__converter)
    
    @final
    def _Convert(self, item: TIn) -> TOut:
        return self.__converter(item)

class Array[TIn, TOut](Collection.Array[TIn, TOut]):
    def __init__(self, items: IArray[TIn]|Sequence[TIn]|Iterable[TIn], converter: Converter[TIn, TOut], backConverter: Converter[TOut, TIn]) -> None:
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
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.FixedSize

class List[TIn, TOut](Collection.List[TIn, TOut]):
    def __init__(self, items: IList[TIn]|MutableSequence[TIn]|Iterable[TIn], converter: Converter[TIn, TOut], backConverter: Converter[TOut, TIn]) -> None:
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
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.Mutable

class Set[TIn: HashableProtocol, TOut: HashableProtocol](Mapping.Set[TIn, TOut]):
    def __init__(self, items: ISet[TIn]|set[TIn]|Iterable[TIn], converter: Converter[TIn, TOut], backConverter: Converter[TOut, TIn]) -> None:
        super().__init__(items)

        self.__converter: Converter[TIn, TOut] = converter
        self.__backConverter: Converter[TOut, TIn] = backConverter
    
    @final
    def _Convert(self, item: TIn) -> TOut:
        return self.__converter(item)
    @final
    def _ConvertBack(self, item: TOut) -> TIn:
        return self.__backConverter(item)

class Dictionary[TKey: HashableProtocol, TValueIn, TValueOut](Mapping.Dictionary[TKey, TValueIn, TValueOut]):
    def __init__(self, items: IDictionary[TKey, TValueIn]|MutableMapping[TKey, TValueIn], converter: Converter[TValueIn, TValueOut], backConverter: Converter[TValueOut, TValueIn]) -> None:
        super().__init__(items)

        self.__converter: Converter[TValueIn, TValueOut] = converter
        self.__backConverter: Converter[TValueOut, TValueIn] = backConverter
    
    @final
    def _Convert(self, item: TValueIn) -> TValueOut:
        return self.__converter(item)
    @final
    def _ConvertBack(self, item: TValueOut) -> TValueIn:
        return self.__backConverter(item)

def CreateTuple[TIn, TOut](items: ITuple[TIn]|Sequence[TIn]|Iterable[TIn], converter: Converter[TIn, TOut]) -> ITuple[TOut]:
    return Tuple[TIn, TOut](items, converter)
def MakeTuple[TIn, TOut](converter: Converter[TIn, TOut], *items: TIn) -> ITuple[TOut]:
    return CreateTuple(items, converter)

def CreateEquatableTuple[TIn: EquatableProtocol, TOut: EquatableProtocol](items: IEquatableTuple[TIn]|Sequence[TIn]|Iterable[TIn], converter: Converter[TIn, TOut]) -> IEquatableTuple[TOut]:
    return EquatableTuple[TIn, TOut](items, converter)
def MakeEquatableTuple[TIn: EquatableProtocol, TOut: EquatableProtocol](converter: Converter[TIn, TOut], *items: TIn) -> IEquatableTuple[TOut]:
    return CreateEquatableTuple(items, converter)

def CreateHashableTuple[TIn: HashableProtocol, TOut: HashableProtocol](items: IHashableTuple[TIn]|Sequence[TIn]|Iterable[TIn], converter: Converter[TIn, TOut]) -> IHashableTuple[TOut]:
    return HashableTuple[TIn, TOut](items, converter)
def MakeHashableTuple[TIn: HashableProtocol, TOut: HashableProtocol](converter: Converter[TIn, TOut], *items: TIn) -> IHashableTuple[TOut]:
    return CreateHashableTuple(items, converter)

def CreateArray[TIn, TOut](items: IArray[TIn]|MutableSequence[TIn]|Iterable[TIn], converter: Converter[TIn, TOut], backConverter: Converter[TOut, TIn]) -> IArray[TOut]:
    return Array[TIn, TOut](items, converter, backConverter)
def MakeArray[TIn, TOut](converter: Converter[TIn, TOut], backConverter: Converter[TOut, TIn], *items: TIn) -> IArray[TOut]:
    return CreateArray(items, converter, backConverter)

def CreateList[TIn, TOut](items: IList[TIn]|MutableSequence[TIn]|Iterable[TIn], converter: Converter[TIn, TOut], backConverter: Converter[TOut, TIn]) -> IList[TOut]:
    return List[TIn, TOut](items, converter, backConverter)
def MakeList[TIn, TOut](converter: Converter[TIn, TOut], backConverter: Converter[TOut, TIn], *items: TIn) -> IList[TOut]:
    return CreateList(items, converter, backConverter)

def CreateSet[TIn: HashableProtocol, TOut: HashableProtocol](items: ISet[TIn]|set[TIn]|Iterable[TIn], converter: Converter[TIn, TOut], backConverter: Converter[TOut, TIn]) -> ISet[TOut]:
    return Set[TIn, TOut](items, converter, backConverter)
def MakeSet[TIn: HashableProtocol, TOut: HashableProtocol](converter: Converter[TIn, TOut], backConverter: Converter[TOut, TIn], *items: TIn) -> ISet[TOut]:
    return CreateSet(items, converter, backConverter)

def CreateDictionary[TKey: HashableProtocol, TValueIn, TValueOut](dictionary: IDictionary[TKey, TValueIn]|MutableMapping[TKey, TValueIn], converter: Converter[TValueIn, TValueOut], backConverter: Converter[TValueOut, TValueIn]) -> IDictionary[TKey, TValueOut]:
    return Dictionary[TKey, TValueIn, TValueOut](dictionary, converter, backConverter)