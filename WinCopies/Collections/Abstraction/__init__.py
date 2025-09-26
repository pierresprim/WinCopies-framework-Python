from typing import final

import WinCopies.Collections

from WinCopies.Collections import ICountable
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

class Countable(WinCopies.Collections.Countable):
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
    def Create(collection: ICountable) -> ICountable:
        return collection if type(collection) == Countable else Countable(collection)