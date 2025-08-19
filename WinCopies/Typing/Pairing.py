from __future__ import annotations

from abc import abstractmethod
from typing import final, Self

from WinCopies.Typing import IEquatable
from WinCopies.Typing.BoolProvider import IBoolProvider, INullableBoolProvider

class IKeyValuePair[TKey, TValue](IEquatable[Self]): # type: ignore
    @abstractmethod
    def IsKeyValuePair(self) -> bool:
        pass

    @abstractmethod
    def GetKey(self) -> TKey:
        pass

    @abstractmethod
    def GetValue(self) -> TValue:
        pass

    def _Equals(self, item: IKeyValuePair[TKey, TValue]|object) -> bool:
        return isinstance(item, IKeyValuePair)
    
    @final
    def Equals(self, item: IKeyValuePair[TKey, TValue]|object) -> bool:
        return self._Equals(item) and item.IsKeyValuePair() == self.IsKeyValuePair() and item.GetKey() == self.GetKey() and item.GetValue() == self.GetValue() # type: ignore

class KeyValuePairBase[TKey, TValue](IKeyValuePair[TKey, TValue]):
    def __init__(self):
        super().__init__()
    
    @final
    def IsKeyValuePair(self) -> bool:
        return True
    
    def _Equals(self, item: IKeyValuePair[TKey, TValue]|object) -> bool:
        return isinstance(item, KeyValuePairBase)
class KeyValuePair[TKey, TValue](KeyValuePairBase[TKey, TValue]):
    def __init__(self, key: TKey, value: TValue):
        super().__init__()

        self.__key = key
        self.__value = value
    
    @final
    def GetKey(self) -> TKey:
        return self.__key
    
    @final
    def GetValue(self) -> TValue:
        return self.__value
    
    @final
    def _Equals(self, item: IKeyValuePair[TKey, TValue]|object) -> bool:
        return isinstance(item, KeyValuePair)

class DualResult[TValue, TInfo](IKeyValuePair[TValue, TInfo]):
    def __init__(self, value: TValue, info: TInfo):
        self.__value: TValue = value
        self.__info: TInfo = info
    
    @final
    def IsKeyValuePair(self) -> bool:
        return False
    
    @final
    def GetKey(self) -> TValue:
        return self.__value
    
    @final
    def GetValue(self) -> TInfo:
        return self.__info
    
    @final
    def _Equals(self, item: DualResult[TValue, TInfo]|object) -> bool:
        return isinstance(item, DualResult)

class DualNullableValueInfo[TValue, TInfo](DualResult[TValue|None, TInfo]):
    def __init__(self, value: TValue|None, info: TInfo):
        super().__init__(value, info)
class DualValueNullableInfo[TValue, TInfo](DualResult[TValue, TInfo|None]):
    def __init__(self, value: TValue, info: TInfo|None):
        super().__init__(value, info)
class DualNullableValueNullableInfo[TValue, TInfo](DualResult[TValue|None, TInfo|None]):
    def __init__(self, value: TValue|None, info: TInfo|None):
        super().__init__(value, info)

class DualValueBool[T](DualResult[T, bool], IBoolProvider):
    def __init__(self, value: T, info: bool):
        super().__init__(value, info)
    
    @final
    def AsBool(self) -> bool:
        return self.GetValue()
class DualValueNullableBool[T](DualValueNullableInfo[T, bool], INullableBoolProvider):
    def __init__(self, value: T, info: bool|None):
        super().__init__(value, info)
    
    @final
    def AsNullableBool(self) -> bool|None:
        return self.GetValue()

class DualNullableValueBool[T](DualNullableValueInfo[T, bool], IBoolProvider):
    def __init__(self, value: T|None, info: bool):
        super().__init__(value, info)
    
    @final
    def AsBool(self) -> bool:
        return self.GetValue()
class DualNullableValueNullableBool[T](DualNullableValueNullableInfo[T, bool], INullableBoolProvider):
    def __init__(self, value: T|None, info: bool|None):
        super().__init__(value, info)
    
    @final
    def AsNullableBool(self) -> bool|None:
        return self.GetValue()