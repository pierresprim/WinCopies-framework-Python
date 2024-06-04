# -*- coding: utf-8 -*-
"""
Created on Tue Jun 04 11:47:00 2024

@author: Pierre Sprimont
"""

from typing import final
from abc import ABC, abstractmethod
import os

from WinCopies import IO

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

class SystemDirEntry(IDirEntry):
    def __init__(self, dirEntry: os.DirEntry):
        self.__dirEntry: os.DirEntry = dirEntry
    
    @final
    def GetPath(self) -> str:
        return self.__dirEntry.path
    
    @final
    def GetDirectory(self) -> str:
        return os.path.dirname(self.GetPath())
    
    @final
    def GetName(self) -> str:
        return os.path.splitext(self.__dirEntry.name)[0]
    
    @final
    def GetExtension(self) -> str:
        return IO.GetExtension(self.GetPath())
    
    @final
    def GetFullName(self) -> str:
        return self.__dirEntry.name

class DirEntry(IDirEntry):
    def __init__(self, directory: str, name: str, extension: str):
        self.__directory = directory
        self.__name = name
        self.__extension = extension
    
    @classmethod
    def FromFileName(cls, directory: str, fileName: str):
        entry = os.path.splitext(fileName)
        
        return cls(directory, entry[0], IO.GetExtensionFromArray(entry))
    
    @classmethod
    def FromPath(cls, path: str):
        entry = os.path.split(path)
        
        return cls.FromFileName(entry[0], entry[1])
    
    @classmethod
    def FromSystemDirEntry(cls, dirEntry: os.DirEntry):
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
        return self.__name + self.__extension