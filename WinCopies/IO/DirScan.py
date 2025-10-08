# -*- coding: utf-8 -*-
"""
Created on Thu May 30 07:37:00 2024

@author: Pierre Sprimont
"""

import os
from typing import Callable, Iterable, AnyStr

from WinCopies import Delegates, Collections, IO
from WinCopies.Typing.Delegate import Converter, Method, Predicate
from WinCopies.Typing.Pairing import DualResult
from WinCopies.Collections import Loop, IterableScanResult
from WinCopies.IO import FileKind

def ProcessDirEntries(path: str, func: Converter[Iterable[os.DirEntry[str]], bool|None]) -> IterableScanResult:
    """Processes directory entries using a custom converter function.

    Args:
        path: The directory path to scan.
        func: A function to process the directory entries.

    Returns:
        An IterableScanResult indicating the outcome of the operation.
    """
    return Collections.TryIterateFrom(path, os.path.isdir, os.scandir, func)

def ParseEntries(path: str, predicate: Predicate[os.DirEntry[str]]) -> IterableScanResult:
    """Parses directory entries until the given predicate returns True.

    Args:
        path: The directory path to scan.
        predicate: A function to test each directory entry.

    Returns:
        An IterableScanResult indicating the outcome of the operation.
    """
    return ProcessDirEntries(path, lambda paths: Loop.ForEachItemUntil(paths, predicate))

def __ParseDir(path: str, func: Callable[[str, Predicate[os.DirEntry[AnyStr]]], IterableScanResult], converter: Converter[Collections.FinderPredicate[os.DirEntry[AnyStr]], Predicate[os.DirEntry[AnyStr]]]) -> DualResult[os.DirEntry[AnyStr]|None, IterableScanResult]:
    predicate = Collections.FinderPredicate[os.DirEntry[AnyStr]]()
    
    dirScanResult: IterableScanResult = func(path, converter(predicate))

    return DualResult[os.DirEntry[AnyStr]|None, IterableScanResult](predicate.GetResult().TryGetValue(), dirScanResult)

def FindDirEntry(path: str, predicate: Predicate[os.DirEntry[str]]) -> DualResult[os.DirEntry[str]|None, IterableScanResult]:
    """Finds the first directory entry matching the given predicate.

    Args:
        path: The directory path to scan.
        predicate: A function to test each directory entry.

    Returns:
        A DualResult containing the matching entry (or None if no entry matched the predicate) and the scan result.
    """
    return __ParseDir(path, ParseEntries, lambda _predicate: _predicate.GetPredicate(predicate))

def ScanDir(path: str, predicate: Predicate[os.DirEntry[str]]) -> IterableScanResult:
    """Scans directory entries while the given predicate returns True.

    Args:
        path: The directory path to scan.
        predicate: A function to test each directory entry.

    Returns:
        An IterableScanResult indicating the outcome of the operation.
    """
    return ParseEntries(path, lambda entry: not predicate(entry)).Not()

def ValidateDirEntries(path: str, predicate: Predicate[os.DirEntry[str]]) -> DualResult[os.DirEntry[str]|None, IterableScanResult]:
    """Validates directory entries and returns the first non-matching entry.

    Args:
        path: The directory path to scan.
        predicate: A function to test each directory entry.

    Returns:
        A DualResult containing the first non-matching entry (or None if all entries matched the predicate) and the scan result.
    """
    return __ParseDir(path, ScanDir, lambda _predicate: _predicate.GetValidationPredicate(predicate))

def HasItems(path: str) -> IterableScanResult:
    """Checks if a directory has any entries.

    Args:
        path: The directory path to check.

    Returns:
        An IterableScanResult indicating whether the directory contains entries.
    """
    def parse(paths: Iterable[os.DirEntry[AnyStr]]) -> bool|None:
        for _ in paths:
            return True

        return None

    return ProcessDirEntries(path, parse)

def ParseDir(path: str, predicate: Predicate[os.DirEntry[str]], action: Method[os.DirEntry[str]]) -> IterableScanResult:
    """Parses directory entries while the given predicate is True and executes an action on each.

    Args:
        path: The directory path to scan.
        predicate: A function to test each directory entry.
        action: A function to execute on each matching entry.

    Returns:
        An IterableScanResult indicating the outcome of the operation.
    """
    return ScanDir(path, Delegates.GetPredicateAction(predicate, action))

def ForEachDirEntry(path: str, predicate: Predicate[os.DirEntry[str]], action: Method[os.DirEntry[str]]) -> DualResult[os.DirEntry[str]|None, IterableScanResult]:
    """Executes an action on directory entries while the given predicate is True and validates.

    Args:
        path: The directory path to scan.
        predicate: A function to test each directory entry.
        action: A function to execute on each matching entry.

    Returns:
        A DualResult containing the first non-matching entry (or None if all entries matched the predicate) and the scan result.
    """
    return ValidateDirEntries(path, Delegates.GetPredicateAction(predicate, action))

def ScanDirEntries(path: str, action: Method[os.DirEntry[str]]) -> IterableScanResult:
    """Executes the given action on all directory entries.

    Args:
        path: The directory path to scan.
        action: A function to execute on each entry.

    Returns:
        An IterableScanResult indicating the outcome of the operation.
    """
    return ProcessDirEntries(path, lambda paths: Loop.DoForEachItem(paths, action))

def ParseDirEntries(path: str, predicate: Predicate[os.DirEntry[str]], action: Method[os.DirEntry[str]]) -> IterableScanResult:
    """Executes the given action on directory entries while all match the given predicate.

    Args:
        path: The directory path to scan.
        predicate: A function to test each directory entry.
        action: A function to execute on each matching entry.

    Returns:
        An IterableScanResult indicating the outcome of the operation.
    """
    return ProcessDirEntries(path, lambda paths: Loop.ScanItems(paths, predicate, action))

def __ParseDirEntries(path: str, predicate: Predicate[os.DirEntry[str]], action: Method[os.DirEntry[str]], dirEntryPredicate: Predicate[os.DirEntry[str]]) -> IterableScanResult:
    return ParseDirEntries(path, Delegates.GetAndAlsoPredicate(dirEntryPredicate, predicate), action)

def ScanSubdirectories(path: str, action: Method[os.DirEntry[str]]) -> IterableScanResult:
    """Executes the given action on all subdirectories.

    Args:
        path: The directory path to scan.
        action: A function to execute on each subdirectory.

    Returns:
        An IterableScanResult indicating the outcome of the operation.
    """
    return ParseDirEntries(path, IO.GetDirectoryPredicate(), action)
def ParseSubdirectories(path: str, predicate: Predicate[os.DirEntry[str]], action: Method[os.DirEntry[str]]) -> IterableScanResult:
    """Executes the given action on subdirectories while all match the given predicate.

    Args:
        path: The directory path to scan.
        predicate: A function to test each subdirectory.
        action: A function to execute on each matching subdirectory.

    Returns:
        An IterableScanResult indicating the outcome of the operation.
    """
    return __ParseDirEntries(path, predicate, action, IO.GetDirectoryPredicate())

def ScanFiles(path: str, action: Method[os.DirEntry[str]]) -> IterableScanResult:
    """Executes the given action on all files.

    Args:
        path: The directory path to scan.
        action: A function to execute on each file.

    Returns:
        An IterableScanResult indicating the outcome of the operation.
    """
    return ParseDirEntries(path, IO.GetFilePredicate(), action)
def ParseFiles(path: str, predicate: Predicate[os.DirEntry[str]], action: Method[os.DirEntry[str]]) -> IterableScanResult:
    """Executes the given action on files while all match the given predicate.

    Args:
        path: The directory path to scan.
        predicate: A function to test each file.
        action: A function to execute on each matching file.

    Returns:
        An IterableScanResult indicating the outcome of the operation.
    """
    return __ParseDirEntries(path, predicate, action, IO.GetFilePredicate())

def GetFindFromExtensionsPredicate(fileKind: FileKind, extensions: Iterable[str]) -> Predicate[os.DirEntry[str]]:
    """Creates a predicate to find entries matching specified file kind and extensions.

    Args:
        fileKind: The type of file system entry to match.
        extensions: The file extensions to match.

    Returns:
        A predicate function to test directory entries.

    Raises:
        ValueError: If the FileKind is not supported.
    """
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

        case _:
            raise ValueError("FileKind not supported.", fileKind)
def GetFindFromExtensionValuesPredicate(fileKind: FileKind, *extensions: str) -> Predicate[os.DirEntry[str]]:
    """Creates a predicate to find entries matching specified file kind and variadic extensions.

    Args:
        fileKind: The type of file system entry to match.
        *extensions: The file extensions to match.

    Returns:
        A predicate function to test directory entries.

    Raises:
        ValueError: If the FileKind is not supported.
    """
    return GetFindFromExtensionsPredicate(fileKind, extensions)

def __FindFromExtensions(path: str, predicate: Predicate[os.DirEntry[str]]) -> os.DirEntry[str]|None:
    result: DualResult[os.DirEntry[str]|None, IterableScanResult] = FindDirEntry(path, predicate)
    
    return result.GetKey() if result.GetValue() == IterableScanResult.Success else None

def FindFromExtensions(path: str, fileKind: FileKind, extensions: Iterable[str]) -> os.DirEntry[str]|None:
    """Finds the first entry matching the specified file kind and extensions.

    Args:
        path: The directory path to search.
        fileKind: The type of file system entry to match.
        extensions: The file extensions to match.

    Returns:
        The matching entry, or None if not found or scan failed.

    Raises:
        ValueError: If the FileKind is not supported.
    """
    return __FindFromExtensions(path, GetFindFromExtensionsPredicate(fileKind, extensions))
def FindFromExtensionValues(path: str, fileKind: FileKind, *extensions: str) -> os.DirEntry[str]|None:
    """Finds the first entry matching the specified file kind and variadic extensions.

    Args:
        path: The directory path to search.
        fileKind: The type of file system entry to match.
        *extensions: The file extensions to match.

    Returns:
        The matching entry, or None if not found or scan failed.

    Raises:
        ValueError: If the FileKind is not supported.
    """
    return FindFromExtensions(path, fileKind, extensions)

def FindFromExtensionsAndCheck(path: str, fileKind: FileKind, predicate: Predicate[os.DirEntry[str]], *extensions: str) -> os.DirEntry[str]|None:
    """Finds the first entry matching the specified file kind and variadic extensions, then checks with the given predicate.

    Args:
        path: The directory path to search.
        fileKind: The type of file system entry to match.
        predicate: An additional predicate to test after extension check.
        *extensions: The file extensions to match.

    Returns:
        The matching entry, or None if not found or scan failed.

    Raises:
        ValueError: If the FileKind is not supported.
    """
    return __FindFromExtensions(path, Delegates.GetAndAlsoPredicate(GetFindFromExtensionsPredicate(fileKind, extensions), predicate))
def FindFromExtensionsAndValidate(path: str, fileKind: FileKind, predicate: Predicate[os.DirEntry[str]], *extensions: str) -> os.DirEntry[str]|None:
    """Finds the first entry matching the specified file kind and variadic extensions, then validates with the given predicate.

    Args:
        path: The directory path to search.
        fileKind: The type of file system entry to match.
        predicate: A validation predicate to test after extension check.
        *extensions: The file extensions to match.

    Returns:
        The matching entry, or None if not found or scan failed.

    Raises:
        ValueError: If the FileKind is not supported.
    """
    return __FindFromExtensions(path, Delegates.GetAndPredicate(GetFindFromExtensionsPredicate(fileKind, extensions), predicate))

def CheckAndFindFromExtensions(path: str, fileKind: FileKind, predicate: Predicate[os.DirEntry[str]], *extensions: str) -> os.DirEntry[str]|None:
    """Checks entries with the given predicate first, then finds matching file kind and variadic extensions.

    Args:
        path: The directory path to search.
        fileKind: The type of file system entry to match.
        predicate: A predicate to check before extension matching.
        *extensions: The file extensions to match.

    Returns:
        The matching entry, or None if not found or scan failed.

    Raises:
        ValueError: If the FileKind is not supported.
    """
    return __FindFromExtensions(path, Delegates.GetAndAlsoPredicate(predicate, GetFindFromExtensionsPredicate(fileKind, extensions)))
def ValidateAndFindFromExtensions(path: str, fileKind: FileKind, predicate: Predicate[os.DirEntry[str]], *extensions: str) -> os.DirEntry[str]|None:
    """Validates entries with the given predicate first, then finds matching file kind and variadic extensions.

    Args:
        path: The directory path to search.
        fileKind: The type of file system entry to match.
        predicate: A validation predicate to test before extension matching.
        *extensions: The file extensions to match.

    Returns:
        The matching entry, or None if not found or scan failed.

    Raises:
        ValueError: If the FileKind is not supported.
    """
    return __FindFromExtensions(path, Delegates.GetAndPredicate(predicate, GetFindFromExtensionsPredicate(fileKind, extensions)))