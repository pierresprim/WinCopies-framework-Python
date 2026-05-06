from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import IStringable, Abstract
from WinCopies.Collections.Abstraction.Collection import SortedList
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator
from WinCopies.Collections.Enumeration.Recursive import IRecursivelyScannable, IRecursivelyEnumerable
from WinCopies.Collections.Enumeration.Recursive.Enumerable import RecursivelyEnumerable
from WinCopies.Collections.Extensions import ISortedList
from WinCopies.Collections.Iteration import Select
from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import IGenericConstraint
from WinCopies.Typing.Object import IComparableObject, String

def GetNameInfo(item: IBrowsable) -> IBrowsableNameInfo:
    return item.GetPathInfo().GetNameInfo()

def TryGetNameInfo(item: IBrowsable|IBrowsablePathInfo|IBrowsableNameInfo|object) -> IBrowsableNameInfo|None:
    match item:
        case IBrowsableNameInfo():
            return item
        case IBrowsablePathInfo():
            return item.GetNameInfo()
        case IBrowsable():
            return GetNameInfo(item)
        
        case _:
            return None

def TryGetName(item: IBrowsable|IBrowsablePathInfo|IBrowsableNameInfo|object) -> str|None:
    name: IBrowsableNameInfo|None = TryGetNameInfo(item)

    return None if name is None else name.GetName()
def TryGetFullName(item: IBrowsable|IBrowsablePathInfo|IBrowsableNameInfo|object) -> str|None:
    name: IBrowsableNameInfo|None = TryGetNameInfo(item)

    return None if name is None else name.GetFullName()

class IBrowsableInfo(IComparableObject["IBrowsable|IBrowsablePathInfo|IBrowsableNameInfo"], IStringable):
    def __init__(self) -> None:
        super().__init__()

class IBrowsableNameInfo(IBrowsableInfo):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetName(self) -> str:
        pass
    @abstractmethod
    def GetExtension(self) -> str:
        pass

    def GetFullName(self) -> str:
        return f"{self.GetName()}.{self.GetExtension()}"
    
    def Equals(self, item: IBrowsable|IBrowsablePathInfo|IBrowsableNameInfo|object) -> bool:
        return String.TryAreEqual(self.GetFullName(), TryGetFullName(item))
    
    def CompareTo(self, item: IBrowsable|IBrowsablePathInfo|IBrowsableNameInfo|object) -> bool|None:
        return String.TryCompare(self.GetFullName(), TryGetFullName(item))

    def ToString(self) -> str:
        return self.GetFullName()
    
    def Hash(self) -> int:
        return hash(self.GetFullName())

class BrowsableFullNameInfo(Abstract, IBrowsableNameInfo):
    def __init__(self, name: str, extension: str) -> None:
        super().__init__()

        self.__name: str = name
        self.__extension: str = extension
    
    @final
    def GetName(self) -> str:
        return self.__name
    @final
    def GetExtension(self) -> str:
        return self.__extension

class BrowsableNameInfoBase(Abstract, IBrowsableNameInfo):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def GetExtension(self) -> str:
        return ''
    
    @final
    def GetFullName(self) -> str:
        return self.GetName()
class BrowsableNameInfo(BrowsableNameInfoBase):
    def __init__(self, name: str) -> None:
        super().__init__()

        self.__name: str = name
    
    @final
    def GetName(self) -> str:
        return self.__name

class IBrowsablePathInfo(IBrowsableInfo):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def GetSeparator(self) -> str:
        pass

    @abstractmethod
    def GetDirectory(self) -> str:
        pass
    @abstractmethod
    def GetNameInfo(self) -> IBrowsableNameInfo:
        pass

    def GetPath(self) -> str:
        return f"{self.GetDirectory()}{self.GetSeparator()}{self.GetNameInfo().GetFullName()}"
    
    def Equals(self, item: IBrowsable|IBrowsablePathInfo|IBrowsableNameInfo|object) -> bool:
        def equals(item: IBrowsablePathInfo) -> bool:
            return String.AreEqual(self.GetPath(), item.GetPath())
        
        if isinstance(item, IBrowsableNameInfo):
            return self.GetNameInfo().Equals(item)
        if isinstance(item, IBrowsablePathInfo):
            return equals(item)
        if isinstance(item, IBrowsable):
            return equals(item.GetPathInfo())
        
        return False
    
    def CompareTo(self, item: IBrowsable|IBrowsablePathInfo|IBrowsableNameInfo|object) -> bool|None:
        def compareTo(item: IBrowsablePathInfo) -> bool|None:
            return String.Compare(self.GetPath(), item.GetPath())
        
        if isinstance(item, IBrowsableNameInfo):
            return self.GetNameInfo().CompareTo(item)
        if isinstance(item, IBrowsablePathInfo):
            return compareTo(item)
        if isinstance(item, IBrowsable):
            return compareTo(item.GetPathInfo())
        
        return False
    
    def ToString(self) -> str:
        return self.GetPath()
    
    def Hash(self) -> int:
        return hash(self.GetPath())
class BrowsablePathInfo(Abstract, IBrowsablePathInfo):
    def __init__(self, directory: str, nameInfo: IBrowsableNameInfo) -> None:
        super().__init__()

        self.__directory: str = directory
        self.__nameInfo: IBrowsableNameInfo = nameInfo
    
    @final
    def GetDirectory(self) -> str:
        return self.__directory
    @final
    def GetNameInfo(self) -> IBrowsableNameInfo:
        return self.__nameInfo

class IBrowsable(IBrowsableInfo):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def GetPathInfo(self) -> IBrowsablePathInfo:
        pass
    
    def Equals(self, item: IBrowsable|IBrowsablePathInfo|IBrowsableNameInfo|object) -> bool:
        def getPathInfo() -> IBrowsablePathInfo:
            return self.GetPathInfo()
        
        def equals(item: IBrowsablePathInfo) -> bool:
            return getPathInfo().Equals(item)
        
        if isinstance(item, IBrowsableNameInfo):
            return getPathInfo().GetNameInfo().Equals(item)
        if isinstance(item, IBrowsablePathInfo):
            return equals(item)
        if isinstance(item, IBrowsable):
            return equals(item.GetPathInfo())
        
        return False
    
    def CompareTo(self, item: IBrowsable|IBrowsablePathInfo|IBrowsableNameInfo|object) -> bool|None:
        def getPathInfo() -> IBrowsablePathInfo:
            return self.GetPathInfo()
        
        def compareTo(item: IBrowsablePathInfo) -> bool|None:
            return getPathInfo().CompareTo(item.GetPath())
        
        if isinstance(item, IBrowsableNameInfo):
            return getPathInfo().GetNameInfo().CompareTo(item)
        if isinstance(item, IBrowsablePathInfo):
            return compareTo(item)
        if isinstance(item, IBrowsable):
            return compareTo(item.GetPathInfo())
        
        return False
    
    def ToString(self) -> str:
        return self.GetPathInfo().GetPath()
    
    def Hash(self) -> int:
        return hash(self.GetPathInfo().GetPath())
class IBrowsableObject[T](IBrowsable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetInnerObject(self) -> T:
        pass

class IScannable(IRecursivelyScannable["IScannable"], IBrowsable):
    def __init__(self) -> None:
        super().__init__()
class IScannableObject[T](IScannable, IBrowsableObject[T]):
    def __init__(self) -> None:
        super().__init__()

class IExplorable(IRecursivelyEnumerable["IExplorable"], IBrowsable):
    def __init__(self) -> None:
        super().__init__()
class IExplorableObject[T](IExplorable, IBrowsableObject[T]):
    def __init__(self) -> None:
        super().__init__()

class BrowsableUpdater[T](ValueFunctionUpdater[ISortedList[IExplorable]]):
    def __init__(self, items: IEnumerable[T], updater: Method[IFunction[ISortedList[IExplorable]]]) -> None:
        super().__init__(updater)

        self.__items: IEnumerable[T] = items
    
    @abstractmethod
    def _Select(self, item: T) -> IExplorable:
        pass
    
    def _GetValue(self) -> ISortedList[IExplorable]:
        return SortedList[IExplorable](Select(self.__items.AsIterable(), lambda item: self._Select(item)))

class BrowsableAbstract[T](RecursivelyEnumerable[IExplorable], IExplorableObject[T]):
    def __init__(self, innerObject: T) -> None:
        super().__init__()

        self.__innerObject: T = innerObject
    
    @final
    def GetInnerObject(self) -> T:
        return self.__innerObject

    @abstractmethod
    def _GetItems(self) -> ISortedList[IExplorable]:
        pass
    
    @final
    def _AsRecursivelyEnumerable(self, container: IExplorable) -> IEnumerable[IExplorable]:
        return container
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[IExplorable]|None:
        return self._GetItems().TryGetEnumerator()
    
    def CompareTo(self, item: IBrowsable|IBrowsablePathInfo|IBrowsableNameInfo|object) -> bool|None:
        return self.GetPathInfo().CompareTo(item)
class BrowsableBase[TIn, TOut](BrowsableAbstract[TIn], IGenericConstraint[TIn, IEnumerable[TOut]]):
    def __init__(self, innerObject: TIn) -> None:
        def update(func: IFunction[ISortedList[IExplorable]]) -> None:
            self.__items = func
        
        super().__init__(innerObject)

        self.__items: IFunction[ISortedList[IExplorable]] = self._CreateUpdater(self._AsContainer(self.GetInnerObject()), update) # type: ignore[no-redef]
    
    @abstractmethod
    def _CreateUpdater(self, items: IEnumerable[TOut], updater: Method[IFunction[ISortedList[IExplorable]]]) -> BrowsableUpdater[TOut]:
        pass

    @final
    def _GetItems(self) -> ISortedList[IExplorable]:
        return self.__items.GetValue()
class Browsable[T](BrowsableBase[T, T], IExplorableObject[T], IGenericConstraint[T, IEnumerable[T]]):
    def __init__(self, innerObject: T) -> None:
        super().__init__(innerObject)