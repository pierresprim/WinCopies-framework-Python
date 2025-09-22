import collections.abc

from collections.abc import Iterator, Sequence, MutableSequence
from typing import final, Callable

from WinCopies import IStringable
from WinCopies.Collections import Enumeration, Extensions, Generator, IndexOf
from WinCopies.Collections.Enumeration import IEnumerator, EnumeratorBase
from WinCopies.Collections.Extensions import IDictionary, ISet
from WinCopies.Typing import GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation, INullable, IEquatableItem, GetNullable, GetNullValue
from WinCopies.Typing.Decorators import Singleton, GetSingletonInstanceProvider
from WinCopies.Typing.Delegate import Function, EqualityComparison
from WinCopies.Typing.Pairing import IKeyValuePair, KeyValuePair

class TupleBase[TItem, TSequence](GenericConstraint[TSequence, Sequence[TItem]], IStringable):
    def __init__(self, items: TSequence):
        super().__init__()

        self.__items: TSequence = items
    
    @final
    def _GetContainer(self) -> TSequence:
        return self.__items
    
    @final
    def GetCount(self) -> int:
        return len(self._GetInnerContainer())
    
    @final
    def GetAt(self, key: int) -> TItem:
        return self._GetInnerContainer()[key]

class Tuple[T](TupleBase[T, tuple[T, ...]], Extensions.Tuple[T], IGenericConstraintImplementation[tuple[T, ...]]):
    def __init__(self, items: tuple[T]|collections.abc.Iterable[T]):
        super().__init__(items if isinstance(items, tuple) else tuple(items))
    
    def ToString(self) -> str:
        return str(self._GetContainer())
class EquatableTuple[T: IEquatableItem](TupleBase[T, tuple[T, ...]], Extensions.EquatableTuple[T], IGenericConstraintImplementation[tuple[T, ...]]):
    def __init__(self, items: tuple[T]|collections.abc.Iterable[T]):
        super().__init__(items if isinstance(items, tuple) else tuple(items))
    
    def Hash(self) -> int:
        return hash(self._GetContainer())
    
    def Equals(self, item: object) -> bool:
        return self is item
    
    def ToString(self) -> str:
        return str(self._GetContainer())

class ArrayBase[TItem, TSequence](TupleBase[TItem, TSequence], GenericSpecializedConstraint[TSequence, Sequence[TItem], MutableSequence[TItem]]):
    def __init__(self, items: TSequence):
        super().__init__(items)
    
    @final
    def SetAt(self, key: int, value: TItem) -> None:
        self._GetSpecializedContainer()[key] = value

class Array[T](ArrayBase[T, MutableSequence[T]], Extensions.Array[T], IGenericSpecializedConstraintImplementation[Sequence[T], MutableSequence[T]]):
    def __init__(self, items: MutableSequence[T]|collections.abc.Iterable[T]):
        super().__init__(items if isinstance(items, MutableSequence) else list(items))
    
    def ToString(self) -> str:
        return str(self._GetContainer())

class List[T](ArrayBase[T, list[T]], Extensions.List[T], IGenericSpecializedConstraintImplementation[Sequence[T], list[T]]):
    def __init__(self, items: list[T]|None = None):
        super().__init__(list[T]() if items is None else items)
    
    @final
    def Add(self, item: T) -> None:
        self._GetContainer().append(item)
    
    @final
    def TryInsert(self, index: int, value: T) -> bool:
        if self.ValidateIndex(index):
            self._GetContainer().insert(index, value)
            
            return True
        
        return False
    
    @final
    def RemoveAt(self, index: int) -> None:
        self._GetContainer().pop(index)
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
        items: list[T] = self._GetContainer()

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
        self._GetContainer().clear()
    
    def ToString(self) -> str:
        return str(self._GetContainer())

class Dictionary[TKey: IEquatableItem, TValue](IDictionary[TKey, TValue]):
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
    def __TryAdd(self, key: TKey, value: TValue) -> int:
        count = self.GetCount()
        
        self._GetDictionary().setdefault(key, value)
    
        return count
    
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
    def TrySetAt(self, key: TKey, value: TValue) -> bool:
        if key in self.GetKeys():
            self._GetDictionary()[key] = value

            return True
        
        return False
    @final
    def SetAt(self, key: TKey, value: TValue) -> None:
        if not self.TrySetAt(key, value):
            raise KeyError(f"Key {key} does not exist.")
    
    @final
    def GetKeys(self) -> Generator[TKey]:
        yield from self._GetDictionary().keys()
    @final
    def GetValues(self) -> Generator[TValue]:
        yield from self._GetDictionary().values()
    
    @final
    def TryAdd(self, key: TKey, value: TValue) -> bool:
        return self.__TryAdd(key, value) < self.GetCount()
    @final
    def TryAddItem(self, item: KeyValuePair[TKey, TValue]) -> bool:
        return self.TryAdd(item.GetKey(), item.GetValue())
    
    @final
    def Add(self, key: TKey, value: TValue) -> None:
        if self.__TryAdd(key, value) == self.GetCount():
            raise KeyError(f"Key {key} already exists.")
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
        self._GetDictionary().clear()
    
    @final
    def TryGetIterator(self) -> IEnumerator[IKeyValuePair[TKey, TValue]]:
        return Dictionary[TKey, TValue].Enumerator(self._GetDictionary())
    
    def ToString(self) -> str:
        return str(self._GetDictionary())

class Set[T: IEquatableItem](ISet[T]):
    def __init__(self, items: set[T]|None = None):
        super().__init__()

        self.__set: set[T] = set[T]() if items is None else items
    
    @final
    def __TryAdd(self, item: T) -> int:
        count = self.GetCount()
        
        self._GetItems().add(item)
    
        return count
    
    @final
    def _GetItems(self) -> set[T]:
        return self.__set
    
    @final
    def GetCount(self) -> int:
        return len(self._GetItems())
    
    @final
    def TryAdd(self, item: T) -> bool:
        return self.__TryAdd(item) < self.GetCount()
    @final
    def Add(self, item: T) -> None:
        if self.__TryAdd(item) == self.GetCount():
            raise ValueError(f"Item {item} already exists.")
    
    @final
    def Remove(self, item: T) -> None:
        self._GetItems().remove(item)
    @final
    def TryRemove(self, item: T) -> bool:
        try:
            self.Remove(item)

            return True
        
        except KeyError:
            return False
    
    @final
    def TryGetIterator(self) -> Iterator[T]|None:
        yield from self._GetItems()
    
    @final
    def Clear(self) -> None:
        self._GetItems().clear()
    
    def ToString(self) -> str:
        return str(self._GetItems())