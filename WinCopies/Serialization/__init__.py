from abc import abstractmethod
from typing import final

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Enumeration.Recursive import IRecursivelyScannable
from WinCopies.IO.Stream import IStreamReader

class IDataReader[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Parse(self) -> IRecursivelyScannable[T]:
        pass

class DataReader[TItem, TData](Abstract, IDataReader[TItem]):
    def __init__(self, stream: IStreamReader[TData]) -> None:
        super().__init__()

        self.__stream: IStreamReader[TData] = stream
    
    @final
    def _GetStream(self) -> IStreamReader[TData]:
        return self.__stream
    
    @abstractmethod
    def _Parse(self, stream: IStreamReader[TData]) -> IRecursivelyScannable[TItem]:
        pass
    
    @final
    def TryParse(self) -> IRecursivelyScannable[TItem]|None:
        stream: IStreamReader[TData] = self._GetStream()

        return self._Parse(stream) if stream.IsOpen() or stream.TryOpen() else None