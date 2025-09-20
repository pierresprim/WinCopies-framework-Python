from __future__ import annotations

from typing import final

from WinCopies.Collections import ICountable
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

class Countable(ICountable):
    def __init__(self, collection: ICountable):
        EnsureDirectModuleCall()

        super().__init__()

        self.__collection: ICountable = collection
    
    @final
    def GetCount(self) -> int:
        return self.__collection.GetCount()
    
    @staticmethod
    def Create(collection: ICountable) -> ICountable:
        return collection if type(collection) == Countable else Countable(collection)