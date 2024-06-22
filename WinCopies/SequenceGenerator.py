from typing import final

from WinCopies.Collections import Enumeration

class SequenceGenerator:
    from ._SequenceGenerator._Data import _Data
    from . import _SequenceGenerator
    
    def __init__(self, pattern: str, start: int, count: int):
        SequenceGenerator._ValidateIndexes(start, count)
        
        self.__pattern: str = pattern
        self.__start: int = start
        self.__count: int = count
        self.__data: SequenceGenerator._Data = None
    
    def _ValidateIndexes(start: int, count: int) -> None:
        if start <= 0 or count < 0:
            raise ValueError
    
    def _GetData(self) -> _Data:
        return self.__data
        
    @final
    def GetPattern(self) -> str:
        return self.__pattern

    @final
    def GetStart(self) -> int:
        return self.__start
    @final
    def SetStart(self, start: int) -> int:
        SequenceGenerator._ValidateIndexes(start, self.__count)
        self.__start = start

    @final
    def GetCount(self) -> int:
        return self.__count
    @final
    def SetCount(self, count: int) -> None:
        SequenceGenerator._ValidateIndexes(self.__start, count)
        self.__count = count

    @final
    def __iter__(self) -> Enumeration.IEnumerator:
        if self.__data == None:
            self.__data = SequenceGenerator._Data(self.__pattern)
        
        return SequenceGenerator._SequenceGenerator._Enumerator(self)