from typing import final

from WinCopies.Collections.Core import ICountable, Countable

@final
class _Countable(Countable):
    def __init__(self, collection: ICountable) -> None:
        super().__init__()

        self.__collection: ICountable = collection
    
    @final
    def GetCount(self) -> int:
        return self.__collection.GetCount()

def CreateCountable(collection: ICountable) -> ICountable:
    return collection if type(collection) == _Countable else _Countable(collection)
def TryCreateCountable(collection: ICountable|None) -> ICountable|None:
    return None if collection is None else CreateCountable(collection)