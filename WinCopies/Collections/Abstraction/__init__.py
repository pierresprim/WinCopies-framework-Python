from typing import final

from WinCopies.Collections import ICountable, Countable as CountableBase
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

class Countable(CountableBase):
    def __init__(self, collection: ICountable):
        EnsureDirectModuleCall()

        super().__init__()

        self.__collection: ICountable = collection
    
    @final
    def _GetCollection(self) -> ICountable:
        return self.__collection
    
    @final
    def GetCount(self) -> int:
        return self._GetCollection().GetCount()
    
    @staticmethod
    def Create(collection: ICountable) -> CountableBase:
        return collection if type(collection) == Countable else Countable(collection)
    @staticmethod
    def TryCreate(collection: ICountable|None) -> CountableBase|None:
        return None if collection is None else Countable.Create(collection)