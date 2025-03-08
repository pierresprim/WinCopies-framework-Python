# -*- coding: utf-8 -*-
"""
Created on Thu May 25 10:31:11 2023

@author: Pierre Sprimont
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import final
from os import remove, path
from io import IOBase, TextIOWrapper, BufferedIOBase
from typing import Self

from WinCopies import IDisposable
from WinCopies.Typing.Decorators import constant, MetaSingleton
from WinCopies.Typing.Delegate import Predicate

class FileMode(Enum):
    Null = 0
    Read = 1
    Append = 2
    Write = 3
    Create = 4
    
    def __str__(self) -> str:
        match self:
            case FileMode.Read:
                return 'r'
            case FileMode.Append:
                return 'a'
            case FileMode.Write:
                return 'w'
            case FileMode.Create:
                return 'x'
            case _:
                return None
                
    def GetMode(fileMode: str):
        match fileMode:
            case 'r':
                return FileMode.Read
            case 'a':
                return FileMode.Append
            case 'w':
                return FileMode.Write
            case 'x':
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
                return 't'
            case FileType.Binary:
                return 'b'
            case _:
                return None
                
    def GetType(fileType: str):
        match fileType:
            case 't':
                return FileType.Text
            case 'b':
                return FileType.Binary
            case _:
                return FileType.Null

class IStream(IDisposable):
    def __init__(self):
        pass

    @abstractmethod
    def IsOpen(self) -> bool:
        pass

    @abstractmethod
    def Close(self) -> bool:
        pass

    def Dispose(self) -> None:
        return self.Close()

class File(IStream):
    @final
    class __Consts(metaclass=MetaSingleton[Self]):
        @constant
        def ASK_PATH_MESSAGE() -> str:
            return "Enter a path: "
    
    CONSTS = __Consts()

    def __init__(self, path: str):
        self.__path: str = path
    
    @abstractmethod
    def GetOpenType(self) -> FileType:
        pass
    
    @final
    def _Open(self, fileMode: FileMode) -> IOBase|None:
        return None if self.IsOpen() else open(self.__path, str(fileMode) + str(self.GetOpenType()))
    
    @abstractmethod
    def Open(self, fileMode: FileMode) -> bool:
        pass
    def TryOpen(self, fileMode: FileMode) -> bool|None:
        try:
            return self.Open(fileMode)
        except IOError:
            return None

    @final
    def GetPath(self) -> str:
        return self.__path
    
    @staticmethod
    def TryInitializeAs(path: str, fileType: FileType):
        match fileType:
            case FileType.Text:
                return TextFile(path)
            
            case FileType.Binary:
                return BinaryFile(path)
        
        return None
    @staticmethod
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
            
        if path.isfile(self.__path):            
            remove(self.__path)

    @staticmethod
    def __GetDelegate(fileType: FileType, path: str):
        match fileType:
            case FileType.Text:
                return lambda: TextFile(path)
            case FileType.Binary:
                return lambda: BinaryFile(path)
        
        # Invalid arguments; no initializer could be created.
        raise ValueError(f"Wrong {type(FileType).name}.", fileType)
    
    @staticmethod
    def TryGetFile(fileType: FileType, validator: Predicate[str]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE):
        if validator is None:
            # No path validator callback provided. Directly create file.
            return File.GetFile(fileType, message)

        def askPath() -> str|None:
            path: str = input(message)

            return path if validator(path) else None
        
        path: str|None = askPath()
        
        while path is None:
            path = askPath()
        
        return File.__GetDelegate(fileType, path)()
    
    @staticmethod
    def GetFile(fileType: FileType, message: str = CONSTS.ASK_PATH_MESSAGE):
        return File.__GetDelegate(fileType, input(message))()
    
    @staticmethod
    def TryOpenFile(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE):
        def open() -> File:
            file: File = File.TryGetFile(fileType, validator, message)

            file.Open(fileMode)

            return file
        
        if onError is None:
            # No IO error callback provided. Try only one time.
            try:
                return open()
            
            except IOError:
                return None
        
        # IO error callback provided. Try until initializer validated or IO error callback invalidated.
        while True:
            try:
                return open()
            
            except IOError as e:
                if onError(e):
                    continue

                return None
    
    @staticmethod
    def OpenFile(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE):
        def open() -> File:
            file: File = File.TryGetFile(fileType, validator, message)

            file.Open(fileMode)

            return file
        
        if onError is None:
            # No IO error callback provided. Try only one time.
            return open()

        # IO error callback provided. Try until initializer validated or IO error callback invalidated.
        while True:
            try:
                return open()
            
            except IOError as e:
                if onError(e):
                    continue

                raise e
    
    @staticmethod
    def TryGetFileCreator(fileType: FileType, validator: Predicate[str]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE):
        return lambda: File.TryGetFile(fileType, validator, message)
    @staticmethod
    def GetFileCreator(fileType: FileType, message: str = CONSTS.ASK_PATH_MESSAGE):
        return lambda: File.GetFile(fileType, message)
    
    @staticmethod
    def TryGetFileInitializer(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE):
        return lambda: File.TryOpenFile(fileMode, fileType, validator, onError, message)
    @staticmethod
    def GetFileInitializer(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE):
        return lambda: File.OpenFile(fileMode, fileType, validator, onError, message)

class TextFile(File):
    def __init__(self, path: str):
        super().__init__(path)
        
        self.__stream: TextIOWrapper|None = None
    
    @final
    def GetOpenType(self) -> FileType:
        return FileType.Text
    
    @final
    def IsOpen(self) -> bool:
        return self.__stream is not None
    
    @final
    def Open(self, fileMode: FileMode) -> bool:
        self.__stream = self._Open(fileMode)

        return self.__stream is not None
    
    @final
    def TryRead(self, size: int = -1) -> str|None:
        return self.__stream.read(size) if self.IsOpen() else None
    
    @final
    def Read(self, size: int = -1) -> str:
        result: str|None = self.TryRead(size)

        if result is None:
            raise IOError
        
        return result
    
    @final
    def TryWrite(self, text: str) -> bool:
        if self.IsOpen():
            self.__stream.write(text)

            return True
        else:
            return False
    @final
    def TryWriteLine(self, text: str) -> bool:
        return self.Write(text + '\n')
    
    @final
    def Write(self, text: str) -> None:
        if not self.TryWrite(text):
            raise IOError
    @final
    def WriteLine(self, text: str) -> None:
        if not self.TryWriteLine(text):
            raise IOError
    
    @final
    def Close(self) -> bool:
        if self.IsOpen():
            self.__stream.close()
            self.__stream = None

            return True
        
        return False

class BinaryFile(File):
    def __init__(self, path: str):
        super().__init__(path)
        
        self.__stream: BufferedIOBase|None = None
    
    @final
    def GetOpenType(self) -> FileType:
        return FileType.Binary
    
    @final
    def IsOpen(self) -> bool:
        return self.__stream is not None
    
    @final
    def Open(self, fileMode: FileMode) -> bool:
        self.__stream = self._Open(fileMode)

        return self.__stream is not None
    
    @final
    def TryRead(self, size: int = -1) -> bytes|None:
        return self.__stream.read(size) if self.IsOpen() else None
    
    @final
    def Read(self, size: int = -1) -> bytes:
        result: bytes|None = self.TryRead(size)

        if result is None:
            raise IOError
        
        return result
    
    @final
    def TryWrite(self, data: bytes) -> bool:
        if self.IsOpen():
            self.__stream.write(data)

            return True
        
        else:
            return False
    @final
    def TryWriteLine(self, data: bytes) -> bool:
        return self.Write(data + '\n')
    
    @final
    def Write(self, data: bytes) -> None:
        if not self.TryWrite(data):
            raise IOError
    @final
    def WriteLine(self, data: bytes) -> None:
        if not self.TryWriteLine(data):
            raise IOError
    
    @final
    def Close(self) -> bool:
        if self.IsOpen():
            self.__stream.close()
            self.__stream = None

            return True
        
        return False