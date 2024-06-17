# -*- coding: utf-8 -*-
"""
Created on Thu May 30 07:37:00 2024

@author: Pierre Sprimont
"""

from enum import Enum
from typing import final
import os

from WinCopies import Delegates
from WinCopies.Collections.Enumeration import Iterable

class DirScanResult(Enum):
    DoesNotExist = -2
    Empty = -1
    Success = 0
    Error = 1

    def __bool__(self):
        return self >= 0
    
    def Not(self):
        return (DirScanResult.Error if self == DirScanResult.Success else DirScanResult.Success) if self else self

def ProcessDirEntries(path: str, func: callable) -> DirScanResult:
    if os.path.exists(path):
        with os.scandir(path) as paths:
            result: bool|None = func(paths)

            return DirScanResult.Empty if result == None else (DirScanResult.Success if result else DirScanResult.Error)
    
    return DirScanResult.DoesNotExist

def ParseEntries(path: str, predicate: callable) -> DirScanResult:
    def scanDir(paths) -> bool|None:
        nonlocal predicate

        result: bool|None = None
        _predicate: callable

        def init(entry) -> bool:
            nonlocal result
            nonlocal predicate
            nonlocal _predicate

            result = False
            return (_predicate := predicate)(entry)
        
        _predicate = init

        for entry in paths:
            if _predicate(entry):
                return True
        
        return result

    return ProcessDirEntries(path, scanDir)

def ScanDir(path: str, predicate: callable) -> DirScanResult:
    return ParseEntries(path, lambda entry: not predicate(entry)).Not()

def HasItems(path: str) -> DirScanResult:
    def parse(paths) -> bool|None:
        for entry in paths:
            return True
        
        return None
    
    return ProcessDirEntries(path, parse)

def ParseDir(path: str, predicate: callable, action: callable) -> DirScanResult:
    return ScanDir(path, Delegates.GetPredicateAction(predicate, action))

def ScanDirEntries(path: str, action: callable) -> DirScanResult:
    def scanDirEntries(paths) -> bool|None:
        nonlocal action

        result: bool|None = None
        _action: callable

        def init(entry):
            nonlocal result
            nonlocal action
            nonlocal _action

            (_action := action)(entry)

            result = True
        
        _action = init

        for entry in paths:
            _action(entry)
        
        return result
    
    return ProcessDirEntries(path, scanDirEntries)

def ParseDirEntries(path: str, predicate: callable, action: callable) -> DirScanResult:
    def parse(paths) -> bool|None:
        nonlocal predicate
        nonlocal action

        result: bool|None = None
        
        def scanDir(entry: os.DirEntry):
            nonlocal predicate
            nonlocal action

            if predicate(entry):
                action(entry)
        
        def tryScanDir(entry: os.DirEntry):
            nonlocal predicate
            nonlocal action
            nonlocal func
            nonlocal result

            if predicate(entry):
                action(entry)
            
            else:
                func = scanDir

                result = False
        
        func: callable

        def init(entry):
            nonlocal result
            nonlocal func

            result = True

            (func := tryScanDir)(entry)
            
        func = init

        for entry in paths:
            func(entry)
            
        return result
    
    return ProcessDirEntries(path, parse)