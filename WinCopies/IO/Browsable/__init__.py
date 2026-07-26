from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import Abstract
from WinCopies.Collections.Abstraction.Collection import SortedList
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator
from WinCopies.Collections.Enumeration.Recursive import IRecursivelyScannable, IRecursivelyEnumerable
from WinCopies.Collections.Enumeration.Recursive.Enumerable import RecursivelyEnumerable
from WinCopies.Collections.Extensions import ISortedList
from WinCopies.Collections.Iteration import Select
from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import IGenericConstraint
from WinCopies.Typing.Object import IComparableItem, String

def GetNameInfo(item: IBrowsable) -> IBrowsableNameInfo: return item.GetPathInfo().GetNameInfo()

def TryGetNameInfo(item: IBrowsableInfo|str|object) -> IBrowsableNameInfo|None:
    match item:
        case IBrowsableNameInfo(): return item
        case IBrowsablePathInfo(): return item.GetNameInfo()
        case IBrowsable(): return GetNameInfo(item)
        
        case _: return None

def TryGetName(item: IBrowsableInfo|str|object) -> str|None:
    name: IBrowsableNameInfo|None = TryGetNameInfo(item)

    return None if name is None else name.GetName()
def TryGetFullName(item: IBrowsableInfo|str|object) -> str|None:
    name: IBrowsableNameInfo|None = TryGetNameInfo(item)

    return None if name is None else name.GetFullName()

class IBrowsableInfo(IComparableItem[str]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetSeparator(self) -> str:
        ...

class IBrowsableNameInfo(IBrowsableInfo):
    def __init__(self) -> None: super().__init__()

    @final
    def _AsComparableValue(self) -> str: return self.GetFullName()
    
    @abstractmethod
    def GetName(self) -> str:
        ...
    @abstractmethod
    def GetExtension(self) -> str:
        ...

    def GetFullName(self) -> str: return f"{self.GetName()}{self.GetSeparator()}{self.GetExtension()}"
    
    def Equals(self, item: IBrowsableInfo|str|object) -> bool:
        return String.TryAreEqual(self.GetFullName(), TryGetFullName(item))
    def Hash(self) -> int: return hash(self.GetFullName())
    
    def _CompareTo(self, item: IBrowsableInfo|str|object) -> bool|None: return String.TryCompare(self.GetFullName(), TryGetFullName(item))

    def ToString(self) -> str: return self.GetFullName()

class BrowsableFullNameInfo(Abstract, IBrowsableNameInfo):
    def __init__(self, name: str, extension: str) -> None:
        super().__init__()

        self.__name: str = name
        self.__extension: str = extension
    
    @final
    def GetName(self) -> str: return self.__name
    @final
    def GetExtension(self) -> str: return self.__extension

class BrowsableNameInfoBase(Abstract, IBrowsableNameInfo):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetExtension(self) -> str: return ''
    
    @final
    def GetFullName(self) -> str: return self.GetName()
class BrowsableNameInfo(BrowsableNameInfoBase):
    def __init__(self, name: str) -> None:
        super().__init__()

        self.__name: str = name
    
    @final
    def GetName(self) -> str: return self.__name

class IBrowsablePathInfo(IBrowsableInfo):
    def __init__(self) -> None: super().__init__()

    @final
    def _AsComparableValue(self) -> str: return self.GetPath()

    @abstractmethod
    def GetDirectory(self) -> str:
        ...
    @abstractmethod
    def GetNameInfo(self) -> IBrowsableNameInfo:
        ...

    def GetPath(self) -> str:
        return f"{self.GetDirectory()}{self.GetSeparator()}{self.GetNameInfo().GetFullName()}"
    
    def Equals(self, item: IBrowsableInfo|str|object) -> bool:
        def equals(item: IBrowsablePathInfo) -> bool: return String.AreEqual(self.GetPath(), item.GetPath())
        
        match item:
            case IBrowsableNameInfo(): return self.GetNameInfo().Equals(item)
            case IBrowsablePathInfo(): return equals(item)
            case IBrowsable(): return equals(item.GetPathInfo())
            
            case _: return False
    def Hash(self) -> int: return hash(self.GetPath())
    
    def _CompareTo(self, item: IBrowsableInfo|str|object) -> bool|None:
        def compareTo(item: IBrowsablePathInfo) -> bool|None: return String.Compare(self.GetPath(), item.GetPath())
        
        match item:
            case IBrowsableNameInfo(): return self.GetNameInfo().CompareTo(item)
            case IBrowsablePathInfo(): return compareTo(item)
            case IBrowsable(): return compareTo(item.GetPathInfo())
            
            case _: return False
    
    def ToString(self) -> str: return self.GetPath()
class BrowsablePathInfo(Abstract, IBrowsablePathInfo):
    def __init__(self, directory: str, nameInfo: IBrowsableNameInfo) -> None:
        super().__init__()

        self.__directory: str = directory
        self.__nameInfo: IBrowsableNameInfo = nameInfo
    
    @final
    def GetDirectory(self) -> str: return self.__directory
    @final
    def GetNameInfo(self) -> IBrowsableNameInfo: return self.__nameInfo

class IBrowsable(IBrowsableInfo):
    def __init__(self) -> None: super().__init__()

    @final
    def _AsComparableValue(self) -> str: return self.GetPathInfo().GetPath()

    @abstractmethod
    def GetPathInfo(self) -> IBrowsablePathInfo:
        ...
    
    @final
    def GetSeparator(self) -> str: return self.GetPathInfo().GetSeparator()
    
    def Equals(self, item: IBrowsableInfo|str|object) -> bool:
        def getPathInfo() -> IBrowsablePathInfo: return self.GetPathInfo()
        
        def equals(item: IBrowsablePathInfo) -> bool: return getPathInfo().Equals(item)
        
        match item:
            case IBrowsableNameInfo(): return getPathInfo().GetNameInfo().Equals(item)
            case IBrowsablePathInfo(): return equals(item)
            case IBrowsable(): return equals(item.GetPathInfo())
            
            case _: return False
    def Hash(self) -> int: return hash(self.GetPathInfo().GetPath())
    
    def _CompareTo(self, item: IBrowsableInfo|str|object) -> bool|None:
        def getPathInfo() -> IBrowsablePathInfo: return self.GetPathInfo()
        
        def compareTo(item: IBrowsablePathInfo) -> bool|None: return getPathInfo().CompareTo(item.GetPath())
        
        match item:
            case IBrowsableNameInfo(): return getPathInfo().GetNameInfo().CompareTo(item)
            case IBrowsablePathInfo(): return compareTo(item)
            case IBrowsable(): return compareTo(item.GetPathInfo())
            
            case _: return False
    
    def ToString(self) -> str: return self.GetPathInfo().GetPath()
class IBrowsableObject[T](IBrowsable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetInnerObject(self) -> T:
        ...

class IScannable(IRecursivelyScannable["IScannable"], IBrowsable):
    def __init__(self) -> None: super().__init__()
class IScannableObject[T](IScannable, IBrowsableObject[T]):
    def __init__(self) -> None: super().__init__()

class IExplorable(IRecursivelyEnumerable["IExplorable"], IBrowsable):
    def __init__(self) -> None: super().__init__()
class IExplorableObject[T](IExplorable, IBrowsableObject[T]):
    def __init__(self) -> None: super().__init__()

class BrowsableUpdater[T](ValueFunctionUpdater[ISortedList[IExplorable]]):
    def __init__(self, items: IEnumerable[T], updater: Method[IFunction[ISortedList[IExplorable]]]) -> None:
        super().__init__(updater)

        self.__items: IEnumerable[T] = items
    
    @abstractmethod
    def _Select(self, item: T) -> IExplorable:
        ...
    
    def _GetValue(self) -> ISortedList[IExplorable]: return SortedList[IExplorable](Select(self.__items.AsIterable(), lambda item: self._Select(item)))

class BrowsableAbstract[T](RecursivelyEnumerable[IExplorable], IExplorableObject[T]):
    def __init__(self, innerObject: T) -> None:
        super().__init__()

        self.__innerObject: T = innerObject
    
    @final
    def GetInnerObject(self) -> T: return self.__innerObject

    @abstractmethod
    def _GetItems(self) -> ISortedList[IExplorable]:
        ...
    
    @final
    def _AsRecursivelyEnumerable(self, container: IExplorable) -> IEnumerable[IExplorable]:
        return container
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[IExplorable]|None: return self._GetItems().TryGetEnumerator()
class BrowsableBase[TIn, TOut](BrowsableAbstract[TIn], IGenericConstraint[TIn, IEnumerable[TOut]]):
    def __init__(self, innerObject: TIn) -> None:
        def update(func: IFunction[ISortedList[IExplorable]]) -> None: self.__items = func
        
        super().__init__(innerObject)

        self.__items: IFunction[ISortedList[IExplorable]] = self._CreateUpdater(self._AsContainer(self.GetInnerObject()), update) # type: ignore[no-redef]
    
    @abstractmethod
    def _CreateUpdater(self, items: IEnumerable[TOut], updater: Method[IFunction[ISortedList[IExplorable]]]) -> BrowsableUpdater[TOut]:
        ...

    @final
    def _GetItems(self) -> ISortedList[IExplorable]:
        return self.__items.GetValue()
class Browsable[T](BrowsableBase[T, T], IExplorableObject[T]):
    def __init__(self, innerObject: T) -> None: super().__init__(innerObject)