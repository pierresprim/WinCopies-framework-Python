# -*- coding: utf-8 -*-
"""
Created on Thu May 30 07:37:00 2024

@author: Pierre Sprimont
"""

from typing import Callable, Iterable, AnyStr
import os

from WinCopies import Delegates, Collections, IO
from WinCopies.Typing.Delegate import Converter, Method, Predicate
from WinCopies.Typing.Pairing import DualResult
from WinCopies.Collections import Loop, IterableScanResult
from WinCopies.IO import FileKind

def ProcessDirEntries(path: str, func: Callable[[Iterable[os.DirEntry[str]]], bool|None]) -> IterableScanResult:
    return Collections.TryIterateFrom(path, os.path.isdir, os.scandir, func)

def ParseEntries(path: str, predicate: Predicate[os.DirEntry[str]]) -> IterableScanResult:
    return ProcessDirEntries(path, lambda paths: Loop.ForEachItemUntil(paths, predicate))

def __ParseDir(path: str, func: Callable[[str, Predicate[os.DirEntry[AnyStr]]], IterableScanResult], converter: Converter[Collections.FinderPredicate[os.DirEntry[AnyStr]], Predicate[os.DirEntry[AnyStr]]]) -> DualResult[os.DirEntry[AnyStr]|None, IterableScanResult]:
    predicate = Collections.FinderPredicate[os.DirEntry[AnyStr]]()
    
    dirScanResult: IterableScanResult = func(path, converter(predicate))

    return DualResult[os.DirEntry[AnyStr]|None, IterableScanResult](predicate.TryGetResult().GetKey(), dirScanResult)

def FindDirEntry(path: str, predicate: Predicate[os.DirEntry[str]]) -> DualResult[os.DirEntry[str]|None, IterableScanResult]:
    return __ParseDir(path, ParseEntries, lambda _predicate: _predicate.GetPredicate(predicate))

def ScanDir(path: str, predicate: Predicate[os.DirEntry[str]]) -> IterableScanResult:
    return ParseEntries(path, lambda entry: not predicate(entry)).Not()

def ValidateDirEntries(path: str, predicate: Predicate[os.DirEntry[str]]) -> DualResult[os.DirEntry[str]|None, IterableScanResult]:
    return __ParseDir(path, ScanDir, lambda _predicate: _predicate.GetValidationPredicate(predicate))

def HasItems(path: str) -> IterableScanResult:
    def parse(paths: Iterable[os.DirEntry[AnyStr]]) -> bool|None:
        for _ in paths:
            return True
        
        return None
    
    return ProcessDirEntries(path, parse)

def ParseDir(path: str, predicate: Predicate[os.DirEntry[str]], action: Method[os.DirEntry[str]]) -> IterableScanResult:
    return ScanDir(path, Delegates.GetPredicateAction(predicate, action))

def ForEachDirEntry(path: str, predicate: Predicate[os.DirEntry[str]], action: Method[os.DirEntry[str]]) -> DualResult[os.DirEntry[str]|None, IterableScanResult]:
    return ValidateDirEntries(path, Delegates.GetPredicateAction(predicate, action))

def ScanDirEntries(path: str, action: Method[os.DirEntry[str]]) -> IterableScanResult:
    return ProcessDirEntries(path, lambda paths: Loop.DoForEachItem(paths, action))

def ParseDirEntries(path: str, predicate: Predicate[os.DirEntry[str]], action: Method[os.DirEntry[str]]) -> IterableScanResult:
    return ProcessDirEntries(path, lambda paths: Loop.ScanItems(paths, predicate, action))

def __ParseDirEntries(path: str, predicate: Predicate[os.DirEntry[str]], action: Method[os.DirEntry[str]], dirEntryPredicate: Predicate[os.DirEntry[str]]) -> IterableScanResult:
    return ParseDirEntries(path, Delegates.GetAndAlsoPredicate(dirEntryPredicate, predicate), action)

def ScanSubdirectories(path: str, action: Method[os.DirEntry[str]]) -> IterableScanResult:
    return ParseDirEntries(path, IO.GetDirectoryPredicate(), action)
def ParseSubdirectories(path: str, predicate: Predicate[os.DirEntry[str]], action: Method[os.DirEntry[str]]) -> IterableScanResult:
    return __ParseDirEntries(path, predicate, action, IO.GetDirectoryPredicate())

def ScanFiles(path: str, action: Method[os.DirEntry[str]]) -> IterableScanResult:
    return ParseDirEntries(path, IO.GetFilePredicate(), action)
def ParseFiles(path: str, predicate: Predicate[os.DirEntry[str]], action: Method[os.DirEntry[str]]) -> IterableScanResult:
    return __ParseDirEntries(path, predicate, action, IO.GetFilePredicate())

def GetFindFromExtensionsPredicate(fileKind: FileKind, extensions: Iterable[str]) -> Predicate[os.DirEntry[str]]:
    predicate: Predicate[os.DirEntry[str]] = lambda entry: IO.TryCheckExtension(entry.path, extensions) == True
    
    match fileKind:
        case FileKind.Null:
            return predicate
        
        case FileKind.Folder:
            return Delegates.GetAndAlsoPredicate(os.DirEntry[str].is_dir, predicate)
        
        case FileKind.File:
            return Delegates.GetAndAlsoPredicate(os.DirEntry[str].is_file, predicate)
        
        case FileKind.Link:
            return Delegates.GetAndAlsoPredicate(os.DirEntry[str].is_symlink, predicate)
        
        case FileKind.Junction:
            return Delegates.GetAndAlsoPredicate(os.DirEntry[str].is_junction, predicate)
    
    raise ValueError("FileKind not supported.", fileKind)
def GetFindFromExtensionValuesPredicate(fileKind: FileKind, *extensions: str) -> Predicate[os.DirEntry[str]]:
    return GetFindFromExtensionsPredicate(fileKind, extensions)

def __FindFromExtensions(path: str, predicate: Predicate[os.DirEntry[str]]) -> os.DirEntry[str]|None:
    result: DualResult[os.DirEntry[str]|None, IterableScanResult] = FindDirEntry(path, predicate)
    
    return result.GetKey() if result.GetValue() == IterableScanResult.Success else None

def FindFromExtensions(path: str, fileKind: FileKind, extensions: Iterable[str]) -> os.DirEntry[str]|None:
    return __FindFromExtensions(path, GetFindFromExtensionsPredicate(fileKind, extensions))
def FindFromExtensionValues(path: str, fileKind: FileKind, *extensions: str) -> os.DirEntry[str]|None:
    return FindFromExtensions(path, fileKind, extensions)

def FindFromExtensionsAndCheck(path: str, fileKind: FileKind, predicate: Predicate[os.DirEntry[str]], *extensions: str) -> os.DirEntry[str]|None:
    return __FindFromExtensions(path, Delegates.GetAndAlsoPredicate(GetFindFromExtensionsPredicate(fileKind, extensions), predicate))
def FindFromExtensionsAndValidate(path: str, fileKind: FileKind, predicate: Predicate[os.DirEntry[str]], *extensions: str) -> os.DirEntry[str]|None:
    return __FindFromExtensions(path, Delegates.GetAndPredicate(GetFindFromExtensionsPredicate(fileKind, extensions), predicate))

def CheckAndFindFromExtensions(path: str, fileKind: FileKind, predicate: Predicate[os.DirEntry[str]], *extensions: str) -> os.DirEntry[str]|None:
    return __FindFromExtensions(path, Delegates.GetAndAlsoPredicate(predicate, GetFindFromExtensionsPredicate(fileKind, extensions)))
def ValidateAndFindFromExtensions(path: str, fileKind: FileKind, predicate: Predicate[os.DirEntry[str]], *extensions: str) -> os.DirEntry[str]|None:
    return __FindFromExtensions(path, Delegates.GetAndPredicate(predicate, GetFindFromExtensionsPredicate(fileKind, extensions)))