import collections.abc

from collections.abc import Sequence
from typing import final, Callable

from WinCopies.Collections import Enumeration, Extensions, Generator, IndexOf
from WinCopies.Collections.Enumeration import IEnumerator, EnumeratorBase
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Decorators import Singleton, GetSingletonInstanceProvider
from WinCopies.Typing.Delegate import Function, EqualityComparison
from WinCopies.Typing.Pairing import IKeyValuePair, KeyValuePair

class Array[T](Extensions.Array[T]):
    def __init__(self, items: Sequence[T]|collections.abc.Iterable[T]):
        super().__init__()

        self.__sequence: Sequence[T] = items if isinstance(items, Sequence) else tuple(items)
    
    def _GetSequence(self) -> Sequence[T]:
        return self.__sequence
    
    @final
    def GetCount(self) -> int:
        return len(self._GetSequence())
    
    @final
    def GetAt(self, key: int) -> T:
        return self._GetSequence()[key]

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
    def GetAt(self, key: int) -> T:
        return self._GetList()[key]
    @final
    def SetAt(self, key: int, value: T) -> None:
        self._GetList()[key] = value
    
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
    def TryRemove(self, item: T, predicate: EqualityComparison[T]|None = None) -> bool:
        items: list[T] = self._GetList()

        index: int|None = IndexOf(items, item, predicate)

        if index is None:
            return False
        
        items.pop(index)

        return True
    @final
    def Remove(self, item: T, predicate: EqualityComparison[T]|None = None) -> None:
        if not self.TryRemove(item, predicate):
            raise ValueError(item)
    
    @final
    def Clear(self) -> None:
        self._GetList().clear()

class Dictionary[TKey, TValue](Extensions.IDictionary[TKey, TValue]):
    @final
    class Enumerator(EnumeratorBase[IKeyValuePair[TKey, TValue]]):
        @final
        class KeyValuePair(IKeyValuePair[TKey, TValue]):
            def __init__(self, item: tuple[TKey, TValue]):
                super().__init__()
                
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
            def _Equals(self, item: IKeyValuePair[TKey, TValue]|object) -> bool:
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
            if self.__iterator is None:
                return False
            
            if self.__iterator.MoveNext():
                item: tuple[TKey, TValue]|None = self.__iterator.GetCurrent()

                if item is None:
                    return False

                self.__current = Dictionary.Enumerator.KeyValuePair(item)

                return True
            
            return False
        
        def GetCurrent(self) -> IKeyValuePair[TKey, TValue]|None:
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
    class __None(Singleton):
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
    def __TryGetValue(self, func: Callable[[dict[TKey, TValue], Dictionary.__None], TValue|Dictionary.__None]) -> INullable[TValue]:
        result: TValue|Dictionary.__None = func(self._GetDictionary(), Dictionary.__getInstance()) # type: ignore

        return GetNullValue() if isinstance(result, Dictionary.__None) else GetNullable(result)
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TValue]:
        return self.__TryGetValue(lambda dic, default: dic.get(key, default))
    
    @final
    def GetAt(self, key: TKey) -> TValue:
        return self._GetDictionary()[key]
    @final
    def TryGetAt[TDefault](self, key: TKey, defaultValue: TDefault) -> TValue|TDefault:
        return self._GetDictionary().get(key, defaultValue)
    
    @final
    def SetAt(self, key: TKey, value: TValue) -> None:
        self._GetDictionary()[key] = value
    @final
    def TrySetAt(self, key: TKey, value: TValue) -> bool:
        self.SetAt(key, value)

        return True
    
    @final
    def GetKeys(self) -> Generator[TKey]:
        yield from self._GetDictionary().keys()
    @final
    def GetValues(self) -> Generator[TValue]:
        yield from self._GetDictionary().values()
    
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
    def TryRemoveValue(self, key: TKey) -> INullable[TValue]:
        return self.__TryGetValue(lambda dic, default: dic.pop(key, default))
    
    @final
    def Clear(self) -> None:
        return self._GetDictionary().clear()
    
    @final
    def TryGetIterator(self) -> IEnumerator[IKeyValuePair[TKey, TValue]]:
        return Dictionary[TKey, TValue].Enumerator(self._GetDictionary())
    
    def __str__(self) -> str:
        return str(self._GetDictionary())