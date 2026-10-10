from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator as _Iterator, Collection, MutableMapping
from typing import overload, final, Callable

from WinCopies import Abstract
from WinCopies.Collections.Enumeration.Core import ICountableEnumerable, IEnumerator, CountableEnumerable, EnumeratorBase, Iterator, TryAsEnumerator
from WinCopies.Collections.Extensions import Mapping, ISet, IDictionary
from WinCopies.Collections.Iteration import GetFirstItemExclusive
from WinCopies.Collections.Iteration.Enumeration import Any
from WinCopies.Collections.Linked.Singly import IEnumerableQueue, CreateEnumerableQueue
from WinCopies.Delegates import Self, GetNotPredicate
from WinCopies.Typing import INullable, GetNullable, GetNullValue, GetNullableValue
from WinCopies.Typing.Comparison import EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import Predicate, Selector
from WinCopies.Typing.Pairing import IKeyValuePair, DualResult, CreateDualResult

def __HasDuplicate[TItem: HashableProtocol, TResult](items: Iterable[TItem], action: Callable[[Iterable[TItem], Predicate[TItem]], TResult], selector: Selector[Predicate[TItem]]) -> TResult:
    return action(items, selector(Set[TItem]().TryAdd))

def HasDuplicate[T: HashableProtocol](items: Iterable[T]) -> bool:
    return __HasDuplicate(items, Any, lambda adder: GetNotPredicate(adder))
def HasDuplicateItem[T: HashableProtocol](items: Iterable[T]) -> INullable[T]:
    return __HasDuplicate(items, GetFirstItemExclusive, Self)

class Set[T: HashableProtocol](Mapping.Set[T]):
    def __init__(self, items: set[T]|None = None) -> None:
        super().__init__()

        self.__set: set[T] = set[T]() if items is None else items
    
    @final
    def __TryAdd(self, item: T) -> int:
        count: int = self.GetCount()
        
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
    def TryAddRange(self, items: Iterable[T]) -> bool:
        _items: IEnumerableQueue[T] = CreateEnumerableQueue(items)

        for item in _items.AsIterable():
            if self.Contains(item): return False
        
        count: int = self.GetCount()
        
        self._GetItems().update(_items.AsGenerator())
    
        return count < self.GetCount()
    
    @final
    def TryRemove(self, item: T) -> bool:
        count: int = self.GetCount()

        self._GetItems().discard(item)

        return self.GetCount() < count
    
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
        self.__iterator: Iterator[tuple[TKey, TValue]]|None = None
        self.__current: INullable[IKeyValuePair[TKey, TValue]] = GetNullValue()
    
    def IsResetSupported(self) -> bool: return True
    
    def _OnStarting(self) -> bool:
        if super()._OnStarting():
            self.__iterator = Iterator(self.__dictionary.items().__iter__())
            
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
    
    def _ResetOverride(self) -> bool: return True

class DictionaryEnumerable[TKey: HashableProtocol, TValue, TItem](CountableEnumerable[TItem]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetDictionary(self) -> IDictionary[TKey, TValue]:
        ...

    @final
    def IsResumable(self) -> bool|None: return True
    
    @final
    def IsEmpty(self) -> bool: return self._GetDictionary().IsEmpty()
    
    @final
    def GetCount(self) -> int: return self._GetDictionary().GetCount()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None: return TryAsEnumerator(self._TryGetIterator())

@final
class _None(Abstract):
    def __init__(self) -> None: super().__init__()

__none: _None = _None()

def _GetNoneInstance() -> _None:
    return __none

# TODO: Should inherit from MutableMapping
class Dictionary[TKey: HashableProtocol, TValue](Mapping.DictionaryBase[TKey, TValue]):
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
        
        def _TryGetIterator(self) -> _Iterator[_TKey]|None: return iter(self._GetInnerDictionary().keys())
    @final
    class _ValueEnumerable[_TKey: HashableProtocol, _TValue](_Enumerable[_TKey, _TValue, _TValue]):
        def __init__(self, dic: Dictionary[_TKey, _TValue]) -> None: super().__init__(dic)
        
        def _TryGetIterator(self) -> _Iterator[_TValue]|None: return iter(self._GetInnerDictionary().values())
    
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
        result: TValue|_None = self._GetDictionary().get(key, _GetNoneInstance())

        return GetNullValue() if isinstance(result, _None) else GetNullable(result)
    
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
    def TryRemoveItem(self, key: TKey) -> INullable[TValue]:
        result: TValue|_None = self._GetDictionary().pop(key, _GetNoneInstance())

        return GetNullValue() if isinstance(result, _None) else GetNullable(result)
    
    @final
    def Clear(self) -> None: self._GetDictionary().clear()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[IKeyValuePair[TKey, TValue]]: return DictionaryEnumerator[TKey, TValue](self._GetDictionary())
    
    def ToString(self) -> str: return str(self._GetDictionary())

def __CreateSet[T: HashableProtocol](items: set[T]|None = None) -> ISet[T]:
    return Set[T](items)
def __TryCreateSet[T: HashableProtocol](items: set[T]|Iterable[T]) -> DualResult[INullable[T], ISet[T]|None]:
    def createSet(items: set[T]) -> DualResult[INullable[T], ISet[T]]: return DualResult[INullable[T], ISet[T]](GetNullValue(), __CreateSet(items))

    if isinstance(items, set): return createSet(items)

    duplicate: INullable[T] = HasDuplicateItem(items if isinstance(items, Collection) else (items := CreateEnumerableQueue(items)))

    return CreateDualResult(duplicate, None) if duplicate.HasValue() else createSet(set[T](items))

@overload
def TryCreateSetInfo[T: HashableProtocol](items: set[T]|Iterable[T]) -> DualResult[INullable[T], ISet[T]|None]: ...
@overload
def TryCreateSetInfo(items: None) -> None: ...

def TryCreateSetInfo[T: HashableProtocol](items: set[T]|Iterable[T]|None) -> DualResult[INullable[T], ISet[T]|None]|None:
    return None if items is None else __TryCreateSet(items)

@overload
def TryCreateSet[T: HashableProtocol](items: set[T]|Iterable[T]) -> INullable[ISet[T]]: ...
@overload
def TryCreateSet(items: None) -> None: ...

def TryCreateSet[T: HashableProtocol](items: set[T]|Iterable[T]|None) -> INullable[ISet[T]]|None:
    return None if items is None else GetNullableValue(__TryCreateSet(items).GetValue())

def CreateSet[T: HashableProtocol](items: set[T]|Iterable[T]|None = None) -> ISet[T]:
    if items is None: return __CreateSet()

    result: DualResult[INullable[T], ISet[T]|None] = __TryCreateSet(items)

    _items: ISet[T]|None = result.GetValue()

    if _items is None: raise KeyError(f"Item '{result.GetKey().GetValue()}' has a duplicate.")

    return _items

def TryMakeSetInfo[T: HashableProtocol](*items: T) -> DualResult[INullable[T], ISet[T]|None]:
    return TryCreateSetInfo(items)
def TryMakeSet[T: HashableProtocol](*items: T) -> ISet[T]|None:
    return TryCreateSet(items).TryGetValue()

def MakeSet[T: HashableProtocol](*items: T) -> ISet[T]:
    return CreateSet(items)

def CreateDictionary[TKey: HashableProtocol, TValue](dictionary: MutableMapping[TKey, TValue]|None = None) -> IDictionary[TKey, TValue]:
    return Dictionary[TKey, TValue](dictionary)

def GetSet[T: HashableProtocol](items: ISet[T]|set[T]|Iterable[T]|None = None) -> ISet[T]:
    return items if isinstance(items, ISet) else CreateSet(items)
def GetDictionary[TKey: HashableProtocol, TValue](dictionary: IDictionary[TKey, TValue]|MutableMapping[TKey, TValue]|None = None) -> IDictionary[TKey, TValue]:
    return dictionary if isinstance(dictionary, IDictionary) else CreateDictionary(dictionary)