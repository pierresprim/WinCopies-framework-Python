# -*- coding: utf-8 -*-
"""
Created on Fri May 26 14:21:00 2023

@author: Pierre Sprimont
"""

from typing import final
from abc import ABC, abstractmethod

from WinCopies.Delegates import Self

def Not(value: bool|None) -> bool|None:
    return None if value is None else not value

def TryConvertToInt(value) -> int|None:
    try:
        return int(value)
    except ValueError:
        return None

def ReadInt(message: str, errorMessage: str = "Invalid value; an integer is expected.") -> int:
    def read() -> int|None:
        return TryConvertToInt(input(message))
        
    value: int|None = read()
    
    while value is None:
        print(errorMessage)
        
        value = read()
    
    return value

def AskInt(message: str, predicate: callable, errorMessage: str = "The value is out of range."):
    value: int = 0
    
    def loop() -> int:
        nonlocal value
        
        value = ReadInt(message)
    
    loop()
    
    while predicate(value):
        print(errorMessage)
        
        loop()
    
    return value

def AskConfirmation(message: str, info: str = " y/[any other key]: ", value: str = "y") -> bool:
    return input(message + info) == value

def Process(action: callable, message: str = "Continue?", info: str = " y/[any other key]: ", value: str = "y"):
    while AskConfirmation(message, info, value):
        action()

def DoProcess(action: callable, message: str = "Continue?", info: str = " y/[any other key]: ", value: str = "y"):
    action()
    
    Process(action, message, info, value)

def TryPredicate(action: callable, predicate: callable) -> bool|None:
    ok: bool = True
    _predicate: callable

    def __predicate(e: Exception) -> bool:
        nonlocal ok
        nonlocal _predicate

        if predicate(e):
            ok = False
            _predicate = predicate

            return True
        
        return False
    
    _predicate = __predicate
    
    while True:
        try:
            action()

        except Exception as e:
            if _predicate(e):
                continue
                
            return None
        
        break

    return ok
def Try(action: callable, onError: callable, func: callable) -> bool|None:
    def _onError(e: Exception) -> bool:
        onError(e)
        
        return func()
    
    return TryPredicate(action, _onError)
def TryMessage(action: callable, onError: callable, message: str = "Continue?") -> bool|None:
    return Try(action, onError, lambda: AskConfirmation(message))

class DualResult[TResultValue, TResultInfo]:
    def __init__(self, resultValue: TResultValue, resultInfo: TResultInfo):
        self.__resultValue: TResultValue = resultValue
        self.__resultInfo: TResultInfo = resultInfo
    
    def GetValue(self) -> TResultValue:
        return self.__resultValue
    
    def GetInfo(self) -> TResultInfo:
        return self.__resultInfo

class DualValueBool[T](DualResult[T, bool]):
    def __init__(self, resultValue: T, resultInfo: bool):
        super().__init__(resultValue, resultInfo)

class DualValueNullableBool[T](DualResult[T, bool|None]):
    def __init__(self, resultValue: T, resultInfo: bool|None):
        super().__init__(resultValue, resultInfo)

class Singleton(type):
    __instances = {}
    
    def WhenExisting(cls, *args, **kwargs) -> None:
        pass
    def WhenNew(cls, *args, **kwargs) -> None:
        cls.__instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
    
    def __call__(cls, *args, **kwargs):
        (Singleton.WhenExisting if cls in cls.__instances else Singleton.WhenNew)(cls, args, kwargs)
            
        return cls.__instances[cls]

class MultiInitializationSingleton(Singleton):
    def WhenExisting(cls, *args, **kwargs) -> None:
        cls._instances[cls].__init__(*args, **kwargs)

def singleton(cls):
    cls.__call__ = Self
    return cls()