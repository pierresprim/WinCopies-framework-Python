from __future__ import annotations

from collections.abc import Iterator
from typing import Callable, Self

from WinCopies.Collections import Collection
from WinCopies.Typing.Delegate import Function
from WinCopies.Typing.Decorators import Singleton, GetSingletonInstanceProvider
from WinCopies.Typing.Pairing import DualNullableValueBool

class Dictionary[TKey, TValue](Collection):
    class __None(Singleton[Self]):
        pass

    __getInstance: Function[Dictionary.__None]|None = GetSingletonInstanceProvider(__None)
    
    def __init__(self, items: dict[TKey, TValue]|None = None):
        self.__items: dict[TKey, TValue] = dict[TKey, TValue]() if items is None else items
    
    def _GetItems(self) -> dict[TKey, TValue]:
        return self.__items
    
    def IsEmpty(self) -> bool:
        return len(self._GetItems()) == 0
    
    def ContainsKey(self, key: TKey) -> bool:
        return key in self._GetItems()
    
    def GetKeys(self) -> Iterator[TKey]:
        for key in self._GetItems().keys():
            yield key
    
    def GetValues(self) -> Iterator[TValue]:
        for value in self._GetItems().values():
            yield value
    
    def __TryGetValue(self, func: Callable[[dict[TKey, TValue], Dictionary.__None], TValue|Dictionary.__None]) -> DualNullableValueBool[TValue]:
        def getResult(value: TValue|None, info: bool) -> DualNullableValueBool[TValue]:
            return DualNullableValueBool[TValue](value, info)
        
        result: TValue|Dictionary.__None = func(self._GetItems(), Dictionary.__getInstance())

        return getResult(None, False) if isinstance(result, Dictionary.__None) else getResult(result, True)
    
    def TryGetValue(self, key: TKey) -> DualNullableValueBool[TValue]:
        return self.__TryGetValue(lambda dic, default: dic.get(key, default))
    
    def SetValue(self, key: TKey, value: TValue) -> None:
        self._GetItems()[key] = value
    
    def TryRemove(self, key: TKey) -> DualNullableValueBool[TValue]:
        return self.__TryGetValue(lambda dic, default: dic.pop(key, default))
    
    def __str__(self) -> str:
        return str(self._GetItems())