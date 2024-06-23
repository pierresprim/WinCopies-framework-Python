# -*- coding: utf-8 -*-
"""
Created on Thu May 30 07:37:00 2024

@author: Pierre Sprimont
"""

from typing import Callable, Iterable
from enum import Enum
import os

from WinCopies import Delegates, DualResult, Collections, IO
from WinCopies.Collections import Loop, IterableScanResult

def ProcessDirEntries(path: str, func: Callable[[Iterable[os.DirEntry]], bool|None]) -> IterableScanResult:
    return Collections.TryIterateFrom(path, os.path.isdir, os.scandir, func)

def ParseEntries(path: str, predicate: Callable[[os.DirEntry], bool]) -> IterableScanResult:
    return ProcessDirEntries(path, lambda paths: Loop.ForEachItemUntil(paths, predicate))

def __ParseDir(path: str, func: Callable[[str, Callable[[os.DirEntry], bool]], IterableScanResult], converter: Callable[[Collections.FinderPredicate[os.DirEntry]], Callable[[os.DirEntry], bool]]) -> DualResult[os.DirEntry|None, IterableScanResult]:
    predicate = Collections.FinderPredicate[os.DirEntry]()
    
    dirScanResult: IterableScanResult = func(path, converter(predicate))

    return DualResult(predicate.TryGetResult().GetValue(), dirScanResult)

def FindDirEntry(path: str, predicate: callable[[os.DirEntry], bool]) -> DualResult[os.DirEntry|None, IterableScanResult]:
    return __ParseDir(path, ParseEntries, lambda _predicate: _predicate.GetPredicate(predicate))

def ScanDir(path: str, predicate: callable[[os.DirEntry], bool]) -> IterableScanResult:
    return ParseEntries(path, lambda entry: not predicate(entry)).Not()

def ValidateDirEntries(path: str, predicate: callable[[os.DirEntry], bool]) -> DualResult[os.DirEntry|None, IterableScanResult]:
    return __ParseDir(path, ScanDir, lambda _predicate: _predicate.GetValidationPredicate(predicate))

def HasItems(path: str) -> IterableScanResult:
    def parse(paths) -> bool|None:
        for entry in paths:
            return True
        
        return None
    
    return ProcessDirEntries(path, parse)

def ParseDir(path: str, predicate: callable, action: callable) -> IterableScanResult:
    return ScanDir(path, Delegates.GetPredicateAction(predicate, action))

def ForEachDirEntry(path: str, predicate: callable, action: callable) -> DualResult[os.DirEntry|None, IterableScanResult]:
    return ValidateDirEntries(path, Delegates.GetPredicateAction(predicate, action))

def ScanDirEntries(path: str, action: callable) -> IterableScanResult:
    return ProcessDirEntries(path, lambda paths: Loop.DoForEachItem(paths, action))

def ParseDirEntries(path: str, predicate: callable, action: callable) -> IterableScanResult:
    return ProcessDirEntries(path, lambda paths: Loop.ScanItems(paths, predicate, action))

def __ParseDirEntries(path: str, predicate: callable, action: callable, dirEntryPredicate: callable) -> IterableScanResult:
    return ParseDirEntries(path, Delegates.GetPredicateAndAlso(dirEntryPredicate, predicate), action)

def ScanSubdirectories(path: str, action: callable) -> IterableScanResult:
    return ParseDirEntries(path, IO.GetDirectoryPredicate(), action)
def ParseSubdirectories(path: str, predicate: callable, action: callable) -> IterableScanResult:
    return __ParseDirEntries(path, predicate, action, IO.GetDirectoryPredicate())

def ScanFiles(path: str, action: callable) -> IterableScanResult:
    return ParseDirEntries(path, IO.GetFilePredicate(), action)
def ParseFiles(path: str, predicate: callable, action: callable) -> IterableScanResult:
    return __ParseDirEntries(path, predicate, action, IO.GetFilePredicate())