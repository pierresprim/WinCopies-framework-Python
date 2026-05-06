from __future__ import annotations

from abc import abstractmethod
from typing import final, Self

from WinCopies import Abstract
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.BoolProvider import IBoolProvider, INullableBoolProvider
from WinCopies.Typing.Comparison import IEquatable

class IKeyValuePair[TKey, TValue](IEquatable["IKeyValuePair[TKey, TValue]"]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def IsKeyValuePair(self) -> bool:
        pass

    @abstractmethod
    def GetKey(self) -> TKey:
        pass

    @abstractmethod
    def GetValue(self) -> TValue:
        pass
    
    @final
    def Equals(self, item: IKeyValuePair[TKey, TValue]) -> bool:
        return type(item) == type(self) and (item.IsKeyValuePair() == self.IsKeyValuePair()) and (item.GetKey() == self.GetKey()) and (item.GetValue() == self.GetValue())

class KeyValuePairBase[TKey, TValue](Abstract, IKeyValuePair[TKey, TValue]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def IsKeyValuePair(self) -> bool:
        return True
class KeyValuePair[TKey, TValue](KeyValuePairBase[TKey, TValue]):
    def __init__(self, key: TKey, value: TValue) -> None:
        super().__init__()

        self.__key = key
        self.__value = value
    
    @final
    def GetKey(self) -> TKey:
        return self.__key
    
    @final
    def GetValue(self) -> TValue:
        return self.__value

class DualResult[TValue, TInfo](Abstract, IKeyValuePair[TValue, TInfo]):
    def __init__(self, value: TValue, info: TInfo) -> None:
        super().__init__()
        
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

class DualNullableValueInfo[TValue, TInfo](DualResult[TValue|None, TInfo]):
    def __init__(self, value: TValue|None, info: TInfo) -> None:
        super().__init__(value, info)
class DualValueNullableInfo[TValue, TInfo](DualResult[TValue, TInfo|None]):
    def __init__(self, value: TValue, info: TInfo|None) -> None:
        super().__init__(value, info)
class DualNullableValueNullableInfo[TValue, TInfo](DualResult[TValue|None, TInfo|None]):
    def __init__(self, value: TValue|None, info: TInfo|None) -> None:
        super().__init__(value, info)

class DualValueBool[T](DualResult[T, bool], IBoolProvider):
    def __init__(self, value: T, info: bool) -> None:
        super().__init__(value, info)
    
    @final
    def AsBool(self) -> bool:
        return self.GetValue()
class DualValueNullableBool[T](DualValueNullableInfo[T, bool], INullableBoolProvider):
    def __init__(self, value: T, info: bool|None) -> None:
        super().__init__(value, info)
    
    @final
    def AsNullableBool(self) -> bool|None:
        return self.GetValue()

__null = None # pyright: ignore[reportAssignmentType]

def GetNullDualValueBool[T]() -> DualNullableValueBool[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __null # type: ignore

class DualNullableValueBool[T](DualNullableValueInfo[T, bool], IBoolProvider):
    def __init__(self, value: T|None, info: bool) -> None:
        super().__init__(value, info)
    
    def __new__(cls, value: T|None, info: bool) -> Self:
        return GetNullDualValueBool() if not info and value is None else super().__new__(value, info) # type: ignore
    
    @final
    def AsBool(self) -> bool:
        return self.GetValue()
class DualNullableValueNullableBool[T](DualNullableValueNullableInfo[T, bool], INullableBoolProvider):
    def __init__(self, value: T|None, info: bool|None) -> None:
        super().__init__(value, info)
    
    @final
    def AsNullableBool(self) -> bool|None:
        return self.GetValue()

__null: DualNullableValueBool[None] = DualNullableValueBool[None](None, False) # type: ignore[no-redef]

def CreateKeyValuePair[TKey, TValue](key: TKey, value: TValue) -> IKeyValuePair[TKey, TValue]:
    return KeyValuePair[TKey, TValue](key, value)

def CreateDualResult[TValue, TInfo](value: TValue, info: TInfo) -> DualResult[TValue, TInfo]:
    return DualResult[TValue, TInfo](value, info)

def CreateDualNullableValueInfo[TValue, TInfo](value: TValue|None, info: TInfo) -> DualNullableValueInfo[TValue, TInfo]:
    return DualNullableValueInfo[TValue, TInfo](value, info)
def CreateDualValueNullableInfo[TValue, TInfo](value: TValue, info: TInfo|None) -> DualValueNullableInfo[TValue, TInfo]:
    return DualValueNullableInfo[TValue, TInfo](value, info)

def CreateDualNullableValueNullableInfo[TValue, TInfo](value: TValue|None, info: TInfo|None) -> DualNullableValueNullableInfo[TValue, TInfo]:
    return DualNullableValueNullableInfo[TValue, TInfo](value, info)

def CreateDualValueBool[T](value: T, info: bool) -> DualValueBool[T]:
    return DualValueBool[T](value, info)

def CreateDualNullableValueBool[T](value: T|None, info: bool) -> DualNullableValueBool[T]:
    return DualNullableValueBool[T](value, info)
def CreateDualValueNullableBool[T](value: T, info: bool|None) -> DualValueNullableBool[T]:
    return DualValueNullableBool[T](value, info)

def CreateDualNullableValueNullableBool[T](value: T|None, info: bool|None) -> DualNullableValueNullableBool[T]:
    return DualNullableValueNullableBool(value, info)

def TryGetKey[TKey, TValue](item: IKeyValuePair[TKey, TValue]|None) -> INullable[TKey]:
    return GetNullValue() if item is None else GetNullable(item.GetKey())
def TryGetValue[TKey, TValue](item: IKeyValuePair[TKey, TValue]|None) -> INullable[TValue]:
    return GetNullValue() if item is None else GetNullable(item.GetValue())

def TryGetKeyOrDefault[TKey, TValue, TDefault](item: IKeyValuePair[TKey, TValue]|None, default: TDefault) -> TKey|TDefault:
    return default if item is None else item.GetKey()
def TryGetValueOrDefault[TKey, TValue, TDefault](item: IKeyValuePair[TKey, TValue]|None, default: TDefault) -> TValue|TDefault:
    return default if item is None else item.GetValue()