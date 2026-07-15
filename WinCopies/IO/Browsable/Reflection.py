from pkgutil import ModuleInfo as ModuleInfoBase
from types import ModuleType
from typing import final

from WinCopies import Abstract
from WinCopies.Collections.Enumeration import IEnumerable, CreateIteratorProvider
from WinCopies.Collections.Extensions import ISortedList
from WinCopies.IO.Browsable import BrowsableUpdater, IBrowsableNameInfo, IBrowsablePathInfo, IExplorable, BrowsableBase, BrowsableNameInfo
from WinCopies.Typing.Delegate import IFunction, Method
from WinCopies.Typing.Reflection.Extensions import ModuleInfo

class ReflectionNameInfo(BrowsableNameInfo):
    def __init__(self, name: str) -> None: super().__init__(name)

    @final
    def GetSeparator(self) -> str: return '.'

class ReflectionPathInfo(Abstract, IBrowsablePathInfo):
    def __init__(self, module: ModuleInfo) -> None:
        super().__init__()

        self.__module: ModuleInfo = module
        self.__nameInfo: IBrowsableNameInfo = ReflectionNameInfo(module.GetName())
    
    @final
    def GetDirectory(self) -> str: return self.__module.GetDirectory()
    @final
    def GetNameInfo(self) -> IBrowsableNameInfo: return self.__nameInfo
    
    @final
    def GetPath(self) -> str: return self.__module.GetPath()
    
    @final
    def GetSeparator(self) -> str: return '.'

@final
class _BrowsableUpdater(BrowsableUpdater[ModuleInfoBase]):
    def __init__(self, items: IEnumerable[ModuleInfoBase], updater: Method[IFunction[ISortedList[IExplorable]]]) -> None: super().__init__(items, updater)
    
    def _Select(self, item: ModuleInfoBase) -> IExplorable:
        return BrowsableReflectionEntry(item)

class BrowsableReflectionEntry(BrowsableBase[ModuleInfo, ModuleInfoBase]):
    def __init__(self, module: ModuleInfo|ModuleInfoBase|ModuleType|str) -> None:
        def getModuleInfo() -> ModuleInfo:
            match module:
                case ModuleInfo(): return module
                
                case ModuleInfoBase(): return ModuleInfo(module.name)
                
                case _: return ModuleInfo(module)
        
        module = getModuleInfo()

        super().__init__(module)

        self.__pathInfo: IBrowsablePathInfo = ReflectionPathInfo(module)
    
    @final
    def _AsContainer(self, container: ModuleInfo) -> IEnumerable[ModuleInfoBase]:
        return CreateIteratorProvider(container.EnumerateSubmodules)
    
    @final
    def _CreateUpdater(self, items: IEnumerable[ModuleInfoBase], updater: Method[IFunction[ISortedList[IExplorable]]]) -> BrowsableUpdater[ModuleInfoBase]:
        return _BrowsableUpdater(items, updater)
    
    @final
    def GetPathInfo(self) -> IBrowsablePathInfo: return self.__pathInfo