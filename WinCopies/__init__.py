# -*- coding: utf-8 -*-
"""
Created on Fri May 26 14:21:00 2023

@author: Pierre Sprimont
"""

from typing import Callable
from enum import Enum

from WinCopies.Typing.Delegate import Action, Predicate

class Endianness(Enum):
    Null = 0
    Little = 1
    Big = 2

class Sign(Enum):
    Signed = 1
    Unsigned = 2
    Float = 3

class BitDepthLevel(Enum):
    One = 8
    Two = 16
    Three = 32
    Four = 64

def Not(value: bool|None) -> bool|None:
    return None if value is None else not value

def TryConvertToInt(value: object) -> int|None:
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

def AskInt(message: str, predicate: Predicate[int], errorMessage: str = "The value is out of range."):
    value: int = 0
    
    def loop() -> int:
        nonlocal value
        
        value = ReadInt(message)
    
    loop()
    
    while predicate(value):
        print(errorMessage)
        
        loop()
    
    return value

def AskConfirmation(message: str, info: str = " [y]/any other key: ", value: str = "y") -> bool:
    return input(message + info) == value

def Process(action: Action, message: str = "Continue?", info: str = " [y]/any other key: ", value: str = "y"):
    while AskConfirmation(message, info, value):
        action()

def DoProcess(action: Action, message: str = "Continue?", info: str = " [y]/any other key: ", value: str = "y"):
    action()
    
    Process(action, message, info, value)

def TryPredicate(predicate: Predicate[Exception], action: Action) -> bool|None:
    ok: bool = True
    _predicate: Predicate[Exception]

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
def Try(action: Action, onError: Callable[[Exception], None], func: Callable[[], bool]) -> bool|None:
    def _onError(e: Exception) -> bool:
        onError(e)
        
        return func()
    
    return TryPredicate(_onError, action)
def TryMessage(action: Action, onError: Callable[[Exception], None], message: str = "Continue?") -> bool|None:
    return Try(action, onError, lambda: AskConfirmation(message))