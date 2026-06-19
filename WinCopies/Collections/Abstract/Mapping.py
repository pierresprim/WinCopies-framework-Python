from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator
from typing import final

from WinCopies import IInterface
from WinCopies.Collections.Abstract import Selector
from WinCopies.Collections.Abstract.Enumeration import EnumerableAbstract, Enumerator
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEnumerator, CountableEnumerable, TryAsEnumerator
from WinCopies.Collections.Extensions import IDictionary, ISet
from WinCopies.Collections.Extensions.Mapping import Set as SetBase, Dictionary as DictionaryBase
from WinCopies.Collections.Iteration import Select
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Comparison import IEquatableValue, IHashableValue
from WinCopies.Typing.Delegate import Converter as ConverterDelegate
from WinCopies.Typing.Pairing import IKeyValuePair, KeyValuePair, DualValueBool

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