# -*- coding: utf-8 -*-
"""
Created on Fri May 26 14:21:00 2023

@author: Pierre Sprimont
"""

from typing import Callable

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

def AskInt(message: str, predicate: Callable[[int], bool], errorMessage: str = "The value is out of range."):
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

def Process(action: Callable[[], None], message: str = "Continue?", info: str = " y/[any other key]: ", value: str = "y"):
    while AskConfirmation(message, info, value):
        action()

def DoProcess(action: Callable[[], None], message: str = "Continue?", info: str = " y/[any other key]: ", value: str = "y"):
    action()
    
    Process(action, message, info, value)

def TryPredicate(predicate: Callable[[Exception], bool], action: Callable[[], None]) -> bool|None:
    ok: bool = True
    _predicate: Callable[[Exception], bool]

    def __predicate(e: Exception) -> bool:
        nonlocal ok
        nonlocal predicate
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
def Try(action: Callable[[], None], onError: Callable[[Exception], None], func: Callable[[], bool]) -> bool|None:
    def _onError(e: Exception) -> bool:
        onError(e)
        
        return func()
    
    return TryPredicate(_onError, action)
def TryMessage(action: Callable[[], None], onError: Callable[[Exception], None], message: str = "Continue?") -> bool|None:
    return Try(action, onError, lambda: AskConfirmation(message))