from __future__ import annotations

import collections.abc

from collections.abc import Iterator
from typing import final, Callable, Self

from WinCopies.Collections import Enumeration, Extensions, Generator, ICountable, IDictionary, IndexOf
from WinCopies.Collections.Enumeration import IIterable, ICountableIterable, IEnumerator, EnumeratorBase
from WinCopies.Typing import EnsureDirectModuleCall
from WinCopies.Typing.Decorators import Singleton, GetSingletonInstanceProvider
from WinCopies.Typing.Delegate import Function, Predicate
from WinCopies.Typing.Pairing import IKeyValuePair, KeyValuePair, DualNullableValueBool

class Array[T](Extensions.Array[T]):
    def __init__(self, items: tuple[T, ...]|collections.abc.Iterable[T]):
        super().__init__()

        self.__tuple: tuple[T] = items if isinstance(items, tuple) else tuple(items)
    
    def _GetTuple(self) -> tuple[T]:
        return self.__tuple
    
    @final
    def GetCount(self) -> int:
        return len(self._GetTuple())
    
    @final
    def GetAt(self, index: int) -> T:
        return self._GetTuple()[index]

class List[T](Extensions.List[T]):
    def __init__(self, items: list[T]|None = None):
        super().__init__()

        self.__list: list[T] = list[T]() if items is None else items
    
    @final
    def _GetList(self) -> list[T]:
        return self.__list
    
    @final
    def GetCount(self) -> int:
        return len(self._GetList())
    
    @final
    def GetAt(self, index: int) -> T:
        return self._GetList()[index]
    @final
    def SetAt(self, index: int, value: T) -> None:
        self._GetList()[index] = value
    
    @final
    def Add(self, item: T) -> None:
        self._GetList().append(item)
    
    @final
    def RemoveAt(self, index: int) -> None:
        self._GetList().pop(index)
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        if index < 0:
            return None
        
        if index >= self.GetCount():
            return False
        
        self.RemoveAt(index)
        
        return True
    
    @final
    def TryRemove(self, item: T, predicate: Predicate[T]|None = None) -> bool:
        items: list[T] = self._GetList()

        index: int|None = IndexOf(items, item, predicate)

        if index is None:
            return False
        
        items.pop(index)

        return True
    @final
    def Remove(self, item: T, predicate: Predicate[T]|None = None) -> None:
        if not self.TryRemove(item, predicate):
            raise ValueError(item)
    
    @final
    def Clear(self) -> None:
        self._GetList().clear()

class Dictionary[TKey, TValue](IDictionary[TKey, TValue]):
    @final
    class Enumerator(EnumeratorBase[IKeyValuePair[TKey, TValue]]):
        @final
        class KeyValuePair(IKeyValuePair[TKey, TValue]):
            def __init__(self, item: tuple[TKey, TValue]):
                self.__item: tuple[TKey, TValue] = item
            
            @final
            def IsKeyValuePair(self) -> bool:
                return True
            
            @final
            def GetKey(self) -> TKey:
                return self.__item[0]
            @final
            def GetValue(self) -> TValue:
                return self.__item[1]
    
            @final
            def _Equals(self, item: IKeyValuePair[TKey, TValue]) -> bool:
                return isinstance(item, Dictionary.Enumerator.KeyValuePair)
        
        def __init__(self, dictionary: dict[TKey, TValue]):
            super().__init__()

            self.__dictionary: dict[TKey, TValue] = dictionary
            self.__iterator: Enumeration.Iterator[tuple[TKey, TValue]]|None = None
            self.__current: IKeyValuePair[TKey, TValue]|None = None
        
        def IsResetSupported(self) -> bool:
            return True
        
        def _OnStarting(self) -> bool:
            if super()._OnStarting():
                self.__iterator = Enumeration.Iterator(self.__dictionary.items().__iter__())
                
                return True
            
            return False
        
        def _MoveNextOverride(self) -> bool:
            if self.__iterator.MoveNext():
                item: tuple[TKey, TValue] = self.__iterator.GetCurrent()

                self.__current = Dictionary.Enumerator.KeyValuePair(item)

                return True
            
            return False
        
        def GetCurrent(self) -> IKeyValuePair[TKey, TValue]:
            return self.__current
        
        def _OnEnded(self) -> None:
            self.__iterator = None
            self.__current = None

            super()._OnEnded()
        
        def _OnStopped(self) -> None:
            pass
        
        def _ResetOverride(self) -> bool:
            return True
    
    @final
    class __None(Singleton[Self]):
        def __init__(self):
            super().__init__()

    __getInstance: Function[Dictionary.__None] = GetSingletonInstanceProvider(__None)
    
    def __init__(self, dictionary: dict[TKey, TValue]|None = None):
        super().__init__()

        self.__dictionary: dict[TKey, TValue] = dict[TKey, TValue]() if dictionary is None else dictionary
    
    @final
    def _GetDictionary(self) -> dict[TKey, TValue]:
        return self.__dictionary
    
    @final
    def GetCount(self) -> int:
        return len(self._GetDictionary())
    
    @final
    def ContainsKey(self, key: TKey) -> bool:
        return key in self._GetDictionary()
    
    @final
    def __TryGetValue(self, func: Callable[[dict[TKey, TValue], Dictionary.__None], TValue|Dictionary.__None]) -> DualNullableValueBool[TValue]:
        def getResult(value: TValue|None, info: bool) -> DualNullableValueBool[TValue]:
            return DualNullableValueBool[TValue](value, info)
        
        result: TValue|Dictionary.__None = func(self._GetDictionary(), Dictionary.__getInstance())

        return getResult(None, False) if isinstance(result, Dictionary.__None) else getResult(result, True)
    
    @final
    def TryGetValue(self, key: TKey) -> DualNullableValueBool[TValue]:
        return self.__TryGetValue(lambda dic, default: dic.get(key, default))
    
    @final
    def GetAt(self, key: TKey) -> TValue:
        return self._GetDictionary()[key]
    @final
    def TryGetAt[TDefault](self, key: TKey, defaultValue: TDefault) -> TValue|TDefault:
        return self._GetDictionary().get[TDefault](key, defaultValue)
    
    @final
    def SetAt(self, key: TKey, value: TValue) -> None:
        self._GetDictionary()[key] = value
    @final
    def TrySetAt(self, key: TKey, value: TValue) -> bool:
        self.SetAt(key, value)

        return True
    
    @final
    def GetKeys(self) -> Generator[TKey]:
        for key in self._GetDictionary().keys():
            yield key
    @final
    def GetValues(self) -> Generator[TValue]:
        for value in self._GetDictionary().values():
            yield value
    
    @final
    def Add(self, key: TKey, value: TValue) -> None:
        self._GetDictionary()[key] = value
    @final
    def AddItem(self, item: KeyValuePair[TKey, TValue]) -> None:
        self.Add(item.GetKey(), item.GetValue())

    @final
    def Remove(self, key: TKey) -> None:
        self._GetDictionary().pop(key)
    
    @final
    def TryRemove[TDefault](self, key: TKey, defaultValue: TDefault) -> TValue|TDefault:
        return self._GetDictionary().pop(key, defaultValue)
    @final
    def TryRemoveValue(self, key: TKey) -> DualNullableValueBool[TValue]:
        return self.__TryGetValue(lambda dic, default: dic.pop(key, default))
    
    @final
    def Clear(self) -> None:
        return self._GetDictionary().clear()
    
    @final
    def TryGetIterator(self) -> IEnumerator[IKeyValuePair[TKey, TValue]]:
        return Dictionary.Enumerator(self._GetDictionary())
    
    def __str__(self) -> str:
        return str(self._GetDictionary())

class Countable(ICountable):
    def __init__(self, collection: ICountable):
        EnsureDirectModuleCall()

        super().__init__()

        self.__collection: ICountable = collection
    
    @final
    def GetCount(self) -> int:
        return self.__collection.GetCount()
    
    @staticmethod
    def Create(collection: ICountable) -> ICountable:
        return collection if type(collection) == Countable else Countable(collection)

class IterableBase[TIterable: IIterable[TItems], TItems](IIterable[TItems]):
    def __init__(self, iterable: TIterable):
        EnsureDirectModuleCall()

        super().__init__()

        self.__iterable: IIterable[TItems] = iterable
    
    @final
    def _GetIterable(self) -> TIterable:
        return self.__iterable
    
    @final
    def TryGetIterator(self) -> Iterator[TItems]|None:
        return self._GetIterable().TryGetIterator()
class Iterable[T](IterableBase[IIterable[T], T]):
    def __init__(self, iterable: IIterable[T]):
        super().__init__(iterable)
    
    @staticmethod
    def Create(iterable: collections.abc.Iterable[T]) -> collections.abc.Iterable[T]:
        return iterable if type(iterable) == Iterable else Iterable(iterable)

class CountableIterable[T](IterableBase[ICountableIterable[T], T], ICountable):
    def __init__(self, collection: ICountableIterable[T]):
        super().__init__(collection)
    
    @final
    def GetCount(self) -> int:
        return self._GetIterable().GetCount()

    @staticmethod
    def Create(collection: ICountableIterable[T]) -> ICountableIterable[T]:
        return collection if type(collection) == CountableIterable else CountableIterable(collection)