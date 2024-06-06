# -*- coding: utf-8 -*-
"""
Created on Tue Jun 04 11:47:00 2024

@author: Pierre Sprimont
"""
import os
from abc import ABC, abstractmethod

from WinCopies import DualValueNullableBool

class IDirEntry(ABC):
    def __init__(self):
        pass
    
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

    def __str__(self) -> str:
        return self.GetPath()

def TryGetExtensionFromArray(entry) -> str|None:
    return entry[1] if len(entry) > 1 else None

def TryGetExtension(name: str) -> str|None:
    return TryGetExtensionFromArray(os.path.splitext(name))

def GetExtensionFromArray(entry) -> str:
    result: str|None = TryGetExtensionFromArray(entry)
    
    return '' if result is None else result

def GetExtension(name: str) -> str:
    result: str|None = TryGetExtension(name)
    
    return '' if result is None else result

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