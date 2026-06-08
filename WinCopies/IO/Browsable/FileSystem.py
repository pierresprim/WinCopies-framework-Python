from os import pathsep
from typing import final

from WinCopies import Abstract
from WinCopies.Collections.Enumeration import IEnumerable
from WinCopies.Collections.Extensions import ISortedList
from WinCopies.IO import IDirEntry
from WinCopies.IO.Browsable import BrowsableUpdater, IBrowsableNameInfo, IBrowsablePathInfo, IExplorable, Browsable
from WinCopies.Typing.Delegate import IFunction, Method

class DirEntryNameInfo(Abstract, IBrowsableNameInfo):
    def __init__(self, entry: IDirEntry) -> None:
        super().__init__()

        self.__entry: IDirEntry = entry
    
    @final
    def GetName(self) -> str: return self.__entry.GetName()
    @final
    def GetExtension(self) -> str: return self.__entry.GetExtension()
    
    @final
    def GetFullName(self) -> str: return self.__entry.GetFullName()

class DirEntryPathInfo(Abstract, IBrowsablePathInfo):
    def __init__(self, entry: IDirEntry) -> None:
        super().__init__()

        self.__entry: IDirEntry = entry
        self.__nameInfo: IBrowsableNameInfo = DirEntryNameInfo(entry)
    
    @final
    def GetDirectory(self) -> str: return self.__entry.GetDirectory()
    @final
    def GetNameInfo(self) -> IBrowsableNameInfo: return self.__nameInfo
    
    @final
    def GetPath(self) -> str: return self.__entry.GetPath()
    
    @final
    def GetSeparator(self) -> str: return pathsep

@final
class _BrowsableUpdater(BrowsableUpdater[IDirEntry]):
    def __init__(self, items: IEnumerable[IDirEntry], updater: Method[IFunction[ISortedList[IExplorable]]]) -> None: super().__init__(items, updater)
    
    def _Select(self, item: IDirEntry) -> IExplorable:
        return BrowsableDirEntry(item)

class BrowsableDirEntry(Browsable[IDirEntry]):
    def __init__(self, entry: IDirEntry) -> None:
        super().__init__(entry)

        self.__pathInfo: IBrowsablePathInfo = DirEntryPathInfo(entry)
    
    @final
    def _AsContainer(self, container: IDirEntry) -> IEnumerable[IDirEntry]:
        return container
    
    @final
    def _CreateUpdater(self, items: IEnumerable[IDirEntry], updater: Method[IFunction[ISortedList[IExplorable]]]) -> BrowsableUpdater[IDirEntry]:
        return _BrowsableUpdater(items, updater)
    
    @final
    def GetPathInfo(self) -> IBrowsablePathInfo: return self.__pathInfo