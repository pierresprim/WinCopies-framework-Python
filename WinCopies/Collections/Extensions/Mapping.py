from __future__ import annotations

from abc import abstractmethod
from collections.abc import Container as ContainerBase
from typing import overload, final



from WinCopies.Collections.Abstraction.Enumeration import TryCreateEnumerator
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEnumerator, CountableEnumerable
from WinCopies.Collections.Extensions import IReadOnlySet, ISet, IReadOnlyDictionary, IDictionary, Container

from WinCopies.Typing import INullable
from WinCopies.Typing.Comparison import HashableProtocol
from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Pairing import IKeyValuePair, KeyValuePair, DualValueBool

@final
class _SetContainer[T: HashableProtocol](Container[T]):
    def __init__(self, items: IReadOnlySet[T]) -> None:
        super().__init__()

        self.__items: IReadOnlySet[T] = items
    
    def Contains(self, value: T|object) -> bool: return self.__items.Contains(value)
@final
class _ReadOnlySetContainerUpdater[T: HashableProtocol](ValueFunctionUpdater[ContainerBase[T]]):
    def __init__(self, items: _ReadOnlySet[T], updater: Method[IFunction[ContainerBase[T]]]) -> None:
        super().__init__(updater)

        self.__items: _ReadOnlySet[T] = items
    
    def _GetValue(self) -> ContainerBase[T]: return _SetContainer[T](self.__items)

class _ReadOnlySet[T: HashableProtocol](CountableEnumerable[T], IReadOnlySet[T]):
    def __init__(self, items: IReadOnlySet[T]) -> None:
        def update(func: IFunction[ContainerBase[T]]) -> None: self.__container = func
        
        super().__init__()

        self.__set: IReadOnlySet[T] = items
        self.__container: IFunction[ContainerBase[T]] = _ReadOnlySetContainerUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def _GetItems(self) -> IReadOnlySet[T]:
        return self.__set
    
    @final
    def GetCount(self) -> int: return self._GetItems().GetCount()
    
    @final
    def Contains(self, value: T|object) -> bool: return self.__set.Contains(value)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return TryCreateEnumerator(self._GetItems().TryGetEnumerator())
    
    def ToString(self) -> str: return self._GetItems().ToString()
    
    @final
    def AsContainer(self) -> ContainerBase[T]: return self.__container.GetValue()
@final
class _ReadOnlySetUpdater[T: HashableProtocol](ValueFunctionUpdater[IReadOnlySet[T]]):
    def __init__(self, items: Set[T], updater: Method[IFunction[IReadOnlySet[T]]]) -> None:
        super().__init__(updater)

        self.__items: Set[T] = items
    
    def _GetValue(self) -> IReadOnlySet[T]: return _ReadOnlySet[T](self.__items)

class Set[T: HashableProtocol](CountableEnumerable[T], ISet[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IReadOnlySet[T]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlySet[T]] = _ReadOnlySetUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlySet[T]: return self.__readOnly.GetValue()
    
    @final
    def AsContainer(self) -> ContainerBase[T]: return self.AsReadOnly().AsContainer()

@final
class _ReadOnlyDictionary[TKey: HashableProtocol, TValue](CountableEnumerable[IKeyValuePair[TKey, TValue]], IReadOnlyDictionary[TKey, TValue]):
    # TODO: Should inherit from Mapping
    def __init__(self, dictionary: DictionaryAbstract[TKey, TValue]) -> None:
        super().__init__()

        self.__dictionary: DictionaryAbstract[TKey, TValue] = dictionary
    
    def IsEmpty(self) -> bool: return self.__dictionary.IsEmpty()
    
    def GetCount(self) -> int: return self.__dictionary.GetCount()
    
    def ContainsKey(self, key: TKey) -> bool: return self.__dictionary.ContainsKey(key)
    
    def TryGetValue(self, key: TKey) -> INullable[TValue]: return self.__dictionary.TryGetValue(key)
    
    def GetKeys(self) -> ICountableEnumerable[TKey]: return self.__dictionary.GetKeys()
    def GetValues(self) -> ICountableEnumerable[TValue]: return self.__dictionary.GetValues()
    
    def TryGetEnumerator(self) -> IEnumerator[IKeyValuePair[TKey, TValue]]|None: return TryCreateEnumerator(self.__dictionary.TryGetEnumerator())
    
    def ToString(self) -> str: return self.__dictionary.ToString()
@final
class _ReadOnlyDictionaryUpdater[TKey: HashableProtocol, TValue](ValueFunctionUpdater[IReadOnlyDictionary[TKey, TValue]]):
    def __init__(self, dictionary: DictionaryAbstract[TKey, TValue], updater: Method[IFunction[IReadOnlyDictionary[TKey, TValue]]]) -> None:
        super().__init__(updater)

        self.__dictionary: DictionaryAbstract[TKey, TValue] = dictionary
    
    def _GetValue(self) -> IReadOnlyDictionary[TKey, TValue]: return _ReadOnlyDictionary[TKey, TValue](self.__dictionary)

class DictionaryAbstract[TKey: HashableProtocol, TValue](CountableEnumerable[IKeyValuePair[TKey, TValue]], IDictionary[TKey, TValue]):
    # TODO: Should inherit from Mapping
    def __init__(self) -> None:
        def update(func: IFunction[IReadOnlyDictionary[TKey, TValue]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyDictionary[TKey, TValue]] = _ReadOnlyDictionaryUpdater[TKey, TValue](self, update) # type: ignore[no-redef]
    
    @abstractmethod
    def _TryRemove[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValue|TDefault]:
        ...
    
    @final
    def IsEmpty(self) -> bool: return self.GetCount() < 1
    
    @overload
    def TryRemove[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValue|TDefault]:
        ...
    @overload
    def TryRemove(self, key: TKey, defaultValue: None = None) -> DualValueBool[TValue]|None:
        ...

    @final
    def TryRemove[TDefault](self, key: TKey, defaultValue: TDefault|None = None) -> DualValueBool[TValue|TDefault]|None: return None if defaultValue is None else self._TryRemove(key, defaultValue)
    
    @final
    def AsReadOnly(self) -> IReadOnlyDictionary[TKey, TValue]: return self.__readOnly.GetValue()
class DictionaryBase[TKey: HashableProtocol, TValue](DictionaryAbstract[TKey, TValue]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def Move(self, x: TKey, y: TKey) -> None:
        def getValue() -> TValue:
            value: INullable[TValue] = self.TryRemoveItem(x)

            if value.HasValue(): return value.GetValue()
            
            raise KeyError(f"The key {x} does not exist.")

        self.Add(y, getValue())
class Dictionary[TKey: HashableProtocol, TValue](DictionaryBase[TKey, TValue]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def Add(self, key: TKey, value: TValue) -> None:
        if not self.TryAdd(key, value): raise KeyError(f"Key {key} already exists.")
    
    @final
    def TryAddItem(self, item: KeyValuePair[TKey, TValue]) -> bool: return self.TryAdd(item.GetKey(), item.GetValue())
    @final
    def AddItem(self, item: KeyValuePair[TKey, TValue]) -> None: self.Add(item.GetKey(), item.GetValue())
    
    @final
    def AddItemOrUpdate(self, item: KeyValuePair[TKey, TValue]) -> bool: return self.AddOrUpdate(item.GetKey(), item.GetValue())