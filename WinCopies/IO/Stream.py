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
        
    def __str__(self) -> str:
        match self:
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
                
    def GetMode(fileMode: str):
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

class FileType(Enum):
    Null = 0
    Text = 1
    Binary = 2
                
    def __str__(self) -> str:
        match self:
            case FileType.Text:
                return "t"
            case FileType.Binary:
                return "b"
            case _:
                return None
                
    def GetType(fileType: str):
        match fileType:
            case "t":
                return FileType.Text
            case "b":
                return FileType.Binary
            case _:
                return FileType.Null

class IStream(ABC):
    def __init__(self):
        pass
    @abstractmethod
    def IsOpen(self) -> bool:
        pass
    @abstractmethod
    def Close(self) -> None:
        pass

class File(IStream):
    def __init__(self, path: str):
        self._path : str = path
    
    @final
    def GetPath(self) -> str:
        return self._path
    
    @abstractmethod
    def Open(self, fileMode: FileMode) -> bool:
        pass
    
    @final
    def Delete(self) -> None:
        if self.IsOpen():
            self.Close()
            
        if path.isfile(self._path):            
            remove(self._path)
    
    def GetFile(onError: callable, message: str = "Enter a path: "):
        while True:
            try:
                return File(input(message))
            
            except IOError as e:
                if onError(e):
                    continue

                return None
    
    def OpenFile(fileMode: FileMode, fileType: FileType, onError: callable, message: str = "Enter a path: "):
        file: File|None = File.GetFile(onError, message)

        if file is None:
            return None
        
        file.Open(fileMode, fileType)

        return file
    
    def GetFileInitializer(fileMode: FileMode, fileType: FileType, onError: callable, message: str = "Enter a path: ") -> callable:
        file: File|None = File.GetFile(onError, message)
        
        if file is None:
            return None
        
        def open() -> File:
            file.Open(fileMode, fileType)

            return file
        
        return open