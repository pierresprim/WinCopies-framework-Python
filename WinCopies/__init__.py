# -*- coding: utf-8 -*-
"""
Created on Fri May 26 14:21:00 2023

@author: Pierre Sprimont
"""

from typing import Type, final
from enum import Enum

from WinCopies.Collections import Enumeration
from WinCopies.Delegates import Self

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

def DoProcess(action: callable, message: str = "Continue?", info: str = " y/[any other key]: ", value: str = "y"):
    action()
    
    Process(action, message, info, value)

def Process(action: callable, message: str = "Continue?", info: str = " y/[any other key]: ", value: str = "y"):
    while AskConfirmation(message):
        action()

def Replace(string: str, esc: str, newEsc: str, *args: str) -> str:
    string = string.replace(esc + esc, esc)
    
    for arg in args:
        
        string = string.replace(esc + arg, newEsc + arg)
    
    return string

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
    def __init__(self, resultValue: TResultValue, resultInfo: TResultInfo) -> None:
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

def AssertEnum(e: Type[Enum]):
    assert(issubclass(e, Enum))

def __IsMemberOfEnum(e: Type[Enum], obj: object, selector: callable) -> bool:
    return obj in [selector(o) for o in e]

def IsMemberOfEnum(e: Type[Enum], n: str) -> bool:
    AssertEnum(e)

    return __IsMemberOfEnum(e, n, lambda o: o.name)

def IsValueOfEnum(e: Type[Enum], v: int) -> bool:
    AssertEnum(e)

    return __IsMemberOfEnum(e, v, lambda o: o.value)

def IsFieldOfEnum(e: Type[Enum], f: Enum) -> bool:
    def assertTypes():
        nonlocal e
        nonlocal f

        t: Type = type(f)

        AssertEnum(t)
        assert(issubclass(e, t))
    
    assertTypes()

    return f in e

def IsInEnum(e: Type[Enum], t: tuple[str, int]) -> bool:
    AssertEnum(e)

    return t in [(o.name, o.value) for o in e]

def __TryGetEnumMember(e: Type[Enum], predicate: callable, selector: callable) -> object|None:
    for o in e:
        if predicate(o):
            return selector(o)
    
    return None

def TryGetEnumMember(e: Type[Enum], predicate: callable, selector: callable) -> object|None:
    AssertEnum(e)
    
    return __TryGetEnumMember(e, predicate, selector)

def __TryGetEnumFieldValue(e: Type[Enum], obj: object, predicateSelector: callable, conversionSelector: callable) -> object|None:
    return __TryGetEnumMember(e, lambda o: predicateSelector(o) == obj, conversionSelector)

def TryGetEnumName(e: Type[Enum], v: int) -> str|None:
    AssertEnum(e)
    
    return __TryGetEnumFieldValue(e, v, lambda o: o.value, lambda o: o.name)

def TryGetEnumValue(e: Type[Enum], n: str) -> int|None:
    AssertEnum(e)
    
    return __TryGetEnumFieldValue(e, n, lambda o: o.name, lambda o: o.value)

def __TryGetEnumField[T: Enum](e: Type[T], predicate: callable) -> T|None:
    return __TryGetEnumMember(e, predicate, Self)

def TryGetEnumField[T: Enum](e: Type[T], predicate: callable) -> T|None:
    AssertEnum(e)

    return __TryGetEnumField(e, predicate)

def TryGetEnumFieldFromName[T: Enum](e: Type[T], n: str) -> T|None:
    AssertEnum(e)
    
    return __TryGetEnumField(e, lambda o: o.name == n)

def TryGetEnumFieldFromValue[T: Enum](e: Type[T], v: int) -> T|None:
    AssertEnum(e)
    
    return __TryGetEnumField(e, lambda o: o.value == v)

class SequenceGenerator:
    from ._SequenceGenerator._Data import _Data
    from . import _SequenceGenerator
    
    def __init__(self, pattern: str, start: int, count: int):
        SequenceGenerator._ValidateIndexes(start, count)
        
        self.__pattern: str = pattern
        self.__start: int = start
        self.__count: int = count
        self.__data: SequenceGenerator._Data = None
    
    def _ValidateIndexes(start: int, count: int) -> None:
        if start <= 0 or count < 0:
            raise ValueError
    
    def _GetData(self) -> _Data:
        return self.__data
        
    @final
    def GetPattern(self) -> str:
        return self.__pattern

    @final
    def GetStart(self) -> int:
        return self.__start
    @final
    def SetStart(self, start: int) -> int:
        SequenceGenerator._ValidateIndexes(start, self.__count)
        self.__start = start

    @final
    def GetCount(self) -> int:
        return self.__count
    @final
    def SetCount(self, count: int) -> None:
        SequenceGenerator._ValidateIndexes(self.__start, count)
        self.__count = count

    @final
    def __iter__(self) -> Enumeration.IEnumerator:
        if self.__data == None:
            self.__data = SequenceGenerator._Data(self.__pattern)
        
        return SequenceGenerator._SequenceGenerator._Enumerator(self)