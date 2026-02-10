from abc import abstractmethod
from typing import final

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Enumeration.Recursive import IRecursivelyScannable
from WinCopies.IO.Stream import ITextStreamReader

class IDataReader[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Parse(self) -> IRecursivelyScannable[T]:
        pass

class DataReader[T](Abstract, IDataReader[T]):
    def __init__(self, stream: ITextStreamReader) -> None:
        super().__init__()

        self.__stream: ITextStreamReader = stream
    
    @final
    def _GetStream(self) -> ITextStreamReader:
        return self.__stream
    
    @abstractmethod
    def _Parse(self, stream: ITextStreamReader) -> IRecursivelyScannable[T]:
        pass
    
    @final
    def TryParse(self) -> IRecursivelyScannable[T]|None:
        stream: ITextStreamReader = self._GetStream()

        return self._Parse(stream) if stream.IsOpen() or stream.TryOpen() else None