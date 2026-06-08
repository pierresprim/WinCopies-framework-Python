from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator, Sequence as SequenceBase, MutableSequence as MutableSequenceBase
from typing import final, overload, Self, SupportsIndex

from WinCopies import IInterface, IStringable
from WinCopies.Collections import Mutability
from WinCopies.Collections.Abstract import StringableConverter, StringableTwoWayConverter, Selector
from WinCopies.Collections.Abstract.Enumeration import EnumerableAbstract, ResumableEnumerableAbstract, Enumerator
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEnumerator, CountableEnumerable, TryAsEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Extensions import ITuple, IEquatableTuple, IHashableTuple, IArray, IList, IDictionary, ISet, Sequence, MutableSequence
from WinCopies.Collections.Extensions.Collection import Collection, TupleAbstract, TupleCollection, EquatableTupleCollection, HashableTupleCollection, ArrayCollection, Set as SetBase, Dictionary as DictionaryBase
from WinCopies.Collections.Iteration import Select
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Comparison import IEquatableValue, IHashableValue
from WinCopies.Typing.Delegate import Converter as ConverterDelegate
from WinCopies.Typing.Generic import GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation
from WinCopies.Typing.Pairing import IKeyValuePair, KeyValuePair, DualValueBool

class TupleCollectionAbstract[TIn, TOut, TSequence: IStringable](StringableConverter[TIn, TOut, TSequence, ITuple[TIn]], Sequence[TOut], TupleAbstract[TOut], ResumableEnumerableAbstract[TIn, TOut]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _Clone(self, items: TSequence) -> Self:
        ...
    
    @final
    def GetCount(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def _GetAt(self, key: int) -> TOut:
        return self._Convert(self._GetInnerContainer().GetAt(key))
    
    @final
    def Contains(self, value: TOut|object) -> bool: return value in self.AsSequence()
    
    @final
    def _TryGetEnumerator(self) -> IEnumerator[TIn]|None:
        return self._GetInnerContainer().TryGetEnumerator()
    @final
    def _TryGetResumableEnumerator(self) -> IResumableEnumerator[TIn]|None:
        return self._GetInnerContainer().TryGetResumableEnumerator()
class TupleBase[TIn, TOut, TSequence: IStringable](TupleCollectionAbstract[TIn, TOut, TSequence]):
    def __init__(self) -> None: super().__init__()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TOut: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[TOut]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TOut|SequenceBase[TOut]: return self._Convert(self._GetInnerContainer().GetAt(int(index))) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsSequence()

class Tuple[TIn, TOut](TupleCollection[TOut], TupleBase[TIn, TOut, ITuple[TIn]], IGenericConstraintImplementation[ITuple[TIn]]):
    def __init__(self, items: ITuple[TIn]) -> None:
        super().__init__()

        self.__items: ITuple[TIn] = items
    
    @final
    def _GetContainer(self) -> ITuple[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.TryGetSourceMutability()
    
    @final
    def SliceAt(self, key: slice) -> ITuple[TOut]: return self._Clone(self._GetContainer().SliceAt(key))
class EquatableTuple[TIn: IEquatableValue, TOut: IEquatableValue](TupleBase[TIn, TOut, IEquatableTuple[TIn]], EquatableTupleCollection[TOut], IGenericConstraintImplementation[IEquatableTuple[TIn]]):
    def __init__(self, items: IEquatableTuple[TIn]) -> None:
        super().__init__()

        self.__items: IEquatableTuple[TIn] = items
    
    @final
    def _GetContainer(self) -> IEquatableTuple[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.TryGetSourceMutability()
    
    def Equals(self, item: object) -> bool: return self is item or self._GetContainer().Equals(item)
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[TOut]: return self._Clone(self._GetContainer().SliceAt(key))
class HashableTuple[TIn: IHashableValue, TOut: IHashableValue](TupleBase[TIn, TOut, IHashableTuple[TIn]], HashableTupleCollection[TOut], IGenericConstraintImplementation[IHashableTuple[TIn]]):
    def __init__(self, items: IHashableTuple[TIn]) -> None:
        super().__init__()

        self.__items: IHashableTuple[TIn] = items
    
    @final
    def _GetContainer(self) -> IHashableTuple[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.TryGetSourceMutability()
    
    def Equals(self, item: object) -> bool: return self is item or self._GetContainer().Equals(item)
    def Hash(self) -> int: return self._GetContainer().Hash()
    
    @final
    def SliceAt(self, key: slice) -> IHashableTuple[TOut]: return self._Clone(self._GetContainer().SliceAt(key))

class ArrayAbstract[TIn, TOut, TSequence: IStringable](TupleCollectionAbstract[TIn, TOut, TSequence], StringableTwoWayConverter[TIn, TOut, TSequence, ITuple[TIn]], GenericSpecializedConstraint[TSequence, ITuple[TIn], IArray[TIn]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def Move(self, x: int, y: int) -> None: self._GetSpecializedContainer().Move(x, y)
    
    @final
    def _SetAt(self, key: int, value: TOut) -> None:
        self._GetSpecializedContainer().SetAt(key, self._ConvertBack(value))
class ArrayBase[TIn, TOut, TSequence: IStringable](TupleBase[TIn, TOut, TSequence], ArrayAbstract[TIn, TOut, TSequence]):
    def __init__(self) -> None: super().__init__()

class Array[TIn, TOut](ArrayBase[TIn, TOut, IArray[TIn]], ArrayCollection[TOut], IGenericSpecializedConstraintImplementation[ITuple[TIn], IArray[TIn]]):
    def __init__(self, items: IArray[TIn]) -> None:
        super().__init__()

        self.__items: IArray[TIn] = items
    
    @final
    def _GetContainer(self) -> IArray[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.TryGetSourceMutability()
    
    @final
    def Swap(self, x: int, y: int) -> None: super().Swap(x, y)
    
    @final
    def SliceAt(self, key: slice) -> IArray[TOut]: return self._Clone(self._GetContainer().SliceAt(key))

class List[TIn, TOut](ArrayAbstract[TIn, TOut, IList[TIn]], Collection[TOut], MutableSequence[TOut], IGenericSpecializedConstraintImplementation[ITuple[TIn], IList[TIn]]):
    def __init__(self, items: IList[TIn]) -> None:
        super().__init__()

        self.__items: IList[TIn] = items
    
    @final
    def _GetContainer(self) -> IList[TIn]: return self.__items
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__items.TryGetSourceMutability()
    
    @final
    def Swap(self, x: int, y: int) -> None: super().Swap(x, y)
    
    @final
    def SliceAt(self, key: slice) -> IList[TOut]: return self._Clone(self._GetContainer().SliceAt(key))
    
    @final
    def Add(self, item: TOut) -> None: self._GetContainer().Add(self._ConvertBack(item))
    
    @final
    def TryInsert(self, index: int, value: TOut) -> bool: return self._GetContainer().TryInsert(index, self._ConvertBack(value))
    @final
    def TryInsertRange(self, index: int, items: Iterable[TOut]) -> bool: return self._GetContainer().TryInsertRange(index, Select(items, lambda item: self._ConvertBack(item)))
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None: return self._GetContainer().TryRemoveAt(index)
    @final
    def TryRemoveRange(self, index: int, count: int) -> bool: return self._GetContainer().TryRemoveRange(index, count)
    
    @final
    def Clear(self) -> None: self._GetContainer().Clear()
    
    @final
    def insert(self, index: int, value: TOut) -> None: self._GetContainer().AsMutableSequence().insert(index, self._ConvertBack(value))
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TOut: ...
    @overload
    def __getitem__(self, index: slice) -> MutableSequenceBase[TOut]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TOut|MutableSequenceBase[TOut]: return self._Convert(self._GetInnerContainer().GetAt(int(index))) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsMutableSequence()
    
    @overload
    def __setitem__(self, index: SupportsIndex, value: TOut) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[TOut]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: TOut|Iterable[TOut]) -> None: self._GetContainer().AsMutableSequence()[index] = value # type: ignore
    
    @final
    def __delitem__(self, index: int|slice) -> None: del self._GetContainer().AsMutableSequence()[index]

class _ICookie[TIn, TOut](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Convert(self, item: TIn) -> TOut: ...

@final
class _ValueEnumerable[TKey: IHashableValue, TValueIn, TValueOut](CountableEnumerable[TValueOut]):
    def __init__(self, dic: IDictionary[TKey, TValueIn], converter: ConverterDelegate[TValueIn, TValueOut]) -> None:
        super().__init__()

        self.__enumerable: ICountableEnumerable[TValueIn] = dic.GetValues()
        self.__iterable: Iterable[TValueOut] = Select(self.__enumerable.AsIterable(), converter)
    
    def GetCount(self) -> int: return self.__enumerable.GetCount()
    
    def _TryGetIterator(self) -> Iterator[TValueOut]|None:
        return iter(self.__iterable)
    
    def TryGetEnumerator(self) -> IEnumerator[TValueOut]|None: return TryAsEnumerator(self._TryGetIterator())
@final
class _Enumerator[TKey: IEquatableValue, TValueIn, TValueOut](Enumerator[IKeyValuePair[TKey, TValueIn], IKeyValuePair[TKey, TValueOut]]):
    def __init__(self, dictionary: _ICookie[TValueIn, TValueOut], enumerator: IEnumerator[IKeyValuePair[TKey, TValueIn]]) -> None:
        super().__init__(enumerator)

        self.__dictionary: _ICookie[TValueIn, TValueOut] = dictionary
    
    def _Convert(self, item: IKeyValuePair[TKey, TValueIn]) -> IKeyValuePair[TKey, TValueOut]:
        return KeyValuePair[TKey, TValueOut](item.GetKey(), self.__dictionary.Convert(item.GetValue()))

class Dictionary[TKey: IHashableValue, TValueIn, TValueOut](Selector[TValueIn, TValueOut, IDictionary[TKey, TValueIn]], DictionaryBase[TKey, TValueOut]):
    @final
    class _Cookie[_TKey: IHashableValue, T, U](_ICookie[T, U]):
        def __init__(self, dic: Dictionary[_TKey, T, U]) -> None:
            super().__init__()

            self.__dic: Dictionary[_TKey, T, U] = dic
        
        def Convert(self, item: T) -> U: return self.__dic._Convert(item)
    
    def __init__(self, dictionary: IDictionary[TKey, TValueIn]) -> None:
        super().__init__(dictionary)

        self.__valueEnumerable: ICountableEnumerable[TValueOut] = _ValueEnumerable[TKey, TValueIn, TValueOut](self._GetItems(), self._Convert)
    
    @abstractmethod
    def _Convert(self, item: TValueIn) -> TValueOut:
        ...
    
    @final
    def GetCount(self) -> int: return self._GetItems().GetCount()
    
    @final
    def ContainsKey(self, key: TKey) -> bool: return self._GetItems().ContainsKey(key)
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TValueOut]:
        result: INullable[TValueIn] = self._GetItems().TryGetValue(key)

        return GetNullable(self._Convert(result.GetValue())) if result.HasValue() else GetNullValue()
    
    @final
    def TrySetAt(self, key: TKey, value: TValueOut) -> bool: return self._GetItems().TrySetAt(key, self._ConvertBack(value))
    
    @final
    def GetKeys(self) -> ICountableEnumerable[TKey]: return self._GetItems().GetKeys()
    @final
    def GetValues(self) -> ICountableEnumerable[TValueOut]: return self.__valueEnumerable
    
    @final
    def TryAdd(self, key: TKey, value: TValueOut) -> bool: return self._GetItems().TryAdd(key, self._ConvertBack(value))
    
    @final
    def Remove(self, key: TKey) -> TValueOut: return self._Convert(self._GetItems().Remove(key))
    
    @final
    def _TryRemove[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValueOut|TDefault]:
        def getResult(key: TValueOut|TDefault, value: bool) -> DualValueBool[TValueOut|TDefault]: return DualValueBool[TValueOut|TDefault](key, value)
        
        result: DualValueBool[TValueIn|None] = self._GetItems().TryRemove(key, None)
        value: TValueIn|None = result.GetKey()

        return getResult(self._Convert(value), True) if result.GetValue() and value is not None else getResult(defaultValue, False)
    
    @final
    def Clear(self) -> None: return self._GetItems().Clear()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[IKeyValuePair[TKey, TValueOut]]|None:
        enumerator: IEnumerator[IKeyValuePair[TKey, TValueIn]]|None = self._GetItems().TryGetEnumerator()

        return None if enumerator is None else _Enumerator[TKey, TValueIn, TValueOut](Dictionary[TKey, TValueIn, TValueOut]._Cookie(self), enumerator)

class Set[TIn: IHashableValue, TOut: IHashableValue](Selector[TIn, TOut, ISet[TIn]], SetBase[TOut], EnumerableAbstract[TIn, TOut]):
    def __init__(self, items: ISet[TIn]) -> None: super().__init__(items)
    
    @final
    def GetCount(self) -> int: return self._GetItems().GetCount()
    
    @final
    def Contains(self, value: TOut|object) -> bool: return self._GetItems().Contains(value)
    
    @final
    def TryAdd(self, item: TOut) -> bool: return self._GetItems().TryAdd(self._ConvertBack(item))
    @final
    def Add(self, item: TOut) -> None: self._GetItems().Add(self._ConvertBack(item))
    
    @final
    def TryAddRange(self, items: Iterable[TOut]) -> bool: return self._GetItems().TryAddRange(Select(items, lambda item: self._ConvertBack(item)))
    
    @final
    def Remove(self, item: TOut) -> None: self._GetItems().Remove(self._ConvertBack(item))
    @final
    def TryRemove(self, item: TOut) -> bool: return self._GetItems().TryRemove(self._ConvertBack(item))
    
    @final
    def _TryGetEnumerator(self) -> IEnumerator[TIn]|None:
        return self._GetItems().TryGetEnumerator()
    
    @final
    def Clear(self) -> None: self._GetItems().Clear()