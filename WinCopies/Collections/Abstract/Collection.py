from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator, Sequence
from typing import final, overload, Self, SupportsIndex

from WinCopies import IStringable
from WinCopies.Collections import Extensions
from WinCopies.Collections.Abstract import Converter, TwoWayConverter, Selector
from WinCopies.Collections.Abstract.Enumeration import EnumerableBase, Enumerator
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEnumerator, CountableEnumerable, TryAsEnumerator
from WinCopies.Collections.Extensions import ITuple, IEquatableTuple, IArray, IList, IDictionary, ISet
from WinCopies.Collections.Iteration import Select
from WinCopies.Typing import GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation, INullable, IEquatableItem
from WinCopies.Typing.Delegate import Converter as ConverterDelegate
from WinCopies.Typing.Pairing import IKeyValuePair, KeyValuePair, DualValueBool

class TupleBase[TIn, TOut, TSequence: IStringable](Converter[TIn, TOut, TSequence, ITuple[TIn]], Extensions.Sequence[TOut], Extensions.TupleBase[TOut], EnumerableBase[TIn, TOut]):
    def __init__(self, items: TSequence):
        super().__init__(items)
    
    @abstractmethod
    def _Clone(self, items: TSequence) -> Self:
        pass
    
    @final
    def GetCount(self) -> int:
        return self._GetInnerContainer().GetCount()
    
    @final
    def _GetAt(self, key: int) -> TOut:
        return self._Convert(self._GetInnerContainer().GetAt(key))
    
    @final
    def Contains(self, value: TOut|object) -> bool:
        return value in self.AsSequence()
    
    @final
    def _TryGetEnumerator(self) -> IEnumerator[TIn]|None:
        return self._GetInnerContainer().TryGetEnumerator()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TOut: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[TOut]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TOut|Sequence[TOut]:
        return self._Convert(self._GetInnerContainer().GetAt(int(index))) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsSequence()

class Tuple[TIn, TOut](TupleBase[TIn, TOut, ITuple[TIn]], Extensions.Tuple[TOut], IGenericConstraintImplementation[ITuple[TIn]]):
    def __init__(self, items: ITuple[TIn]):
        super().__init__(items)
    
    @final
    def SliceAt(self, key: slice) -> ITuple[TOut]:
        return self._Clone(self._GetContainer().SliceAt(key))
class EquatableTuple[TIn: IEquatableItem, TOut: IEquatableItem](TupleBase[TIn, TOut, IEquatableTuple[TIn]], Extensions.EquatableTuple[TOut], IGenericConstraintImplementation[IEquatableTuple[TIn]]):
    def __init__(self, items: IEquatableTuple[TIn]):
        super().__init__(items)
    
    def Hash(self) -> int:
        return self._GetContainer().Hash()
    
    def Equals(self, item: object) -> bool:
        return self is item or self._GetContainer().Equals(item)
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[TOut]:
        return self._Clone(self._GetContainer().SliceAt(key))

class ArrayBase[TIn, TOut, TSequence: IStringable](TupleBase[TIn, TOut, TSequence], TwoWayConverter[TIn, TOut, TSequence, ITuple[TIn]], GenericSpecializedConstraint[TSequence, ITuple[TIn], IArray[TIn]]):
    def __init__(self, items: TSequence):
        super().__init__(items)
    
    @final
    def Move(self, x: int, y: int) -> None:
        self._GetSpecializedContainer().Move(x, y)
    
    @final
    def _SetAt(self, key: int, value: TOut) -> None:
        self._GetSpecializedContainer().SetAt(key, self._ConvertBack(value))

class Array[TIn, TOut](ArrayBase[TIn, TOut, IArray[TIn]], Extensions.Array[TOut], IGenericSpecializedConstraintImplementation[ITuple[TIn], IArray[TIn]]):
    def __init__(self, items: IArray[TIn]):
        super().__init__(items)
    
    @final
    def Swap(self, x: int, y: int) -> None:
        super().Swap(x, y)
    
    @final
    def SliceAt(self, key: slice) -> IArray[TOut]:
        return self._Clone(self._GetContainer().SliceAt(key))

class List[TIn, TOut](ArrayBase[TIn, TOut, IList[TIn]], Extensions.List[TOut], Extensions.MutableSequence[TOut], IGenericSpecializedConstraintImplementation[ITuple[TIn], IList[TIn]]):
    def __init__(self, items: IList[TIn]):
        super().__init__(items)
    
    @final
    def Swap(self, x: int, y: int) -> None:
        super().Swap(x, y)
    
    @final
    def SliceAt(self, key: slice) -> IList[TOut]:
        return self._Clone(self._GetContainer().SliceAt(key))
    
    @final
    def Add(self, item: TOut) -> None:
        self._GetContainer().Add(self._ConvertBack(item))
    
    @final
    def TryInsert(self, index: int, value: TOut) -> bool:
        return self._GetContainer().TryInsert(index, self._ConvertBack(value))
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        return self._GetContainer().TryRemoveAt(index)
    
    @final
    def Clear(self) -> None:
        self._GetContainer().Clear()
    
    @final
    def insert(self, index: int, value: TOut) -> None:
        self._GetContainer().AsMutableSequence().insert(index, self._ConvertBack(value))
    
    @overload
    def __setitem__(self, index: SupportsIndex, value: TOut) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[TOut]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: TOut|Iterable[TOut]) -> None:
        self._GetContainer().AsMutableSequence()[index] = value # type: ignore
    
    @final
    def __delitem__(self, index: int|slice):
        del self._GetContainer().AsMutableSequence()[index]

class Dictionary[TKey: IEquatableItem, TValueIn, TValueOut](Selector[TValueIn, TValueOut, IDictionary[TKey, TValueIn]], Extensions.Dictionary[TKey, TValueOut]):
    @final
    class __ValueEnumerable(CountableEnumerable[TValueOut]):
        def __init__(self, dic: IDictionary[TKey, TValueIn], converter: ConverterDelegate[TValueIn, TValueOut]):
            super().__init__()

            self.__enumerable: ICountableEnumerable[TValueIn] = dic.GetValues()
            self.__iterable: Iterable[TValueOut] = Select(self.__enumerable.AsIterable(), converter)
        
        def GetCount(self) -> int:
            return self.__enumerable.GetCount()
        
        def _TryGetIterator(self) -> Iterator[TValueOut]|None:
            return iter(self.__iterable)
        
        def TryGetEnumerator(self) -> IEnumerator[TValueOut]|None:
            return TryAsEnumerator(self._TryGetIterator())
    @final
    class __Enumerator(Enumerator[IKeyValuePair[TKey, TValueIn], IKeyValuePair[TKey, TValueOut]]):
        def __init__(self, dictionary: Dictionary[TKey, TValueIn, TValueOut], enumerator: IEnumerator[IKeyValuePair[TKey, TValueIn]]):
            super().__init__(enumerator)

            self.__dictionary: Dictionary[TKey, TValueIn, TValueOut] = dictionary
        
        def _Convert(self, item: IKeyValuePair[TKey, TValueIn]) -> IKeyValuePair[TKey, TValueOut]:
            return KeyValuePair[TKey, TValueOut](item.GetKey(), self.__dictionary._Convert(item.GetValue()))
    
    def __init__(self, dictionary: IDictionary[TKey, TValueIn]):
        super().__init__(dictionary)

        self.__valueEnumerable: ICountableEnumerable[TValueOut] = Dictionary[TKey, TValueIn, TValueOut].__ValueEnumerable(self._GetItems(), self._Convert)
    
    @abstractmethod
    def _Convert(self, item: TValueIn) -> TValueOut:
        pass
    
    @final
    def GetCount(self) -> int:
        return self._GetItems().GetCount()
    
    @final
    def ContainsKey(self, key: TKey) -> bool:
        return self._GetItems().ContainsKey(key)
    
    @final
    def TryGetAt[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValueOut|TDefault]:
        result: DualValueBool[TValueIn|TDefault] = self._GetItems().TryGetAt(key, defaultValue)

        return DualValueBool[TValueOut](self._Convert(result.GetKey()), True) if result.GetValue() else DualValueBool[TDefault](defaultValue, False) # type: ignore
    
    @final
    def TrySetAt(self, key: TKey, value: TValueOut) -> bool:
        return self._GetItems().TrySetAt(key, self._ConvertBack(value))
    
    @final
    def GetKeys(self) -> ICountableEnumerable[TKey]:
        return self._GetItems().GetKeys()
    @final
    def GetValues(self) -> ICountableEnumerable[TValueOut]:
        return self.__valueEnumerable
    
    @final
    def TryAdd(self, key: TKey, value: TValueOut) -> bool:
        return self._GetItems().TryAdd(key, self._ConvertBack(value))
    @final
    def TryAddItem(self, item: KeyValuePair[TKey, TValueOut]) -> bool:
        return self.TryAdd(item.GetKey(), item.GetValue())
    
    @final
    def Add(self, key: TKey, value: TValueOut) -> None:
        self._GetItems().Add(key, self._ConvertBack(value))
    @final
    def AddItem(self, item: KeyValuePair[TKey, TValueOut]) -> None:
        self.Add(item.GetKey(), item.GetValue())

    @final
    def Remove(self, key: TKey) -> None:
        self._GetItems().Remove(key)
    
    @final
    def TryRemoveValue(self, key: TKey) -> INullable[TValueOut]:
        return self._GetItems().TryRemoveValue(key).TryConvertToNullable(self._Convert)
    @final
    def TryRemove[TDefault](self, key: TKey, defaultValue: TDefault) -> TValueOut|TDefault:
        result: INullable[TValueOut] = self.TryRemoveValue(key)

        return result.GetValue() if result.HasValue() else defaultValue
    
    @final
    def Clear(self) -> None:
        return self._GetItems().Clear()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[IKeyValuePair[TKey, TValueOut]]|None:
        enumerator: IEnumerator[IKeyValuePair[TKey, TValueIn]]|None = self._GetItems().TryGetEnumerator()

        return None if enumerator is None else Dictionary[TKey, TValueIn, TValueOut].__Enumerator(self, enumerator)

class Set[TIn: IEquatableItem, TOut: IEquatableItem](Selector[TIn, TOut, ISet[TIn]], Extensions.Set[TOut], EnumerableBase[TIn, TOut]):
    def __init__(self, items: Extensions.ISet[TIn]):
        super().__init__(items)

    @final
    def GetCount(self) -> int:
        return self._GetItems().GetCount()
    
    @final
    def TryAdd(self, item: TOut) -> bool:
        return self._GetItems().TryAdd(self._ConvertBack(item))
    @final
    def Add(self, item: TOut) -> None:
        self._GetItems().Add(self._ConvertBack(item))
    
    @final
    def Remove(self, item: TOut) -> None:
        self._GetItems().Remove(self._ConvertBack(item))
    @final
    def TryRemove(self, item: TOut) -> bool:
        return self._GetItems().TryRemove(self._ConvertBack(item))
    
    @final
    def _TryGetEnumerator(self) -> IEnumerator[TIn]|None:
        return self._GetItems().TryGetEnumerator()
    
    @final
    def Clear(self) -> None:
        self._GetItems().Clear()