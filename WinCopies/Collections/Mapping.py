from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import overload, final

from WinCopies.Collections.Core import ICountable, IGetter, ISwappableBase, IClearable, IReadOnlyCollection, IReadOnlyList, IEquatableTuple, IList
from WinCopies.Collections.Util import GetDuplicateKeyError, ThrowDuplicateKeyError, ThrowDuplicateItemError, ThrowDuplicateRangeError, ThrowKeyNotFoundError
from WinCopies.Typing import INullable
from WinCopies.Typing.Comparison import HashableProtocol
from WinCopies.Typing.Delegate import ItemComparison
from WinCopies.Typing.Pairing import KeyValuePair, DualValueBool

class IReadOnlySet[T: HashableProtocol](IReadOnlyList[T], ICountable):
    def __init__(self) -> None: super().__init__()
    
    @final
    def IsEmpty(self) -> bool: return self.GetCount() < 1
class ISet[T: HashableProtocol](IReadOnlySet[T], IClearable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlySet[T]:
        ...
    
    @abstractmethod
    def TryAdd(self, item: T) -> bool:
        ...
    @final
    def Add(self, item: T) -> None:
        if not self.TryAdd(item): ThrowDuplicateItemError(item)

    @abstractmethod
    def TryAddRange(self, items: Iterable[T]) -> bool|None:
        ...
    @final
    def AddRange(self, items: Iterable[T]) -> None:
        result: bool|None = self.TryAddRange(items)

        if result is None: ThrowDuplicateRangeError()

    @final
    def TryAddValues(self, *values: T) -> bool:
        return True if self.TryAddRange(values) is True else False
    @final
    def AddValues(self, *values: T) -> None:
        self.AddRange(values)
    
    @abstractmethod
    def TryRemove(self, item: T) -> bool:
        ...
    @final
    def Remove(self, item: T) -> None:
        if not self.TryRemove(item): ThrowKeyNotFoundError(item)

class IReadOnlyDictionary[TKey: HashableProtocol, TValue](IGetter[TKey, TValue], IReadOnlyCollection, ICountable):
    def __init__(self) -> None: super().__init__()
class IDictionary[TKey: HashableProtocol, TValue](IReadOnlyDictionary[TKey, TValue], ISwappableBase[TKey, TValue], IClearable):
    def __init__(self) -> None: super().__init__()

    @final
    def __ChangePosition(self, x: TKey, y: TKey, move: bool, updater: ItemComparison[TKey, None]) -> bool|None: return self._ChangePosition(x, y, lambda x, y: self.ValidateKeys(x, y, move), updater)

    def _GetKeysError(self, x: TKey, y: TKey) -> LookupError:
        return (GetDuplicateKeyError(y) if self.ContainsKey(y) else self._GetKeyNotFoundError(y)) if self.ContainsKey(x) else self._GetKeyNotFoundError(x)

    @final
    def ValidateKeys(self, x: TKey, y: TKey, move: bool = False) -> bool:
        return self.ContainsKey(x) and self.ContainsKey(y) != move

    @abstractmethod
    def _Move(self, x: TKey, y: TKey) -> None:
        ...
    @final
    def TryMove(self, x: TKey, y: TKey) -> bool|None: return self.__ChangePosition(x, y, True, self._Move)

    @final
    def TrySwap(self, x: TKey, y: TKey) -> bool|None: return self.__ChangePosition(x, y, False, self._Swap)
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyDictionary[TKey, TValue]:
        ...
    
    @abstractmethod
    def TryAdd(self, key: TKey, value: TValue) -> bool:
        ...
    @final
    def Add(self, key: TKey, value: TValue) -> None:
        if not self.TryAdd(key, value): ThrowDuplicateKeyError(key)

    @final
    def TryAddItem(self, item: KeyValuePair[TKey, TValue]) -> bool:
        return self.TryAdd(item.GetKey(), item.GetValue())
    @final
    def AddItem(self, item: KeyValuePair[TKey, TValue]) -> None:
        self.Add(item.GetKey(), item.GetValue())

    @abstractmethod
    def AddOrUpdate(self, key: TKey, value: TValue) -> bool:
        ...
    @final
    def AddItemOrUpdate(self, item: KeyValuePair[TKey, TValue]) -> bool:
        return self.AddOrUpdate(item.GetKey(), item.GetValue())

    @abstractmethod
    def TryRemoveItem(self, key: TKey) -> INullable[TValue]:
        ...
    
    @overload
    def TryRemove[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValue|TDefault]: ...
    @overload
    def TryRemove(self, key: TKey, defaultValue: None = None) -> DualValueBool[TValue|None]: ...

    @final
    def TryRemove[TDefault](self, key: TKey, defaultValue: TDefault|None = None) -> DualValueBool[TValue|TDefault|None]:
        result: INullable[TValue] = self.TryRemoveItem(key)

        return DualValueBool[TValue](result.GetValue(), True) if result.HasValue() else DualValueBool[TDefault|None](defaultValue, False)

    @final
    def Remove(self, key: TKey) -> TValue:
        result: INullable[TValue] = self.TryRemoveItem(key)

        if result.HasValue(): return result.GetValue()

        ThrowKeyNotFoundError(key)

class IReadOnlyOrderedSet[T: HashableProtocol](IReadOnlySet[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsTuple(self) -> IEquatableTuple[T]:
        ...
class IOrderedSet[T: HashableProtocol](ISet[T], IReadOnlyOrderedSet[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyOrderedSet[T]:
        ...

    @abstractmethod
    def AsList(self) -> IList[T]:
        ...