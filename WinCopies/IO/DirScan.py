# -*- coding: utf-8 -*-
"""
Created on Thu May 30 07:37:00 2024

@author: Pierre Sprimont
"""

from enum import Enum
import os

from WinCopies import Delegates, DualResult, Collections

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
    return ProcessDirEntries(path, lambda paths: Collections.ParseItems(paths, predicate))

def __ParseDir(path: str, func: callable, converter: callable) -> DualResult[os.DirEntry|None, DirScanResult]:
    _predicate = Collections.FinderPredicate[os.DirEntry]()
    
    dirScanResult: DirScanResult = func(path, converter(_predicate))

    return DualResult(_predicate.TryGetResult().GetValue(), dirScanResult)

def FindDirEntry(path: str, predicate: callable) -> DualResult[os.DirEntry|None, DirScanResult]:
    return __ParseDir(path, ParseEntries, lambda _predicate: _predicate.GetPredicate(predicate))

def ScanDir(path: str, predicate: callable) -> DirScanResult:
    return ParseEntries(path, lambda entry: not predicate(entry)).Not()

def ValidateDirEntries(path: str, predicate: callable) -> DualResult[os.DirEntry|None, DirScanResult]:
    return __ParseDir(path, ScanDir, lambda _predicate: _predicate.GetValidationPredicate(predicate))

def HasItems(path: str) -> DirScanResult:
    def parse(paths) -> bool|None:
        for entry in paths:
            return True
        
        return None
    
    return ProcessDirEntries(path, parse)

def ParseDir(path: str, predicate: callable, action: callable) -> DirScanResult:
    return ScanDir(path, Delegates.GetPredicateAction(predicate, action))

def ForEachDirEntry(path: str, predicate: callable, action: callable) -> DualResult[os.DirEntry|None, DirScanResult]:
    return ValidateDirEntries(path, Delegates.GetPredicateAction(predicate, action))

def ScanDirEntries(path: str, action: callable) -> DirScanResult:
    return ProcessDirEntries(path, lambda paths: Collections.ScanItems(paths, action))

def ParseDirEntries(path: str, predicate: callable, action: callable) -> DirScanResult:
    return ProcessDirEntries(path, lambda paths: Collections.ScanAllItems(paths, predicate, action))