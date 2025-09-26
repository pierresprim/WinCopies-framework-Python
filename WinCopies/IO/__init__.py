# -*- coding: utf-8 -*-
"""
Created on Tue Jun 04 11:47:00 2024

@author: Pierre Sprimont
"""

import os

from abc import abstractmethod
from collections.abc import Iterable
from enum import Enum
from typing import Sequence, AnyStr

from WinCopies.Collections.Enumeration.Extensions import IRecursivelyEnumerable
from WinCopies.Collections.Loop import ForEachItemUntil
from WinCopies.Typing.Delegate import Predicate
from WinCopies.Typing.Pairing import DualValueNullableBool

class FileKind(Enum):
    Null = 0
    Drive = 1
    Folder = 2
    File = 3
    Link = 4
    Junction = 5
    Archive = 6

class IDirEntry(IRecursivelyEnumerable['IDirEntry']):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetPath(self) -> str:
        pass
    @abstractmethod
    def GetDirectory(self) -> str:
        pass
    @abstractmethod
    def GetName(self) -> str:
        pass
    @abstractmethod
    def GetExtension(self) -> str:
        pass
    @abstractmethod
    def GetFullName(self) -> str:
        pass
    
    @abstractmethod
    def IsDirectory(self) -> bool:
        pass

    def __str__(self) -> str:
        return self.GetPath()

def TryGetFileNameFromArray(entry: Sequence[str]|None) -> str|None:
    return None if entry is None or len(entry) < 2 else entry[0]
def TryGetFileName(name: str) -> str|None:
    return TryGetFileNameFromArray(os.path.splitext(name))

def GetFileNameFromArray(entry: Sequence[str]|None) -> str:
    return '' if entry is None or len(entry) < 1 else entry[0]
def GetFileName(name: str) -> str:
    return GetFileNameFromArray(os.path.splitext(name))

def TryGetFullExtensionFromArray(entry: Sequence[str]|None) -> str|None:
    return None if entry is None or len(entry) < 2 else entry[1]
def TryGetFullExtension(name: str) -> str|None:
    return TryGetFullExtensionFromArray(os.path.splitext(name))

def GetFullExtensionFromArray(entry: Sequence[str]|None) -> str:
    result: str|None = TryGetFullExtensionFromArray(entry)

    return '' if result is None else result
def GetFullExtension(name: str) -> str:
    return GetFullExtensionFromArray(os.path.splitext(name))

def TryGetExtensionFromArray(entry: Sequence[str]|None) -> str|None:
    result: str|None = TryGetFullExtensionFromArray(entry)

    return None if result is None or len(result) < 2 else result[1:]
def TryGetExtension(name: str) -> str|None:
    return TryGetExtensionFromArray(os.path.splitext(name))

def GetExtensionFromArray(entry: Sequence[str]) -> str:
    result: str|None = TryGetExtensionFromArray(entry)
    
    return '' if result is None else result
def GetExtension(name: str) -> str:
    return GetExtensionFromArray(os.path.splitext(name))

def TryCheckExtension(path: str, extensions: Iterable[str]) -> bool|None:
    extension: str|None = TryGetExtension(path)
    
    return extension is not None and ForEachItemUntil(extensions, lambda fileExtension: extension == fileExtension)
def TryCheckExtensionOf(path: str, *extensions: str) -> bool|None:
    return TryCheckExtension(path, extensions)

def TryCreateDirectory(directory: str) -> bool|None:
    try:
        if os.path.exists(directory):
            return False
    
        os.mkdir(directory)

        return True
    
    except FileExistsError:
        return None

def TryCreateSubdirectory(directory: str, subdirectory: str) -> DualValueNullableBool[str]:
    directory = os.path.join(directory, subdirectory)

    return DualValueNullableBool(directory, TryCreateDirectory(directory))

def TryCreateSubdirEntry(dirEntry: IDirEntry, subdirectory: str) -> DualValueNullableBool[str]:
    return TryCreateSubdirectory(dirEntry.GetDirectory(), subdirectory)

def TryRemoveDirectory(directory: str) -> bool|None:
    try:
        if os.path.exists(directory):
            os.rmdir(directory)

            return True
        
        return False
    
    except IOError:
        return None

def GetDirectoryPredicate() -> Predicate[os.DirEntry[AnyStr]]:
    return lambda entry: entry.is_dir()
def GetFilePredicate() -> Predicate[os.DirEntry[AnyStr]]:
    return lambda entry: entry.is_file()