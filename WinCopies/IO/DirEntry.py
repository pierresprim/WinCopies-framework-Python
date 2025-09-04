# -*- coding: utf-8 -*-
"""
Created on Tue Jun 04 11:47:00 2024

@author: Pierre Sprimont
"""

from __future__ import annotations

import os

from typing import final

from WinCopies import IO, String
from WinCopies.Collections import Generator
from WinCopies.Collections.Enumeration import IIterable
from WinCopies.Collections.Enumeration.Extensions import RecursivelyIterable
from WinCopies.IO import IDirEntry
from WinCopies.String import StringifyIfNone

class IterableDirEntry(RecursivelyIterable[IDirEntry], IDirEntry):
    def __init__(self):
        super().__init__()
    
    @final
    def _AsRecursivelyIterable(self, container: IDirEntry) -> IIterable[IDirEntry]:
        return container
    
    @final
    def IsDirectory(self):
        return os.path.isdir(self.GetPath())
    
    @final
    def TryGetIterator(self) -> Generator[IterableDirEntry]|None:
        return (SystemDirEntry(dirEntry) for dirEntry in os.scandir(self.GetPath())) if self.IsDirectory() else None

class SystemDirEntry(IterableDirEntry):
    def __init__(self, dirEntry: os.DirEntry[str]):
        super().__init__()

        self.__dirEntry: os.DirEntry[str] = dirEntry
    
    @final
    def GetPath(self) -> str:
        return self.__dirEntry.path
    
    @final
    def GetDirectory(self) -> str:
        return os.path.dirname(self.GetPath())
    
    @final
    def GetName(self) -> str:
        return IO.GetFileName(self.__dirEntry.name)
    
    @final
    def GetExtension(self) -> str:
        return IO.GetExtension(self.GetPath())
    
    @final
    def GetFullName(self) -> str:
        return self.__dirEntry.name

class DirEntry(IterableDirEntry):
    def __init__(self, directory: str|None, name: str|None, extension: str|None):
        super().__init__()
        
        self.__directory: str = StringifyIfNone(directory)
        self.__name: str = StringifyIfNone(name)
        self.__extension: str = StringifyIfNone(extension)
    
    @classmethod
    def FromFileName(cls, directory: str, fileName: str):
        entry = os.path.splitext(fileName)
        
        return cls(directory, entry[0], IO.GetExtensionFromArray(entry))
    
    @classmethod
    def FromPath(cls, path: str):
        entry = os.path.split(path)
        
        return cls.FromFileName(entry[0], entry[1])
    
    @classmethod
    def FromSystemDirEntry(cls, dirEntry: os.DirEntry[str]):
        entry: SystemDirEntry = SystemDirEntry(dirEntry)
        array = os.path.splitext(entry.GetFullName())
        
        return cls(entry.GetDirectory(), array[0], IO.GetExtensionFromArray(array))
    
    @final
    def GetPath(self) -> str:
        return os.path.join(self.__directory, self.GetFullName())
    
    @final
    def GetDirectory(self) -> str:
        return self.__directory
    
    @final
    def GetName(self) -> str:
        return self.__name
    
    @final
    def GetExtension(self) -> str:
        return self.__extension
    
    @final
    def GetFullName(self) -> str:
        return String.SurroundWith(self.__name, None if self.__extension == '' else '.', self.__extension)