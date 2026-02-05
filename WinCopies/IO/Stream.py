# -*- coding: utf-8 -*-
"""
Created on Thu May 25 10:31:11 2023

@author: Pierre Sprimont
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Buffer
from enum import Enum, Flag, auto
from io import SEEK_SET, SEEK_CUR, SEEK_END, IOBase, TextIOBase, BufferedIOBase, StringIO
from os import remove, path
from types import TracebackType
from typing import cast, final

from WinCopies import IInterface, IDisposableObject, IDisposable, IStringable, Abstract
from WinCopies.Enum import TryGetFieldFromValue
from WinCopies.String import StringifyIfNone
from WinCopies.Typing.Delegate import Function, Predicate, Method, IFunction, ValueFunctionUpdater

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

class StreamPosition(Enum):
    Null = 0
    Start = 1
    Current = 2
    End = 3

    def TryToInt(self) -> int|None:
        match self:
            case StreamPosition.Start:
                return SEEK_SET
            case StreamPosition.Current:
                return SEEK_CUR
            case StreamPosition.End:
                return SEEK_END
            case _:
                return None
    def ForceToInt(self) -> int:
        value: int|None = self.TryToInt()

        return SEEK_SET if value is None else value
    
    @staticmethod
    def TryFromInt(offset: int) -> StreamPosition:
        value: StreamPosition|None = TryGetFieldFromValue(StreamPosition, offset + 1)

        return StreamPosition.Null if value is None else value

class StreamProperties(Flag):
    Null = 0
    Readable = auto()
    Writable = auto()
    Seekable = auto()

class IAsStream[T: IOBase](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsStream(self) -> T:
        pass

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
    def Flush(self) -> bool:
        pass

    @abstractmethod
    def Close(self) -> bool:
        pass

    def Dispose(self) -> None:
        self.Close()

class IStreamObject(IStream):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetProperties(self) -> StreamProperties:
        pass

    @final
    def CheckProperty(self, property: StreamProperties) -> bool:
        return property in self.GetProperties()
class ISeekable(IStreamObject):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryGetPosition(self) -> int|None:
        pass
    @abstractmethod
    def TrySetPosition(self, offset: int, whence: StreamPosition = StreamPosition.Start) -> bool:
        pass

class IStreamReader[T](IStream):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def TryRead(self, size: int) -> T|None:
        pass
    @abstractmethod
    def Read(self, size: int) -> T:
        pass
class IStreamWriter[T](IStream):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryWrite(self, value: T) -> int|None:
        pass
    @abstractmethod
    def Write(self, value: T) -> None:
        pass

class IDataStreamAbstract[TIn, TOut](IStreamReader[TOut], IStreamWriter[TIn], IStreamObject):
    def __init__(self) -> None:
        super().__init__()
class IDataStream[T](IDataStreamAbstract[T, T]):
    def __init__(self) -> None:
        super().__init__()

class ISeekableStreamAbstract[TIn, TOut](IDataStreamAbstract[TIn, TOut], ISeekable):
    def __init__(self) -> None:
        super().__init__()
class ISeekableStream[T](ISeekableStreamAbstract[T, T], IDataStream[T], ISeekable):
    def __init__(self) -> None:
        super().__init__()

class ITextReader(IStreamReader[str]):
    def __init__(self) -> None:
        super().__init__()
class ITextWriter(IStreamWriter[str]):
    def __init__(self) -> None:
        super().__init__()
    
    def TryWriteLine(self, text: str, eol: str = '\n') -> int|None:
        return self.TryWrite(text + eol)
    def WriteLine(self, text: str) -> None:
        if not self.TryWriteLine(text):
            raise IOError()

class IBinaryReader(IStreamReader[bytes]):
    def __init__(self) -> None:
        super().__init__()
class IBinaryWriter(IStreamWriter[Buffer]):
    def __init__(self) -> None:
        super().__init__()

class ITextStream(IDataStream[str], ITextReader, ITextWriter):
    def __init__(self) -> None:
        super().__init__()
class IBinaryStream(IDataStreamAbstract[Buffer, bytes], IBinaryReader, IBinaryWriter):
    def __init__(self) -> None:
        super().__init__()

class ISeekableTextReader(ITextReader, ISeekable):
    def __init__(self) -> None:
        super().__init__()
class ISeekableTextWriter(ITextWriter, ISeekable):
    def __init__(self) -> None:
        super().__init__()

class ISeekableBinaryReader(IBinaryReader, ISeekable):
    def __init__(self) -> None:
        super().__init__()
class ISeekableBinaryWriter(IBinaryWriter, ISeekable):
    def __init__(self) -> None:
        super().__init__()

class ISeekableTextStream(ISeekableStream[str], ITextStream):
    def __init__(self) -> None:
        super().__init__()
class ISeekableBinaryStream(ISeekableStreamAbstract[Buffer, bytes], IBinaryStream):
    def __init__(self) -> None:
        super().__init__()

class IExtendedStreamAbstract[TIn, TOut](IDataStreamAbstract[TIn, TOut]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryReadToEnd(self) -> TOut|None:
        pass
class IExtendedStream[T](IExtendedStreamAbstract[T, T], IDataStream[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryReadToEnd(self) -> T|None:
        pass

class ISeekableExtendedStreamAbstract[TIn, TOut](IExtendedStreamAbstract[TIn, TOut], ISeekableStreamAbstract[TIn, TOut]):
    def __init__(self) -> None:
        super().__init__()
class ISeekableExtendedStream[T](ISeekableExtendedStreamAbstract[T, T], IExtendedStream[T], ISeekableStream[T]):
    def __init__(self) -> None:
        super().__init__()

class IExtendedTextStream(IExtendedStream[str], ITextStream):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryReadLine(self, size: int|None) -> str|None:
        pass
class IExtendedBinaryStream(IExtendedStreamAbstract[Buffer, bytes], IBinaryStream):
    def __init__(self) -> None:
        super().__init__()

class IExtendedSeekableTextStream(ISeekableExtendedStream[str], IExtendedTextStream, ISeekableTextStream):
    def __init__(self) -> None:
        super().__init__()
class IExtendedSeekableBinaryStream(ISeekableExtendedStreamAbstract[Buffer, bytes], IExtendedBinaryStream, ISeekableBinaryStream):
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

class IFileStreamAbstract[TIn, TOut](IDataStreamAbstract[TIn, TOut], IFile):
    def __init__(self) -> None:
        super().__init__()
class IFileStream[T](IFileStreamAbstract[T, T], IDataStream[T]):
    def __init__(self) -> None:
        super().__init__()

class ITextFile(IFileStream[str], ITextStream):
    def __init__(self) -> None:
        super().__init__()
class IBinaryFile(IFileStreamAbstract[Buffer, bytes], IBinaryStream):
    def __init__(self) -> None:
        super().__init__()

class StreamBase[T: ISeekable](IOBase, IDisposableObject):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetStream(self) -> T:
        pass
    
    @property
    @final
    def closed(self) -> bool:
        return not self._GetStream().IsOpen()
    
    @final
    def CheckProperty(self, property: StreamProperties) -> bool:
        return property in self._GetStream().GetProperties()
    
    @final
    def fileno(self) -> int:
        raise OSError("Invalid operation.")
    
    @final
    def isatty(self) -> bool:
        return False
    
    @final
    def seekable(self) -> bool:
        return self.CheckProperty(StreamProperties.Seekable)
    
    @final
    def readable(self) -> bool:
        return self.CheckProperty(StreamProperties.Readable)
    @final
    def writable(self) -> bool:
        return self.CheckProperty(StreamProperties.Writable)
    
    @final
    def tell(self) -> int:
        offset: int|None = self._GetStream().TryGetPosition()

        return 0 if offset is None else offset
    @final
    def seek(self, offset: int, whence: int = 0) -> int:
        if self._GetStream().TrySetPosition(offset, StreamPosition.TryFromInt(whence)):
            return self.tell()
        
        raise OSError("Seek failed.")
    
    @final
    def flush(self) -> None:
        self._GetStream().Flush()
    
    @final
    def close(self) -> None:
        self._GetStream().Close()
    @final
    def Dispose(self) -> None:
        self._GetStream().Dispose()
    
    @final
    def __exit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None, exc_tb: TracebackType|None) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)

        self.Dispose()

class TextStreamBase[T: IExtendedSeekableTextStream](StreamBase[T], TextIOBase):
    def __init__(self) -> None:
        super().__init__()
    
    @final # type: ignore[misc] # Ambiguity IOBase (attribute) vs TextIOBase (method)
    def read(self, size: int|None = -1) -> str:
        stream: T = self._GetStream()

        result: str|None = stream.TryReadToEnd() if size is None or size < 0 else stream.TryRead(size)
        
        return '' if result is None else result
    
    @final
    def readline(self, size: int = -1) -> str: # type: ignore[override]
        result: str|None = self._GetStream().TryReadLine(size if size >= 0 else None)

        return '' if result is None else result
    
    @final # type: ignore[misc] # Ambiguity IOBase (attribute) vs TextIOBase (method)
    def write(self, s: str) -> int:
        result: int|None = self._GetStream().TryWrite(s)

        if result is None:
            raise IOError("Write operation failed.")
        
        return result
class BinaryStreamBase[T: IExtendedSeekableBinaryStream](StreamBase[T], BufferedIOBase):
    def __init__(self) -> None:
        super().__init__()
    
    @final # type: ignore[misc] # Ambiguity IOBase (attribute) vs BufferedIOBase (method)
    def read(self, size: int|None = -1) -> bytes:
        stream: T = self._GetStream()
        
        result: bytes|None = stream.TryReadToEnd() if size is None or size < 0 else stream.TryRead(size)
        
        return b'' if result is None else result
    
    @final # type: ignore[misc] # Ambiguity IOBase (attribute) vs BufferedIOBase (method)
    def write(self, b: Buffer) -> int:
        result: int|None = self._GetStream().TryWrite(b)
        
        if result is None:
            raise IOError("Write operation failed.")
        
        return result

class IStreamCookie[T: IOBase](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetStream(self) -> T|None:
        pass

class StreamAbstractBase[T: IOBase](IOBase):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetInnerStream(self) -> T|None:
        pass
class StreamAbstract[T: IOBase](IOBase):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetStream(self) -> IStreamCookie[T]:
        pass
    @final
    def _GetInnerStream(self) -> T|None:
        return self._GetStream().GetStream()
    
    @property
    @final
    def closed(self) -> bool:
        return self._GetInnerStream() is None
    
    @final
    def fileno(self) -> int:
        raise OSError("Invalid operation.")
    
    @final
    def isatty(self) -> bool:
        stream: T|None = self._GetInnerStream()

        return stream is not None and stream.isatty()
    
    @final
    def seekable(self) -> bool:
        stream: T|None = self._GetInnerStream()

        return stream is not None and stream.seekable()
    
    @final
    def readable(self) -> bool:
        stream: T|None = self._GetInnerStream()

        return stream is not None and stream.readable()
    @final
    def writable(self) -> bool:
        stream: T|None = self._GetInnerStream()

        return stream is not None and stream.writable()
    
    @final
    def tell(self) -> int:
        stream: T|None = self._GetInnerStream()

        if stream is None:
            raise OSError("Invalid operation.")

        return stream.tell()
    @final
    def seek(self, offset: int, whence: int = 0) -> int:
        stream: T|None = self._GetInnerStream()

        if stream is None:
            raise OSError("Invalid operation.")

        return stream.seek(offset, whence)
    
    @final
    def flush(self) -> None:
        stream: T|None = self._GetInnerStream()

        if stream is not None:
            stream.flush()
    
    @final
    def close(self) -> None:
        stream: T|None = self._GetInnerStream()

        if stream is not None:
            stream.close()

class ReaderAbstract[T: IOBase](StreamAbstractBase[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def readable(self) -> bool:
        stream: T|None = self._GetInnerStream()

        return stream is not None and stream.readable()
class WriterAbstract[T: IOBase](StreamAbstractBase[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def writable(self) -> bool:
        stream: T|None = self._GetInnerStream()

        return stream is not None and stream.writable()

class Stream[T: IOBase](StreamAbstract[T]):
    def __init__(self) -> None:
        super().__init__()

class TextReaderAbstract[T: TextIOBase](StreamAbstractBase[T], TextIOBase):
    def __init__(self) -> None:
        super().__init__()
    
    @final # type: ignore[misc] # Ambiguity IOBase (attribute) vs TextIOBase (method)
    def read(self, size: int|None = -1) -> str:
        stream: T|None = self._GetInnerStream()

        return '' if stream is None else stream.read(size)
    
    @final
    def readline(self, size: int = -1) -> str: # type: ignore[override]
        stream: T|None = self._GetInnerStream()

        return '' if stream is None else stream.readline(size)
class TextWriterAbstract[T: TextIOBase](StreamAbstractBase[T], TextIOBase):
    def __init__(self) -> None:
        super().__init__()
    
    @final # type: ignore[misc] # Ambiguity IOBase (attribute) vs TextIOBase (method)
    def write(self, s: str) -> int:
        stream: T|None = self._GetInnerStream()

        if stream is None:
            raise IOError("Write operation failed.")
        
        return stream.write(s)

class BinaryReaderAbstract[T: BufferedIOBase](StreamAbstractBase[T], BufferedIOBase):
    def __init__(self) -> None:
        super().__init__()
    
    @final # type: ignore[misc] # Ambiguity IOBase (attribute) vs BufferedIOBase (method)
    def read(self, size: int|None = -1) -> bytes:
        stream: T|None = self._GetInnerStream()
        
        return b'' if stream is None else stream.read(size)
class BinaryWriterAbstract[T: BufferedIOBase](StreamAbstractBase[T], BufferedIOBase):
    def __init__(self) -> None:
        super().__init__()
    
    @final # type: ignore[misc] # Ambiguity IOBase (attribute) vs BufferedIOBase (method)
    def write(self, b: Buffer) -> int:
        stream: T|None = self._GetInnerStream()

        if stream is None:
            raise IOError("Write operation failed.")
        
        return stream.write(b)

class TextStreamAbstract[T: TextIOBase](Stream[T], TextReaderAbstract[T], TextWriterAbstract[T]):
    def __init__(self, cookie: IStreamCookie[T]) -> None:
        super().__init__()

        self.__cookie: IStreamCookie[T] = cookie
    
    @final
    def _GetStream(self) -> IStreamCookie[T]:
        return self.__cookie
class TextStream(TextStreamAbstract[TextIOBase]):
    def __init__(self, cookie: IStreamCookie[TextIOBase]) -> None:
        super().__init__(cookie)

class BinaryStreamAbstract[T: BufferedIOBase](Stream[T], BufferedIOBase):
    def __init__(self, cookie: IStreamCookie[T]) -> None:
        super().__init__()

        self.__cookie: IStreamCookie[T] = cookie
    
    @final
    def _GetStream(self) -> IStreamCookie[T]:
        return self.__cookie
    
    @final # type: ignore[misc] # Ambiguity IOBase (attribute) vs BufferedIOBase (method)
    def read(self, size: int|None = -1) -> bytes:
        stream: T|None = self._GetInnerStream()
        
        return b'' if stream is None else stream.read(size)
    
    @final # type: ignore[misc] # Ambiguity IOBase (attribute) vs BufferedIOBase (method)
    def write(self, b: Buffer) -> int:
        stream: T|None = self._GetInnerStream()

        if stream is None:
            raise IOError("Write operation failed.")
        
        return stream.write(b)
class BinaryStream(BinaryStreamAbstract[BufferedIOBase]):
    def __init__(self, cookie: IStreamCookie[BufferedIOBase]) -> None:
        super().__init__(cookie)

class FileBase[TIn, TOut](Abstract, IFileStreamAbstract[TIn, TOut]):
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
    def _Read(self, size: int) -> TOut:
        pass

    @final
    def TryRead(self, size: int) -> TOut|None:
        return self._Read(size) if self.IsOpen() else None
    def Read(self, size: int) -> TOut:
        result: TOut|None = self.TryRead(size)

        if result is None:
            raise IOError()
        
        return result
    
    @abstractmethod
    def TryWrite(self, value: TIn) -> int|None:
        pass
    def Write(self, value: TIn) -> None:
        if self.TryWrite(value) is None:
            raise IOError()
    
    @final
    def Delete(self) -> None:
        if self.IsOpen():
            self.Close()
            
        if path.isfile(self.__path):            
            remove(self.__path)
class File[T](FileBase[T, T], IFileStream[T]):
    def __init__(self, path: str) -> None:
        super().__init__(path)

__ASK_PATH_MESSAGE: str = "Enter a path: "

def TryInitializeAs(path: str, fileType: FileType) -> TextFile|BinaryFile|None:
    match fileType:
        case FileType.Text:
            return TextFile(path)
        
        case FileType.Binary:
            return BinaryFile(path)
        
        case _:
            return None
def TryOpenAs(path: str, fileMode: FileMode, fileType: FileType) -> TextFile|BinaryFile|None:
    stream: TextFile|BinaryFile|None = TryInitializeAs(path, fileType)

    if stream is None:
        return None
    
    stream.OpenFile(fileMode)

    return stream

def __GetDelegate(fileType: FileType, path: str) -> Function[TextFile]|Function[BinaryFile]:
    match fileType:
        case FileType.Text:
            return lambda: TextFile(path)
        case FileType.Binary:
            return lambda: BinaryFile(path)

        case _:
            # Invalid arguments; no initializer could be created.
            raise ValueError(f"Wrong {FileType.__name__}.", fileType)

def TryGetFile(fileType: FileType, validator: Predicate[str]|None = None, message: str = __ASK_PATH_MESSAGE) -> TextFile|BinaryFile:
    if validator is None:
        # No path validator callback provided. Directly create file.
        return GetFile(fileType, message)

    def askPath() -> str|None:
        path: str = input(message)

        return path if validator(path) else None
    
    path: str|None = askPath()
    
    while path is None:
        path = askPath()
    
    return __GetDelegate(fileType, path)()

def GetFile(fileType: FileType, message: str = __ASK_PATH_MESSAGE) -> TextFile|BinaryFile:
    return __GetDelegate(fileType, input(message))()

def TryCreate(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = __ASK_PATH_MESSAGE) -> TextFile|BinaryFile|None:
    def open() -> TextFile|BinaryFile:
        file: TextFile|BinaryFile = TryGetFile(fileType, validator, message)

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

def Create(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = __ASK_PATH_MESSAGE) -> TextFile|BinaryFile:
    def open() -> TextFile|BinaryFile:
        file: TextFile|BinaryFile = TryGetFile(fileType, validator, message)

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

def TryGetFileCreator(fileType: FileType, validator: Predicate[str]|None = None, message: str = __ASK_PATH_MESSAGE) -> Function[TextFile|BinaryFile]:
    return lambda: TryGetFile(fileType, validator, message)
def GetFileCreator(fileType: FileType, message: str = __ASK_PATH_MESSAGE) -> Function[TextFile|BinaryFile]:
    return lambda: GetFile(fileType, message)

def TryGetFileInitializer(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = __ASK_PATH_MESSAGE) -> Function[TextFile|BinaryFile|None]:
    return lambda: TryCreate(fileMode, fileType, validator, onError, message)
def GetFileInitializer(fileMode: FileMode, fileType: FileType, validator: Predicate[str]|None = None, onError: Predicate[IOError]|None = None, message: str = __ASK_PATH_MESSAGE) -> Function[TextFile|BinaryFile|None]:
    return lambda: Create(fileMode, fileType, validator, onError, message)

class IStreamBaseAbstract[TStream: IOBase, TIn, TOut](IDataStreamAbstract[TIn, TOut]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetStream(self) -> TStream|None:
        pass

    @abstractmethod
    def _GetExtraProperties(self) -> StreamProperties:
        pass
    
    @final
    def GetProperties(self) -> StreamProperties:
        stream: TStream|None = self._GetStream()
        properties: StreamProperties = StreamProperties.Null

        if stream is not None:
            if stream.readable():
                properties |= StreamProperties.Readable
            if stream.writable():
                properties |= StreamProperties.Writable

        return properties | self._GetExtraProperties()
class IStreamBase[TStream: IOBase, TData](IStreamBaseAbstract[TStream, TData, TData], IDataStream[TData]):
    def __init__(self) -> None:
        super().__init__()

class ISeekableStreamBaseAbstract[TStream: IOBase, TIn, TOut](IStreamBaseAbstract[TStream, TIn, TOut], ISeekableStreamAbstract[TIn, TOut]):
    def __init__(self) -> None:
        super().__init__()
    
    def _GetExtraProperties(self) -> StreamProperties:
        stream: IOBase|None = self._GetStream()

        if stream is None:
            return StreamProperties.Null
        
        properties: StreamProperties = self.GetProperties()

        return properties | StreamProperties.Seekable if stream.seekable() else properties
    
    @final
    def TryGetPosition(self) -> int|None:
        stream: TStream|None = self._GetStream()

        return None if stream is None else stream.tell()
    @final
    def TrySetPosition(self, offset: int, whence: StreamPosition = StreamPosition.Start) -> bool:
        stream: TStream|None = self._GetStream()

        if stream is None:
            return False
        
        if stream.seekable():
            stream.seek(offset, whence.ForceToInt())

            return True
        
        return False
class ISeekableStreamBase[TStream: IOBase, TData](ISeekableStreamBaseAbstract[TStream, TData, TData], IStreamBase[TStream, TData], ISeekableStream[TData]):
    def __init__(self) -> None:
        super().__init__()

class FileStreamBase[TStream: IOBase, TIn, TOut](FileBase[TIn, TOut], ISeekableStreamBaseAbstract[TStream, TIn, TOut], IAsStream[TStream]):
    @final
    class __Cookie[_TStream: IOBase, _TIn, _TOut](Abstract, IStreamCookie[_TStream]):
        def __init__(self, stream: FileStreamBase[_TStream, _TIn, _TOut]) -> None:
            super().__init__()

            self.__stream: FileStreamBase[_TStream, _TIn, _TOut] = stream
        
        def GetStream(self) -> _TStream|None:
            return self.__stream._GetStream()
    
    def __init__(self, path: str) -> None:
        super().__init__(path)

        self.__stream: TStream|None = None
        self.__cookie: IStreamCookie[TStream] = FileStreamBase[TStream, TIn, TOut].__Cookie(self)
    
    @abstractmethod
    def _Open(self, path: str, fileMode: str) -> TStream:
        pass
    
    @final
    def _GetStream(self) -> TStream|None:
        return self.__stream
    @final
    def _GetCookie(self) -> IStreamCookie[TStream]:
        return self.__cookie
    
    @final
    def IsOpen(self) -> bool:
        return self._GetStream() is not None
    
    @final
    def OpenFile(self, fileMode: FileMode) -> bool:
        if not self.IsOpen():
            self.__stream = self._Open(self.GetPath(), fileMode.ToString(self.GetOpenType()))

        return True
    
    @abstractmethod
    def _Write(self, stream: TStream, value: TIn) -> int:
        pass
    @final
    def TryWrite(self, value: TIn) -> int|None:
        stream: TStream|None = self._GetStream()

        return None if stream is None else self._Write(stream, value)
    
    @final
    def Flush(self) -> bool:
        stream: TStream|None = self._GetStream()

        if stream is None:
            return False
        
        stream.flush()
        
        return True
    
    @final
    def Close(self) -> bool:
        stream: TStream|None = self._GetStream()

        if stream is None:
            return False
        
        stream.close()
        self.__stream = None

        return True
class FileStream[TStream: IOBase, TData](FileStreamBase[TStream, TData, TData], ISeekableStreamBase[TStream, TData]):
    def __init__(self, path: str) -> None:
        super().__init__(path)

class StreamUpdater[T: IOBase](ValueFunctionUpdater[T]):
    def __init__(self, cookie: IStreamCookie[T], updater: Method[IFunction[T]]) -> None:
        super().__init__(updater)

        self.__cookie: IStreamCookie[T] = cookie
    
    @final
    def _GetCookie(self) -> IStreamCookie[T]:
        return self.__cookie

@final
class TextStreamUpdater(StreamUpdater[TextIOBase]):
    def __init__(self, cookie: IStreamCookie[TextIOBase], updater: Method[IFunction[TextIOBase]]) -> None:
        super().__init__(cookie, updater)
    
    def _GetValue(self) -> TextIOBase:
        return TextStream(self._GetCookie())
@final
class BinaryStreamUpdater(StreamUpdater[BufferedIOBase]):
    def __init__(self, cookie: IStreamCookie[BufferedIOBase], updater: Method[IFunction[BufferedIOBase]]) -> None:
        super().__init__(cookie, updater)
    
    def _GetValue(self) -> BufferedIOBase:
        return BinaryStream(self._GetCookie())

class TextFile(FileStream[TextIOBase, str], ITextFile):
    def __init__(self, path: str) -> None:
        def update(func: IFunction[TextIOBase]) -> None:
            self.__stream = func
        
        super().__init__(path)
        
        self.__stream: IFunction[TextIOBase] = TextStreamUpdater(self._GetCookie(), update)
    
    @final
    def _Open(self, path: str, fileMode: str) -> TextIOBase:
        return cast(TextIOBase, open(path, fileMode))
    
    @final
    def GetOpenType(self) -> FileType:
        return FileType.Text
    
    @final
    def _Read(self, size: int) -> str:
        stream: TextIOBase|None = self._GetStream()

        return '' if stream is None else stream.read(size)
    @final
    def _Write(self, stream: TextIOBase, value: str) -> int:
        return stream.write(value)
    
    @final
    def AsStream(self) -> TextIOBase:
        return self.__stream.GetValue()

class BinaryFile(FileStreamBase[BufferedIOBase, Buffer, bytes], IBinaryFile):
    def __init__(self, path: str) -> None:
        def update(func: IFunction[BufferedIOBase]) -> None:
            self.__stream = func
        
        super().__init__(path)
        
        self.__stream: IFunction[BufferedIOBase] = BinaryStreamUpdater(self._GetCookie(), update)
    
    @final
    def _Open(self, path: str, fileMode: str) -> BufferedIOBase:
        return cast(BufferedIOBase, open(path, fileMode))
    
    @final
    def GetOpenType(self) -> FileType:
        return FileType.Binary
    
    @final
    def _Read(self, size: int) -> bytes:
        stream: BufferedIOBase|None = self._GetStream()

        return bytes(0) if stream is None else stream.read(size)
    @final
    def _Write(self, stream: BufferedIOBase, value: Buffer) -> int:
        return stream.write(value)
    
    @final
    def AsStream(self) -> BufferedIOBase:
        return self.__stream.GetValue()

class IMemoryTextStream(ITextStream, IStringable):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def TryToString(self) -> str|None:
        pass
class MemoryTextStream(Abstract, IMemoryTextStream, ISeekableStreamBase[StringIO, str], IAsStream[TextIOBase]):
    @final
    class __Cookie(Abstract, IStreamCookie[TextIOBase]):
        def __init__(self, stream: MemoryTextStream) -> None:
            super().__init__()

            self.__stream: MemoryTextStream = stream
        
        def GetStream(self) -> TextIOBase|None:
            return self.__stream._GetStream()
    
    def __init__(self) -> None:
        def update(func: IFunction[TextIOBase]) -> None:
            self.__streamUpdater = func
        
        super().__init__()

        self.__stream: StringIO|None = None
        self.__streamUpdater: IFunction[TextIOBase] = TextStreamUpdater(MemoryTextStream.__Cookie(self), update) # type: ignore[no-redef]
    
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
    def TryWrite(self, value: str) -> int|None:
        stream: StringIO|None = self._GetStream()

        return None if stream is None else stream.write(value)
    @final
    def Write(self, value: str) -> None:
        if self.TryWrite(value) is None:
            raise IOError()
    
    @final
    def TryToString(self) -> str|None:
        stream: StringIO|None = self._GetStream()

        return None if stream is None else stream.getvalue()
    @final
    def ToString(self) -> str:
        return StringifyIfNone(self.TryToString())
    
    @final
    def Flush(self) -> bool:
        stream: StringIO|None = self._GetStream()

        if stream is None:
            return False
        
        stream.flush()

        return True
    
    @final
    def Close(self) -> bool:
        stream: StringIO|None = self._GetStream()
        
        if stream is None:
            return False
        
        stream.close()
        self.__stream = None

        return True
    
    @final
    def AsStream(self) -> TextIOBase:
        return self.__streamUpdater.GetValue()

class AbstractStreamBase[TIn, TOut](Abstract, IStream):
    def __init__(self, stream: IDataStreamAbstract[TIn, TOut]) -> None:
        super().__init__()

        self.__stream: IDataStreamAbstract[TIn, TOut] = stream
    
    @final
    def _GetStream(self) -> IDataStreamAbstract[TIn, TOut]:
        return self.__stream

    @final
    def IsOpen(self) -> bool:
        return self._GetStream().IsOpen()

    @final
    def Open(self) -> bool:
        return self._GetStream().Open()
    @final
    def TryOpen(self) -> bool|None:
        return self._GetStream().TryOpen()
    
    @final
    def Flush(self) -> bool:
        return self._GetStream().Flush()

    @final
    def Close(self) -> bool:
        return self._GetStream().Close()

    def Dispose(self) -> None:
        self._GetStream().Dispose()
class AbstractStream[T](AbstractStreamBase[T, T]):
    def __init__(self, stream: IDataStream[T]) -> None:
        super().__init__(stream)

class StreamReaderBase[TIn, TOut](AbstractStreamBase[TIn, TOut], IStreamReader[TOut]):
    def __init__(self, stream: IDataStreamAbstract[TIn, TOut]) -> None:
        super().__init__(stream)

    @final
    def TryRead(self, size: int) -> TOut|None:
        return self._GetStream().TryRead(size)
    @final
    def Read(self, size: int) -> TOut:
        result: TOut|None = self.TryRead(size)

        if result is None:
            raise IOError()
        
        return result
    
    @staticmethod
    def TryCreate(stream: IDataStreamAbstract[TIn, TOut]) -> IStreamReader[TOut]|None:
        return StreamReaderBase[TIn, TOut](stream) if StreamProperties.Readable in stream.GetProperties() else None
class StreamReader[T](StreamReaderBase[T, T]):
    def __init__(self, stream: IDataStream[T]) -> None:
        super().__init__(stream)
    
    @staticmethod
    def TryCreateStream(stream: IDataStream[T]) -> IStreamReader[T]|None:
        return StreamReader[T](stream) if StreamProperties.Readable in stream.GetProperties() else None

class StreamWriterBase[TIn, TOut](AbstractStreamBase[TIn, TOut], IStreamWriter[TIn]):
    def __init__(self, stream: IDataStreamAbstract[TIn, TOut]) -> None:
        super().__init__(stream)

    @final
    def TryWrite(self, value: TIn) -> int|None:
        return self._GetStream().TryWrite(value)
    @final
    def Write(self, value: TIn) -> None:
        if self.TryWrite(value) is None:
            raise IOError()
    
    @staticmethod
    def TryCreate(stream: IDataStreamAbstract[TIn, TOut]) -> IStreamWriter[TIn]|None:
        return StreamWriterBase[TIn, TOut](stream) if StreamProperties.Writable in stream.GetProperties() else None
class StreamWriter[T](StreamWriterBase[T, T]):
    def __init__(self, stream: IDataStream[T]) -> None:
        super().__init__(stream)
    
    @staticmethod
    def TryCreateStream(stream: IDataStream[T]) -> IStreamWriter[T]|None:
        return StreamWriter[T](stream) if StreamProperties.Writable in stream.GetProperties() else None

class TextReader(StreamReader[str], ITextReader):
    def __init__(self, stream: IDataStream[str]) -> None:
        super().__init__(stream)
    
    @staticmethod
    def TryCreateTextReader(stream: ITextStream) -> ITextReader|None:
        return TextReader(stream) if StreamProperties.Readable in stream.GetProperties() else None
class TextWriter(StreamWriter[str], ITextWriter):
    def __init__(self, stream: IDataStream[str]) -> None:
        super().__init__(stream)
    
    @staticmethod
    def TryCreateTextWriter(stream: ITextStream) -> ITextWriter|None:
        return TextWriter(stream) if StreamProperties.Writable in stream.GetProperties() else None

class BinaryReader(StreamReaderBase[Buffer, bytes], IBinaryReader):
    def __init__(self, stream: IDataStreamAbstract[Buffer, bytes]) -> None:
        super().__init__(stream)
    
    @staticmethod
    def TryCreateBinaryReader(stream: IBinaryStream) -> IBinaryReader|None:
        return BinaryReader(stream) if StreamProperties.Readable in stream.GetProperties() else None
class BinaryWriter(StreamWriterBase[Buffer, bytes], IBinaryWriter):
    def __init__(self, stream: IDataStreamAbstract[Buffer, bytes]) -> None:
        super().__init__(stream)
    
    @staticmethod
    def TryCreateBinaryWriter(stream: IBinaryStream) -> IBinaryWriter|None:
        return BinaryWriter(stream) if StreamProperties.Writable in stream.GetProperties() else None