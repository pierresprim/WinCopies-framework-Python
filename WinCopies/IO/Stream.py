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
from typing import Callable

from WinCopies.Typing import constant, singleton

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
    @singleton
    @final
    class __Consts:
        @constant
        def ASK_PATH_MESSAGE() -> str:
            return "Enter a path: "
    
    CONSTS = __Consts()

    def __init__(self, path: str):
        self._path : str = path
    
    @abstractmethod
    def GetOpenType(self) -> FileType:
        pass
    
    @final
    def _Open(self, fileMode: FileMode) -> IOBase|None:
        
        return None if self.IsOpen() else open(self._path, str(fileMode) + str(self.GetOpenType()))
    @abstractmethod
    def Open(self, fileMode: FileMode) -> bool:
        pass

    @final
    def GetPath(self) -> str:
        return self._path
    
    def TryInitializeAs(path: str, fileType: FileType):
        match fileType:
            case FileType.Text:
                return TextFile(path)
            
            case FileType.Binary:
                return BinaryFile(path)
        
        return None
    def TryOpenAs(path: str, fileMode: FileMode, fileType: FileType):
        stream: File|None = File.TryInitializeAs(path, fileType)

        if stream is None:
            return None
        
        stream.Open(fileMode)

        return stream
    
    @final
    def Delete(self) -> None:
        if self.IsOpen():
            self.Close()
            
        if path.isfile(self._path):            
            remove(self._path)

    def __GetDelegate(fileType: FileType, message: str):
        def prompt() -> str:
            return input(message)
        
        match fileType:
            case FileType.Text:
                return lambda: TextFile(prompt())
            case FileType.Binary:
                return lambda: BinaryFile(prompt())
        
        return None
    
    def TryGetFile(fileType: FileType, onError: Callable[[IOError], bool]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE):
        getFile: Callable[[], File]|None = File.__GetDelegate(fileType, message)

        if getFile is None:
            "Invalid arguments; no initializer could be created."
            return None
        
        if onError is None:
            "No IO error callback provided. Trying only one time."
            try:
                return getFile()
            
            except IOError:
                return None

        "IO error callback provided. Trying until initializer or IO error callback validated."
        while True:
            try:
                return getFile()
            
            except IOError as e:
                if onError(e):
                    continue

                return None
    
    def GetFile(fileType: FileType, onError: Callable[[IOError], bool]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE):
        getFile: Callable[[], File]|None = File.__GetDelegate(fileType, message)

        if getFile is None:
            return None
        
        if onError is None:
            return getFile()

        while True:
            try:
                return getFile()
            
            except IOError as e:
                if onError(e):
                    continue

                raise e
    
    def TryOpenFile(fileMode: FileMode, fileType: FileType, onError: Callable[[IOError], bool]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE):
        file: File|None = File.TryGetFile(fileType, onError, message)

        if file is None:
            return None
        
        file.Open(fileMode)

        return file
    
    def OpenFile(fileMode: FileMode, fileType: FileType, onError: Callable[[IOError], bool]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE):
        file: File|None = File.GetFile(fileType, onError, message)
        
        file.Open(fileMode)

        return file
    
    def TryGetFileInitializer(fileMode: FileMode, fileType: FileType, onError: Callable[[IOError], bool]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE) -> callable:
        file: File|None = File.TryGetFile(fileType, onError, message)
        
        if file is None:
            return None
        
        def open() -> File:
            file.Open(fileMode)

            return file
        
        return open
    
    def GetFileInitializer(fileMode: FileMode, fileType: FileType, onError: Callable[[IOError], bool]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE) -> callable:
        file: File|None = File.GetFile(fileType, onError, message)
        
        def open() -> File:
            file.Open(fileMode)

            return file
        
        return open
    
    def TryGetFileCreator(fileMode: FileMode, fileType: FileType, onError: Callable[[IOError], bool]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE) -> callable:
        return lambda: File.TryGetFileInitializer(fileMode, fileType, onError, message)
    
    def TryGetFileOpener(fileMode: FileMode, fileType: FileType, onError: Callable[[IOError], bool]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE):
        return lambda: File.TryOpenFile(fileMode, fileType, onError, message)