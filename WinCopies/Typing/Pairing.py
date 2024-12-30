from typing import final
from abc import ABC, abstractmethod

class IKeyValuePair[TKey, TValue](ABC):
    @abstractmethod
    def IsKeyValuePair(self) -> bool:
        pass

    @abstractmethod
    def GetKey(self) -> TKey:
        pass

    @abstractmethod
    def GetValue(self) -> TValue:
        pass

class KeyValuePair[TKey, TValue](IKeyValuePair[TKey, TValue]):
    def __init__(self, key: TKey, value: TValue):
        self.__key = key
        self.__value = value
    
    @final
    def IsKeyValuePair(self) -> bool:
        return True
    
    @final
    def GetKey(self) -> TKey:
        return self.__key
    
    @final
    def GetValue(self) -> TValue:
        return self.__value

class DualResult[TValue, TInfo](IKeyValuePair[TInfo, TValue]):
    def __init__(self, value: TValue, info: TInfo):
        self.__value: TValue = value
        self.__info: TInfo = info
    
    @final
    def IsKeyValuePair(self) -> bool:
        return False
    
    @final
    def GetValue(self) -> TValue:
        return self.__value
    
    @final
    def GetKey(self) -> TInfo:
        return self.__info

class DualValueBool[T](DualResult[T, bool]):
    def __init__(self, resultValue: T, resultInfo: bool):
        super().__init__(resultValue, resultInfo)

class DualValueNullableBool[T](DualResult[T, bool|None]):
    def __init__(self, resultValue: T, resultInfo: bool|None):
        super().__init__(resultValue, resultInfo)