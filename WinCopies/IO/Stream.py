# -*- coding: utf-8 -*-
"""
Created on Thu May 25 10:31:11 2023

@author: Pierre Sprimont
"""

from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from io import IOBase, TextIOWrapper, BufferedIOBase, StringIO
from os import remove, path
from typing import cast, final

from WinCopies import IDisposable, IStringable
from WinCopies.String import StringifyIfNone
from WinCopies.Typing.Decorators import constant, SingletonMeta
from WinCopies.Typing.Delegate import Function, Predicate

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
                return ''
    
    @staticmethod
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
                return ''
    
    @staticmethod
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
        super().__init__()

    @abstractmethod
    def IsOpen(self) -> bool:
        pass

    @abstractmethod
    def Close(self) -> bool:
        pass

    def Dispose(self) -> None:
        self.Close()

class IFile(IStream):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetOpenType(self) -> FileType:
        pass
    
    @abstractmethod
    def Open(self, fileMode: FileMode) -> bool:
        pass
    @abstractmethod
    def TryOpen(self, fileMode: FileMode) -> bool|None:
        pass

    @abstractmethod
    def GetPath(self) -> str:
        pass
    
    @abstractmethod
    def Delete(self) -> None:
        pass

class IFileStream[T](IFile):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def TryRead(self, size: int) -> T|None:
        pass
    @abstractmethod
    def Read(self, size: int) -> T:
        pass
    
    @abstractmethod
    def TryWrite(self, value: T) -> bool:
        pass
    @abstractmethod
    def Write(self, value: T) -> None:
        pass

class File[T](IFileStream[T]):
    @final
    class __Consts(metaclass=SingletonMeta):
        @constant
        def ASK_PATH_MESSAGE() -> str:
            return "Enter a path: "
    
    CONSTS = __Consts()

    def __init__(self, path: str):
        super().__init__()
        
        self.__path: str = path
    
    def TryOpen(self, fileMode: FileMode) -> bool|None:
        try:
            return self.Open(fileMode)
        except IOError:
            return None

    @final
    def GetPath(self) -> str:
        return self.__path
    
    @abstractmethod
    def _Read(self, size: int) -> T:
        pass

    @final
    def TryRead(self, size: int) -> T|None:
        return self._Read(size) if self.IsOpen() else None
    def Read(self, size: int) -> T:
        result: T|None = self.TryRead(size)

        if result is None:
            raise IOError()
        
        return result
    
    @abstractmethod
    def _Write(self, value: T) -> None:
        pass
    
    def TryWrite(self, value: T) -> bool:
        if self.IsOpen():
            self._Write(value)

            return True
        
        else:
            return False
    def Write(self, value: T) -> None:
        if not self.TryWrite(value):
            raise IOError()
    
    @staticmethod
    def TryInitializeAs(path: str, fileType: FileType) -> TextFile|BinaryFile|None:
        match fileType:
            case FileType.Text:
                return TextFile(path)
            
            case FileType.Binary:
                return BinaryFile(path)
            
            case _:
                return None
    @staticmethod
    def TryOpenAs(path: str, fileMode: FileMode, fileType: FileType) -> TextFile|BinaryFile|None:
        stream: TextFile|BinaryFile|None = File.TryInitializeAs(path, fileType)

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
    def __GetDelegate(fileType: FileType, path: str) -> Function[TextFile]|Function[BinaryFile]:
        match fileType:
            case FileType.Text:
                return lambda: TextFile(path)
            case FileType.Binary:
                return lambda: BinaryFile(path)

            case _:
                # Invalid arguments; no initializer could be created.
                raise ValueError(f"Wrong {type(FileType).name}.", fileType)
    
    @staticmethod
    def TryGetFile(fileType: FileType, validator: Predicate[str]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE) -> TextFile|BinaryFile:
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
    def TryOpenFile(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE) -> TextFile|BinaryFile|None:
        def open() -> TextFile|BinaryFile:
            file: TextFile|BinaryFile = File.TryGetFile(fileType, validator, message)

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
    def OpenFile(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE) -> TextFile|BinaryFile:
        def open() -> TextFile|BinaryFile:
            file: TextFile|BinaryFile = File.TryGetFile(fileType, validator, message)

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
    def TryGetFileCreator(fileType: FileType, validator: Predicate[str]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE) -> Function[TextFile|BinaryFile]:
        return lambda: File.TryGetFile(fileType, validator, message)
    @staticmethod
    def GetFileCreator(fileType: FileType, message: str = CONSTS.ASK_PATH_MESSAGE) -> Function[TextFile|BinaryFile]:
        return lambda: File.GetFile(fileType, message)
    
    @staticmethod
    def TryGetFileInitializer(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE):
        return lambda: File.TryOpenFile(fileMode, fileType, validator, onError, message)
    @staticmethod
    def GetFileInitializer(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = CONSTS.ASK_PATH_MESSAGE):
        return lambda: File.OpenFile(fileMode, fileType, validator, onError, message)

class FileStream[TStream: IOBase, TData](File[TData]):
    def __init__(self, path: str):
        super().__init__(path)

        self.__stream: TStream|None = None
    
    @final
    def _GetStream(self) -> TStream|None:
        return self.__stream
    
    @final
    def IsOpen(self) -> bool:
        return self._GetStream() is not None
    
    @final
    def Open(self, fileMode: FileMode) -> bool:
        if not self.IsOpen():
            self.__stream = cast(TStream, open(self.GetPath(), str(fileMode) + str(self.GetOpenType())))

        return True
    
    @final
    def Close(self) -> bool:
        if self.IsOpen():
            stream: TStream|None = self._GetStream()

            if stream is not None:
                stream.close()
                self.__stream = None

            return True
        
        return False

class TextFile(FileStream[TextIOWrapper, str]):
    def __init__(self, path: str):
        super().__init__(path)
    
    @final
    def GetOpenType(self) -> FileType:
        return FileType.Text
    
    @final
    def _Read(self, size: int) -> str:
        stream: TextIOWrapper|None = self._GetStream()

        return '' if stream is None else stream.read(size)
    @final
    def _Write(self, value: str) -> None:
        stream: TextIOWrapper|None = self._GetStream()

        if stream is not None:
            stream.write(value)
    
    @final
    def TryWriteLine(self, text: str, eol: str = '\n') -> bool:
        return self.TryWrite(text + eol)
    @final
    def WriteLine(self, text: str) -> None:
        if not self.TryWriteLine(text):
            raise IOError()

class BinaryFile(FileStream[BufferedIOBase, bytes]):
    def __init__(self, path: str):
        super().__init__(path)
    
    @final
    def GetOpenType(self) -> FileType:
        return FileType.Binary
    
    @final
    def _Read(self, size: int) -> bytes:
        stream: BufferedIOBase|None = self._GetStream()

        return bytes(0) if stream is None else stream.read(size)
    @final
    def _Write(self, value: bytes) -> None:
        stream: BufferedIOBase|None = self._GetStream()

        if stream is not None:
            stream.write(value)

class MemoryTextStream(IStream, IStringable):
    def __init__(self):
        super().__init__()

        self.__stream: StringIO|None = None
    
    @final
    def _GetStream(self) -> StringIO|None:
        return self.__stream
    
    @final
    def IsOpen(self) -> bool:
        return self._GetStream() is not None
    
    @final
    def Open(self) -> None:
        self.__stream = StringIO()
    
    @final
    def TryRead(self, size: int) -> str|None:
        stream: StringIO|None = self._GetStream()

        return stream.read(size) if self.IsOpen() and stream is not None else None
    def Read(self, size: int) -> str:
        result: str|None = self.TryRead(size)

        if result is None:
            raise IOError()
        
        return result
    
    @final
    def TryWrite(self, text: str) -> bool:
        stream: StringIO|None = self._GetStream()

        if self.IsOpen() and stream is not None:
            stream.write(text)

            return True
        
        return False
    @final
    def Write(self, text: str) -> None:
        if not self.TryWrite(text):
            raise IOError()

    @final
    def TryWriteLine(self, text: str, eol: str = '\n') -> bool:
        return self.TryWrite(text + eol)
    @final
    def WriteLine(self, text: str) -> None:
        if not self.TryWriteLine(text):
            raise IOError()
    
    @final
    def TryToString(self) -> str|None:
        if self.IsOpen():
            stream: StringIO|None = self._GetStream()

            return None if stream is None else stream.getvalue()

        return None
    @final
    def ToString(self) -> str:
        return StringifyIfNone(self.TryToString())
    
    @final
    def Close(self) -> bool:
        if self.IsOpen():
            stream: StringIO|None = self._GetStream()
            
            if stream is not None:
                stream.close()
                self.__stream = None

            return True
        
        return False