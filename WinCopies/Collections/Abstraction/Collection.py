from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence, MutableSequence, MutableMapping
from typing import overload, final, Callable, SupportsIndex

from WinCopies import IStringable
from WinCopies.Collections import Enumeration, Extensions
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEnumerator, CountableEnumerable, EnumeratorBase, TryAsEnumerator
from WinCopies.Collections.Extensions import ITuple, IEquatableTuple, IArray, IList
from WinCopies.Typing import GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation, INullable, IEquatableItem, GetNullable, GetNullValue
from WinCopies.Typing.Decorators import Singleton, GetSingletonInstanceProvider
from WinCopies.Typing.Delegate import Function
from WinCopies.Typing.Pairing import IKeyValuePair, KeyValuePair, DualValueBool

class TupleBase[TItem, TSequence](Extensions.Sequence[TItem], Extensions.Tuple[TItem], GenericConstraint[TSequence, Sequence[TItem]], IStringable):
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
    def _GetAt(self, key: int) -> TItem:
        return self._GetInnerContainer()[key]
    
    @final
    def Contains(self, value: TItem|object) -> bool:
        return value in self._GetInnerContainer()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TItem: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[TItem]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TItem|Sequence[TItem]:
        return self._GetInnerContainer()[int(index) if isinstance(index, SupportsIndex) else index]

class Tuple[T](TupleBase[T, Sequence[T]], IGenericConstraintImplementation[Sequence[T]]):
    def __init__(self, items: tuple[T]|Iterable[T]):
        super().__init__(items if isinstance(items, tuple) else tuple(items))
    
    @final
    def SliceAt(self, key: slice) -> ITuple[T]:
        return Tuple[T](self._GetContainer()[key])
    
    def ToString(self) -> str:
        return str(self._GetContainer())
class EquatableTuple[T: IEquatableItem](TupleBase[T, tuple[T, ...]], Extensions.EquatableTuple[T], IGenericConstraintImplementation[tuple[T, ...]]):
    def __init__(self, items: tuple[T]|Iterable[T]):
        super().__init__(items if isinstance(items, tuple) else tuple(items))
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        return EquatableTuple[T](self._GetContainer()[key])
    
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
    def __init__(self, items: MutableSequence[T]|Iterable[T]):
        super().__init__(items if isinstance(items, MutableSequence) else list(items))
    
    @final
    def SliceAt(self, key: slice) -> IArray[T]:
        return Array[T](self._GetContainer()[key])
    
    def ToString(self) -> str:
        return str(self._GetContainer())

class List[T](ArrayBase[T, list[T]], Extensions.MutableSequence[T], Extensions.List[T], IGenericSpecializedConstraintImplementation[Sequence[T], list[T]]):
    def __init__(self, items: list[T]|None = None):
        super().__init__(list[T]() if items is None else items)
    
    @final
    def SliceAt(self, key: slice) -> IList[T]:
        return List[T](self._GetContainer()[key])
    
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
    def TryRemoveAt(self, index: int) -> bool|None:
        if index < 0:
            return None
        
        if index >= self.GetCount():
            return False
        
        self._GetContainer().pop(index)
        
        return True
    
    @final
    def Clear(self) -> None:
        self._GetContainer().clear()
    
    def ToString(self) -> str:
        return str(self._GetContainer())
    
    @final
    def insert(self, index: int, value: T) -> None:
        self._GetContainer().insert(index, value)
    
    @overload
    def __setitem__(self, index: SupportsIndex, value: T) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: T|Iterable[T]) -> None:
        self._GetContainer()[index] = value # type: ignore
    
    @final
    def __delitem__(self, index: int|slice):
        del self._GetContainer()[index]

# TODO: Should inherit from MutableMapping
class Dictionary[TKey: IEquatableItem, TValue](Extensions.Dictionary[TKey, TValue]):
    class __Enumerable[T](CountableEnumerable[T]):
        def __init__(self, dic: Dictionary[TKey, TValue]):
            super().__init__()

            self.__dic: Dictionary[TKey, TValue] = dic
        
        @final
        def _GetDictionary(self) -> MutableMapping[TKey, TValue]:
            return self.__dic._GetDictionary()
        
        @final
        def GetCount(self) -> int:
            return self.__dic.GetCount()
        
        @final
        def TryGetEnumerator(self) -> IEnumerator[T]|None:
            return TryAsEnumerator(self._TryGetIterator())
    @final
    class __KeyEnumerable(__Enumerable[TKey]):
        def __init__(self, dic: Dictionary[TKey, TValue]):
            super().__init__(dic)
        
        def _TryGetIterator(self) -> Iterator[TKey]|None:
            return iter(self._GetDictionary().keys())
    @final
    class __ValueEnumerable(__Enumerable[TValue]):
        def __init__(self, dic: Dictionary[TKey, TValue]):
            super().__init__(dic)
        
        def _TryGetIterator(self) -> Iterator[TValue]|None:
            return iter(self._GetDictionary().values())
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
        
        def __init__(self, dictionary: MutableMapping[TKey, TValue]):
            super().__init__()

            self.__dictionary: MutableMapping[TKey, TValue] = dictionary
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
    
    def __init__(self, dictionary: MutableMapping[TKey, TValue]|None = None):
        super().__init__()

        self.__dictionary: MutableMapping[TKey, TValue] = dict[TKey, TValue]() if dictionary is None else dictionary
        self.__keys: ICountableEnumerable[TKey] = Dictionary[TKey, TValue].__KeyEnumerable(self)
        self.__values: ICountableEnumerable[TValue] = Dictionary[TKey, TValue].__ValueEnumerable(self)
    
    @final
    def __TryAdd(self, key: TKey, value: TValue) -> int:
        count = self.GetCount()
        
        self._GetDictionary().setdefault(key, value)
    
        return count
    
    @final
    def _GetDictionary(self) -> MutableMapping[TKey, TValue]:
        return self.__dictionary
    
    @final
    def GetCount(self) -> int:
        return len(self._GetDictionary())
    
    @final
    def ContainsKey(self, key: TKey) -> bool:
        return key in self._GetDictionary()
    
    @final
    def TryGetAt[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValue|TDefault]:
        result: TValue|Dictionary[TKey, TValue].__None = self._GetDictionary().get(key, Dictionary[TKey, TValue].__getInstance()) # type: ignore

        return DualValueBool[TDefault](defaultValue, False) if isinstance(result, Dictionary[TKey, TValue].__None) else DualValueBool[TValue](result, True)
    
    @final
    def TrySetAt(self, key: TKey, value: TValue) -> bool:
        if key in self.GetKeys().AsIterable():
            self._GetDictionary()[key] = value

            return True
        
        return False
    
    @final
    def __TryGetValue(self, func: Callable[[dict[TKey, TValue], Dictionary.__None], TValue|Dictionary.__None]) -> INullable[TValue]:
        result: TValue|Dictionary.__None = func(self._GetDictionary(), Dictionary.__getInstance()) # type: ignore

        return GetNullValue() if isinstance(result, Dictionary.__None) else GetNullable(result)
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TValue]:
        return self.__TryGetValue(lambda dic, default: dic.get(key, default))
    
    @final
    def GetKeys(self) -> ICountableEnumerable[TKey]:
        return self.__keys
    @final
    def GetValues(self) -> ICountableEnumerable[TValue]:
        return self.__values
    
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
    def TryGetEnumerator(self) -> IEnumerator[IKeyValuePair[TKey, TValue]]:
        return Dictionary[TKey, TValue].Enumerator(self._GetDictionary())
    
    def ToString(self) -> str:
        return str(self._GetDictionary())

class Set[T: IEquatableItem](Extensions.Set[T]):
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
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return TryAsEnumerator(item for item in self._GetItems())
    
    @final
    def Clear(self) -> None:
        self._GetItems().clear()
    
    def ToString(self) -> str:
        return str(self._GetItems())