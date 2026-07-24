from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator, MutableMapping
from typing import final

from WinCopies import Abstract
from WinCopies.Collections import Enumeration
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEnumerator, CountableEnumerable, EnumeratorBase, TryAsEnumerator
from WinCopies.Collections.Extensions import Mapping, ISet, IDictionary
from WinCopies.Collections.Linked.Singly import IEnumerableQueue, CreateEnumerableQueue
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Comparison import EquatableProtocol, HashableProtocol
from WinCopies.Typing.Pairing import IKeyValuePair, DualValueBool, CreateDualValueBool

class Set[T: HashableProtocol](Mapping.Set[T]):
    def __init__(self, items: set[T]|Iterable[T]|None = None) -> None:
        super().__init__()

        self.__set: set[T] = set[T]() if items is None else (items if isinstance(items, set) else set[T](items))
    
    @final
    def __TryAdd(self, item: T) -> int:
        count = self.GetCount()
        
        self._GetItems().add(item)
    
        return count
    
    @final
    def _GetItems(self) -> set[T]:
        return self.__set
    
    @final
    def GetCount(self) -> int: return len(self._GetItems())
    
    @final
    def Contains(self, value: T|object) -> bool: return value in self.__set
    
    @final
    def TryAdd(self, item: T) -> bool: return self.__TryAdd(item) < self.GetCount()
    @final
    def Add(self, item: T) -> None:
        if self.__TryAdd(item) == self.GetCount(): raise ValueError(f"Item {item} already exists.")
    
    @final
    def TryAddRange(self, items: Iterable[T]) -> bool:
        _items: IEnumerableQueue[T] = CreateEnumerableQueue(items)

        for item in _items.AsIterable():
            if self.Contains(item): return False
        
        count = self.GetCount()
        
        self._GetItems().update(_items.AsGenerator())
    
        return count < self.GetCount()
    
    @final
    def Remove(self, item: T) -> None: self._GetItems().remove(item)
    @final
    def TryRemove(self, item: T) -> bool:
        try:
            self.Remove(item)

            return True
        
        except KeyError: return False
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return TryAsEnumerator(item for item in self._GetItems())
    
    @final
    def Clear(self) -> None: self._GetItems().clear()
    
    def ToString(self) -> str: return str(self._GetItems())

@final
class EnumerationKeyValuePair[TKey: EquatableProtocol, TValue](Abstract, IKeyValuePair[TKey, TValue]):
    def __init__(self, item: tuple[TKey, TValue]) -> None:
        super().__init__()
        
        self.__item: tuple[TKey, TValue] = item
    
    @final
    def IsKeyValuePair(self) -> bool: return True
    
    @final
    def GetKey(self) -> TKey: return self.__item[0]
    @final
    def GetValue(self) -> TValue: return self.__item[1]

    @final
    def _Equals(self, item: IKeyValuePair[TKey, TValue]|object) -> bool:
        return isinstance(item, EnumerationKeyValuePair)

@final
class DictionaryEnumerator[TKey: HashableProtocol, TValue](EnumeratorBase[IKeyValuePair[TKey, TValue]]):
    def __init__(self, dictionary: MutableMapping[TKey, TValue]) -> None:
        super().__init__()

        self.__dictionary: MutableMapping[TKey, TValue] = dictionary
        self.__iterator: Enumeration.Iterator[tuple[TKey, TValue]]|None = None
        self.__current: INullable[IKeyValuePair[TKey, TValue]] = GetNullValue()
    
    def IsResetSupported(self) -> bool: return True
    
    def _OnStarting(self) -> bool:
        if super()._OnStarting():
            self.__iterator = Enumeration.Iterator(self.__dictionary.items().__iter__())
            
            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        if self.__iterator is None: return False
        
        if self.__iterator.MoveNext():
            self.__current = GetNullable(EnumerationKeyValuePair[TKey, TValue](self.__iterator.GetCurrent()))

            return True
        
        return False
    
    def _GetCurrent(self) -> IKeyValuePair[TKey, TValue]: return self.__current.GetValue()
    
    def _OnEnded(self) -> None:
        self.__iterator = None
        self.__current = GetNullValue()

        super()._OnEnded()
    
    def _OnStopped(self) -> None:
        pass
    
    def _ResetOverride(self) -> bool: return True

class DictionaryEnumerable[TKey: HashableProtocol, TValue, TItem](CountableEnumerable[TItem]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetDictionary(self) -> IDictionary[TKey, TValue]:
        ...
    
    @final
    def IsEmpty(self) -> bool: return self._GetDictionary().IsEmpty()
    
    @final
    def GetCount(self) -> int: return self._GetDictionary().GetCount()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None: return TryAsEnumerator(self._TryGetIterator())

@final
class __None(Abstract):
    def __init__(self) -> None: super().__init__()

__none: __None = __None()

def _GetNoneInstance() -> __None:
    return __none

# TODO: Should inherit from MutableMapping
class Dictionary[TKey: HashableProtocol, TValue](Mapping.Dictionary[TKey, TValue]):
    class _Enumerable[_TKey: HashableProtocol, _TValue, _TItem](DictionaryEnumerable[_TKey, _TValue, _TItem]):
        def __init__(self, dic: Dictionary[_TKey, _TValue]) -> None:
            super().__init__()

            self.__dic: Dictionary[_TKey, _TValue] = dic
        
        @final
        def _GetDictionary(self) -> Dictionary[_TKey, _TValue]: return self.__dic
        
        @final
        def _GetInnerDictionary(self) -> MutableMapping[_TKey, _TValue]: return self._GetDictionary()._GetDictionary()
    
    @final
    class _KeyEnumerable[_TKey: HashableProtocol, _TValue](_Enumerable[_TKey, _TValue, _TKey]):
        def __init__(self, dic: Dictionary[_TKey, _TValue]) -> None: super().__init__(dic)
        
        def _TryGetIterator(self) -> Iterator[_TKey]|None: return iter(self._GetInnerDictionary().keys())
    @final
    class _ValueEnumerable[_TKey: HashableProtocol, _TValue](_Enumerable[_TKey, _TValue, _TValue]):
        def __init__(self, dic: Dictionary[_TKey, _TValue]) -> None: super().__init__(dic)
        
        def _TryGetIterator(self) -> Iterator[_TValue]|None: return iter(self._GetInnerDictionary().values())
    
    def __init__(self, dictionary: MutableMapping[TKey, TValue]|None = None) -> None:
        super().__init__()

        self.__dictionary: MutableMapping[TKey, TValue] = dict[TKey, TValue]() if dictionary is None else dictionary
        
        self.__keys: ICountableEnumerable[TKey] = Dictionary._KeyEnumerable(self)
        self.__values: ICountableEnumerable[TValue] = Dictionary._ValueEnumerable(self)
    
    @final
    def __SetAt(self, key: TKey, value: TValue) -> None:
        self._GetDictionary()[key] = value
    
    @final
    def _GetDictionary(self) -> MutableMapping[TKey, TValue]:
        return self.__dictionary
    
    @final
    def GetCount(self) -> int: return len(self._GetDictionary())
    
    @final
    def ContainsKey(self, key: TKey) -> bool: return key in self._GetDictionary()
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TValue]:
        result: TValue|__None = self._GetDictionary().get(key, _GetNoneInstance())

        return GetNullValue() if isinstance(result, __None) else GetNullable(result)
    
    @final
    def TrySetAt(self, key: TKey, value: TValue) -> bool:
        if key in self.GetKeys().AsIterable():
            self.__SetAt(key, value)

            return True
        
        return False
    
    @final
    def GetKeys(self) -> ICountableEnumerable[TKey]: return self.__keys
    @final
    def GetValues(self) -> ICountableEnumerable[TValue]: return self.__values
    
    @final
    def TryAdd(self, key: TKey, value: TValue) -> bool:
        count = self.GetCount()
        
        self._GetDictionary().setdefault(key, value)
    
        return count < self.GetCount()
    
    @final
    def AddOrUpdate(self, key: TKey, value: TValue) -> bool:
        if self.TryAdd(key, value): return True
        
        self.__SetAt(key, value)

        return False
    
    @final
    def _TryRemove[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValue|TDefault]:
        result: TValue|__None = self._GetDictionary().pop(key, _GetNoneInstance())

        return CreateDualValueBool(defaultValue, False) if isinstance(result, __None) else CreateDualValueBool(result, True)
    @final
    def Remove(self, key: TKey) -> TValue: return self._GetDictionary().pop(key)
    
    @final
    def Clear(self) -> None: self._GetDictionary().clear()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[IKeyValuePair[TKey, TValue]]: return DictionaryEnumerator[TKey, TValue](self._GetDictionary())
    
    def ToString(self) -> str: return str(self._GetDictionary())

def CreateSet[T: HashableProtocol](items: set[T]|Iterable[T]) -> ISet[T]:
    return Set[T](items)
def MakeSet[T: HashableProtocol](*items: T) -> ISet[T]:
    return CreateSet(items)

def CreateDictionary[TKey: HashableProtocol, TValue](dictionary: MutableMapping[TKey, TValue]|None = None) -> IDictionary[TKey, TValue]:
    return Dictionary[TKey, TValue](dictionary)

def GetSet[T: HashableProtocol](items: ISet[T]|set[T]|Iterable[T]) -> ISet[T]:
    return items if isinstance(items, ISet) else CreateSet(items)
def GetDictionary[TKey: HashableProtocol, TValue](dictionary: IDictionary[TKey, TValue]|MutableMapping[TKey, TValue]|None = None) -> IDictionary[TKey, TValue]:
    return dictionary if isinstance(dictionary, IDictionary) else CreateDictionary(dictionary)