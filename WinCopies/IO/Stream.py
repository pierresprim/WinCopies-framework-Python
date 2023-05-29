# -*- coding: utf-8 -*-
"""
Created on Thu May 25 10:31:11 2023

@author: Pierre Sprimont
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import final
from os import remove, path
from io import TextIOWrapper

class FileMode(Enum):
    Null = 0
    Read = 1
    Append = 2
    Write = 3
    Create = 4

class FileType(Enum):
    Null = 0
    Text = 1
    Binary = 2

class IStream(ABC):
    def __init__(self):
        pass
    @abstractmethod
    def IsOpen(self) -> bool:
        pass
    @abstractmethod
    def Open(self) -> None:
        pass
    @abstractmethod
    def Close(self) -> None:
        pass

class File(IStream):
    def __init__(self, path: str):
        self._path : str = path
        self._textStream: TextIOWrapper = None
        
    def GetStrMode(fileMode : FileMode) -> str:
        match fileMode:
            case FileMode.Read:
                return "r"
            case FileMode.Append:
                return "a"
            case FileMode.Write:
                return "w"
            case FileMode.Create:
                return "x"
            case _:
                return None
                
    def GetMode(fileMode : str) -> FileMode:
        match fileMode:
            case "r":
                return FileMode.Read
            case "a":
                return FileMode.Append
            case "w":
                return FileMode.Write
            case "x":
                return FileMode.Create
            case _:
                return FileMode.Null
                
    def GetStrType(fileType : FileType) -> str:
        match fileType:
            case FileType.Text:
                return "t"
            case FileType.Binary:
                return "b"
            case _:
                return None
                
    def GetType(fileType : str) -> FileType:
        match fileType:
            case "t":
                return FileType.Text
            case "b":
                return FileType.Binary
            case _:
                return FileType.Null
    
    @final
    def GetPath(self) -> str:
        return self._path
    
    @final
    def IsOpen(self) -> bool:
        return not self._textStream is None
    
    @final
    def Open(self, fileMode: FileMode, fileType: FileType) -> None:
        if self.IsOpen():
            return
        
        self._textStream = open(self._path, File.GetStrMode(fileMode) + File.GetStrType(fileType))
    
    @final
    def Write(self, text: str) -> None:
        if (self.IsOpen()):
            self._textStream.write(text)
        else:
            raise IOError()
    
    @final
    def Close(self) -> None:
        if self.IsOpen():
            self._textStream.close()
            self._textStream = None
    
    @final
    def Delete(self) -> None:
        if self.IsOpen():
            self.Close()
            
        if path.isfile(self._path):            
            remove(self._path)