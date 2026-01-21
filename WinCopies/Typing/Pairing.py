from __future__ import annotations

from abc import abstractmethod
from typing import final, Self

from WinCopies import Abstract
from WinCopies.Typing import IEquatableObject
from WinCopies.Typing.BoolProvider import IBoolProvider, INullableBoolProvider

class IKeyValuePair[TKey, TValue](IEquatableObject["IKeyValuePair[TKey, TValue]"]):
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