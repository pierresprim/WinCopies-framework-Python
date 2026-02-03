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

from WinCopies import IDisposable, IStringable, Abstract
from WinCopies.String import StringifyIfNone
from WinCopies.Typing.Delegate import Function, Predicate

class FileMode(Enum):
    Null = 0
    Read = 1
    """Open the file for reading. Error if not existing."""
    Write = 2
    """Open the file for writing. Truncate if existing, create otherwise."""
    ReadWrite = 3
    """Open the file. Error if not existing."""
    Truncate = 4
    """Open the file. Truncate if existing, create otherwise."""
    Append = 5
    """Open the file for writing. Seek to EOF if existing, create otherwise."""
    AppendExtended = 6
    """Open the file. Seek to EOF if existing, create otherwise."""
    Create = 7
    """Open the file for writing. Error if existing."""
    CreateExtended = 7
    """Open the file. Error if existing."""
    
    def __str__(self) -> str:
        match self:
            case FileMode.Read:
                return 'r'
            case FileMode.Write:
                return 'w'
            case FileMode.Append:
                return 'a'
            case FileMode.Create:
                return 'x'
            case _:
                return ''
    
    def ToString(self, fileType: FileType) -> str:
        def getMode() -> str:
            return str(self)
        
        def _getValue(mode: str, extension: str) -> str:
            return f"{mode}{fileType}{extension}"
        def getValue(mode: str) -> str:
            return _getValue(mode, '')
        def getValueExtended(mode: str) -> str:
            return _getValue(mode, '+')
        
        match self:
            case FileMode.Read:
                return getValue(getMode())
            case FileMode.Write:
                return getValue(getMode())
            case FileMode.ReadWrite:
                return getValueExtended(str(FileMode.Read))
            case FileMode.Truncate:
                return getValueExtended(str(FileMode.Write))
            case FileMode.Append:
                return getValue(getMode())
            case FileMode.AppendExtended:
                return getValueExtended(str(FileMode.Append))
            case FileMode.Create:
                return getValue(getMode())
            case FileMode.CreateExtended:
                return getValueExtended(str(FileMode.Create))
            case _:
                return ''
    
    @staticmethod
    def GetMode(fileMode: str) -> FileMode:
        match fileMode:
            case 'r':
                return FileMode.Read
            case 'a':
                return FileMode.Append
            case 'w':
                return FileMode.Write
            case 'x':
                return FileMode.Create
            case 'r+':
                return FileMode.ReadWrite
            case 'w+':
                return FileMode.Truncate
            case 'a+':
                return FileMode.AppendExtended
            case 'x+':
                return FileMode.CreateExtended
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
    def GetType(fileType: str) -> FileType:
        match fileType:
            case 't':
                return FileType.Text
            case 'b':
                return FileType.Binary
            case _:
                return FileType.Null

class IStream(IDisposable):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def IsOpen(self) -> bool:
        pass

    @abstractmethod
    def Open(self) -> bool:
        pass
    @abstractmethod
    def TryOpen(self) -> bool|None:
        pass

    @abstractmethod
    def Close(self) -> bool:
        pass

    def Dispose(self) -> None:
        self.Close()

class IDataStream[T](IStream):
    def __init__(self) -> None:
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

class ITextStream(IDataStream[str]):
    def __init__(self) -> None:
        super().__init__()
    
    def TryWriteLine(self, text: str, eol: str = '\n') -> bool:
        return self.TryWrite(text + eol)
    def WriteLine(self, text: str) -> None:
        if not self.TryWriteLine(text):
            raise IOError()
class IBinaryStream(IDataStream[bytes]):
    def __init__(self) -> None:
        super().__init__()

class IFile(IStream):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetOpenType(self) -> FileType:
        pass
    
    @abstractmethod
    def OpenFile(self, fileMode: FileMode) -> bool:
        pass
    @abstractmethod
    def TryOpenFile(self, fileMode: FileMode) -> bool|None:
        pass

    @abstractmethod
    def GetPath(self) -> str:
        pass
    
    @abstractmethod
    def Delete(self) -> None:
        pass

class IFileStream[T](IDataStream[T], IFile):
    def __init__(self) -> None:
        super().__init__()

class File[T](Abstract, IFileStream[T]):
    __ASK_PATH_MESSAGE: str = "Enter a path: "
    
    def __init__(self, path: str) -> None:
        super().__init__()
        
        self.__path: str = path
    
    @final
    def TryOpen(self) -> bool|None:
        return self.TryOpenFile(FileMode.ReadWrite)
    @final
    def Open(self) -> bool:
        return self.OpenFile(FileMode.ReadWrite)
    
    def TryOpenFile(self, fileMode: FileMode) -> bool|None:
        try:
            return self.OpenFile(fileMode)
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
        
        stream.OpenFile(fileMode)

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
                raise ValueError(f"Wrong {FileType.__name__}.", fileType)
    
    @staticmethod
    def TryGetFile(fileType: FileType, validator: Predicate[str]|None = None, message: str = __ASK_PATH_MESSAGE) -> TextFile|BinaryFile:
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
    def GetFile(fileType: FileType, message: str = __ASK_PATH_MESSAGE) -> TextFile|BinaryFile:
        return File.__GetDelegate(fileType, input(message))()
    
    @staticmethod
    def TryCreate(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = __ASK_PATH_MESSAGE) -> TextFile|BinaryFile|None:
        def open() -> TextFile|BinaryFile:
            file: TextFile|BinaryFile = File.TryGetFile(fileType, validator, message)

            file.OpenFile(fileMode)

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
    def Create(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = __ASK_PATH_MESSAGE) -> TextFile|BinaryFile:
        def open() -> TextFile|BinaryFile:
            file: TextFile|BinaryFile = File.TryGetFile(fileType, validator, message)

            file.OpenFile(fileMode)

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
    def TryGetFileCreator(fileType: FileType, validator: Predicate[str]|None = None, message: str = __ASK_PATH_MESSAGE) -> Function[TextFile|BinaryFile]:
        return lambda: File.TryGetFile(fileType, validator, message)
    @staticmethod
    def GetFileCreator(fileType: FileType, message: str = __ASK_PATH_MESSAGE) -> Function[TextFile|BinaryFile]:
        return lambda: File.GetFile(fileType, message)
    
    @staticmethod
    def TryGetFileInitializer(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = __ASK_PATH_MESSAGE) -> Function[TextFile|BinaryFile|None]:
        return lambda: File.TryCreate(fileMode, fileType, validator, onError, message)
    @staticmethod
    def GetFileInitializer(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = __ASK_PATH_MESSAGE) -> Function[TextFile|BinaryFile|None]:
        return lambda: File.Create(fileMode, fileType, validator, onError, message)

class FileStream[TStream: IOBase, TData](File[TData]):
    def __init__(self, path: str) -> None:
        super().__init__(path)

        self.__stream: TStream|None = None
    
    @final
    def _GetStream(self) -> TStream|None:
        return self.__stream
    
    @final
    def IsOpen(self) -> bool:
        return self._GetStream() is not None
    
    @final
    def OpenFile(self, fileMode: FileMode) -> bool:
        if not self.IsOpen():
            self.__stream = cast(TStream, open(self.GetPath(), fileMode.ToString(self.GetOpenType())))

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

class TextFile(FileStream[TextIOWrapper, str], ITextStream):
    def __init__(self, path: str) -> None:
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

class BinaryFile(FileStream[BufferedIOBase, bytes], IBinaryStream):
    def __init__(self, path: str) -> None:
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

class IMemoryTextStream(ITextStream, IStringable):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def TryToString(self) -> str|None:
        pass
class MemoryTextStream(Abstract, IMemoryTextStream):
    def __init__(self) -> None:
        super().__init__()

        self.__stream: StringIO|None = None
    
    @final
    def _GetStream(self) -> StringIO|None:
        return self.__stream
    
    @final
    def IsOpen(self) -> bool:
        return self._GetStream() is not None
    
    @final
    def Open(self) -> bool:
        self.__stream = StringIO(newline='')

        return True
    @final
    def TryOpen(self) -> bool|None:
        return self.Open()
    
    @final
    def TryRead(self, size: int) -> str|None:
        stream: StringIO|None = self._GetStream()

        return stream.read(size) if stream is not None else None
    def Read(self, size: int) -> str:
        result: str|None = self.TryRead(size)

        if result is None:
            raise IOError()
        
        return result
    
    @final
    def TryWrite(self, value: str) -> bool:
        stream: StringIO|None = self._GetStream()

        if stream is not None:
            stream.write(value)

            return True
        
        return False
    @final
    def Write(self, value: str) -> None:
        if not self.TryWrite(value):
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